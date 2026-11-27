"""Die Testsuite läuft auf GitHub: .github/workflows/test.yml.

Das Repo ist öffentlich. Ohne diesen Workflow sieht ein Beitragender nicht, ob sein
Stand grün ist, und ein roter Pull Request ließe sich mergen. Geprüft wird der
Workflow als Text (ohne YAML-Bibliothek, damit die Suite ohne Abhängigkeiten
läuft): schlank (ein Job), gepinnter Runner, Python 3.9 und eine aktuelle Version,
nur Lesezugriff, Zeitlimit, alte Läufe werden abgebrochen, und er führt die
volle Suite aus, nicht den schnellen Modus.

Außerdem: CONTRIBUTING.md nennt den Testbefehl, den schnellen Modus und die Dauer.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "test.yml")
CONTRIBUTING = os.path.join(ROOT, "CONTRIBUTING.md")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def top_level_block(text, key):
    """Der eingerückte Block unter einem Schlüssel der obersten Ebene, ohne Kommentare."""
    lines = text.splitlines()
    out, inside = [], False
    for line in lines:
        if re.match(r"^%s:" % re.escape(key), line):
            inside = True
            out.append(line)
            continue
        if inside:
            if line and not line.startswith((" ", "#")):
                break
            out.append(line.split(" #", 1)[0].rstrip())
    return "\n".join(out)


def run_lines(text):
    """Alle Shell-Befehle aus `run:`-Schritten (einzeilig und als Block)."""
    cmds, block_indent = [], None
    for line in text.splitlines():
        if block_indent is not None:
            if line.strip() and len(line) - len(line.lstrip()) > block_indent:
                cmds.append(line.strip())
                continue
            block_indent = None
        m = re.match(r"^(\s*)(?:- )?run:\s*(.*)$", line)
        if m:
            if m.group(2) in ("|", ">", "|-", ">-"):
                block_indent = len(m.group(1))
            else:
                cmds.append(m.group(2).strip())
    return cmds


class TestWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.isfile(WORKFLOW), "fehlt: .github/workflows/test.yml")
        self.text = read(WORKFLOW)

    def test_triggers_only_pull_request_and_push_to_main(self):
        on = top_level_block(self.text, "on")
        self.assertRegex(on, r"\n  pull_request:")
        self.assertRegex(on, r"\n  push:\n    branches: \[main\]")
        events = re.findall(r"^  ([a-z_]+):", on, re.M)
        self.assertEqual(sorted(events), ["pull_request", "push"], on)

    def test_exactly_one_job(self):
        jobs = top_level_block(self.text, "jobs")
        names = re.findall(r"^  ([A-Za-z0-9_-]+):", jobs, re.M)
        self.assertEqual(len(names), 1, names)

    def test_runner_is_pinned(self):
        runs_on = re.findall(r"^\s*runs-on:\s*(\S+)", self.text, re.M)
        self.assertEqual(runs_on, ["ubuntu-24.04"])

    def test_matrix_is_python_39_and_one_current(self):
        m = re.search(r"python-version: \[([^\]]*)\]", self.text)
        self.assertIsNotNone(m, self.text)
        versions = [v.strip().strip("\"'") for v in m.group(1).split(",")]
        self.assertEqual(len(versions), 2, versions)
        self.assertEqual(versions[0], "3.9")
        self.assertRegex(versions[1], r"^3\.(x|1[3-9])$")
        self.assertIn("actions/setup-python@", self.text)
        self.assertIn("python-version: ${{ matrix.python-version }}", self.text)

    def test_read_only_permissions(self):
        perms = top_level_block(self.text, "permissions")
        self.assertEqual(perms.strip().splitlines(), ["permissions:", "  contents: read"])

    def test_has_timeout(self):
        m = re.search(r"\n    timeout-minutes: (\d+)\n", self.text)
        self.assertIsNotNone(m)
        self.assertTrue(10 <= int(m.group(1)) <= 30, m.group(1))

    def test_cancels_outdated_runs(self):
        conc = top_level_block(self.text, "concurrency")
        self.assertIn("cancel-in-progress: true", conc)
        self.assertIn("group:", conc)

    def test_runs_full_suite_not_fast_mode(self):
        cmds = run_lines(self.text)
        self.assertIn("sh tests/run.sh", cmds)
        self.assertFalse([c for c in cmds if "--fast" in c], cmds)

    def test_actions_versions_match_other_workflows(self):
        # Gleiche Major-Version wie in den übrigen Workflows; Dependabot hält sie aktuell.
        for action in re.findall(r"uses: (actions/checkout@\S+)", self.text):
            self.assertIn(action, read(os.path.join(ROOT, ".github", "workflows", "pr-size.yml")))


class RunLinesTest(unittest.TestCase):
    """Der Hilfsparser selbst, damit test_runs_full_suite_not_fast_mode nichts übersieht."""

    def test_block_and_inline(self):
        text = ("      - run: echo a\n"
                "      - name: x\n"
                "        run: |\n"
                "          sh tests/run.sh --fast\n"
                "          echo b\n"
                "      - run: echo c\n")
        self.assertEqual(run_lines(text), ["echo a", "sh tests/run.sh --fast", "echo b", "echo c"])


class ContributingTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.isfile(CONTRIBUTING), "fehlt: CONTRIBUTING.md")
        self.text = read(CONTRIBUTING)

    def test_names_test_command_and_fast_mode(self):
        self.assertIn("sh tests/run.sh", self.text)
        self.assertIn("sh tests/run.sh --fast", self.text)

    def test_names_duration(self):
        self.assertRegex(self.text, r"\d+\s*(minutes|seconds)")

    def test_names_python_minimum(self):
        self.assertIn("3.9", self.text)


if __name__ == "__main__":
    unittest.main()
