#!/usr/bin/env python3
"""Prüfung des Wegweisers fab.

- Die Schritt-Tabelle in skills/fab/SKILL.md (Block `<!-- regel:schritte -->`,
  je Zeile `| `name` | …`) nennt genau die Schritte, die als
  skills/<name>/SKILL.md existieren: keiner fehlt, keiner ist erfunden.
- Jeder Befehl `/slickfab:<name>` in fab, in README.md, README.de.md und in
  docs/*.md (ohne Unterordner) ist ein existierender Schritt.
- Jeder andere Name `slickfab:<name>` dort ist ein Schritt, eine Rolle aus
  agents/ oder ein Label aus dem Tracker-Vertrag (Review PR #14, R1).
- Die Schritt-Tabelle jeder README nennt genau die vorhandenen Schritte
  (Review PR #14, R1): README.md ist englisch (Abschnitt `## Steps`),
  README.de.md deutsch (Abschnitt `## Schritte`). Fehlt eine README, ist das
  ein Befund.
- Jedes Werkzeug `runtime/herdr/<name>` in README und docs existiert
  (Review PR #14, A2).
- Solange es kein ausführbares runtime/herdr/slickfab-dispatch gibt, beginnen
  der Autopilot-Abschnitt von README.de.md mit „noch nicht nutzbar“, die von
  README.md und docs/operating-modes.md mit „not yet usable“, und keiner nennt
  slickfab-dispatch (Review PR #14, A2).
  Gibt es ihn, sagen sie „noch nicht live“ bzw. „not yet live“ und nicht mehr
  „noch nicht nutzbar“ bzw. „not yet usable“: Der Dispatcher ist
  gebaut, aber nicht eingeschaltet. Wer ihn live schaltet, hebt diese Regel auf.

Aufruf: python3 tests/check_fab.py [repo-root]
Exit 0 = in Ordnung, 1 = mindestens ein Befund (je Befund eine Zeile FAIL ...).
Nur Standardbibliothek, läuft mit Python 3.9.
"""
import glob
import os
import re
import sys

FAB = os.path.join("skills", "fab", "SKILL.md")
TABLE = re.compile(r"<!-- regel:schritte -->\n(.*?)<!-- /regel:schritte -->", re.S)
ROW = re.compile(r"^\| `([a-z][a-z0-9-]*)` \|", re.M)
COMMAND = re.compile(r"/slickfab:([a-z][a-z0-9-]*)")
NAME = re.compile(r"(?<![/\w])slickfab:([a-z][a-z0-9-]*)")
RUNTIME = re.compile(r"runtime/herdr/([A-Za-z0-9_.-]+)")
# README.md englisch, README.de.md deutsch; je README die Überschrift der Schritt-Tabelle.
READMES = {"README.md": "## Steps", "README.de.md": "## Schritte"}
# Autopilot-Abschnitt: README-Zeile „- **Autopilot:**“ bzw. Abschnitt „## Autopilot“, je mit
# den Sätzen für „nicht ausführbar“ und „gebaut, nicht eingeschaltet“ in seiner Sprache.
README_AUTOPILOT = re.compile(r"^- \*\*Autopilot:\*\*([^\n]*)", re.M)
AUTOPILOT = {"README.md": (README_AUTOPILOT, "not yet usable", "not yet live"),
             "README.de.md": (README_AUTOPILOT, "noch nicht nutzbar", "noch nicht live"),
             os.path.join("docs", "operating-modes.md"): (
                 re.compile(r"^## Autopilot\n(.*?)(?=^## |\Z)", re.S | re.M), "not yet usable", "not yet live")}
# Das Werkzeug selbst, mit oder ohne Pfad davor (Pre-Push-Review), nicht das
# Dossier docs/features/slickfab-dispatch.md (danach „.md“).
DISPATCH_TOOL = re.compile(r"(?<![\w-])slickfab-dispatch(?![\w-]|\.\w)")
# Labels der Gruppe slickfab aus tracker/linear.md (Vertrag „labels“).
LABELS = {"rework", "ready", "needs-human", "replan"}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def existing_steps(root):
    return {os.path.basename(os.path.dirname(p))
            for p in glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))}


def roles(root):
    return {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(root, "agents", "*.md"))}


def listed_steps(text):
    """Schritte aus der Tabelle im Block regel:schritte; None ohne Block."""
    m = TABLE.search(text)
    return None if m is None else ROW.findall(m.group(1))


def doc_files(root):
    out = [os.path.join(root, rel) for rel in sorted(READMES)]
    out += sorted(glob.glob(os.path.join(root, "docs", "*.md")))
    return [p for p in out if os.path.exists(p)]


def check(root):
    fails = []
    steps = existing_steps(root)
    path = os.path.join(root, FAB)
    if not os.path.exists(path):
        return ["%s: fehlt" % FAB]
    text = read(path)
    listed = listed_steps(text)
    if listed is None:
        fails.append("%s: Schritt-Tabelle (<!-- regel:schritte -->) fehlt" % FAB)
        listed = []
    for name in sorted(set(listed) - steps):
        fails.append("%s: Schritt '%s' existiert nicht, steht aber in der Tabelle" % (FAB, name))
    for name in sorted(steps - set(listed)):
        fails.append("%s: Schritt '%s' fehlt im Wegweiser" % (FAB, name))
    known = steps | roles(root) | LABELS
    for p in [path] + doc_files(root):
        rel = os.path.relpath(p, root)
        body = read(p)
        for name in sorted(set(COMMAND.findall(body)) - steps):
            fails.append("%s: Befehl '/slickfab:%s' existiert nicht" % (rel, name))
        for name in sorted(set(NAME.findall(body)) - known):
            fails.append("%s: 'slickfab:%s' ist weder Schritt noch Rolle noch Label" % (rel, name))
        if p != path:
            for name in sorted(set(RUNTIME.findall(body))):
                if not os.path.exists(os.path.join(root, "runtime", "herdr", name)):
                    fails.append("%s: Werkzeug 'runtime/herdr/%s' existiert nicht" % (rel, name))
    built = os.access(os.path.join(root, "runtime", "herdr", "slickfab-dispatch"), os.X_OK)
    for rel, (pattern, usable, live) in sorted(AUTOPILOT.items()):
        p = os.path.join(root, rel)
        m = pattern.search(read(p)) if os.path.exists(p) else None
        body = m.group(1).strip() if m else ""
        text = body.lower()
        # Ohne Dispatcher steht der Hinweis vorn, nicht irgendwo im Abschnitt, und
        # daneben steht keine Anleitung, den Dispatcher zu starten.
        if not built and not text.lstrip("*").startswith(usable):
            fails.append("%s: Autopilot-Abschnitt muss mit „%s“ beginnen "
                         "(kein ausführbares runtime/herdr/slickfab-dispatch)" % (rel, usable))
        if not built and DISPATCH_TOOL.search(body):
            fails.append("%s: Autopilot-Abschnitt nennt slickfab-dispatch, das es noch nicht "
                         "ausführbar gibt" % rel)
        if built and (live not in text or usable in text):
            fails.append("%s: Autopilot-Abschnitt muss sagen, dass er %s ist (Dispatcher gebaut, "
                         "nicht eingeschaltet) und nicht mehr „%s“" % (rel, live, usable))
    for rel, heading in sorted(READMES.items()):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            fails.append("%s: fehlt" % rel)
            continue
        m = re.search(r"^%s\n(.*?)(?=^## )" % re.escape(heading), read(p), re.S | re.M)
        if m is None:
            fails.append("%s: Abschnitt '%s' mit Tabelle fehlt" % (rel, heading))
            continue
        rows = set(ROW.findall(m.group(1)))
        for name in sorted(rows - steps):
            fails.append("%s: Schritt '%s' steht in der Tabelle, existiert aber nicht" % (rel, name))
        for name in sorted(steps - rows):
            fails.append("%s: Schritt '%s' fehlt in der Tabelle" % (rel, name))
    return fails


def main(argv):
    fails = check(argv[1] if len(argv) > 1 else ".")
    for msg in fails:
        print("FAIL " + msg)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
