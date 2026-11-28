"""Die Zahlen der Pressure-Läufe in Dossier und READMEs stimmen mit den abgelegten Läufen.

Quelle der Wahrheit sind die Läufe unter tests/pressure/<rolle>/runs/<szenario>-<arm>/:
`bewertung.md` (gehalten / nicht gehalten) und `lauf.md` (Kosten). Geprüft wird:

- Die Tabelle im Abschnitt „## Protokoll“ des Dossiers hat für jedes Szenario genau eine Zeile,
  und Ergebnis und Kosten je Arm stimmen mit Bewertung und Laufparametern.
- Die Zeile „**Summe:**“ darunter nennt die gezählten Treffer je Arm.
- Beide READMEs nennen dieselben Zahlen („held in N of M“ / „hielten in N von M“).
- Beide READMEs sagen nicht mehr, Schritte und Rollen seien deutsch.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESSURE = os.path.join(ROOT, "tests", "pressure")
DOSSIER = os.path.join(ROOT, "docs", "features", "pressure-szenarien.md")
ROLLEN = ("planner", "challenger", "implementer", "reviewer", "debugger", "verifier", "retro")
ERGEBNIS = re.compile(r"^\*\*Ergebnis:\*\*\s*(gehalten|nicht gehalten)\b", re.M)
KOSTEN = re.compile(r"^- Kosten: ([0-9.]+) USD", re.M)
README_EN = re.compile(r"The roles held in (\d+) of (\d+) scenarios, the control [^\n]*? in (\d+) of (\d+)\.")
README_DE = re.compile(r"Die Rollen hielten in (\d+) von (\d+) Szenarien, die Kontrolle [^\n]*? in (\d+) von (\d+)\.")
# Der alte Hinweis, Schritte und Rollen seien deutsch, in beiden Sprachen.
DEUTSCH_EN = re.compile(r"\b(?:steps|roles)\b[^.\n]*\b(?:in German|written in German)", re.I)
DEUTSCH_DE = re.compile(r"\b(?:Schritte|Rollen)\b[^.\n]*(?:auf Deutsch|deutsch geschrieben)", re.I)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def laeufe(base=PRESSURE):
    """{(rolle/szenario, arm): (gehalten: bool, kosten: str mit Komma, 2 Stellen)}."""
    out = {}
    for rolle in ROLLEN:
        d = os.path.join(base, rolle)
        for name in sorted(os.listdir(d)):
            if name == "runs" or not os.path.isdir(os.path.join(d, name)):
                continue
            for arm in ("neu", "kontrolle"):
                lauf = os.path.join(d, "runs", "%s-%s" % (name, arm))
                m = ERGEBNIS.search(read(os.path.join(lauf, "bewertung.md")))
                k = KOSTEN.search(read(os.path.join(lauf, "lauf.md")))
                kosten = ("%.2f" % float(k.group(1))).replace(".", ",") if k else None
                out[("%s/%s" % (rolle, name), arm)] = (m.group(1) == "gehalten" if m else None, kosten)
    return out


def protokoll(text):
    """Tabellenzeilen im Abschnitt „## Protokoll…“: {szenario: (neu-zelle, kontrolle-zelle)}."""
    start = re.search(r"^## Protokoll\b.*$", text, re.M)
    if not start:
        return None
    ende = text.find("\n## ", start.end())
    abschnitt = text[start.end():ende if ende != -1 else len(text)]
    zeilen = {}
    for line in abschnitt.split("\n"):
        zellen = [z.strip() for z in line.strip().strip("|").split("|")]
        if len(zellen) == 5 and "/" in zellen[1] and not zellen[1].startswith("-"):
            zeilen.setdefault(zellen[1].strip("`"), []).append((zellen[3], zellen[4]))
    return zeilen, abschnitt


def zelle(text):
    """'gehalten (0,50)' / 'nicht gehalten (0,37): …' → (bool, '0,50') oder (None, None)."""
    m = re.match(r"(nicht gehalten|gehalten)\b[^(]*\((\d+,\d\d)\)", text)
    return (m.group(1) == "gehalten", m.group(2)) if m else (None, None)


def befunde(text, runs):
    """Abweichungen zwischen Dossier-Text und Läufen als Liste von Sätzen."""
    out = []
    p = protokoll(text)
    if p is None:
        return ["Abschnitt „## Protokoll“ fehlt"]
    zeilen, abschnitt = p
    szenarien = sorted({sz for sz, _ in runs})
    for sz in szenarien:
        if len(zeilen.get(sz, [])) != 1:
            out.append("%s: %d Zeile(n) in der Tabelle" % (sz, len(zeilen.get(sz, []))))
            continue
        for arm, inhalt in zip(("neu", "kontrolle"), zeilen[sz][0]):
            if zelle(inhalt) != runs[(sz, arm)]:
                out.append("%s %s: Tabelle %r, Lauf %r" % (sz, arm, zelle(inhalt), runs[(sz, arm)]))
    for sz in zeilen:
        if sz not in szenarien:
            out.append("%s: Zeile ohne Szenario" % sz)
    n = len(szenarien)
    neu = sum(1 for sz in szenarien if runs[(sz, "neu")][0])
    kontrolle = sum(1 for sz in szenarien if runs[(sz, "kontrolle")][0])
    summe = "**Summe:** neu %d von %d gehalten, Kontrolle %d von %d" % (neu, n, kontrolle, n)
    if summe not in abschnitt:
        out.append("Summenzeile fehlt oder stimmt nicht, erwartet: %s" % summe)
    return out


def zaehlung(runs):
    szenarien = {sz for sz, _ in runs}
    n = len(szenarien)
    return (sum(1 for sz in szenarien if runs[(sz, "neu")][0]), n,
            sum(1 for sz in szenarien if runs[(sz, "kontrolle")][0]), n)


class PressureZahlenTest(unittest.TestCase):
    def setUp(self):
        self.runs = laeufe()

    def test_every_run_has_result_and_cost(self):
        fehlend = [k for k, v in self.runs.items() if None in v]
        self.assertEqual(fehlend, [])
        self.assertEqual(len(self.runs), 28)

    def test_dossier_table_matches_runs(self):
        self.assertEqual(befunde(read(DOSSIER), self.runs), [])

    def test_readmes_state_the_counted_numbers(self):
        erwartet = zaehlung(self.runs)
        for rel, rx in (("README.md", README_EN), ("README.de.md", README_DE)):
            with self.subTest(file=rel):
                m = rx.search(read(os.path.join(ROOT, rel)))
                self.assertIsNotNone(m, "Satz mit den Zahlen fehlt")
                self.assertEqual(tuple(int(g) for g in m.groups()), erwartet)

    def test_readmes_no_longer_say_steps_and_roles_are_german(self):
        for rel, rx in (("README.md", DEUTSCH_EN), ("README.de.md", DEUTSCH_DE)):
            with self.subTest(file=rel):
                treffer = [l for l in read(os.path.join(ROOT, rel)).split("\n") if rx.search(l)]
                self.assertEqual(treffer, [])


class BefundeFindetTest(unittest.TestCase):
    """Fehlerfälle: Der Abgleich meldet falsche Zellen, fehlende Zeilen und Summen."""

    RUNS = {("a/1-x", "neu"): (True, "0,50"), ("a/1-x", "kontrolle"): (False, "0,37"),
            ("b/1-y", "neu"): (True, "0,20"), ("b/1-y", "kontrolle"): (True, "0,10")}
    KOPF = "## Protokoll (Test)\n\n| # | Szenario | Pflichtfall | Neu | Kontrolle |\n|---|---|---|---|---|\n"
    SUMME = "\n**Summe:** neu 2 von 2 gehalten, Kontrolle 1 von 2.\n"

    def test_matching_table_has_no_findings(self):
        text = (self.KOPF + "| A1 | a/1-x | – | gehalten (0,50) | nicht gehalten (0,37): x |\n"
                "| B1 | b/1-y | – | gehalten in der Lesart (0,20) | gehalten (0,10) |\n" + self.SUMME)
        self.assertEqual(befunde(text, self.RUNS), [])

    def test_wrong_cost_wrong_result_missing_row_and_sum(self):
        text = (self.KOPF + "| A1 | a/1-x | – | gehalten (0,51) | gehalten (0,37) |\n"
                "\n**Summe:** neu 1 von 2 gehalten, Kontrolle 1 von 2.\n")
        out = befunde(text, self.RUNS)
        self.assertEqual(len(out), 4, out)
        self.assertTrue(any(s.startswith("a/1-x neu") for s in out))
        self.assertTrue(any(s.startswith("a/1-x kontrolle") for s in out))
        self.assertTrue(any(s.startswith("b/1-y: 0 Zeile") for s in out))
        self.assertTrue(any(s.startswith("Summenzeile") for s in out))

    def test_missing_section_and_unparsable_cell(self):
        self.assertEqual(befunde("# Dossier\n", self.RUNS), ["Abschnitt „## Protokoll“ fehlt"])
        self.assertEqual(zelle("gehalten"), (None, None))
        self.assertEqual(zelle("nicht gehalten (0,37): x"), (False, "0,37"))

    def test_readme_patterns_find_the_old_hint(self):
        self.assertTrue(DEUTSCH_EN.search("The steps, roles and the docs under `docs/` are currently written in German."))
        self.assertTrue(DEUTSCH_DE.search("Schritte, Rollen und Doku sind derzeit deutsch geschrieben."))
        self.assertFalse(DEUTSCH_EN.search("The docs under `docs/` are currently written in German."))
        self.assertFalse(DEUTSCH_DE.search("Die Doku unter `docs/` ist derzeit auf Deutsch."))


if __name__ == "__main__":
    unittest.main()
