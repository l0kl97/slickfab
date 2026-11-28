#!/usr/bin/env python3
"""Auszug aus einem Pressure-Lauf: python3 auszug.py <lauf-ordner> [--ablage <ordner> --root <slickfab>]

Liest transcript.jsonl (claude -p --output-format stream-json), start-commit, repo/ und
linear.json.calls und schreibt daneben:
- ergebnis.md: die letzte Nachricht der Rolle, Kosten und Züge
- befehle.md: jeder Werkzeugaufruf in Reihenfolge (Name und Eingabe)
- nachher.md: Commits seit dem Start, Arbeitsbaum, geänderte Dateien, Diff, Tracker-Schreibzugriffe

Mit --ablage legt es den Lauf zum Einchecken ab: die drei Dateien, lauf.md (Laufparameter plus
Kosten) und transkript.md (Transkript ohne Systemzeilen, jeder Block gekürzt). Alles bereinigt:
Lauf-Ordner, slickfab-Checkout und Home-Ordner werden zu <lauf>, <slickfab> und ~, Temp-Pfade zu
<tmp>, der lokale Nutzername zu <nutzer>, der Rechnername zu <rechner>, Mailadressen zu <mail>, bekannte
Schlüsselformate zu <geheim>.
"""
import functools
import json
import os
import re
import shutil
import socket
import subprocess
import sys

KUERZE_TEXT = 1500
KUERZE_WERKZEUG = 600
SECRET_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_-]{10,}", r"sk-[A-Za-z0-9]{20,}", r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}", r"lin_(?:api|oauth)_[A-Za-z0-9]{20,}", r"xox[abposr]-[A-Za-z0-9-]{10,}",
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]


def git(repo, *args):
    # Dateien im Wegwerf-Repo können jede Kodierung haben; nie an einem Diff sterben.
    res = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return res.stdout.strip() if res.returncode == 0 else "(git: %s)" % res.stderr.strip()


def events(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def nutzernamen():
    """Login und Name des Home-Ordners; zu kurze Namen nicht, sonst träfe es gewöhnliche Wörter."""
    import getpass
    names = set()
    try:
        names.add(getpass.getuser())
    except (KeyError, OSError):
        pass
    names.add(os.path.basename(os.path.expanduser("~")))
    return sorted(n for n in names if n and len(n) >= 3)


def kurze_logins():
    """Login und Home-Ordner unter 3 Zeichen: nur an Stellen ersetzt, an denen sie sicher der Nutzer sind."""
    import getpass
    names = set()
    try:
        names.add(getpass.getuser())
    except (KeyError, OSError):
        pass
    names.add(os.path.basename(os.path.expanduser("~")))
    return sorted(n for n in names if n and len(n) < 3)


# Computer- und LocalHostName von macOS; gelesen statt über `scutil`, das unter Last hängen kann.
SYSTEMKONFIG = "/Library/Preferences/SystemConfiguration/preferences.plist"


@functools.lru_cache(maxsize=None)
def rechnernamen():
    """Hostname lang und kurz, unter macOS auch ComputerName und LocalHostName; längste zuerst.

    Gibt es die Systemkonfiguration, lässt sie sich aber nicht lesen, bricht der Auszug ab: lieber
    keine Ablage (die Rohdaten bleiben, der Auszug lässt sich wiederholen) als eine mit Rechnernamen."""
    import plistlib
    names = set()
    try:
        lang = socket.gethostname()
        names.update((lang, lang.split(".")[0]))
    except OSError:
        pass
    if os.path.exists(SYSTEMKONFIG):
        try:
            with open(SYSTEMKONFIG, "rb") as f:
                system = plistlib.load(f).get("System") or {}
            names.add((system.get("System") or {}).get("ComputerName") or "")
            names.add(((system.get("Network") or {}).get("HostNames") or {}).get("LocalHostName") or "")
        except (OSError, ValueError, AttributeError, plistlib.InvalidFileException) as e:
            sys.exit("auszug: Rechnername nicht lesbar aus %s (%s); Abbruch, damit er nicht in die Ablage gerät"
                     % (SYSTEMKONFIG, e))
    names = {n for n in names if isinstance(n, str) and len(n) >= 3 and n.lower() != "localhost"}
    return sorted(names, key=lambda n: (-len(n), n))


_LS_ZEILE = re.compile(r"^([-bcdlps][rwxsStT-]{9}[@+.]?\s+\d+\s+)(\S+)(\s+)(\S+)(?=\s)", re.M)


def bereinige(text, run, root):
    for path, ersatz in ((os.path.realpath(run), "<lauf>"), (run, "<lauf>"),
                         (os.path.realpath(root), "<slickfab>"), (root, "<slickfab>"),
                         (os.path.expanduser("~"), "~")):
        if path and path not in ("/", "~"):
            text = text.replace(path, ersatz)
    text = re.sub(r"(?:/private)?/var/folders/[^\s\"'`)]+", "<tmp>", text)
    text = re.sub(r"(?:/private)?/tmp/[^\s\"'`)]+", "<tmp>", text)
    text = re.sub(r"/(?:Users|home)/[^/\s\"'`)]+", "~", text)
    # Rechnername (Prompt, `hostname`, `scutil`) vor dem Nutzer, egal in welcher Schreibweise.
    for name in rechnernamen():
        text = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(name), "<rechner>", text, flags=re.I)
    # Ein kurzer Login träfe als Wort gewöhnliche Wörter; ersetzt nur als Besitzer/Gruppe in `ls -l`
    # und vor dem @ eines Prompts.
    kurz_ = kurze_logins()
    if kurz_:
        text = _LS_ZEILE.sub(lambda m: m.group(1) + ("<nutzer>" if m.group(2) in kurz_ else m.group(2))
                             + m.group(3) + ("<nutzer>" if m.group(4) in kurz_ else m.group(4)), text)
        for name in kurz_:
            text = re.sub(r"(?<![\w.-])%s(?=@)" % re.escape(name), "<nutzer>", text)
    # Der lokale Nutzer steht ohne Pfad etwa als Besitzer in `ls -l`; als ganzes Wort ersetzen.
    for name in nutzernamen():
        text = re.sub(r"\b%s\b" % re.escape(name), "<nutzer>", text)
    for pat in SECRET_PATTERNS:
        text = re.sub(pat, "<geheim>", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@(?!example\.invalid\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<mail>", text)
    return text


def kurz(text, n):
    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    return text if len(text) <= n else text[:n] + " …[gekürzt, %d Zeichen]" % len(text)


_kurz = kurz


def transkript(run, root=""):
    """Transkript ohne Systemzeilen; jeder Block wird erst bereinigt, dann gekürzt."""
    def kurz(text, n):
        text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        return _kurz(bereinige(text, run, root), n)
    out = ["# Transkript (gekürzt, ohne Systemzeilen)", ""]
    for ev in events(os.path.join(run, "transcript.jsonl")):
        typ = ev.get("type")
        if typ == "assistant":
            for b in (ev.get("message") or {}).get("content") or []:
                if b.get("type") == "text":
                    out.append("**Rolle:** " + kurz(b.get("text", ""), KUERZE_TEXT))
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    shown = inp.get("command") if b.get("name") == "Bash" else inp
                    out.append("**Werkzeug %s:** %s" % (b.get("name"), kurz(shown, KUERZE_WERKZEUG)))
        elif typ == "user":
            content = (ev.get("message") or {}).get("content")
            for b in content if isinstance(content, list) else []:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    if isinstance(c, list):
                        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                    out.append("**Antwort:** " + kurz(c or "", KUERZE_WERKZEUG))
        elif typ == "result":
            out.append("**Ende:** " + kurz(ev.get("result") or "", KUERZE_TEXT * 4))
        else:
            continue
        out.append("")
    return "\n".join(out) + "\n"


def ablegen(run, ablage, root, result):
    if os.path.isdir(ablage):
        shutil.rmtree(ablage)
    os.makedirs(ablage)
    for name in ("ergebnis.md", "befehle.md", "nachher.md", "lauf.md"):
        src = os.path.join(run, name)
        text = open(src, encoding="utf-8").read() if os.path.exists(src) else "(fehlt)\n"
        if name == "lauf.md" and result is not None:
            text += "- Kosten: %s USD · Züge: %s\n" % (result.get("total_cost_usd"), result.get("num_turns"))
        with open(os.path.join(ablage, name), "w", encoding="utf-8") as f:
            f.write(bereinige(text, run, root))
    with open(os.path.join(ablage, "transkript.md"), "w", encoding="utf-8") as f:
        f.write(bereinige(transkript(run, root), run, root))


def main(run, ablage=None, root=None):
    if not os.path.isdir(run):
        sys.exit("Lauf-Ordner fehlt: %s" % run)
    # Mit --root wird vor jedem Kürzen bereinigt, damit kein Pfad an der Schnittkante übrig bleibt.
    san = (lambda t: bereinige(t, run, root)) if root else (lambda t: t)
    result, calls = None, []
    for ev in events(os.path.join(run, "transcript.jsonl")):
        if ev.get("type") == "result":
            result = ev
        elif ev.get("type") == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_use":
                    calls.append((block.get("name"), block.get("input")))

    with open(os.path.join(run, "ergebnis.md"), "w", encoding="utf-8") as f:
        if result is None:
            f.write("(kein Ergebnis im Transkript: Lauf abgebrochen? stderr.log ansehen)\n")
        else:
            f.write("Kosten: %s USD · Züge: %s\n\n" % (result.get("total_cost_usd"), result.get("num_turns")))
            f.write((result.get("result") or "(leer)") + "\n")

    with open(os.path.join(run, "befehle.md"), "w", encoding="utf-8") as f:
        for i, (name, inp) in enumerate(calls, 1):
            if name == "Bash":
                shown = (inp or {}).get("command", "")
            else:
                shown = json.dumps(inp, ensure_ascii=False)
            f.write("%d. %s: %s\n" % (i, name, san(shown)[:2000]))
        if not calls:
            f.write("(keine Werkzeugaufrufe)\n")

    repo = os.path.join(run, "repo")
    start = ""
    if os.path.exists(os.path.join(run, "start-commit")):
        with open(os.path.join(run, "start-commit"), encoding="utf-8") as f:
            start = f.read().strip()
    tracker = os.path.join(run, "linear.json.calls")
    writes = ""
    if os.path.exists(tracker):
        with open(tracker, encoding="utf-8") as f:
            writes = f.read().strip()
    with open(os.path.join(run, "nachher.md"), "w", encoding="utf-8") as f:
        refs = [start] if start else []
        start_of = {}  # Branch -> Stand nach setup.sh
        refs_file = os.path.join(run, "start-refs")
        if os.path.exists(refs_file):  # alle Branches nach setup.sh: deren Commits gab es schon
            with open(refs_file, encoding="utf-8") as rf:
                for line in rf:
                    teile = line.split()
                    if teile:
                        refs.append(teile[0])
                        if len(teile) > 1:
                            start_of[teile[1]] = teile[0]
        commits = git(repo, "log", "--all", "--oneline", "--not", *refs) if refs else git(repo, "log", "--all", "--oneline")
        f.write("## Commits seit dem Start\n%s\n\n" % (commits or "keine"))
        f.write("## Arbeitsbaum\n%s\n\n" % (git(repo, "status", "--short", "--untracked-files=all") or "sauber"))
        f.write("## Geänderte Dateien seit dem Start\n")
        if start:
            f.write("Arbeitsbaum gegen Start:\n%s\n" % (git(repo, "diff", "--stat", start) or "keine"))
            for ref in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").split("\n"):
                if ref:
                    f.write("Branch %s gegen seinen Stand beim Start:\n%s\n" % (
                        ref, git(repo, "diff", "--stat", start_of.get(ref, start), ref) or "keine"))
        f.write("\n")
        f.write("## Tracker-Schreibzugriffe\n%s\n" % (writes or "keine"))
        if start:
            diff = git(repo, "diff", start)
            for ref in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").split("\n"):
                if ref:
                    d = git(repo, "diff", start_of.get(ref, start), ref)
                    if d:
                        diff += "\n# Branch %s\n%s" % (ref, d)
            f.write("\n## Diff seit dem Start (gekürzt)\n```diff\n%s\n```\n" % (kurz(san(diff.strip()), 6000) or "keiner"))

    if ablage:
        ablegen(run, ablage, root or "", result)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--ablage")
    ap.add_argument("--root")
    a = ap.parse_args()
    main(a.run, a.ablage, a.root)
