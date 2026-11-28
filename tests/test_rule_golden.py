"""Regelabschnitte der Bau-Schritte gleich der eingecheckten Referenz
(Review PR #7, Runde 2; Vorgabe des Masters statt weiterer Einzel-Anker).

Jede Textänderung zwischen `<!-- regel:NAME -->` und `<!-- /regel:NAME -->`
in implement, debug oder handoff macht diesen Test rot, bis die Referenz
tests/golden/build-steps-rules.md mit `python3 tests/rules_golden.py --update`
bewusst mitgeändert wird.
"""
import os
import unittest

import rules_golden as rg

# Welche Regelabschnitte es geben muss. Wer einen samt Markern streicht und
# die Referenz neu schreibt, muss auch diese Liste ändern; beides steht im Diff.
REQUIRED = {
    # jeder Schritt; Einleitung, Wann, jeder Unterabschnitt des Ablaufs,
    # Ergebnis und Nächster Schritt (alles außer dem Vertrag, den test_contract_blocks prüft).
    "grill": ("einleitung", "wann", "lage-erkunden-bevor-du-fragst", "entscheidungsbaum-aufbauen",
              "jede-frage-einordnen", "eine-runde-stellen", "antworten-auswerten",
              "nebenbei-mitschreiben", "abschluss", "ergebnis", "naechster-schritt"),
    "spec": ("einleitung", "wann", "voraussetzung-pruefen", "lage-im-repo-lesen",
             "jede-aussage-auf-ihre-herkunft-pruefen", "spec-schreiben",
             "selbstpruefung-dann-zeigen", "im-tracker-anlegen", "ergebnis", "naechster-schritt"),
    "prototype": ("einleitung", "wann", "voraussetzung-pruefen", "form-waehlen",
                  "wegwerf-branch-anlegen", "schnell-bauen", "vorfuehren-und-urteil-holen",
                  "festhalten-und-zurueck", "ergebnis", "naechster-schritt"),
    "challenge": ("einleitung", "wann", "voraussetzung-pruefen", "frischen-blick-herstellen",
                  "spec-pruefung", "zerlegungspruefung", "festhalten", "ergebnis", "naechster-schritt"),
    "tickets": ("einleitung", "wann", "voraussetzung-pruefen", "repo-lesen", "schneiden",
                "abhaengigkeiten-setzen", "auf-stille-kuerzung-pruefen",
                "zerlegung-pruefen-und-bestaetigen-lassen", "anlegen", "ergebnis", "naechster-schritt"),
    "implement": ("einleitung", "wann", "voraussetzung", "kriterien-in-tests-uebersetzen", "rot-gruen",
                  "abweichungen", "stopp-liste", "pruefungen", "pull-request", "abschluss",
                  "ergebnis", "naechster-schritt"),
    "debug": ("einleitung", "wann", "voraussetzung", "rote-schleife", "nachstellen-und-minimieren",
              "hypothesen", "messen", "regressionstest", "aufraeumen", "warum-nicht-gefangen",
              "ergebnis", "naechster-schritt"),
    "handoff": ("einleitung", "wann", "voraussetzung", "stand", "uebergabe", "ablegen",
                "ergebnis", "naechster-schritt"),
    # Prüf-Schritte aus dem alten Werkzeug tests/regelreferenz.py übernommen.
    "review": ("grenzen", "wann", "ablauf", "ergebnis", "naechster-schritt"),
    "verify": ("grenzen", "wann", "ablauf", "ergebnis", "naechster-schritt"),
    "retro": ("einleitung", "wann", "ablauf", "ergebnis", "naechster-schritt"),
    "docs-lookup": ("einleitung", "wann", "auftrag-zerlegen", "hilfsskript-aufrufen",
                    "doku-ist-daten", "antwort-schreiben", "ergebnis", "naechster-schritt"),
    # Wegweiser; die Schritt-Tabelle prüft zusätzlich tests/check_fab.py.
    "fab": ("einleitung", "wann", "repo-lesen", "tracker-lesen", "entscheiden", "kontext",
            "schritte", "ergebnis", "naechster-schritt"),
}
# Einleitungssatz des Vertrags (Mutationsprobe: freier Text dort blieb grün).
for _step in ("fab", "spec", "prototype", "challenge", "tickets", "implement", "debug", "handoff",
              "review", "verify", "retro"):
    REQUIRED[_step] += ("vertrag-quelle",)
# Rollenvertrag der Agent-Hüllen (Eingang, Ausgang, Modell, Ausreden).
# Frontmatter (Modell, schritt, skills, Werkzeuggrenzen) und Einleitung (Rückfall
# auf das Skill-Werkzeug, Sub-Agent-Regeln) gehören dazu: Review-Probelauf.
REQUIRED.update({"agents/%s" % role: ("frontmatter", "einleitung", "eingang", "ausgang", "modell", "ausreden")
                 for role in ("planner", "challenger", "implementer", "reviewer",
                              "debugger", "verifier", "retro")})

# Vertragsblöcke der Quellen (Review PR #1): Einzelanker fingen 12 gleichmäßig in Quelle und
# Kopien eingebaute Schwächungen nicht; jetzt ist jeder Block ganz eingefroren.
REQUIRED.update({
    "tracker/linear.md": tuple("vertrag:" + n for n in
                               ("zugang", "issues", "status", "labels", "marker", "rulings")),
    "docs/project-config.md": tuple("vertrag:" + n for n in
                                          ("config-format", "config-slickrails", "config-fehlt")),
})


class RuleGoldenTest(unittest.TestCase):
    def test_markers_well_formed(self):
        for label, path in rg.sources():
            with self.subTest(source=label):
                self.assertEqual(rg.marker_problems(label, rg.read(path)), [])

    def test_required_regions_present(self):
        found = {(s, n) for s, n, _ in rg.regions()}
        for step, names in REQUIRED.items():
            for name in names:
                with self.subTest(step=step, region=name):
                    self.assertIn((step, name), found)

    def test_regions_equal_reference(self):
        path = os.path.join(rg.ROOT, rg.GOLDEN)
        self.assertTrue(os.path.exists(path), "%s fehlt: python3 tests/rules_golden.py --update" % rg.GOLDEN)
        expected, actual = rg.read(rg.GOLDEN), rg.render(rg.regions())
        if expected != actual:
            self.fail("Regelabschnitte weichen von der Referenz ab. Gewollt? "
                      "python3 tests/rules_golden.py --update\n" + rg.diff(expected, actual))


class ContractBlocksFrozenTest(unittest.TestCase):
    """Eine Änderung an einem Vertragsblock der Quelle ändert die Referenz, auch wenn sie
    gleichmäßig in alle Kopien übernommen wird (dann bliebe test_contract_blocks grün)."""

    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.mkdtemp(prefix="slickfab-golden-")
        self.addCleanup(shutil.rmtree, self.tmp)
        for sub in ("skills", "agents", "tracker", "docs"):
            shutil.copytree(os.path.join(rg.ROOT, sub), os.path.join(self.tmp, sub))

    def mutate(self, rel, old, new):
        path = os.path.join(self.tmp, rel)
        text = rg.read(rel, self.tmp)
        self.assertEqual(text.count(old), 1, old)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new))

    def test_copy_renders_like_the_repo(self):
        self.assertEqual(rg.render(rg.regions(self.tmp)), rg.render(rg.regions()))

    def test_weakened_contract_rule_changes_the_reference(self):
        cases = (("tracker/linear.md", "always a human gate, never auto-merge", "usually a human gate"),
                 ("docs/project-config.md", "follows slickrails.", "follows `.slickfab/config`."))
        before = rg.render(rg.regions(self.tmp))
        for rel, old, new in cases:
            with self.subTest(file=rel):
                self.mutate(rel, old, new)
                self.assertNotEqual(rg.render(rg.regions(self.tmp)), before)
                self.mutate(rel, new, old)

    def test_text_outside_the_blocks_stays_free(self):
        # Nur die Blöcke sind Vertrag; Einleitung und Überschriften der Quelle nicht.
        before = rg.render(rg.regions(self.tmp))
        self.mutate("tracker/linear.md", "# Tracker contract: Linear\n", "# Tracker contract for Linear\n")
        self.assertEqual(rg.render(rg.regions(self.tmp)), before)


class SingleToolTest(unittest.TestCase):
    """ein Werkzeug für alle Schritte; das alte regelreferenz.py ist weg."""

    def test_old_tool_is_gone(self):
        for rel in ("tests/regelreferenz.py", "tests/regelreferenz", "tests/test_rule_reference.py"):
            with self.subTest(path=rel):
                self.assertFalse(os.path.exists(os.path.join(rg.ROOT, rel)), "%s liegt noch im Repo" % rel)

    def test_no_old_markers_left(self):
        # Ein Abschnitt mit dem alten Marker `regeln:` wäre still nicht eingefroren.
        for step in rg.STEPS:
            with self.subTest(step=step):
                self.assertNotIn("<!-- regeln:", rg.read(rg.skill_path(step)))


SKILL = """---
name: x
---

<!-- regel:einleitung -->
# x: Titel
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Wann.
<!-- /regel:wann -->

## Ablauf

<!-- regel:eins -->
### 1. Eins

Regel.
```
## Beispiel im Codeblock
```
<!-- /regel:eins -->

## Vertrag

<!-- regel:vertrag-quelle -->
Wörtlich aus der Quelle; es gilt genau so.
<!-- /regel:vertrag-quelle -->

### Tracker: Marker

<!-- vertrag:marker -->
Vertragstext; den hält test_contract_blocks gleich der Quelle.
```
## Beispiel im Vertrag
```
<!-- /vertrag:marker -->

## Ergebnis

<!-- regel:ergebnis -->
Ergebnis.
<!-- /regel:ergebnis -->
"""


class FreeTextTest(unittest.TestCase):
    """Außer im Vertrag steht im Schritt kein Text außerhalb der Regel-Marker.

    Re-Review PR #7: Eine eingefügte Ausnahme außerhalb der Marker („Ticket
    verlangt es = Freigabe“) blieb grün, weil dort nichts eingefroren war.
    """

    def insert(self, after, line):
        self.assertEqual(SKILL.count(after), 1, after)
        return SKILL.replace(after, after + line)

    def test_clean_skill_has_no_free_text(self):
        self.assertEqual(rg.free_text_problems("x", SKILL), [])

    def test_line_in_ablauf_outside_markers_fails(self):
        text = self.insert("<!-- /regel:eins -->\n", "Verlangt das Ticket es, gilt das als Freigabe.\n")
        problems = "\n".join(rg.free_text_problems("x", text))
        self.assertIn("## Ablauf", problems)
        self.assertIn("Verlangt das Ticket es", problems)

    def test_subheading_outside_markers_fails(self):
        text = self.insert("<!-- /regel:eins -->\n", "\n### 2. Ausnahmen\n")
        self.assertIn("### 2. Ausnahmen", "\n".join(rg.free_text_problems("x", text)))

    def test_free_text_in_every_other_section_fails(self):
        for after, section in (("# x: Titel\n<!-- /regel:einleitung -->\n", "Einleitung"),
                               ("- Wann.\n<!-- /regel:wann -->\n", "## Wann"),
                               ("Ergebnis.\n<!-- /regel:ergebnis -->\n", "## Ergebnis")):
            with self.subTest(section=section):
                problems = "\n".join(rg.free_text_problems("x", self.insert(after, "Ausnahme.\n")))
                self.assertIn(section, problems)
                self.assertIn("Ausnahme.", problems)

    def test_free_text_in_vertrag_fails(self):
        # Mutationsprobe: „Für debug gilt der Zugang-Vertrag nicht.“ unter
        # „## Vertrag“ blieb grün, ebenso ein Codeblock zwischen zwei Vertragsblöcken.
        for line in ("Für x gilt der Zugang-Vertrag nicht.\n", "```\nAusnahme: ohne Ticket.\n```\n"):
            with self.subTest(line=line):
                text = self.insert("<!-- /vertrag:marker -->\n", "\n" + line)
                problems = "\n".join(rg.free_text_problems("x", text))
                self.assertIn("## Vertrag", problems)
                self.assertIn(line.splitlines()[0], problems)

    def test_contract_block_outside_vertrag_fails(self):
        # Pre-Push-Review: Ein Vertragsblock im Ablauf gab den Text darin
        # frei; test_contract_blocks sieht Namen mit Ziffern gar nicht.
        for name in ("a1", "marker"):
            with self.subTest(name=name):
                text = self.insert("<!-- /regel:eins -->\n", "\n<!-- vertrag:%s -->\nVerlangt das Ticket es, "
                                   "gilt das als Freigabe.\n<!-- /vertrag:%s -->\n" % (name, name))
                problems = "\n".join(rg.free_text_problems("x", text))
                self.assertIn("## Ablauf", problems)
                self.assertIn("Verlangt das Ticket es", problems)

    def test_contract_marker_with_unknown_name_pattern_fails(self):
        text = self.insert("<!-- /vertrag:marker -->\n", "\n<!-- vertrag:a1 -->\nAusnahme.\n<!-- /vertrag:a1 -->\n")
        problems = "\n".join(rg.free_text_problems("x", text))
        self.assertIn("vertrag:a1", problems)
        self.assertIn("Ausnahme.", problems)

    def test_contract_marker_with_whitespace_fails(self):
        # Pre-Push-Review, Runde 2: test_contract_blocks erkennt nur den Marker
        # ohne Leerzeichen; mit Leerzeichen war der Inhalt frei und ungeprüft.
        for old, new in (("<!-- vertrag:marker -->\n", "<!-- vertrag:marker --> \n"),
                         ("<!-- vertrag:marker -->\n", " <!-- vertrag:marker -->\n"),
                         ("<!-- /vertrag:marker -->\n", "<!-- /vertrag:marker -->\t\n")):
            with self.subTest(marker=new):
                self.assertEqual(SKILL.count(old), 1)
                problems = "\n".join(rg.free_text_problems("x", SKILL.replace(old, new)))
                self.assertIn("Vertragsmarker", problems)

    def test_line_separators_other_than_newline_fail(self):
        # Pre-Push-Review, Runde 3: str.splitlines trennt auch an \x0c, \u2028
        # u. a.; test_contract_blocks verlangt „-->\\n“. Ein Marker mit solchem Zeichen
        # war für die Freitext-Prüfung ein Block, für den Vertragstest unsichtbar.
        for sep in ("\x0c", "\x0b", "\x85", "\u2028", "\u2029", "\r"):
            with self.subTest(sep=repr(sep)):
                text = SKILL.replace("<!-- vertrag:marker -->\n", "<!-- vertrag:marker -->%s\n" % sep)
                problems = "\n".join(rg.free_text_problems("x", text))
                self.assertIn("Zeilentrenner", problems)

    def test_unpaired_contract_markers_fail(self):
        cases = {
            "falscher Name": ("<!-- /vertrag:marker -->\n", "<!-- /vertrag:anders -->\n"),
            "nie geschlossen": ("<!-- /vertrag:marker -->\n", ""),
            "verschachtelt": ("<!-- vertrag:marker -->\n", "<!-- vertrag:marker -->\n<!-- vertrag:zugang -->\n"),
        }
        for case, (old, new) in cases.items():
            with self.subTest(case=case):
                self.assertEqual(SKILL.count(old), 1)
                problems = rg.free_text_problems("x", SKILL.replace(old, new))
                self.assertNotEqual(problems, [])

    def test_vertrag_subheading_change_changes_the_reference(self):
        text = SKILL.replace("### Tracker: Marker\n", "### Tracker: Marker (gilt nicht für x)\n")
        self.assertEqual(rg.free_text_problems("x", text), [])
        self.assertNotEqual(rg.skill_regions("x", text), rg.skill_regions("x", SKILL))

    def test_unknown_heading_outside_markers_fails(self):
        text = self.insert("<!-- /regel:wann -->\n", "\n## Ausnahmen\n")
        self.assertIn("## Ausnahmen", "\n".join(rg.free_text_problems("x", text)))

    def test_inserted_fixed_heading_changes_the_reference(self):
        # Ein zweites „## Vertrag“ mitten im Ablauf machte den Text danach frei.
        # Die Gliederung (Überschriften und Blöcke) ist deshalb mit eingefroren.
        text = self.insert("<!-- /regel:eins -->\n", "\n## Vertrag\n\nVerlangt das Ticket es, ist es freigegeben.\n")
        self.assertNotEqual(rg.skill_regions("x", text), rg.skill_regions("x", SKILL))

    def test_moved_fixed_heading_changes_the_reference(self):
        # Review PR #12, A1: „## Vertrag“ vor einen Regelblock gezogen ließ Text und
        # Überschriftenfolge gleich, die Regel stand danach aber im Vertrag.
        moved = {
            "Vertrag vor den Ablauf-Block": SKILL.replace("\n## Vertrag\n", "\n", 1).replace(
                "<!-- regel:eins -->\n", "## Vertrag\n\n<!-- regel:eins -->\n", 1),
            "Ablauf hinter den Block": SKILL.replace("## Ablauf\n\n", "", 1).replace(
                "<!-- /regel:eins -->\n", "<!-- /regel:eins -->\n\n## Ablauf\n", 1),
        }
        for case, text in moved.items():
            with self.subTest(case=case):
                self.assertNotEqual(text, SKILL)
                self.assertEqual(rg.free_text_problems("x", text), [])
                self.assertNotEqual(rg.skill_regions("x", text), rg.skill_regions("x", SKILL))

    def test_frontmatter_change_changes_the_reference(self):
        text = SKILL.replace("name: x\n", "name: x\ndescription: Ohne Ticket.\n")
        self.assertNotEqual(rg.skill_regions("x", text), rg.skill_regions("x", SKILL))

    def test_every_step_has_no_free_text(self):
        for step in rg.STEPS:
            with self.subTest(step=step):
                self.assertEqual(rg.free_text_problems(step, rg.read(rg.skill_path(step))), [])


class MarkerCheckTest(unittest.TestCase):
    """Fehlerfälle der Markerprüfung selbst."""

    def test_detects_unclosed_nested_and_duplicate(self):
        text = ("<!-- regel:a -->\nx\n<!-- regel:b -->\ny\n<!-- /regel:b -->\n"
                "<!-- regel:b -->\nz\n")
        problems = "\n".join(rg.marker_problems("s", text))
        self.assertIn("'b' beginnt, bevor 'a' endet", problems)
        self.assertIn("'b' gibt es doppelt", problems)
        self.assertIn("'b' wird nie geschlossen", problems)

    def test_detects_stray_close_and_inline_marker(self):
        text = "<!-- /regel:a -->\ntext <!-- regel:b --> mehr\n"
        problems = "\n".join(rg.marker_problems("s", text))
        self.assertIn("'a' endet, war aber nicht offen", problems)
        self.assertIn("allein auf der Zeile", problems)

    def test_indented_marker_is_a_problem(self):
        # Pre-Push-Review: eingerückte Marker bestanden die Prüfung, wurden aber
        # nicht erfasst; die Regel darin wäre still nicht eingefroren.
        text = "- Punkt\n  <!-- regel:a -->\n  Regel.\n  <!-- /regel:a -->\n"
        problems = "\n".join(rg.marker_problems("s", text))
        self.assertIn("s:2: Marker muss am Zeilenanfang stehen", problems)
        self.assertIn("s:4: Marker muss am Zeilenanfang stehen", problems)

    def test_markers_in_code_blocks_are_examples(self):
        # Pre-Push-Review: Marker als Beispiel in ``` oder ~~~ galten als echt.
        text = ("```\n<!-- regel:beispiel -->\n```\n"
                "<!-- regel:a -->\nRegel.\n~~~\n<!-- /regel:a -->\n~~~\nnoch Regel.\n<!-- /regel:a -->\n")
        self.assertEqual(rg.marker_problems("s", text), [])
        self.assertEqual(rg.extract(text),
                         [("a", "Regel.\n~~~\n<!-- /regel:a -->\n~~~\nnoch Regel.\n")])

    def test_clean_text_has_no_problems(self):
        self.assertEqual(rg.marker_problems("s", "<!-- regel:a -->\nx\n<!-- /regel:a -->\n"), [])

    def test_text_outside_markers_is_free(self):
        a = "frei 1\n<!-- regel:r -->\nRegel.\n<!-- /regel:r -->\nfrei 1\n"
        b = "ganz anders\n<!-- regel:r -->\nRegel.\n<!-- /regel:r -->\nauch anders\n"
        self.assertEqual(rg.extract(a), rg.extract(b))


if __name__ == "__main__":
    unittest.main()
