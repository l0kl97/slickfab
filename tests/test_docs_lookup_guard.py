"""Prüft den PreToolUse-Wächter für den Doku-Agent über seine Hook-Schnittstelle:
JSON auf stdin wie von Claude Code, Entscheidung als JSON auf stdout.

Der Wächter ist der technische Schutz gegen eingeschleuste Anweisungen in
fremder Doku: Im Agent `slickfab:docs-reader` darf nur lookup.py laufen, keine
freie Shell und kein Schreiben. Andere Agents und die Hauptsession lässt er in Ruhe.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GUARD = os.path.join(ROOT, "hooks", "docs_lookup_guard.py")
LOOKUP = os.path.join(ROOT, "skills", "docs-lookup", "lookup.py")
AGENT = "slickfab:docs-reader"


def decide(tool, tool_input, agent_type=AGENT, guard=GUARD):
    event = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": tool,
             "tool_input": tool_input, "cwd": "/tmp"}
    if agent_type is not None:
        event.update(agent_id="a1", agent_type=agent_type)
    root = os.path.dirname(os.path.dirname(guard))
    r = subprocess.run([sys.executable, guard], input=json.dumps(event), capture_output=True,
                       text=True, timeout=30, env=dict(os.environ, CLAUDE_PLUGIN_ROOT=root))
    assert r.returncode == 0, r.stderr
    if not r.stdout.strip():
        return "pass", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out.get("permissionDecisionReason", "")


class GuardTest(unittest.TestCase):
    def bash(self, command, agent_type=AGENT):
        return decide("Bash", {"command": command}, agent_type)[0]

    def test_lookup_call_passes(self):
        for cmd in ('python3 "%s" zod email message --repo .' % LOOKUP,
                    # shlex.quote: ohne Anführungszeichen, solange der Pfad keine Leerzeichen
                    # hat; liegt das Repo unter "My Code/…", wird er korrekt gequotet.
                    "python3 %s @tanstack/react-query useQuery --repo /tmp/x --url "
                    "https://tanstack.com/llms.txt --timeout 5" % shlex.quote(LOOKUP),
                    "python3 '%s' zod 'z.string().email()' --repo ." % LOOKUP):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "pass")

    def test_path_with_spaces_must_be_quoted(self):
        # Plugin-Kopie unter einem Pfad mit Leerzeichen, unabhängig davon, wo dieses Repo liegt.
        tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        root = os.path.join(tmp, "mit leer", "slickfab")
        guard = os.path.join(root, "hooks", "docs_lookup_guard.py")
        lookup = os.path.join(root, "skills", "docs-lookup", "lookup.py")
        for src, dst in ((GUARD, guard), (LOOKUP, lookup)):
            os.makedirs(os.path.dirname(dst))
            shutil.copy(src, dst)
        args = " zod email --repo ."
        for cmd, expected in (("python3 " + lookup + args, "deny"),
                              ('python3 "%s"' % lookup + args, "pass"),
                              ("python3 %s" % shlex.quote(lookup) + args, "pass")):
            with self.subTest(cmd=cmd):
                self.assertEqual(decide("Bash", {"command": cmd}, guard=guard)[0], expected)

    def test_free_shell_is_denied(self):
        for cmd in ("ls -la",
                    "cat ~/.ssh/id_rsa",
                    "touch PWNED.txt",
                    "python3 -c 'import os; os.system(\"rm -r ~\")'",
                    "python3 /tmp/other.py zod email",
                    "python3 %s/../../tests/run.sh zod" % os.path.dirname(LOOKUP),
                    'python3 "%s" zod email; touch PWNED.txt' % LOOKUP,
                    'python3 "%s" zod email && rm -rf ~' % LOOKUP,
                    'python3 "%s" zod email | sh' % LOOKUP,
                    'python3 "%s" zod $(cat ~/.ssh/id_rsa)' % LOOKUP,
                    'python3 "%s" zod `id`' % LOOKUP,
                    'python3 "%s" zod email > package-lock.json' % LOOKUP,
                    'python3 "%s" zod email\ntouch PWNED.txt' % LOOKUP,
                    'python3 "%s" zod "unclosed' % LOOKUP,
                    'FOO=1 python3 "%s" zod email' % LOOKUP,
                    ""):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd), "deny")

    def test_url_must_be_https(self):
        # Angriff aus dem Re-Review (B1): lokalen Dienst per --url auslesen.
        for args in ("evil api_token --url http://127.0.0.1:8765/secret.txt",
                     "evil api_token --url=http://127.0.0.1:8765/secret.txt",
                     "zod email --url HTTP://127.0.0.1/x",
                     "zod email --url 127.0.0.1:8765/secret.txt",
                     "zod email --url file:///etc/passwd",
                     "zod email --url",
                     "zod email --u http://127.0.0.1/x",
                     "zod email http://127.0.0.1/x"):
            with self.subTest(args=args):
                self.assertEqual(self.bash('python3 "%s" %s' % (LOOKUP, args)), "deny")
        for args in ("zod email --url https://zod.dev/llms.txt",
                     "zod email --url=https://zod.dev/llms.txt --url https://zod.dev/llms-full.txt"):
            with self.subTest(args=args):
                self.assertEqual(self.bash('python3 "%s" %s' % (LOOKUP, args)), "pass")

    def test_writing_tools_are_denied(self):
        for tool, inp in (("Write", {"file_path": "/tmp/x", "content": "x"}),
                          ("Edit", {"file_path": "/tmp/x", "old_string": "a", "new_string": "b"}),
                          ("NotebookEdit", {"notebook_path": "/tmp/x.ipynb"})):
            with self.subTest(tool=tool):
                self.assertEqual(decide(tool, inp)[0], "deny")

    def test_deny_reason_names_the_rule(self):
        decision, reason = decide("Bash", {"command": "touch PWNED.txt"})
        self.assertEqual(decision, "deny")
        self.assertIn("lookup.py", reason)

    def test_other_agents_and_main_session_are_untouched(self):
        for agent_type in (None, "general-purpose", "Explore", "slickfab:docs-reader-x"):
            with self.subTest(agent_type=agent_type):
                self.assertEqual(self.bash("touch PWNED.txt", agent_type), "pass")
                self.assertEqual(decide("Write", {"file_path": "/tmp/x", "content": ""}, agent_type)[0],
                                 "pass")

    def test_unreadable_input_is_left_alone(self):
        r = subprocess.run([sys.executable, GUARD], input="not json", capture_output=True, text=True,
                           timeout=30)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")  # kein Agent erkennbar: nicht eingreifen



def interpreters():
    """Der Wächter läuft mit dem `python3` des Nutzers; der Absturz aus dem Review tritt
    erst ab Python 3.10 auf. Darum zusätzlich jede neuere Version auf dem PATH."""
    found = [sys.executable]
    for name in ("python3.10", "python3.11", "python3.12", "python3.13", "python3.14"):
        path = shutil.which(name)
        if path and path not in found:
            found.append(path)
    return found


def run_guard(python, event):
    r = subprocess.run([python, GUARD], input=json.dumps(event), capture_output=True, text=True,
                       timeout=30, env=dict(os.environ, CLAUDE_PLUGIN_ROOT=ROOT))
    out = r.stdout.strip()
    decision = json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "pass"
    return r.returncode, decision, r.stderr


class FailClosedTest(unittest.TestCase):
    """Unerwartete Eingaben dürfen den Wächter nicht abstürzen lassen: im Doku-Agent
    heißt jeder Fehler deny, überall sonst wird durchgelassen."""

    CASES = {
        "tool_input ist eine Liste": ("Bash", ["python3", "x"]),
        "tool_input ist ein Text": ("Bash", "touch PWNED"),
        "NUL-Byte im Skriptpfad": ("Bash", {"command": 'python3 "%s\x00" zod email' % LOOKUP}),
        "einzelnes Surrogate im Skriptpfad": ("Bash", {"command": 'python3 "%s\ud800" zod email' % LOOKUP}),
        "Beispiel aus dem Review": ("Bash", {"command": 'python3 "-c__import__(\'os\').system(\'touch PWNED\')'
                                                      '#\ud800" a b'}),
    }

    def event(self, tool, tool_input, agent_type):
        e = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": tool,
             "tool_input": tool_input, "cwd": "/tmp"}
        if agent_type is not None:
            e.update(agent_id="a1", agent_type=agent_type)
        return e

    def test_docs_agent_denies_on_unexpected_input(self):
        for python in interpreters():
            for name, (tool, tool_input) in self.CASES.items():
                with self.subTest(python=python, case=name):
                    code, decision, err = run_guard(python, self.event(tool, tool_input, AGENT))
                    self.assertEqual((code, decision), (0, "deny"), err)

    def test_other_sessions_pass_the_same_input(self):
        for python in interpreters():
            for name, (tool, tool_input) in self.CASES.items():
                for agent_type in (None, "general-purpose"):
                    with self.subTest(python=python, case=name, agent_type=agent_type):
                        code, decision, err = run_guard(python, self.event(tool, tool_input, agent_type))
                        self.assertEqual((code, decision), (0, "pass"), err)

    def test_unusual_agent_type_value_does_not_crash(self):
        for agent_type in (["slickfab:docs-reader"], {"x": 1}, 7, None):
            with self.subTest(agent_type=agent_type):
                e = self.event("Bash", {"command": "touch PWNED"}, None)
                e["agent_type"] = agent_type
                code, decision, err = run_guard(sys.executable, e)
                self.assertEqual((code, decision), (0, "pass"), err)


def frontmatter(path):
    with open(path, encoding="utf-8") as f:
        head = f.read().split("---", 2)[1]
    fields = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            fields[key.strip()] = value.strip()
    return fields


class WiringTest(unittest.TestCase):
    """Kritische Verbindung: Skill → Agent-Hülle ohne Schreibwerkzeuge → Hook → Wächter."""

    def test_skill_forks_into_the_docs_agent(self):
        fm = frontmatter(os.path.join(ROOT, "skills", "docs-lookup", "SKILL.md"))
        self.assertEqual(fm.get("context"), "fork")
        self.assertEqual(fm.get("agent"), AGENT)

    def test_docs_agent_has_only_bash(self):
        fm = frontmatter(os.path.join(ROOT, "agents", AGENT.split(":")[1] + ".md"))
        self.assertEqual(fm.get("name"), AGENT.split(":")[1])
        self.assertEqual(fm.get("tools"), "Bash")

    def test_plugin_hook_runs_the_guard_for_bash_and_writes(self):
        with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
            hooks = json.load(f)["hooks"]["PreToolUse"]
        entries = [(h["matcher"], c["command"]) for h in hooks for c in h["hooks"]
                   if "docs_lookup_guard.py" in c["command"]]
        self.assertEqual(len(entries), 1, hooks)
        matcher, command = entries[0]
        for tool in ("Bash", "Write", "Edit", "NotebookEdit"):
            self.assertIn(tool, matcher.split("|"))
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)

if __name__ == "__main__":
    unittest.main()
