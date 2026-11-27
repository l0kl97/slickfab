"""Eingebettete Vertragsblöcke (Review PR #2, Befund A1).

Claude Code lädt den Text einer SKILL.md selbst; Dateien im Plugin-Ordner
dagegen liegen außerhalb des Projekts und brauchen eine Leseerlaubnis, die
ohne Auto-Modus verweigert wird. Deshalb trägt jeder Schritt die
Vertragsteile, die er braucht, wörtlich in sich. Quelle bleiben
tracker/linear.md und docs/projektkonfiguration.md; dieser Test hält die
Kopien Zeichen für Zeichen gleich.

Ein Block steht zwischen `<!-- vertrag:NAME -->` und `<!-- /vertrag:NAME -->`.
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ("tracker/linear.md", "docs/projektkonfiguration.md")
BLOCK = re.compile(r"<!-- vertrag:([a-z-]+) -->\n(.*?)<!-- /vertrag:\1 -->", re.S)

# Welche Vertragsteile ein Schritt braucht, um ohne Nachlesen richtig zu handeln.
REQUIRED = {
    "spec": ("zugang", "issues", "marker", "config-format", "config-fehlt"),
    "challenge": ("zugang", "marker", "config-format", "config-fehlt"),
    "tickets": ("zugang", "issues", "status", "labels", "marker",
                "config-format", "config-fehlt"),
    "prototype": ("marker", "config-format"),
    # Prüfbefehle kommen mit slickrails von dort (config-slickrails).
    # review und verify prüfen ohne Tracker gegen einen Auftrag als Text weiter; der
    # Zugang-Block sagt „hört auf“ (Review PR #6, A2). Regeln dafür stehen im Schritt.
    "review": ("marker", "config-format", "config-slickrails"),
    # verify legt Fix-Tickets an; der Statusblock nennt dafür nur spec/tickets (Pre-Push-Review).
    # Befund 4 der Pressure-Szenarien: Der Zugang-Block nennt die Ausnahme „Spec als Text“ selbst, verify bettet ihn ein.
    "verify": ("zugang", "issues", "marker", "config-format",
               "config-fehlt", "config-slickrails"),
    # retro liest den Tracker nur und arbeitet ohne ihn weiter; der Zugang-Block sagt „hört auf“.
    "retro": ("marker", "config-format", "config-slickrails"),
    # fab liest nur; ohne Tracker macht es mit dem Repo weiter, deshalb kein Zugang-Block.
    "fab": ("marker", "config-format"),
}


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def blocks(text):
    found = {}
    for name, body in BLOCK.findall(text):
        found.setdefault(name, []).append(body)
    return found


def source_blocks():
    out = {}
    for rel in SOURCES:
        for name, bodies in blocks(read(rel)).items():
            out.setdefault(name, []).extend((rel, b) for b in bodies)
    return out


class SourceBlocksTest(unittest.TestCase):
    def test_every_required_block_has_exactly_one_source(self):
        src = source_blocks()
        for name in sorted({n for names in REQUIRED.values() for n in names}):
            with self.subTest(block=name):
                self.assertEqual(len(src.get(name, [])), 1,
                                 "Block '%s' muss genau einmal in %s stehen" % (name, SOURCES))


class EmbeddedBlocksTest(unittest.TestCase):
    def test_steps_embed_required_blocks(self):
        for step, names in REQUIRED.items():
            text = read("skills/%s/SKILL.md" % step)
            for name in names:
                with self.subTest(step=step, block=name):
                    self.assertIn(name, blocks(text), "%s bettet '%s' nicht ein" % (step, name))

    def test_embedded_blocks_equal_source(self):
        src = source_blocks()
        # Agent-Rollen betten den Marker-Vertrag ebenso wörtlich ein.
        paths = glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")) + \
            glob.glob(os.path.join(ROOT, "agents", "*.md"))
        for path in sorted(paths):
            rel = os.path.relpath(path, ROOT)
            for name, bodies in blocks(read(rel)).items():
                for body in bodies:
                    with self.subTest(file=rel, block=name):
                        self.assertIn(name, src, "%s: Block '%s' hat keine Quelle" % (rel, name))
                        self.assertEqual(body, src[name][0][1],
                                         "%s: Block '%s' weicht von %s ab" % (rel, name, src[name][0][0]))

    def test_steps_do_not_need_to_read_plugin_files(self):
        for step in REQUIRED:
            with self.subTest(step=step):
                self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", read("skills/%s/SKILL.md" % step))


class ReviewerExampleTest(unittest.TestCase):
    """Das Reviewer-Beispiel im Marker-Vertrag zeigte REWORK mit DONE_WITH_CONCERNS.
    Ein Review-Lauf ging danach mit DONE_WITH_CONCERNS aus, obwohl er vollständig war. STATUS
    beschreibt den Lauf; das Beispiel zeigt REWORK mit DONE, in der Quelle und in jeder Kopie,
    auch in den erzeugten Herdr-Vorlagen."""

    OLD = "SLICKFAB-VERDICT: REWORK\nSLICKFAB-STATUS: DONE_WITH_CONCERNS\n"
    NEW = "SLICKFAB-VERDICT: REWORK\nSLICKFAB-STATUS: DONE\n"

    def copies(self):
        paths = [os.path.join(ROOT, "tracker", "linear.md")]
        for pattern in (("skills", "*", "SKILL.md"), ("agents", "*.md"),
                        ("runtime", "herdr", "templates", "*.md")):
            paths += glob.glob(os.path.join(ROOT, *pattern))
        return [os.path.relpath(p, ROOT) for p in sorted(paths) if "<!-- vertrag:marker -->" in read(os.path.relpath(p, ROOT))]

    def test_example_shows_rework_with_done_everywhere(self):
        copies = self.copies()
        self.assertIn("tracker/linear.md", copies)
        self.assertTrue(any(c.startswith("runtime/herdr/templates/") for c in copies))
        for rel in copies:
            marker = blocks(read(rel))["marker"][0]
            with self.subTest(file=rel):
                self.assertNotIn(self.OLD, marker)
                self.assertIn(self.NEW, marker)


if __name__ == "__main__":
    unittest.main()
