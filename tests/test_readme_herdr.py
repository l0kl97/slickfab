"""README: Herdr ist verlinkt, und es steht da, dass nur der Autopilot Herdr braucht.

Wer slickfab von außen ansieht, liest in beiden READMEs „Herdr“ (Terminals des
Autopiloten, context-guard). Ohne Link und Hinweis bleibt offen, ob Hand und
Assistiert Herdr voraussetzen; sie tun es nicht.
Dazu: Der Abschnitt der Betriebsarten-Doku, auf den beide READMEs verweisen, existiert.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = "[Herdr](https://herdr.dev/)"
# (Datei, Abschnitt mit den Betriebsarten, Satz zu Herdr)
READMES = (
    ("README.md", "## Operating modes",
     "Only the autopilot needs " + LINK + "; manual and assisted mode run without it."),
    ("README.de.md", "## Betriebsarten",
     "Nur der Autopilot braucht " + LINK + "; Hand und Assistiert laufen ohne."),
)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def section(text, heading):
    start = text.index(heading + "\n")
    end = text.find("\n## ", start + len(heading))
    return text[start:end if end != -1 else len(text)]


class ReadmeHerdrTest(unittest.TestCase):
    def test_modes_section_links_herdr_and_says_only_autopilot_needs_it(self):
        for rel, heading, sentence in READMES:
            with self.subTest(file=rel):
                self.assertIn(sentence, section(read(rel), heading))

    def test_herdr_link_points_to_the_project_site(self):
        for rel, _, _ in READMES:
            with self.subTest(file=rel):
                links = re.findall(r"\[Herdr\]\(([^)]*)\)", read(rel))
                self.assertTrue(links)
                self.assertEqual(set(links), {"https://herdr.dev/"})

    def test_readmes_point_to_an_existing_section_of_the_modes_doc(self):
        doc = read(os.path.join("docs", "operating-modes.md"))
        headings = set(re.findall(r"^## (.+)$", doc, re.M))
        for rel, pattern in (("README.md", r'`docs/operating-modes\.md`, section "([^"]+)"'),
                             ("README.de.md", r"`docs/operating-modes\.md`, Abschnitt „([^“]+)“")):
            with self.subTest(file=rel):
                names = re.findall(pattern, read(rel))
                self.assertEqual(len(names), 1, names)
                self.assertIn(names[0], headings)


if __name__ == "__main__":
    unittest.main()
