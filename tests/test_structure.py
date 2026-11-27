"""Prüft die Repo-Prüfung selbst: `sh tests/run.sh` in einem Wegwerf-Repo.

Jeder Test baut ein kleines, gültiges Plugin-Repo in einem Temp-Ordner (mit
Kopien von run.sh und check_structure.py), macht genau eine Sache kaputt und
erwartet, dass run.sh rot wird und den Grund nennt.
"""
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

VALID_SKILL = textwrap.dedent("""\
    ---
    name: demo
    description: Verwenden, wenn jemand eine Demo will.
    ---

    # Demo

    ## Wann
    Wenn eine Demo gebraucht wird.

    ## Ablauf
    1. Demo zeigen.

    ## Ergebnis
    Eine Demo.

    ## Nächster Schritt
    `spec`
    """)


class FixtureRepo:
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="slickfab-fixture-")
        os.makedirs(os.path.join(self.root, "tests"))
        for name in ("run.sh", "check_structure.py"):
            shutil.copy(os.path.join(HERE, name), os.path.join(self.root, "tests", name))
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "demo-plugin"}))
        self.write("skills/demo/SKILL.md", VALID_SKILL)

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def run(self):
        env = dict(os.environ)
        return subprocess.run(["sh", "tests/run.sh"], cwd=self.root, env=env,
                              capture_output=True, text=True, timeout=120)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


class StructureCheckTest(unittest.TestCase):
    def setUp(self):
        self.repo = FixtureRepo()
        self.addCleanup(self.repo.cleanup)

    def assertGreen(self):
        r = self.repo.run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def assertRed(self, *needles):
        r = self.repo.run()
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, "erwartet rot, war grün:\n" + out)
        for n in needles:
            self.assertIn(n, out)

    def test_valid_repo_is_green(self):
        self.assertGreen()

    def test_missing_required_section_is_red(self):
        self.repo.write("skills/demo/SKILL.md", VALID_SKILL.replace("## Ergebnis\nEine Demo.\n\n", ""))
        self.assertRed("skills/demo/SKILL.md", "Ergebnis")

    def test_missing_frontmatter_is_red(self):
        self.repo.write("skills/demo/SKILL.md", VALID_SKILL.split("---\n", 2)[2])
        self.assertRed("skills/demo/SKILL.md", "Frontmatter")

    def test_missing_name_is_red(self):
        self.repo.write("skills/demo/SKILL.md", VALID_SKILL.replace("name: demo\n", ""))
        self.assertRed("skills/demo/SKILL.md", "name")

    def test_empty_description_is_red(self):
        self.repo.write("skills/demo/SKILL.md",
                        VALID_SKILL.replace("Verwenden, wenn jemand eine Demo will.", ""))
        self.assertRed("skills/demo/SKILL.md", "description")

    def _skill_with_description(self, desc):
        return VALID_SKILL.replace("Verwenden, wenn jemand eine Demo will.", desc)

    def test_description_with_workflow_summary_over_limit_is_red(self):
        desc = ("Verwenden, wenn ein Plan geprüft werden soll. Ablauf: erst den Entscheidungsbaum "
                "aufbauen, dann je Runde alle offenen Fragen nummeriert mit Empfehlung stellen, "
                "Fakten per Sub-Agent holen, umkehrbare Fragen selbst entscheiden, Glossar und ADRs "
                "pflegen und am Ende die Liste Autonom entschieden ausgeben und spec empfehlen.")
        self.assertGreater(len(desc), 300)
        self.repo.write("skills/demo/SKILL.md", self._skill_with_description(desc))
        self.assertRed("skills/demo/SKILL.md", "description", "300")

    def test_description_exactly_at_limit_is_green(self):
        desc = "Verwenden, wenn " + "x" * (300 - len("Verwenden, wenn "))
        self.assertEqual(len(desc), 300)
        self.repo.write("skills/demo/SKILL.md", self._skill_with_description(desc))
        self.assertGreen()

    def test_block_scalar_description_over_limit_is_red(self):
        long_line = "  Verwenden, wenn " + "sehr " * 70 + "\n"
        text = VALID_SKILL.replace("description: Verwenden, wenn jemand eine Demo will.\n",
                                   "description: >\n" + long_line)
        self.repo.write("skills/demo/SKILL.md", text)
        self.assertRed("skills/demo/SKILL.md", "description")

    def test_required_section_only_inside_code_block_is_red(self):
        text = VALID_SKILL.replace("## Nächster Schritt\n`spec`\n",
                                   "Beispiel:\n\n```\n## Nächster Schritt\n`spec`\n```\n")
        self.repo.write("skills/demo/SKILL.md", text)
        self.assertRed("skills/demo/SKILL.md", "Nächster Schritt")

    def test_required_section_only_inside_tilde_block_is_red(self):
        text = VALID_SKILL.replace("## Nächster Schritt\n`spec`\n",
                                   "~~~markdown\n## Nächster Schritt\n~~~\n")
        self.repo.write("skills/demo/SKILL.md", text)
        self.assertRed("skills/demo/SKILL.md", "Nächster Schritt")

    def test_quoted_empty_description_is_red(self):
        for empty in ('""', "''"):
            with self.subTest(empty=empty):
                self.repo.write("skills/demo/SKILL.md",
                                self._skill_with_description(empty))
                self.assertRed("skills/demo/SKILL.md", "description fehlt")

    def test_quoted_empty_name_on_agent_is_red(self):
        self.repo.write("agents/r.md",
                        '---\nname: ""\ndescription: Verwenden, wenn geprüft wird.\n---\n\nText.\n')
        self.assertRed("agents/r.md", "name fehlt")

    def test_quoted_description_is_green(self):
        self.repo.write("skills/demo/SKILL.md",
                        self._skill_with_description('"Verwenden, wenn jemand eine Demo will."'))
        self.assertGreen()

    def test_agent_without_frontmatter_is_red(self):
        self.repo.write("agents/x.md", "# Rolle ohne Frontmatter\n\nPrüft PRs.\n")
        self.assertRed("agents/x.md", "Frontmatter")

    def test_new_agent_role_is_checked(self):
        self.repo.write("agents/reviewer.md", "---\nname: reviewer\n---\n\nPrüft PRs.\n")
        self.assertRed("agents/reviewer.md", "description")

    def test_valid_agent_role_is_green(self):
        self.repo.write("agents/reviewer.md",
                        "---\nname: reviewer\ndescription: Verwenden, wenn ein PR geprüft wird.\n---\n\nPrüft PRs.\n")
        self.assertGreen()

    def test_agent_description_over_limit_is_red(self):
        self.repo.write("agents/reviewer.md",
                        "---\nname: reviewer\ndescription: " + "x" * 301 + "\n---\n\nPrüft PRs.\n")
        self.assertRed("agents/reviewer.md", "description")

    def test_new_failing_shell_test_file_runs(self):
        self.repo.write("tests/test_extra.sh", "#!/bin/sh\necho 'extra-shell-test lief'\nexit 1\n")
        self.assertRed("extra-shell-test lief")

    def test_new_passing_shell_test_file_is_green(self):
        self.repo.write("tests/test_extra.sh", "#!/bin/sh\nexit 0\n")
        self.assertGreen()

    def test_new_failing_python_test_file_runs(self):
        self.repo.write("tests/test_extra.py", textwrap.dedent("""\
            import unittest
            class T(unittest.TestCase):
                def test_fails(self):
                    self.fail("extra-python-test lief")
            """))
        self.assertRed("extra-python-test lief")

    def test_plugin_manifest_invalid_json_is_red(self):
        self.repo.write(".claude-plugin/plugin.json", '{"name": "demo-plugin",}')
        self.assertRed(".claude-plugin/plugin.json", "JSON")

    def test_plugin_manifest_missing_is_red(self):
        os.remove(os.path.join(self.repo.root, ".claude-plugin", "plugin.json"))
        self.assertRed(".claude-plugin/plugin.json")

    def test_plugin_manifest_without_name_is_red(self):
        self.repo.write(".claude-plugin/plugin.json", json.dumps({"version": "0.1.0"}))
        self.assertRed(".claude-plugin/plugin.json", "name")

    def test_marketplace_invalid_json_is_red(self):
        self.repo.write(".claude-plugin/marketplace.json", "{ kaputt")
        self.assertRed(".claude-plugin/marketplace.json", "JSON")


if __name__ == "__main__":
    unittest.main()
