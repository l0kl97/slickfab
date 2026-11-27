"""Die Bau- und Prüf-Schritte sind englisch (öffentliches Repo).

Fließtext außerhalb der Vertragsblöcke darf kein Deutsch mehr enthalten. Deutsch
bleiben nur Namen, die andere Stellen wörtlich lesen oder zitieren, und die stehen
in `Code`, in Codeblöcken, in “Anführungszeichen” oder als feste `## `-Überschrift
(tests/check_structure.py verlangt Wann, Ablauf, Ergebnis, Nächster Schritt):
- `## Ergebnis <schritt>`, `Nächster Schritt:`, `Bedenken`, `Nicht beurteilt` (zitieren die Rollen),
- die Abschnitte des PR-Texts von implement (liest review),
- die Statuswerte von verify (liest fab) und die Abschnitte der Spec (schreibt spec).
"""
import re
import unittest

from test_agent_roles import GERMAN, prose
from test_planning_steps import read

STEPS = ("implement", "review", "debug", "verify", "retro", "handoff", "docs-lookup")
CONTRACT = re.compile(r"(?ms)<!-- vertrag:([a-z-]+) -->.*?<!-- /vertrag:\1 -->")
# Ein Name, den review als Abschnittsüberschrift im Bericht führt (fett, ohne Anführungszeichen).
INTERFACE = ("**Nicht beurteilt:**",)


def english_prose(text):
    text = CONTRACT.sub("", text)
    text = re.sub(r"(?m)^## .*$", "", text)
    for name in INTERFACE:
        text = text.replace(name, "")
    return re.sub(r"“[^”\n]*”", "", prose(text))


class EnglishStepsTest(unittest.TestCase):
    def test_steps_have_no_german_prose(self):
        for step in STEPS:
            with self.subTest(step=step):
                text = english_prose(read("skills/%s/SKILL.md" % step))
                found = GERMAN.search(text)
                self.assertIsNone(found, found and text[max(0, found.start() - 40):found.end() + 40])

    def test_guard_is_sharp(self):
        # Mutationsprobe des Wächters: ein deutscher Satz fällt auf, auch zwischen englischen.
        sample = "You stop.\nDu hörst auf und meldest das.\n"
        self.assertIsNotNone(GERMAN.search(english_prose(sample)))
        self.assertIsNotNone(GERMAN.search(english_prose("Name it under „Bedenken“ und weiter.")))
        # Erlaubte Namen fallen nicht auf.
        self.assertIsNone(GERMAN.search(english_prose(
            "Name it under “Nicht angefasst”.\n**Nicht beurteilt:** list.\n## Nächster Schritt\n`bestanden`\n")))

    def test_frontmatter_is_english(self):
        for step in STEPS:
            with self.subTest(step=step):
                head = read("skills/%s/SKILL.md" % step).split("\n---\n", 1)[0]
                self.assertTrue(re.search(r"(?m)^description: Use when ", head), head)
                found = GERMAN.search(re.sub(r"“[^”\n]*”", "", head))
                self.assertIsNone(found, head)


if __name__ == "__main__":
    unittest.main()
