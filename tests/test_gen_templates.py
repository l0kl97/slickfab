"""Prüft `runtime/herdr/gen-templates` über die Befehlszeile.

Alle Ausgaben landen in Wegwerf-Ordnern unter `<repo>/.test-tmp/`, nie im
Herdr-Vorlagenverzeichnis des Benutzers. HOME zeigt in den Tests auf einen
eigenen Ordner, damit ein Fehlgriff dort sichtbar würde statt in ~/.config.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "runtime", "herdr", "gen-templates")
AGENTS = os.path.join(REPO, "agents")
CHECKED_IN = os.path.join(REPO, "runtime", "herdr", "templates")
ROLES = ("planner", "challenger", "implementer", "reviewer", "debugger", "verifier", "retro")


def scratch(test):
    base = os.path.join(REPO, ".test-tmp")
    os.makedirs(base, exist_ok=True)
    path = tempfile.mkdtemp(prefix="gen-", dir=base)
    test.addCleanup(shutil.rmtree, path, True)
    return path


def run(args, home):
    env = dict(os.environ, HOME=home)
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True,
                          env=env, timeout=60)


HERDR_LINE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*: \S")


def herdr_frontmatter(text, where):
    """Herdrs Regel nachgebildet (hc templates ist im Test nicht auf einen Wegwerf-Ordner umlenkbar):
    Datei beginnt mit `---`, bis zum zweiten `---` nur Zeilen der Form `key: value`."""
    lines = text.split("\n")
    assert lines[0] == "---", "%s: beginnt nicht mit ---" % where
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        assert HERDR_LINE.match(line), "%s: not key: value: %r" % (where, line)
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields


def snapshot(folder):
    out = {}
    for name in sorted(os.listdir(folder)):
        with open(os.path.join(folder, name), "rb") as f:
            out[name] = f.read()
    return out


class GenTemplates(unittest.TestCase):
    def test_one_template_per_role_and_stable(self):
        tmp = scratch(self)
        out = os.path.join(tmp, "out")
        first = run(["--out", out], tmp)
        self.assertEqual(first.returncode, 0, first.stderr)
        one = snapshot(out)
        self.assertEqual(sorted(one), sorted(r + ".md" for r in ROLES))
        second = run(["--out", out], tmp)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(snapshot(out), one)

    def test_each_template_says_generated_and_names_source(self):
        tmp = scratch(self)
        out = os.path.join(tmp, "out")
        self.assertEqual(run(["--out", out], tmp).returncode, 0)
        for role in ROLES:
            with open(os.path.join(out, role + ".md"), encoding="utf-8") as f:
                fields = herdr_frontmatter(f.read(), role)
            notice = fields.get("generated", "")
            self.assertIn("nicht bearbeiten", notice.lower(), role)
            self.assertIn("erzeugt", notice.lower(), role)
            self.assertIn("agents/%s.md" % role, notice, role)

    def test_frontmatter_follows_herdr_rule(self):
        # Herdr (`hc templates`) lehnt jede Vorlage ab, deren Frontmatter eine Zeile ohne
        # `key: value` hat ("not key: value"). Geprüft an frisch erzeugten und an eingecheckten Vorlagen.
        tmp = scratch(self)
        out = os.path.join(tmp, "out")
        self.assertEqual(run(["--out", out], tmp).returncode, 0)
        for folder in (out, CHECKED_IN):
            for role in ROLES:
                with open(os.path.join(folder, role + ".md"), encoding="utf-8") as f:
                    fields = herdr_frontmatter(f.read(), role)
                self.assertEqual(fields["name"], role)
                self.assertTrue(fields["command"].startswith("claude "), role)

    def test_studio_run_still_reads_command(self):
        # awk-Ausdruck aus dem früheren privaten Startskript studio-run (liest command: aus der Vorlage).
        studio = r'/^---$/{n++; next} n==1 && /^command:/{sub(/^command:[ ]*/,""); print; exit}'
        res = subprocess.run(["awk", studio, os.path.join(CHECKED_IN, "implementer.md")],
                             capture_output=True, text=True, timeout=10)
        self.assertEqual(res.stdout.strip(), "claude --model opus")
        res = subprocess.run(["awk", studio, os.path.join(CHECKED_IN, "reviewer.md")],
                             capture_output=True, text=True, timeout=10)
        self.assertRegex(res.stdout.strip(), r"^claude --disallowedTools \S+ --model \S+$")

    def test_herdr_rule_rejects_comment_line(self):
        # Die Nachbildung selbst ist scharf: genau der alte Fehler fällt durch.
        bad = "---\n# erzeugt von gen-templates\nname: x\ncommand: claude --model opus\n---\nText\n"
        with self.assertRaises(AssertionError):
            herdr_frontmatter(bad, "x")
        for line in ("name x", " name: x", "name:", ": x", ""):
            with self.assertRaises(AssertionError, msg=repr(line)):
                herdr_frontmatter("---\n%s\n---\n" % line, "x")

    def test_checked_in_templates_match_hulls(self):
        tmp = scratch(self)
        res = run(["--check", CHECKED_IN], tmp)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_check_fails_when_hull_changed_without_regenerating(self):
        tmp = scratch(self)
        agents = os.path.join(tmp, "agents")
        shutil.copytree(AGENTS, agents)
        path = os.path.join(agents, "implementer.md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace("model: opus", "model: sonnet", 1))
        res = run(["--agents", agents, "--check", CHECKED_IN], tmp)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("implementer.md", res.stderr)
        self.assertNotIn("planner.md", res.stderr)

    def test_check_fails_on_hand_edited_or_missing_template(self):
        tmp = scratch(self)
        copy = os.path.join(tmp, "tpl")
        shutil.copytree(CHECKED_IN, copy)
        with open(os.path.join(copy, "reviewer.md"), "a", encoding="utf-8") as f:
            f.write("Von Hand ergänzt.\n")
        os.remove(os.path.join(copy, "retro.md"))
        with open(os.path.join(copy, "alt.md"), "w", encoding="utf-8") as f:
            f.write("Vorlage einer gelöschten Rolle\n")
        res = run(["--check", copy], tmp)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("reviewer.md passt nicht", res.stderr)
        self.assertIn("retro.md fehlt", res.stderr)
        self.assertIn("alt.md hat keine Hülle mehr", res.stderr)
        self.assertEqual(sorted(os.listdir(copy)), sorted(["alt.md"] + [r + ".md" for r in ROLES if r != "retro"]),
                         "--check schreibt und löscht nichts")

    def test_check_fails_on_orphan_template_alone(self):
        tmp = scratch(self)
        copy = os.path.join(tmp, "tpl")
        shutil.copytree(CHECKED_IN, copy)
        with open(os.path.join(copy, "alt.md"), "w", encoding="utf-8") as f:
            f.write("Vorlage einer gelöschten Rolle\n")
        res = run(["--check", copy], tmp)
        self.assertEqual(res.returncode, 1)
        self.assertIn("alt.md hat keine Hülle mehr", res.stderr)

    def broken_hull(self, role, old, new):
        tmp = scratch(self)
        agents = os.path.join(tmp, "agents")
        shutil.copytree(AGENTS, agents)
        path = os.path.join(agents, role + ".md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))
        out = os.path.join(tmp, "out")
        os.makedirs(out)
        return run(["--agents", agents, "--out", out], tmp), out

    def assert_refused(self, res, out, *words):
        self.assertNotEqual(res.returncode, 0)
        for w in words:
            self.assertIn(w, res.stderr)
        self.assertNotIn("Traceback", res.stderr)
        self.assertEqual(os.listdir(out), [], "keine halbe Vorlage, auch nicht für andere Rollen")

    def test_missing_model_writes_nothing(self):
        res, out = self.broken_hull("verifier", "model: opus\n", "")
        self.assert_refused(res, out, "verifier.md", "model")

    def test_empty_model_writes_nothing(self):
        res, out = self.broken_hull("verifier", "model: opus\n", "model:\n")
        self.assert_refused(res, out, "verifier.md", "model")

    def test_missing_step_writes_nothing(self):
        res, out = self.broken_hull("challenger", "schritt: challenge\n", "")
        self.assert_refused(res, out, "challenger.md", "schritt")

    def test_missing_name_writes_nothing(self):
        res, out = self.broken_hull("planner", "name: planner\n", "")
        self.assert_refused(res, out, "planner.md", "Pflichtfeld fehlt oder ist leer: name")

    def test_missing_description_writes_nothing(self):
        with open(os.path.join(AGENTS, "implementer.md"), encoding="utf-8") as f:
            line = next(l for l in f.read().splitlines(True) if l.startswith("description:"))
        res, out = self.broken_hull("implementer", line, "")
        self.assert_refused(res, out, "implementer.md", "Pflichtfeld fehlt oder ist leer: description")

    def test_empty_step_writes_nothing(self):
        res, out = self.broken_hull("challenger", "schritt: challenge\n", "schritt:\n")
        self.assert_refused(res, out, "challenger.md", "schritt")

    def test_quoted_empty_fields_write_nothing(self):
        for old, new, word in (("schritt: challenge\n", 'schritt: ""\n', "schritt"),
                               ("model: opus\n", "model: ''\n", "model")):
            res, out = self.broken_hull("challenger", old, new)
            self.assert_refused(res, out, "challenger.md", word)

    def test_quoted_model_is_unquoted(self):
        tmp = scratch(self)
        agents = os.path.join(tmp, "agents")
        shutil.copytree(AGENTS, agents)
        path = os.path.join(agents, "debugger.md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace("model: opus\n", 'model: "sonnet"\n', 1))
        out = os.path.join(tmp, "out")
        self.assertEqual(run(["--agents", agents, "--out", out], tmp).returncode, 0)
        with open(os.path.join(out, "debugger.md"), encoding="utf-8") as f:
            self.assertIn("command: claude --model sonnet", f.read().splitlines())

    def test_broken_encoding_fails_cleanly(self):
        tmp = scratch(self)
        agents = os.path.join(tmp, "agents")
        shutil.copytree(AGENTS, agents)
        with open(os.path.join(agents, "retro.md"), "ab") as f:
            f.write(b"\xff\xfe kaputt\n")
        out = os.path.join(tmp, "out")
        os.makedirs(out)
        self.assert_refused(run(["--agents", agents, "--out", out], tmp), out, "retro.md")
        tpl = os.path.join(tmp, "tpl")
        shutil.copytree(CHECKED_IN, tpl)
        with open(os.path.join(tpl, "planner.md"), "ab") as f:
            f.write(b"\xff\xfe kaputt\n")
        res = run(["--check", tpl], tmp)
        self.assertEqual(res.returncode, 1)
        self.assertIn("planner.md", res.stderr)
        self.assertNotIn("Traceback", res.stderr)

    def test_block_scalar_is_refused(self):
        with open(os.path.join(AGENTS, "verifier.md"), encoding="utf-8") as f:
            line = next(l for l in f.read().splitlines(True) if l.startswith("description:"))
        for indicator in (">", "|", ">-", "|+"):
            res, out = self.broken_hull("verifier", line, "description: %s\n  Prüft das Ziel.\n  Zweite Zeile.\n" % indicator)
            self.assert_refused(res, out, "verifier.md", "description", "Blockskalar")
        res, out = self.broken_hull("verifier", "schritt: verify\n", "schritt: >\n  verify\n")
        self.assert_refused(res, out, "verifier.md", "schritt", "Blockskalar")

    def test_quoted_description_is_kept_as_written(self):
        tmp = scratch(self)
        agents = os.path.join(tmp, "agents")
        shutil.copytree(AGENTS, agents)
        path = os.path.join(agents, "debugger.md")
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines(True)
        quoted = 'description: "Sucht Fehler: rote Schleife zuerst."\n'
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(quoted if l.startswith("description:") else l for l in lines))
        out = os.path.join(tmp, "out")
        self.assertEqual(run(["--agents", agents, "--out", out], tmp).returncode, 0)
        with open(os.path.join(out, "debugger.md"), encoding="utf-8") as f:
            self.assertIn(quoted, f.read())

    def test_hull_without_frontmatter_writes_nothing(self):
        res, out = self.broken_hull("debugger", "---\nname: debugger", "name: debugger")
        self.assert_refused(res, out, "debugger.md", "Frontmatter")

    def test_model_with_shell_characters_writes_nothing(self):
        res, out = self.broken_hull("retro", "model: opus\n", "model: opus; touch x\n")
        self.assert_refused(res, out, "retro.md", "model")

    def test_without_target_never_touches_herdr_templates(self):
        home = scratch(self)
        herdr = os.path.join(home, ".config", "herdr-core", "templates")
        os.makedirs(herdr)
        with open(os.path.join(herdr, "implementer.md"), "w", encoding="utf-8") as f:
            f.write("handgeschrieben\n")
        before = snapshot(herdr)
        for args in ([], ["--agents", AGENTS]):
            res = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True,
                                 env=dict(os.environ, HOME=home), cwd=herdr, timeout=60)
            self.assertNotEqual(res.returncode, 0, args)
            self.assertIn("--out", res.stderr)
            self.assertEqual(snapshot(herdr), before, args)

    def test_out_is_a_file_fails_cleanly(self):
        tmp = scratch(self)
        out = os.path.join(tmp, "datei")
        open(out, "w").close()
        res = run(["--out", out], tmp)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("datei", res.stderr)
        self.assertNotIn("Traceback", res.stderr)

    def test_tool_boundary_of_hull_is_in_command(self):
        # Werte aus docs/features/agent-rollen.md (Werkzeuggrenzen je Rolle).
        expected = {
            "planner": "claude --disallowedTools Bash,Edit,Write,NotebookEdit --model opus",
            "challenger": "claude --disallowedTools Bash,Edit,Write,NotebookEdit,Agent,Task --model opus",
            "verifier": "claude --disallowedTools Edit,Write,NotebookEdit --model opus",
            "retro": "claude --disallowedTools Edit,Write,NotebookEdit --model opus",
            "reviewer": "claude --disallowedTools Write,NotebookEdit --model opus",
            "implementer": "claude --model opus",
            "debugger": "claude --model opus",
        }
        tmp = scratch(self)
        out = os.path.join(tmp, "out")
        self.assertEqual(run(["--out", out], tmp).returncode, 0)
        for role, command in expected.items():
            with open(os.path.join(out, role + ".md"), encoding="utf-8") as f:
                lines = f.read().splitlines()
            self.assertIn("command: " + command, lines, role)

    def test_tool_allowlist_is_refused_not_dropped(self):
        res, out = self.broken_hull("debugger", "model: opus\n", "model: opus\ntools: Read, Grep\n")
        self.assert_refused(res, out, "debugger.md", "tools")

    def test_unknown_frontmatter_keys_are_refused_not_dropped(self):
        for extra, key in (("permissionMode: plan\n", "permissionMode"),
                           ("hooks:\n  PreToolUse:\n    - matcher: Bash\n", "hooks"),
                           ("mcpServers: [linear]\n", "mcpServers")):
            res, out = self.broken_hull("reviewer", "model: opus\n", "model: opus\n" + extra)
            self.assert_refused(res, out, "reviewer.md", key)

    def test_odd_tool_boundary_writes_nothing(self):
        res, out = self.broken_hull("reviewer", "disallowedTools: Write, NotebookEdit\n",
                                    "disallowedTools: Write; touch x\n")
        self.assert_refused(res, out, "reviewer.md", "disallowedTools")


if __name__ == "__main__":
    unittest.main()
