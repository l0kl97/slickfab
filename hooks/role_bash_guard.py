#!/usr/bin/env python3
"""PreToolUse-Wächter für Bash in den prüfenden Rollen reviewer, verifier und retro.

Die Rollen brauchen Bash für Prüfbefehle. `disallowedTools` sperrt Edit/Write, aber nicht
die Shell. Der Wächter lässt in genau diesen drei Rollen nur freigegebene Programme zu
(Allowlist: Lesewerkzeuge, git/gh-Unterbefehle, Prüfbefehle des Projekts, Skripte und
Tests im Worktree) und jedes Schreiben nur im Worktree der Session.

Er zerlegt den Befehl selbst wie die Shell. Was er nicht sicher versteht (Ersetzung,
Variablen, Subshell, Heredoc, Kommentar, Zeilenumbruch), lehnt er ab. Andere Agents und
die Hauptsession lässt er immer durch. Gestartet wird er über hooks/guard_start.py.

Ein: Hook-JSON auf stdin. Aus: bei Verbot ein JSON mit permissionDecision deny, Exit 0.
Nur Standardbibliothek, läuft mit Python 3.9.
"""
import importlib.machinery
import json
import os
import re
import sys
import sysconfig
import unicodedata

ROLES = ("slickfab:reviewer", "slickfab:verifier", "slickfab:retro")
RULE = ("Prüfende Rolle (reviewer, verifier, retro): Bash darf das Repo nicht dauerhaft ändern "
        "und nichts nach außen schicken (kein git push, git commit, git merge, gh pr merge, "
        "keine Freigabe) und nicht außerhalb des Worktrees der Session schreiben. Erlaubt sind "
        "Prüfbefehle, die Mutationsprobe im Worktree, `git checkout -- <datei>` und "
        "`gh pr review --comment`. Abgelehnt, weil: %s")


class Unsafe(Exception):
    """Befehl ist verboten oder nicht sicher zu verstehen."""


# --- Zerlegen wie die Shell -------------------------------------------------------------

class Word:
    def __init__(self):
        self.text = ""
        self.glob = False      # ungequotetes * ? [
        self.started = False   # auch "" ist ein Wort


def lex(command):
    """Liefert Segmente [(wörter, umleitungen, trenner)], getrennt an ; & | && ||.
    trenner ist der Operator nach dem Segment, am Befehlsende "".

    Zeilenumbruch und # außerhalb von Anführungszeichen lehnt er ab: Ein Kommentar endet am
    Zeilenende, und ein ' oder " darin verschiebt sonst die Zerlegung (Review PR #15, A1.1)."""
    if any((ord(c) < 32 and c not in "\t\n\r") or 0xD800 <= ord(c) <= 0xDFFF or ord(c) == 127
           for c in command):
        raise Unsafe("Steuerzeichen oder ungültiges Zeichen im Befehl")
    segments, words, redirects = [], [], []
    word, pending = Word(), None   # pending: Umleitung, die auf ihr Ziel wartet
    i, n = 0, len(command)

    def finish():
        nonlocal word, pending
        if word.started:
            if pending is not None:
                redirects.append((pending, word))
                pending = None
            else:
                words.append(word)
        word = Word()

    def end_segment(sep):
        nonlocal words, redirects
        finish()
        if pending is not None:
            raise Unsafe("Umleitung ohne Ziel")
        segments.append((words, redirects, sep))
        words, redirects = [], []

    while i < n:
        c = command[i]
        if c in " \t":
            finish()
        elif c in "\n\r#":
            raise Unsafe("Zeilenumbruch oder # außerhalb von Anführungszeichen")
        elif c in ";&|":
            if c == "&" and command[i + 1:i + 2] == ">":   # &> datei
                finish()
                pending = "&>"
                i += 2
                if command[i:i + 1] == ">":
                    i += 1
                if command[i:i + 1] == "!":   # zsh: &>! wie &>|
                    i += 1
                continue
            sep = command[i:i + 2] if command[i:i + 2] in ("&&", "||", "|&") else c
            end_segment(sep)
            i += len(sep) - 1
        elif c in "<>":
            if word.started and word.text.isdigit() and not word.glob:
                word = Word()          # 2> datei: die Zahl ist der Kanal, kein Wort
            finish()
            if pending is not None:
                raise Unsafe("Umleitung ohne Ziel")
            op = c
            nxt = command[i + 1:i + 2]
            if c == "<" and nxt in ("<", ">", "("):
                raise Unsafe("Heredoc, Here-String oder Prozessersetzung")
            if c == ">" and nxt == "(":
                raise Unsafe("Prozessersetzung")
            if nxt in (">", "|", "&") and c == ">":
                op += nxt
                i += 1
            elif c == "<" and nxt == "&":
                op += nxt
                i += 1
            if c == ">" and command[i + 1:i + 2] == "!":   # zsh: >! und >>! wie >|
                op += "!"
                i += 1
            pending = op
        elif c in "()":
            raise Unsafe("Subshell oder Klammern")
        elif c in "{}":
            raise Unsafe("geschweifte Klammern (Gruppierung oder Klammerexpansion)")
        elif c in "$`":
            raise Unsafe("Variable oder Befehlsersetzung")
        elif c == "=" and not word.started:
            raise Unsafe("Wort beginnt mit = (zsh-Pfadersetzung)")
        elif c == "~":
            if not word.started and command[i + 1:i + 2] in ("", "/", " ", "\t", ";", "&", "|"):
                word.text += os.path.expanduser("~")
                word.started = True
            elif not word.started or word.text[-1:] in ("=", ":"):
                raise Unsafe("Tilde-Expansion")
            else:
                word.text += c
        elif c == "\\":
            if i + 1 >= n or command[i + 1] in "\n\r#":
                raise Unsafe("Backslash am Ende, vor Zeilenumbruch oder vor #")
            word.text += command[i + 1]
            word.started = True
            i += 1
        elif c == "'":
            j = command.find("'", i + 1)
            if j < 0:
                raise Unsafe("Anführungszeichen nicht geschlossen")
            word.text += command[i + 1:j]
            word.started = True
            i = j
        elif c == '"':
            i += 1
            while True:
                if i >= n:
                    raise Unsafe("Anführungszeichen nicht geschlossen")
                d = command[i]
                if d == '"':
                    break
                if d in "$`":
                    raise Unsafe("Variable oder Befehlsersetzung")
                if d == "\\" and i + 1 < n and command[i + 1] in '$`"\\\n':
                    if command[i + 1] != "\n":
                        word.text += command[i + 1]
                    i += 2
                    continue
                word.text += d
                i += 1
            word.started = True
        else:
            if c in "*?[":
                word.glob = True
            word.text += c
            word.started = True
        i += 1
    end_segment("")
    return segments


# --- Pfade -------------------------------------------------------------------------------

class Paths:
    def __init__(self, root):
        self.root = os.path.realpath(root)

    def resolve(self, path, cwd):
        return os.path.realpath(os.path.join(cwd, path))

    def is_inside(self, real):
        if real != self.root and not real.startswith(self.root + os.sep):
            return False
        return ".git" not in os.path.relpath(real, self.root).split(os.sep)

    def inside(self, word, cwd, what):
        """Pfad muss im Worktree liegen (nicht unter .git); Globs werden nicht geraten."""
        text = word.text if isinstance(word, Word) else word
        if isinstance(word, Word) and word.glob:
            raise Unsafe("Platzhalter in einem Schreibziel (%s)" % text)
        real = self.resolve(text, cwd)
        if not self.is_inside(real):
            raise Unsafe("%s außerhalb des Worktrees oder unter .git: %s" % (what, text))
        return real


# --- Regeln je Programm ------------------------------------------------------------------
# Allowlist (Entscheidung des Masters, Rework 1 von PR #15): Eine Sperrliste blieb offen (zsh-
# Vorbefehle, Programm-Starter, Schreibwerkzeuge). Erlaubt ist nur, was hier steht; das
# erste Wort jedes Teilbefehls muss genau einer dieser Namen sein, ohne Pfad.

READ_TOOLS = {"cat", "ls", "grep", "rg", "sed", "head", "tail", "wc", "diff", "find", "sort",
              "uniq", "cut", "tr", "jq", "stat", "file", "pwd", "echo", "printf", "test", "["}
GLOB_OK = {"cat", "ls", "grep", "head", "tail", "wc", "stat", "file", "diff", "echo", "printf"}
TEST_MODULES = {"unittest", "pytest", "doctest"}
PY_FLAGS = "BbdIOqSsuvx"   # Python-Schalter ohne Argument
FIND_ACTIONS = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0",
                "-fprintf", "-fls"}
# Optionen mit getrenntem Wert, der ein Schreibziel ist (Wert hinter "=" zählt ebenso)
# Optionen von sort, uniq und sed als Allowlist (Pre-Push-Review zu Rework 1): getopt_long
# nimmt gebündelte Kurzschalter (-ro x) und abgekürzte lange Namen (--out=x) an. Erlaubt sind
# nur diese Schalter, lange Namen nur ausgeschrieben; eine Ausgabedatei gibt es nicht, die
# Ausgabe geht per Umleitung (die der Wächter prüft).
#   (Schalter ohne Wert, Schalter mit Wert, lange Namen ohne Wert, lange Namen mit Wert)
STRICT = {
    "sort": ("bdfghinrsuVMRcz", "kt", {"--reverse", "--numeric-sort", "--unique",
             "--ignore-case", "--version-sort", "--human-numeric-sort", "--stable",
             "--general-numeric-sort", "--dictionary-order", "--ignore-leading-blanks",
             "--month-sort", "--check", "--zero-terminated"}, {"--key", "--field-separator"}),
    "uniq": ("cdiuDz", "fsw", {"--count", "--repeated", "--ignore-case", "--unique",
             "--zero-terminated"}, {"--skip-fields", "--skip-chars", "--check-chars"}),
    "sed": ("nErsuz", "e", {"--quiet", "--silent", "--regexp-extended", "--separate",
            "--unbuffered", "--null-data", "--posix", "--sandbox", "--debug"}, {"--expression"}),
}
MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
# Ordner der Standardbibliothek (für Python 3.9 ohne sys.stdlib_module_names).
# Endungen, unter denen Python ein Modul findet (Quelle, Bytecode, Erweiterungsmodul).
MODULE_SUFFIXES = set(importlib.machinery.all_suffixes())
STDLIB_DIRS = sorted({sysconfig.get_paths()[k] for k in ("stdlib", "platstdlib")})
CHECK_KEY = re.compile(r'^(CHECK_[A-Z0-9_]+)="([^"]*)"\s*$')

GIT_READ = {"status", "diff", "log", "show", "rev-parse", "ls-files", "ls-tree", "grep",
            "blame", "merge-base", "cat-file", "rev-list", "describe", "shortlog",
            "ls-remote", "fetch", "diff-tree", "name-rev", "version"}
GIT_GLOBAL = {"--no-pager", "-P", "--no-optional-locks"}
GIT_BRANCH_READ = {"--show-current", "-a", "--all", "-r", "--remotes", "-v", "-vv",
                   "--verbose", "--list", "-l"}
GIT_CONFIG_READ = {"--get", "--get-all", "--get-regexp", "--list", "-l"}
GIT_RUNS_PROGRAM = ("--output", "--open-files-in-pager", "--upload-pack", "--receive-pack",
                    "--exec", "--ext-diff", "--textconv")

GH_READ = {"pr": {"view", "diff", "checks", "list", "status"},
           "issue": {"view", "list", "status"}, "repo": {"view"}, "run": {"view", "list"},
           "search": {"prs", "issues", "code", "commits", "repos"}}


class Checker:
    def __init__(self, root, cwd):
        self.paths = Paths(root)
        self.cwd = os.path.realpath(cwd)
        self.added = set()   # Pfade, die `git worktree add` in diesem Befehl davor anlegt
        if not self.paths.is_inside(self.cwd):
            raise Unsafe("Arbeitsverzeichnis liegt außerhalb des Worktrees")
        self.checks = project_checks(self.paths.root)

    def check(self, command):
        prev, moved = "", False
        for words, redirects, sep in lex(command):
            if moved and sep == "||":
                raise Unsafe("nach cd kein ||: scheitert cd, liefe der Rest im alten Verzeichnis")
            if words and words[0].text == "cd":
                if prev not in ("", "&&", ";") or sep not in ("&&", ""):
                    raise Unsafe("cd nur am Anfang oder nach && bzw. ; und nur vor && oder am Ende "
                                 "(in einer Pipeline oder im Hintergrund wirkt cd nicht)")
                moved = True
            prev = sep
            for op, target in redirects:
                if op in ("<", "<&"):
                    continue
                if op in (">&", "<&") and (target.text.isdigit() or target.text == "-"):
                    continue
                if target.text in ("/dev/null", "/dev/stdout", "/dev/stderr"):
                    continue
                self.not_fresh(self.paths.inside(target, self.cwd, "Umleitung"), target.text)
            if words:
                self.command([w.text for w in words], words)

    def command(self, argv, words):
        name, args = argv[0], argv[1:]
        if words[0].glob:
            raise Unsafe("Platzhalter im Programmnamen")
        if name not in GLOB_OK:
            cut = argv.index("--") if name == "git" and "--" in argv else len(argv)
            if any(w.glob for w in words[:cut]):
                raise Unsafe("Platzhalter bei `%s` (könnte zu einer Option oder einem "
                             "Unterbefehl werden)" % name)
        if name == "cd":      # nur das bloße Wort; chdir, pushd, /usr/bin/cd sind nicht frei
            return self.cd(args)
        if name == "git":
            return self.git(args)
        if name == "gh":
            return self.gh(args)
        if name in ("sh", "bash"):
            if not args or args[0].startswith("-"):
                raise Unsafe("Shell nur mit einer Skriptdatei, ohne -c oder stdin")
            self.paths.inside(args[0], self.cwd, "Skript")
            return self.paths_in_args(args[1:])
        if name == "python3":
            return self.python(args)
        if name == "pytest":
            return self.paths_in_args(args)
        if name == "node":
            if not args or args[0].startswith("-"):
                raise Unsafe("node nur mit einer Skriptdatei, ohne Optionen")
            self.paths.inside(args[0], self.cwd, "Skript")
            return self.paths_in_args(args[1:])
        if name == "npm" and args == ["test"]:
            return
        if argv in self.checks:
            # Prüfbefehl des Projekts, wörtlich aus der Konfiguration. Er schaltet nur
            # Programme ohne eigene Regel frei (make, cargo, npm run …); sh, python3 & Co.
            # bleiben geprüft, weil ein PR die Konfiguration ändern kann.
            return
        if name not in READ_TOOLS:
            raise Unsafe("`%s` ist in prüfenden Rollen nicht freigegeben (erlaubt: Lesewerkzeuge, "
                         "git/gh-Unterbefehle, Prüfbefehle des Projekts, sh/bash/python3/pytest/"
                         "node mit Ziel im Worktree, npm test)" % name)
        if name in STRICT:
            positional, values = strict_options(name, args)
            if name == "sed":
                scripts = values or positional[:1]
                if not scripts:
                    raise Unsafe("sed ohne Skript")
                for script in scripts:
                    sed_script_ok(script)
            if name == "uniq" and len(positional) > 1:
                raise Unsafe("uniq nur mit einer Eingabedatei; Ausgabe per Umleitung")
            return
        if name == "find" and FIND_ACTIONS.intersection(args):
            raise Unsafe("find mit -exec/-delete/-fprint")
        if name == "rg" and any(a.startswith("--pre") for a in args):
            raise Unsafe("rg --pre startet ein Programm")

    def cd(self, args):
        if len(args) != 1 or args[0] == "-":
            raise Unsafe("cd nur mit genau einem Ziel im Worktree")
        target = self.paths.inside(args[0], self.cwd, "cd-Ziel")
        # Ein Prüf-Worktree, den derselbe Befehl davor anlegt, existiert zur Prüfzeit noch nicht.
        # Scheitert das Anlegen, scheitert cd, und nach cd folgt nur && oder nichts.
        if not os.path.isdir(target) and target not in self.added:
            raise Unsafe("cd-Ziel ist kein vorhandener Ordner: %s" % args[0])
        self.cwd = target

    def python(self, args):
        seen = ""   # alle Schalter bis hier, auch aus früheren Wörtern (-I -m x)
        for k, a in enumerate(args):
            if a.startswith("--") or a == "-":
                raise Unsafe("python3 mit Option %s vor dem Skript" % a.split("=", 1)[0])
            if a.startswith("-"):
                # Nur Schalter ohne Argument; sonst hielte der Wächter das Argument
                # (-W ignore, -c code) für das Skript und sähe den Rest nicht mehr.
                flags = a[1:a.index("m")] if "m" in a[1:] else a[1:]
                if not set(flags) <= set(PY_FLAGS):
                    raise Unsafe("python3 mit Option %s vor dem Skript" % a)
                seen += flags
                if "m" in a[1:]:
                    module = a[a.index("m") + 1:]
                    rest = args[k + 1:]
                    if not module:
                        if not rest:
                            raise Unsafe("python3 -m ohne Modul")
                        module, rest = rest[0], rest[1:]
                    if module not in TEST_MODULES:
                        self.worktree_module(module, "I" in seen)
                    return self.paths_in_args(rest)
                continue
            # Erstes Nicht-Optionswort ist das Skript; es muss aus dem Worktree stammen.
            self.paths.inside(a, self.cwd, "Skript")
            return self.paths_in_args(args[k + 1:])
        raise Unsafe("python3 ohne Skriptdatei liest Code von stdin")

    def worktree_module(self, module, isolated):
        """`-m <modul>` außer den Testmodulen nur für ein Modul, das als Datei im Worktree liegt
        (CLI-Befehl aus der Spec, etwa `python3 -m reports.cli`). Das ist so viel wie ein
        Skript im Worktree. Python sucht bei -m zuerst im Arbeitsverzeichnis, eingebaute und
        eingefrorene Module aber nicht von dort; -I und PYTHONSAFEPATH nehmen das Arbeitsverzeichnis
        ganz aus dem Suchpfad. Dann wäre nicht sicher, was läuft. Namen der Standardbibliothek
        sperrt der Wächter zusätzlich, auch wo eine Datei im Worktree sie überschatten würde."""
        allowed = "python3 -m nur mit %s oder einem Modul, das als Datei im Worktree liegt" \
            % ", ".join(sorted(TEST_MODULES))
        if not MODULE_RE.match(module):
            raise Unsafe("%s; %r ist kein Modulname" % (allowed, module))
        top = module.split(".")[0]
        if top in sys.builtin_module_names or top in getattr(sys, "stdlib_module_names", ()) \
                or importlib.machinery.FrozenImporter.find_spec(top) is not None \
                or importlib.machinery.PathFinder.find_spec(top, STDLIB_DIRS) is not None:
            raise Unsafe("%s; %s gehört zur Standardbibliothek" % (allowed, top))
        if isolated or os.environ.get("PYTHONSAFEPATH"):
            raise Unsafe("%s; mit -I oder PYTHONSAFEPATH sucht Python nicht im Arbeitsverzeichnis" % allowed)
        if os.environ.get("PYTHONCASEOK"):
            raise Unsafe("%s; mit PYTHONCASEOK sucht Python ohne Groß/klein" % allowed)
        # Auflösen wie Pythons FileFinder (Review PR #22, A1): Auf jeder Stufe gibt es genau einen
        # Kandidaten, sonst ist unklar, welchen Python nimmt (Paket vor Erweiterungsmodul vor .py).
        # Pakete brauchen eine echte __init__.py (ein Namespace-Ordner verliert gegen ein
        # gleichnamiges installiertes Paket). Jede Datei, die Python dabei ausführt (jede
        # __init__.py, das Modul bzw. __main__.py), liegt per realpath im Worktree und ist kein
        # Symlink, ebenso jeder Paketordner und __pycache__.
        parts, folder = module.split("."), self.cwd
        for k, name in enumerate(parts):
            path = self.module_entry(folder, name, allowed)
            self.no_link_cache(folder, allowed)
            if os.path.isfile(path):
                if k < len(parts) - 1:
                    raise Unsafe("%s; %s ist kein Paket" % (allowed, name))
                return self.module_file(path, allowed)
            self.module_file(self.module_entry(path, "__init__", allowed), allowed)
            folder = path
        self.no_link_cache(folder, allowed)
        self.module_file(self.module_entry(folder, "__main__", allowed), allowed)

    def module_entry(self, folder, name, allowed):
        """Der eine Eintrag, den Python für name in folder nimmt: Paketordner oder name.py."""
        try:
            entries = os.listdir(folder)
        except OSError:
            raise Unsafe("%s; Ordner nicht lesbar" % allowed)
        found = [e for e in entries if e == name or (e.startswith(name) and e[len(name):] in MODULE_SUFFIXES)]
        if len(found) != 1:
            raise Unsafe("%s; für %s gibt es %s" % (allowed, name, "keine Datei" if not found
                                                       else "mehrere Kandidaten: " + ", ".join(sorted(found))))
        path = os.path.join(folder, found[0])
        if os.path.islink(path):
            raise Unsafe("%s; %s ist ein Symlink" % (allowed, found[0]))
        if found[0] == name + ".py" and os.path.isfile(path):
            return path
        if found[0] == name and os.path.isdir(path):
            return path
        raise Unsafe("%s; %s ist weder Paket mit __init__.py noch .py-Datei" % (allowed, found[0]))

    def module_file(self, path, allowed):
        """Eine Datei, die Python ausführt (Symlinks schließt module_entry schon aus)."""
        if not os.path.isfile(path):
            raise Unsafe("%s; %s ist keine echte Datei" % (allowed, path))
        self.paths.inside(path, self.cwd, "Modul")

    @staticmethod
    def no_link_cache(folder, allowed):
        """Kein Symlink als __pycache__ und keiner darin: Python lädt eine .pyc mit Unchecked-Hash
        ohne Abgleich mit der Quelle (Review PR #22, B1)."""
        cache = os.path.join(folder, "__pycache__")
        if os.path.islink(cache):
            raise Unsafe("%s; __pycache__ ist ein Symlink" % allowed)
        if os.path.isdir(cache):
            try:
                entries = os.listdir(cache)
            except OSError:
                raise Unsafe("%s; __pycache__ nicht lesbar" % allowed)
            if any(os.path.islink(os.path.join(cache, e)) for e in entries):
                raise Unsafe("%s; Symlink in __pycache__" % allowed)

    def not_fresh(self, real, text):
        """Kein Schreibziel in einem Worktree, den dieser Befehl erst anlegt (Security-Review):
        Seine Dateien gibt es zur Prüfzeit nicht, ein Symlink aus dem geprüften Commit
        (z -> ~/.zshrc) bliebe für realpath unsichtbar. Im nächsten Befehl sieht realpath ihn.
        Gilt auch, wenn der Ordner schon existiert: git legt Worktrees in leere Ordner."""
        # Vergleich ohne Groß/klein und Unicode-Normalform: macOS (APFS) unterscheidet beides
        # nicht, und realpath gleicht nicht vorhandene Pfade nicht an (Pre-Push-Review).
        key = fold(real)
        for fresh in map(fold, self.added):
            if key == fresh or key.startswith(fresh + os.sep):
                raise Unsafe("Schreibziel %s im gerade angelegten Worktree: erst im nächsten Befehl" % text)

    def paths_in_args(self, args):
        """Jedes Argument, das ein Pfad sein kann, muss im Worktree liegen: jedes
        Positionsargument (auch der Wert nach einer Schreib-Option wie --junitxml), der
        angehängte Wert kurzer Optionen und jeder Teil hinter jedem = (log_file=/x=1)."""
        prev = ""
        for a in args:
            if a.startswith("--"):
                candidates = []
            elif a.startswith("-"):
                candidates = [a[2:]] if len(a) > 2 else []
            else:
                candidates = [a]
            # Nicht nur hinter dem letzten =: "/x=1" ist ein Pfad, und "o=/x=1" enthält ihn.
            candidates += [a[k + 1:] for k, c in enumerate(a) if c == "="]
            # Mögliche Schreibziele: Werte von Optionen (angehängt, hinter =, oder das Wort direkt
            # nach einer langen Option wie --junitxml out.xml). Ein bloßes Positionsargument und
            # der Wert einer Kurzoption (-s tests) sind Ziele zum Lesen oder Ausführen und dürfen
            # auch im gerade angelegten Worktree liegen (Pressure-Nachlauf R2).
            option_value = a.startswith("-") or "=" in a or (prev.startswith("--") and "=" not in prev)
            for value in candidates:
                real = self.paths.inside(value, self.cwd, "Pfad in %s" % a)
                if option_value:
                    self.not_fresh(real, value)
            prev = a

    def git(self, args):
        cwd = self.cwd
        i = 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-C" and i + 1 < len(args):
                cwd = self.paths.inside(args[i + 1], cwd, "git -C")
                i += 2
            elif args[i] in GIT_GLOBAL:
                i += 1
            else:
                raise Unsafe("git-Option %s" % args[i])
        if i >= len(args):
            raise Unsafe("git ohne Unterbefehl")
        sub, rest = args[i], args[i + 1:]
        for a in rest:
            # git nimmt eindeutige Abkürzungen an (--outp=, --upload-p=): jeder Anfang eines
            # gefährlichen Namens zählt wie der Name selbst.
            stem = a.split("=", 1)[0]
            if a.startswith(GIT_RUNS_PROGRAM) or (sub == "grep" and a.startswith("-O")) or \
                    (len(stem) > 3 and any(d.startswith(stem) for d in GIT_RUNS_PROGRAM)):
                raise Unsafe("git-Option %s schreibt oder startet ein Programm" % a)
        if sub in ("fetch", "ls-remote"):
            for a in rest:
                if not a.startswith("-") and (":" in a or a.startswith((".", "/"))):
                    raise Unsafe("git %s nur mit benanntem Remote, ohne URL, Pfad oder "
                                 "Ziel-Refspec: %s" % (sub, a))
        if sub in GIT_READ:
            return
        if sub == "worktree":
            return self.git_worktree(rest, cwd)
        if sub == "checkout":
            return self.git_checkout(rest, cwd)
        if sub == "branch" and set(rest) <= GIT_BRANCH_READ:
            return
        if sub == "config" and rest and rest[0] in GIT_CONFIG_READ:
            return
        if sub == "remote" and (rest in ([], ["-v"]) or rest[:1] == ["get-url"]):
            return
        raise Unsafe("`git %s` ändert das Repo oder schickt etwas nach außen (z. B. git push, "
                     "git commit, git merge)" % sub)

    def git_worktree(self, rest, cwd):
        if rest in (["list"], ["prune"]) or rest[:1] == ["list"]:
            return
        if rest[:1] in (["add"], ["remove"]):
            options = {"add": {"--detach", "-f", "--force", "-q", "--quiet", "--no-checkout"},
                       "remove": {"-f", "--force"}}[rest[0]]
            positional = [a for a in rest[1:] if not a.startswith("-")]
            if any(a.startswith("-") and a not in options for a in rest[1:]) or not positional:
                raise Unsafe("git worktree %s mit unerwarteten Optionen" % rest[0])
            path = self.paths.inside(positional[0], cwd, "Worktree-Pfad")
            if rest[0] == "add":
                self.added.add(path)
            return
        raise Unsafe("git worktree %s" % " ".join(rest[:1]))

    def git_checkout(self, rest, cwd):
        if "--" not in rest:
            raise Unsafe("git checkout nur als `git checkout [<commit>] -- <datei>`")
        k = rest.index("--")
        before, files = rest[:k], rest[k + 1:]
        if len(before) > 1 or any(a.startswith("-") for a in before) or not files:
            raise Unsafe("git checkout nur als `git checkout [<commit>] -- <datei>`")
        for f in files:
            self.not_fresh(self.paths.inside(f, cwd, "git checkout Datei"), f)

    def gh(self, args):
        if len(args) < 2:
            raise Unsafe("gh ohne Unterbefehl")
        group, sub, rest = args[0], args[1], args[2:]
        if sub in GH_READ.get(group, ()):
            return
        if group == "pr" and sub in ("review", "comment"):
            self.gh_comment(rest)
        if group == "pr" and sub == "review":
            if not any(a in ("-c", "--comment") for a in rest):   # Freigabe: gh_comment
                raise Unsafe("gh pr review nur mit --comment, ohne Freigabe")
            return
        if group == "pr" and sub == "comment":
            return
        if group == "api":
            return self.gh_api(args[1:])
        raise Unsafe("`gh %s %s` ändert oder schickt etwas nach außen (z. B. gh pr merge)"
                     % (group, sub))

    def gh_comment(self, rest):
        """Kommentar nur am eigenen Repo und nur mit einer Textdatei aus dem Worktree."""
        skip = False
        for i, a in enumerate(rest):
            if skip:          # Wert von -b/--body: freier Text, darf eine URL enthalten
                skip = False
                continue
            if a in ("-b", "--body"):
                skip = True
                continue
            if a.startswith(("-R", "--repo")):
                raise Unsafe("Kommentar nur am Repo der Session, kein -R/--repo")
            if a.startswith(("--delete-last", "--edit-last")):
                raise Unsafe("gh pr comment: vorhandene Kommentare werden weder geändert noch gelöscht")
            if not a.startswith("-") and ("://" in a or "github.com" in a):
                raise Unsafe("Kommentar nur am Repo der Session, keine PR-URL: %s" % a)
            if a.startswith(("--approve", "--request-changes")) or \
                    (a.startswith("-") and not a.startswith("--") and set(a[1:]) & set("ar")):
                raise Unsafe("gh pr review nur mit --comment, ohne Freigabe")
            if a in ("-F", "--body-file"):
                value = rest[i + 1] if i + 1 < len(rest) else ""
            elif a.startswith("--body-file="):
                value = a.split("=", 1)[1]
            elif a.startswith("-F") and len(a) > 2:
                value = a[2:]
            else:
                continue
            if value != "-":
                self.paths.inside(value, self.cwd, "Textdatei")

    def gh_api(self, rest):
        for i, a in enumerate(rest):
            if a.startswith("--hostname"):
                raise Unsafe("gh api nur gegen github.com, kein --hostname")
            method = None
            if a in ("-X", "--method"):
                method = rest[i + 1] if i + 1 < len(rest) else ""
            elif a.startswith("--method="):
                method = a.split("=", 1)[1]
            elif a.startswith("-X") and len(a) > 2:
                method = a[2:]
            if method is not None and method.upper() != "GET":
                raise Unsafe("gh api nur lesend (GET)")
            if a.startswith(("-f", "-F", "--field", "--raw-field", "--input")):
                raise Unsafe("gh api mit Feldern sendet (POST)")


SED_FLAGS = set("gpiIM0123456789")


def fold(path):
    """Pfad so, wie ein Dateisystem ohne Groß/klein und mit Unicode-Normalisierung ihn sieht."""
    return unicodedata.normalize("NFC", path).casefold()


def sed_script_ok(script):
    """Nur s///, d, p, q, = mit Zeilen- oder Musteradresse: kein w (schreibt), kein e (Shell)."""
    i, n = 0, len(script)
    while i < n:
        while i < n and script[i] in " \t\n;":
            i += 1
        if i >= n:
            return
        while i < n and (script[i].isdigit() or script[i] in ",$!"):
            i += 1
        if i < n and script[i] == "/":
            j = i + 1
            while j < n and script[j] != "/":
                j += 2 if script[j] == "\\" else 1
            i = j + 1
            if i < n and script[i] == ",":
                i += 1
                while i < n and (script[i].isdigit() or script[i] == "$"):
                    i += 1
        if i >= n:
            raise Unsafe("sed-Skript unvollständig")
        cmd = script[i]
        if cmd == "s" and i + 1 < n:
            delim, j, parts = script[i + 1], i + 2, 0
            if delim in "\\\n":
                raise Unsafe("sed-Skript nicht lesbar")
            while j < n and parts < 2:
                if script[j] == "\\":
                    j += 2
                    continue
                if script[j] == delim:
                    parts += 1
                j += 1
            if parts < 2:
                raise Unsafe("sed-Skript nicht lesbar")
            while j < n and script[j] in SED_FLAGS:
                j += 1
            i = j
        elif cmd in "dpqn=":
            i += 1
        else:
            raise Unsafe("sed-Befehl %r ist nicht erlaubt (nur s, d, p, q, n, =)" % cmd)
        if i < n and script[i] not in " \t\n;":
            raise Unsafe("sed-Skript nicht lesbar")


# --- Hook --------------------------------------------------------------------------------

def strict_options(name, args):
    """Zerlegt die Argumente nach STRICT[name]. Liefert (Positionsargumente, Werte von -e bzw.
    --expression bei sed); jede nicht freigegebene Option wirft Unsafe."""
    flags, valued, longs, long_valued = STRICT[name]
    positional, values = [], []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            positional.extend(args[i + 1:])
            break
        if a.startswith("--"):
            stem, eq, value = a.partition("=")
            if stem in long_valued:
                if not eq:
                    if i + 1 >= len(args):
                        raise Unsafe("%s %s ohne Wert" % (name, stem))
                    i += 1
                    value = args[i]
                values.append(value)
            elif a not in longs:
                raise Unsafe("%s: Option %s ist nicht freigegeben (nur ausgeschrieben)" % (name, stem))
        elif a.startswith("-") and len(a) > 1:
            for k, c in enumerate(a[1:], 1):
                if c in valued:
                    value = a[k + 1:]
                    if not value:
                        if i + 1 >= len(args):
                            raise Unsafe("%s -%s ohne Wert" % (name, c))
                        i += 1
                        value = args[i]
                    values.append(value)
                    break
                if c not in flags:
                    raise Unsafe("%s: Schalter -%s ist nicht freigegeben" % (name, c))
        else:
            # BSD-getopt (macOS) hört am ersten Wort ohne - auf, GNU sortiert um. Damit beide
            # dasselbe lesen, dürfen danach keine Optionen mehr kommen.
            if any(b.startswith("-") and len(b) > 1 for b in args[i + 1:]):
                raise Unsafe("%s: Optionen nur vor Datei bzw. Skript" % name)
            positional.append(a)
        i += 1
    return positional, (values if name == "sed" else [])


def project_checks(root):
    """Prüfbefehle des Projekts als Liste von Wortlisten je Teilbefehl. Quelle wie im
    Konfigurationsvertrag: .slickrails/config.sh, sonst .slickfab/config; nur als Text gelesen,
    nur CHECK_*-Werte, die sich ohne Variablen und Ersetzung zerlegen lassen."""
    for rel in (os.path.join(".slickrails", "config.sh"), os.path.join(".slickfab", "config")):
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        checks = []
        with open(path, encoding="utf-8", errors="replace") as f:   # tolerant: Repo-Datei
            for line in f:
                m = CHECK_KEY.match(line.strip())
                if not m:
                    continue
                try:
                    segments = lex(m.group(2))
                except Unsafe:
                    continue
                if any(redirects for _, redirects, _ in segments):
                    continue
                checks.extend([w.text for w in words] for words, _, _ in segments if words)
        return checks
    return []


def is_checking_role(event):
    """Kann selbst nicht werfen: nur Typprüfungen und ein Vergleich von Texten."""
    return isinstance(event, dict) and isinstance(event.get("agent_type"), str) \
        and event["agent_type"] in ROLES


def verdict(event):
    """None = erlaubt, sonst der Grund."""
    if event.get("tool_name") != "Bash":
        return None
    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        raise Unsafe("kein lesbarer Befehl")
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    cwd = event.get("cwd")
    if not root or not isinstance(cwd, str):
        raise Unsafe("Worktree unbekannt (CLAUDE_PROJECT_DIR oder cwd fehlt)")
    Checker(root, cwd).check(command)
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:  # unlesbar: keine Rolle erkennbar, normale Arbeit nie blockieren
        return 0
    if not is_checking_role(event):
        return 0
    # Ab hier fail-closed: Jeder unerwartete Fehler wird zu deny statt zu einem Absturz,
    # den Claude Code als nicht blockierend behandeln würde.
    try:
        reason = verdict(event)
    except Unsafe as e:
        reason = str(e)
    except Exception as e:
        reason = "interner Fehler (%s), im Zweifel abgelehnt" % type(e).__name__
    if reason is None:
        return 0
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": "deny",
                                      "permissionDecisionReason": RULE % reason}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
