#!/usr/bin/env python3
"""Eingefrorene Regelabschnitte aller Schritte und der Agent-Rollen.

Die Regeln der Schritte (Stopp-Listen, Ausnahmen und Freigaben, Urteils- und
Statusregeln, Abschluss und Marker) stehen in skills/*/SKILL.md zwischen
`<!-- regel:NAME -->` und `<!-- /regel:NAME -->`. Dieses Skript sammelt sie in
der Reihenfolge der Dateien und vergleicht sie Zeichen für Zeichen mit der
eingecheckten Referenz tests/golden/rules.md (Ruling).

Warum so: Einzelne Ankersätze fingen nur die Sätze, die jemand vorher
bedacht hatte; fremde Mutationsproben fanden in denselben Absätzen immer neue
Überlebende. Jetzt macht jede Textänderung an einer Regel den Test rot, bis
die Referenz bewusst mitgeändert wird. Die Änderung steht dann sichtbar im
Diff der Referenz.

Kein freier Text: In einem Schritt steht außerhalb der Marker nur
Frontmatter, Leerzeilen und die festen Überschriften (FIXED_HEADINGS). Im
Abschnitt `## Vertrag` stehen dazu die Vertragsblöcke (`<!-- vertrag:NAME -->`,
gleich der Quelle laut test_contract_blocks) und ihre `### `-Überschriften.
Frontmatter und die Gliederung (Überschriften und Blöcke in Reihenfolge) sind mit eingefroren, damit ein
eingeschobenes `## Vertrag` oder eine geänderte Überschrift auffällt.

Aufruf:
  python3 tests/rules_golden.py            prüfen, bei Abweichung Diff und Exit 1
  python3 tests/rules_golden.py --update   Referenz aus den SKILL.md neu schreiben

Nur Standardbibliothek, läuft mit Python 3.9.
"""
import difflib
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# alle Schritte, gefunden über skills/*/SKILL.md (vorher nur die Bau-Schritte;
# review, verify und retro hatten ein eigenes Werkzeug tests/regelreferenz.py).
STEPS = tuple(sorted(os.path.basename(os.path.dirname(p))
                     for p in glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))))
# Rollenvertrag der Agent-Hüllen wird ebenso eingefroren.
ROLES = ("planner", "challenger", "implementer", "reviewer", "debugger", "verifier", "retro")
GOLDEN = os.path.join("tests", "golden", "rules.md")
MARKER = re.compile(r"<!-- (/?)regel:([a-z0-9-]+) -->")
# Überschriften, die in einem Schritt außerhalb der Marker stehen dürfen.
FIXED_HEADINGS = ("## Wann", "## Ablauf", "## Vertrag", "## Ergebnis", "## Nächster Schritt")
# Abschnitt mit Vertragsblöcken; dort sind außerhalb der Blöcke '### '-Überschriften erlaubt.
CONTRACT_SECTION = "## Vertrag"
# Gleiches Namensmuster wie test_contract_blocks; nur solche Blöcke prüft der Vertragstest.
CONTRACT = re.compile(r"<!-- (/?)vertrag:([a-z-]+) -->")
# Zeichen, an denen str.splitlines trennt, außer \n. test_contract_blocks sieht nur
# \n; ein Marker vor einem dieser Zeichen wäre für beide Leser verschieden.
LINE_BREAKS = "\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"
# Quellen der Vertragsblöcke (wie test_contract_blocks). Ihre Blöcke werden ganz eingefroren:
# Eine gleichmäßig in Quelle und alle Kopien eingebaute Schwächung hielt der Gleichheitstest
# nicht auf, Einzelanker nur an ihren Sätzen (Review PR #1, 12 überlebende Mutationen).
CONTRACT_SOURCES = ("tracker/linear.md", "docs/projektkonfiguration.md")
CONTRACT_BLOCK = re.compile(r"<!-- vertrag:([a-z-]+) -->\n(.*?)<!-- /vertrag:\1 -->", re.S)
CONTRACT_LIKE = re.compile(r"<!--\s*/?\s*vertrag:")

HEADER = """# Eingefrorene Regeln der Schritte und Rollen

Erzeugt mit `python3 tests/rules_golden.py --update` aus den Abschnitten
`<!-- regel:NAME -->` … `<!-- /regel:NAME -->` in allen `skills/*/SKILL.md`
(dazu je Schritt Frontmatter und Gliederung), den Agent-Rollen in
`agents/` und den Vertragsblöcken `<!-- vertrag:NAME -->` der Quellen
`tracker/linear.md` und `docs/projektkonfiguration.md`. Nicht von Hand bearbeiten.

Ändert sich eine Regel, wird `tests/test_rule_golden.py` rot. Ist die
Änderung gewollt, Skript mit `--update` laufen lassen und diese Datei
mitcommitten; der Diff hier zeigt dem Review genau, welche Regel sich
geändert hat.
"""


def skill_path(step):
    return os.path.join("skills", step, "SKILL.md")


def role_path(role):
    return os.path.join("agents", "%s.md" % role)


def sources():
    """[(bezeichnung, pfad)]: Bau-Schritte, dann Agent-Rollen."""
    return [(s, skill_path(s)) for s in STEPS] + [("agents/" + r, role_path(r)) for r in ROLES]


def read(rel, root=ROOT):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def scan(text):
    """Ein Durchgang für Prüfung und Erfassung, damit beide nie auseinanderlaufen.

    Marker zählen nur außerhalb von Codeblöcken (``` oder ~~~); dort sind sie
    Beispiele. Ein Marker steht allein und am Zeilenanfang. Gibt (Abschnitte,
    Probleme) zurück, Abschnitte als [(name, text)] in Datei-Reihenfolge.
    """
    found, problems, seen = [], [], set()
    current, body, fence = None, [], None
    for no, line in enumerate(text.splitlines(True), 1):
        bare = line.rstrip("\n")
        mark = bare.lstrip()[:3]
        if mark in ("```", "~~~"):
            fence = mark if fence is None else (None if mark == fence else fence)
        m = MARKER.fullmatch(bare.strip()) if fence is None and mark not in ("```", "~~~") else None
        if m and bare != bare.lstrip():
            problems.append("%d: Marker muss am Zeilenanfang stehen" % no)
        elif m and m.group(1) == "":
            name = m.group(2)
            if current:
                problems.append("%d: '%s' beginnt, bevor '%s' endet" % (no, name, current))
            if name in seen:
                problems.append("%d: '%s' gibt es doppelt" % (no, name))
            current, body = name, []
            seen.add(name)
            continue
        elif m:
            if m.group(2) != current:
                problems.append("%d: '%s' endet, war aber nicht offen" % (no, m.group(2)))
            else:
                found.append((current, "".join(body)))
            current = None
            continue
        elif fence is None and ("<!-- regel:" in bare or "<!-- /regel:" in bare):
            problems.append("%d: Marker muss allein auf der Zeile stehen" % no)
        if current:
            body.append(line)
    if current:
        problems.append("'%s' wird nie geschlossen" % current)
    return found, problems


def marker_problems(step, text):
    """Unpaarige, verschachtelte, doppelte, eingerückte Marker; leer = in Ordnung."""
    out = []
    for p in scan(text)[1]:
        out.append(("%s:%s" % (step, p)) if p[0].isdigit() else ("%s: %s" % (step, p)))
    return out


def outline(text):
    """(Überschriften, Funde) eines Schritts außerhalb der Regel-Marker.

    Gliederung: jede '## '-Zeile außerhalb von Markern und Codeblöcken, die
    '### '-Zeilen im Abschnitt CONTRACT_SECTION und der Anfang jedes Regel- und
    Vertragsblocks als `[regel:NAME]` bzw. `[vertrag:NAME]`, in Datei-Reihenfolge.
    So fällt auch auf, wenn eine feste Überschrift an einem Block vorbei
    verschoben wird (Review PR #12, A1).
    Funde (zeile, abschnitt, grund, text): jede andere nicht leere Zeile außerhalb
    der Regel- und Vertragsblöcke, auch jede '## '-Zeile, die nicht in
    FIXED_HEADINGS steht. Vertragsblöcke gelten nur unter CONTRACT_SECTION, mit
    dem Namensmuster des Vertragstests und paarig; sonst sind ihre Marker Funde
    und ihr Inhalt freier Text (Pre-Push-Review). Frontmatter zählt
    nicht (wird eigens eingefroren).
    """
    free = "freier Text außerhalb der Regel-Marker"
    lines = text.split("\n")
    start = 0
    if lines and lines[0] == "---":
        start = next((i + 1 for i in range(1, len(lines)) if lines[i] == "---"), 0)
    headings, found, section = [], [], "Einleitung"
    block, vblock, fence = None, None, None
    for no in range(start, len(lines)):
        line = lines[no]
        odd = sorted({c for c in line if c in LINE_BREAKS})
        if odd:
            found.append((no + 1, section, "Zeilentrenner außer \\n (%s)" % ", ".join(map(repr, odd)), line))
        mark = line.lstrip()[:3]
        is_fence = mark in ("```", "~~~")
        if is_fence:
            fence = mark if fence is None else (None if mark == fence else fence)
        bare = line.strip()
        m = MARKER.fullmatch(bare) if fence is None and not is_fence else None
        if m:
            block = None if m.group(1) else m.group(2)
            if block:
                headings.append("[regel:%s]" % block)
            continue
        if fence is None and not is_fence and not block and CONTRACT_LIKE.search(bare):
            # Ohne strip: test_contract_blocks erkennt nur den Marker allein auf der
            # Zeile, ohne Leerzeichen davor oder danach (Pre-Push-Review, Runde 2).
            c = CONTRACT.fullmatch(line)
            if not c:
                found.append((no + 1, section, "ungültiger Vertragsmarker (Name oder Leerzeichen)", line))
            elif section != CONTRACT_SECTION:
                found.append((no + 1, section, "Vertragsblock nur unter %s" % CONTRACT_SECTION, bare))
            elif c.group(1) == "" and vblock:
                found.append((no + 1, section, "'%s' beginnt, bevor '%s' endet" % (c.group(2), vblock), bare))
            elif c.group(1) == "":
                vblock = c.group(2)
                headings.append("[vertrag:%s]" % vblock)
            elif c.group(2) != vblock:
                found.append((no + 1, section, "'%s' endet, war aber nicht offen" % c.group(2), bare))
                vblock = None
            else:
                vblock = None
            continue
        if block or vblock or not line.strip():
            continue
        if fence is None and not is_fence and line.startswith("## "):
            headings.append(line.rstrip())
            if line.rstrip() in FIXED_HEADINGS:
                section = line.rstrip()
                continue
        elif section == CONTRACT_SECTION and fence is None and line.startswith("### "):
            headings.append(line.rstrip())
            continue
        found.append((no + 1, section, free, line.strip()))
    if vblock:
        found.append((len(lines), section, "'%s' wird nie geschlossen" % vblock, "<!-- vertrag:%s -->" % vblock))
    return headings, found


def free_text_problems(step, text):
    """Text außerhalb der Regel-Marker; leer = in Ordnung."""
    return ["%s:%d: %s (%s): „%s“" % (step, no, reason, section, line[:70])
            for no, section, reason, line in outline(text)[1]]


def skill_regions(label, text):
    """[(schritt, name, text)] eines Schritts: Frontmatter, Gliederung, Regelabschnitte."""
    out = [(label, "frontmatter", frontmatter(text)),
           (label, "gliederung", "".join(h + "\n" for h in outline(text)[0]))]
    return out + [(label, name, body) for name, body in extract(text)]


def frontmatter(text):
    """Text zwischen den beiden ersten '---'-Zeilen, leer ohne Frontmatter."""
    m = re.match(r"---\n(.*?\n)---\n", text, re.S)
    return m.group(1) if m else ""


def extract(text):
    """[(name, text)] der Regelabschnitte, Marker in Codeblöcken ausgenommen."""
    return scan(text)[0]


def regions(root=ROOT):
    """[(schritt, name, text)] in Datei-Reihenfolge."""
    out = []
    for label, path in sources():
        text = read(path, root)
        if not label.startswith("agents/"):
            out += skill_regions(label, text)
            continue
        if label.startswith("agents/"):
            # Das Frontmatter einer Rolle (Modell, schritt, skills, Werkzeuggrenzen)
            # bestimmt, was startet; es wird mit eingefroren (Review-Probelauf).
            out.append((label, "frontmatter", frontmatter(text)))
        for name, body in extract(text):
            out.append((label, name, body))
    for rel in CONTRACT_SOURCES:
        for name, body in CONTRACT_BLOCK.findall(read(rel, root)):
            out.append((rel, "vertrag:" + name, body))
    return out


def render(found):
    parts = [HEADER]
    for step, name, body in found:
        parts.append("<!-- regel:%s/%s -->\n%s<!-- /regel:%s/%s -->\n" % (step, name, body, step, name))
    return "\n".join(parts)


def diff(expected, actual):
    return "".join(difflib.unified_diff(
        expected.splitlines(True), actual.splitlines(True),
        fromfile=GOLDEN + " (Referenz)", tofile="skills/*/SKILL.md (jetzt)"))


def main(argv):
    problems = [p for s, path in sources() for p in marker_problems(s, read(path))]
    problems += [p for s in STEPS for p in free_text_problems(s, read(skill_path(s)))]
    if problems:
        print("\n".join("FAIL " + p for p in problems))
        return 1
    actual = render(regions())
    path = os.path.join(ROOT, GOLDEN)
    if "--update" in argv:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(actual)
        print("geschrieben: %s (%d Abschnitte)" % (GOLDEN, len(regions())))
        return 0
    expected = read(GOLDEN) if os.path.exists(path) else ""
    if expected != actual:
        print(diff(expected, actual))
        print("FAIL Regelabschnitte weichen von %s ab. Gewollt? python3 tests/rules_golden.py --update" % GOLDEN)
        return 1
    print("Regelabschnitte gleich der Referenz (%d)" % len(regions()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
