"""Prüft den gemeinsamen Starter beider Wächter (role_bash_guard, docs_lookup_guard) über den
registrierten Befehl aus hooks/hooks.json, so wie Claude Code ihn per Shell startet.

In einer geschützten Rolle heißt jeder Fehler des Wächters deny: Datei fehlt, Absturz beim
Laden, Frist überschritten. Außerhalb bleibt der Starter still und endet mit Exit 0, damit
ein kaputtes Plugin nie eine fremde Session anhält (Rework 1 von PR #15, Entscheidung des Masters).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "hooks"))
import docs_lookup_guard  # noqa: E402
import role_bash_guard  # noqa: E402

GUARDS = {"role_bash_guard.py": ("slickfab:reviewer", role_bash_guard.ROLES),
          "docs_lookup_guard.py": ("slickfab:docs-reader", (docs_lookup_guard.AGENT,))}
OUTSIDE = (None, "slickfab:implementer", "general-purpose")


def entries():
    with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
        hooks = json.load(f)["hooks"]["PreToolUse"]
    return {name: c for h in hooks for c in h["hooks"] for name in GUARDS if name in c["command"]}


def start(tc, guard, content, agent_type):
    """Registrierten Befehl mit einer Plugin-Kopie starten, deren Wächter `content` ist
    (None = Datei fehlt)."""
    plugin = tempfile.mkdtemp()
    tc.addCleanup(shutil.rmtree, plugin)
    os.makedirs(os.path.join(plugin, "hooks"))
    if content is not None:
        with open(os.path.join(plugin, "hooks", guard), "w", encoding="utf-8") as f:
            f.write(content)
    event = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": "git push"}, "cwd": plugin}
    if agent_type is not None:
        event.update(agent_id="a1", agent_type=agent_type)
    t0 = time.monotonic()
    r = subprocess.run(["/bin/sh", "-c", entries()[guard]["command"]], input=json.dumps(event),
                       capture_output=True, text=True, timeout=30,
                       env=dict(os.environ, CLAUDE_PLUGIN_ROOT=plugin, CLAUDE_PROJECT_DIR=plugin))
    return r, time.monotonic() - t0


BROKEN = {"Datei fehlt": None, "Syntaxfehler": "def (:\n", "Absturz beim Import": "import gibt_es_nicht\n",
          "Exit 1": "import sys\nsys.exit(1)\n"}


class StarterTest(unittest.TestCase):
    def assertDeny(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual((out["hookEventName"], out["permissionDecision"]), ("PreToolUse", "deny"))

    def test_broken_guard_denies_in_the_role(self):
        for guard, (role, _) in GUARDS.items():
            for case, content in BROKEN.items():
                with self.subTest(guard=guard, case=case):
                    self.assertDeny(start(self, guard, content, role)[0])

    def test_broken_guard_is_silent_outside(self):
        for guard in GUARDS:
            for case, content in BROKEN.items():
                for agent_type in OUTSIDE:
                    with self.subTest(guard=guard, case=case, agent_type=agent_type):
                        r, _ = start(self, guard, content, agent_type)
                        self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)

    def test_hanging_guard_denies_before_the_hook_timeout(self):
        for guard, (role, _) in GUARDS.items():
            with self.subTest(guard=guard):
                r, took = start(self, guard, "import time\ntime.sleep(60)\n", role)
                self.assertDeny(r)
                self.assertLess(took, entries()[guard]["timeout"])

    def test_hanging_guard_is_never_started_outside(self):
        for guard in GUARDS:
            r, took = start(self, guard, "import time\ntime.sleep(60)\n", "slickfab:implementer")
            self.assertEqual((r.returncode, r.stdout), (0, ""))
            self.assertLess(took, 5)

    def test_working_guard_output_passes_through(self):
        content = ('import json, sys\njson.load(sys.stdin)\njson.dump({"hookSpecificOutput": '
                   '{"hookEventName": "PreToolUse", "permissionDecision": "deny", '
                   '"permissionDecisionReason": "echt"}}, sys.stdout)\n')
        r, _ = start(self, "role_bash_guard.py", content, "slickfab:retro")
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"], "echt")
        r, _ = start(self, "role_bash_guard.py", "import sys\nsys.stdin.read()\n", "slickfab:retro")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_unreadable_input_is_left_alone(self):
        for guard in GUARDS:
            r = subprocess.run(["/bin/sh", "-c", entries()[guard]["command"]], input="kein json",
                               capture_output=True, text=True, timeout=30,
                               env=dict(os.environ, CLAUDE_PLUGIN_ROOT="/gibt/es/nicht"))
            self.assertEqual((r.returncode, r.stdout), (0, ""))


class RegistrationTest(unittest.TestCase):
    def test_both_guards_use_the_same_starter_with_their_roles(self):
        with open(os.path.join(ROOT, "hooks", "guard_start.py"), encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("'", code)   # steht in hooks.json zwischen einfachen Anführungszeichen
        found = entries()
        self.assertEqual(set(found), set(GUARDS))
        for guard, (_, roles) in GUARDS.items():
            with self.subTest(guard=guard):
                expected = "python3 -c '%s' \"${CLAUDE_PLUGIN_ROOT}/hooks/%s\" %s || true" % (
                    code, guard, ",".join(roles))
                self.assertEqual(found[guard]["command"], expected)
                self.assertEqual(found[guard]["type"], "command")
                self.assertNotIn("onFailure", found[guard])


if __name__ == "__main__":
    unittest.main()
