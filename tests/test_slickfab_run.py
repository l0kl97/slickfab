"""Prüft `runtime/herdr/slickfab-run` über die Befehlszeile.

`hc` ist die Systemgrenze zu Herdr und wird durch ein kleines Skript im PATH
ersetzt, das seinen Aufruf als JSON ablegt. Kein Test startet ein echtes
Terminal oder einen Agent. Ordner liegen unter `<repo>/.test-tmp/`.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "runtime", "herdr", "slickfab-run")
AGENTS = os.path.join(REPO, "agents")

# `hc` ist ein Shell-Wrapper: Er schreibt im Modus hang seine PID (atomar), bevor der
# Python-Interpreter startet; `exec` behält die PID. So hängt der Test nicht davon ab, wie
# schnell Python unter Last startet (Review A2). PATH enthält nur bin/, darum /bin/mv.
FAKE_HC_SH = """#!/bin/sh
if [ "$FAKE_HC_MODE" = hang ]; then
  echo $$ > "$FAKE_HC_LOG.pid.tmp" && /bin/mv "$FAKE_HC_LOG.pid.tmp" "$FAKE_HC_LOG.pid"
fi
exec "%s" "${0%%/*}/fake_hc.py" "$@"
"""

FAKE_HC = """import json, os, sys, time
mode = os.environ.get("FAKE_HC_MODE", "ok")
if mode == "hang":
    # hängt, bis es beendet wird; spätestens wenn der Test seinen Ordner aufräumt, endet es selbst
    tmp, end = os.path.dirname(os.environ["FAKE_HC_LOG"]), time.monotonic() + 600
    while os.path.isdir(tmp) and time.monotonic() < end:
        time.sleep(0.1)
    sys.exit(9)
with open(os.environ["FAKE_HC_LOG"], "w", encoding="utf-8") as f:
    json.dump(sys.argv[1:], f)
if mode == "fail":
    print("core nicht erreichbar", file=sys.stderr)
    sys.exit(3)
print("t42")
"""


class Env:
    def __init__(self, test, with_hc=True):
        base = os.path.join(REPO, ".test-tmp")
        os.makedirs(base, exist_ok=True)
        self.tmp = tempfile.mkdtemp(prefix="run-", dir=base)
        test.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = os.path.join(self.tmp, "bin")
        self.work = os.path.join(self.tmp, "work")
        os.makedirs(self.bin)
        os.makedirs(self.work)
        self.log = os.path.join(self.tmp, "hc.json")
        if with_hc:
            with open(os.path.join(self.bin, "fake_hc.py"), "w", encoding="utf-8") as f:
                f.write(FAKE_HC)
            hc = os.path.join(self.bin, "hc")
            with open(hc, "w", encoding="utf-8") as f:
                f.write(FAKE_HC_SH % sys.executable)
            os.chmod(hc, 0o755)

    def run(self, args, mode="ok", timeout=60, extra=None):
        env = {"PATH": self.bin, "HOME": self.tmp, "FAKE_HC_LOG": self.log, "FAKE_HC_MODE": mode}
        env.update(extra or {})
        return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True,
                              env=env, timeout=timeout)

    def call(self):
        with open(self.log, encoding="utf-8") as f:
            return json.load(f)


def wait_for(cond, limit=60):
    """Wartet auf einen Zustand statt eine feste Zeit; die Obergrenze greift nur, wenn er nie kommt."""
    deadline = time.monotonic() + limit
    while not cond():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)
    return True


def read_pid(path):
    with open(path) as f:
        return int(f.read())


def gone(pid):
    """True, sobald der Prozess nicht mehr existiert; lebt er nach der Obergrenze noch, wird er
    beendet (kein Rest für die nächsten Tests) und das Ergebnis ist False."""
    def dead():
        try:
            os.kill(pid, 0)
            return False
        except ProcessLookupError:
            return True
    if wait_for(dead, limit=30):
        return True
    os.kill(pid, signal.SIGKILL)
    return False


def labels(argv):
    return [argv[i + 1] for i, a in enumerate(argv) if a == "--label"]


class SlickfabRun(unittest.TestCase):
    def test_starts_role_with_task_and_labels(self):
        e = Env(self)
        res = e.run(["implementer", "impl-126", e.work, "sp1", "Baue EX-126.", "EX-126"])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("t42", res.stdout)
        argv = e.call()
        self.assertEqual(argv[:2], ["run", "--bg"])
        self.assertEqual(argv[argv.index("--name") + 1], "impl-126")
        self.assertEqual(argv[argv.index("--cwd") + 1], e.work)
        self.assertEqual(sorted(labels(argv)), sorted([
            "studio.role=implementer", "studio.issue=EX-126", "herdr.space=sp1", "slickfab.dispatch=1"]))
        self.assertEqual(argv[-4:-1], ["claude", "--model", "opus"])
        prompt = argv[-1]
        self.assertTrue(prompt.endswith("\n\n## Auftrag\nBaue EX-126."), prompt[-80:])
        self.assertIn("Du bist der Umsetzer.", prompt)
        self.assertNotIn("model: opus", prompt, "Frontmatter gehört nicht in die erste Nachricht")

    def test_without_issue_and_space_only_role_and_dispatch(self):
        e = Env(self)
        res = e.run(["reviewer", "rev-1", e.work, "-", "Prüfe PR 7."])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(sorted(labels(e.call())), ["slickfab.dispatch=1", "studio.role=reviewer"])

    def test_model_option_overrides_role_model(self):
        e = Env(self)
        res = e.run(["--model", "sonnet", "implementer", "impl-1", e.work, "-", "Klein.", "EX-9"])
        self.assertEqual(res.returncode, 0, res.stderr)
        argv = e.call()
        self.assertEqual(argv[-4:-1], ["claude", "--model", "sonnet"])
        self.assertEqual(argv.count("--model"), 1)
        self.assertNotIn("opus", argv[:-1])

    def test_effort_option_reaches_claude(self):
        # Nachbessern Runde 3: frischer Umsetzer mit höherer Reasoning-Effort.
        e = Env(self)
        res = e.run(["--effort", "high", "--model", "opus", "implementer", "impl-1", e.work, "-", "R3.", "EX-9"])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(e.call()[-6:-1], ["claude", "--model", "opus", "--effort", "high"])
        res = e.run(["implementer", "impl-1", e.work, "-", "Ohne.", "EX-9"])
        self.assertNotIn("--effort", e.call())

    def test_invalid_effort_is_refused_before_hc(self):
        e = Env(self)
        for bad in ("extreme", "-p", "", "high; rm"):
            res = e.run(["--effort", bad, "implementer", "impl-1", e.work, "-", "x"])
            self.assertEqual(res.returncode, 2, bad)
            self.assertIn("effort", res.stderr, bad)
            self.assertFalse(os.path.exists(e.log), bad)

    def test_invalid_model_is_refused_before_hc(self):
        e = Env(self)
        for bad in ("opus; touch x", "-p", ""):
            res = e.run(["--model", bad, "implementer", "impl-1", e.work, "-", "x"])
            self.assertEqual(res.returncode, 2, bad)
            self.assertIn("model", res.stderr, bad)
            self.assertFalse(os.path.exists(e.log), bad)

    def assert_refused(self, e, res, code, *words):
        self.assertEqual(res.returncode, code, res.stderr)
        for w in words:
            self.assertIn(w, res.stderr)
        self.assertNotIn("Traceback", res.stderr)

    def test_unknown_role(self):
        e = Env(self)
        for role in ("foo", "docs-reader", "../agents/implementer", "Implementer", ""):
            res = e.run([role, "n1", e.work, "-", "x"])
            self.assert_refused(e, res, 2, "Rolle")
            self.assertFalse(os.path.exists(e.log), role)

    def test_empty_task(self):
        e = Env(self)
        for task in ("", "   ", "\n\t\n"):
            res = e.run(["implementer", "n1", e.work, "-", task, "EX-1"])
            self.assert_refused(e, res, 2, "Auftrag")
            self.assertFalse(os.path.exists(e.log), repr(task))

    def test_missing_folder(self):
        e = Env(self)
        res = e.run(["implementer", "n1", os.path.join(e.tmp, "gibtsnicht"), "-", "x"])
        self.assert_refused(e, res, 2, "Ordner", "gibtsnicht")
        self.assertFalse(os.path.exists(e.log))

    def test_wrong_number_of_arguments(self):
        e = Env(self)
        for args in ([], ["implementer", "n1", e.work, "-"], ["implementer", "n1", e.work, "-", "x", "EX-1", "zuviel"],
                     ["--model"], ["--model", "sonnet"], ["--model", "sonnet", "implementer"]):
            res = e.run(args)
            self.assert_refused(e, res, 2, "usage")
            self.assertFalse(os.path.exists(e.log), args)

    def test_invalid_name_issue_or_space(self):
        e = Env(self)
        for args in (["implementer", "-x", e.work, "-", "t"],
                     ["implementer", "Name mit Leer", e.work, "-", "t"],
                     ["implementer", "n" * 33, e.work, "-", "t"],
                     ["implementer", "n1", e.work, "a=b", "t"],
                     ["implementer", "n1", e.work, "-", "t", "SLI 1"],
                     ["implementer", "n1", e.work, "-", "t", "-x"]):
            res = e.run(args)
            self.assert_refused(e, res, 2)
            self.assertFalse(os.path.exists(e.log), args)

    def copy_agents(self, e, role, old, new):
        agents = os.path.join(e.tmp, "agents")
        shutil.copytree(AGENTS, agents)
        path = os.path.join(agents, role + ".md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))
        return agents

    def test_other_agents_folder(self):
        e = Env(self)
        agents = self.copy_agents(e, "debugger", "model: opus\n", "model: sonnet\n")
        for args in (["--agents", agents], ["--agents", agents, "--model", "haiku"], ["--model", "haiku", "--agents", agents]):
            res = e.run(args + ["debugger", "dbg-1", e.work, "-", "x"])
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(e.call()[-4:-1], ["claude", "--model", "haiku" if "--model" in args else "sonnet"])

    def test_broken_hull_fails_cleanly(self):
        e = Env(self)
        for old, new, word in (("model: opus\n", "model: opus; x\n", "model"),
                               ("model: opus\n", "model: opus\npermissionMode: plan\n", "permissionMode")):
            agents = self.copy_agents(e, "implementer", old, new)
            res = e.run(["--agents", agents, "implementer", "n1", e.work, "-", "x"])
            self.assert_refused(e, res, 1, "Hülle nicht lesbar", "implementer.md", word)
            self.assertFalse(os.path.exists(e.log))
            shutil.rmtree(agents)

    def test_option_twice_is_refused(self):
        e = Env(self)
        for args in (["--model", "sonnet", "--model", "haiku"], ["--agents", AGENTS, "--agents", AGENTS]):
            res = e.run(args + ["implementer", "n1", e.work, "-", "x"])
            self.assert_refused(e, res, 2, "usage")
            self.assertFalse(os.path.exists(e.log), args)

    def test_missing_agents_folder(self):
        e = Env(self)
        for args in (["--agents", os.path.join(e.tmp, "gibtsnicht")], ["--agents"]):
            res = e.run(args + ["implementer", "n1", e.work, "-", "x"])
            self.assert_refused(e, res, 2, "agents")
            self.assertFalse(os.path.exists(e.log), args)

    def test_hc_missing(self):
        e = Env(self, with_hc=False)
        res = e.run(["implementer", "n1", e.work, "-", "x"])
        self.assert_refused(e, res, 1, "hc")

    def test_hc_fails(self):
        e = Env(self)
        res = e.run(["implementer", "n1", e.work, "-", "x"], mode="fail")
        self.assert_refused(e, res, 1, "hc", "core nicht erreichbar")

    def test_invalid_hc_timeout_is_refused_before_hc(self):
        e = Env(self)
        for bad in ("0", "-1", "abc", "", "nan", "inf", "-inf"):
            res = e.run(["implementer", "n1", e.work, "-", "x"], extra={"SLICKFAB_HC_TIMEOUT": bad})
            self.assert_refused(e, res, 2, "SLICKFAB_HC_TIMEOUT")
            self.assertFalse(os.path.exists(e.log), bad)

    def test_hc_hangs(self):
        e = Env(self)
        # hc hängt; endet der Aufruf vor der großzügigen Obergrenze, hat die Zeitgrenze gegriffen.
        # 5 s decken den Start der Shell bis zur PID-Datei auch unter Last ab (Review A2).
        res = e.run(["implementer", "n1", e.work, "-", "x"], mode="hang", timeout=120,
                    extra={"SLICKFAB_HC_TIMEOUT": "5"})
        self.assert_refused(e, res, 1, "hc", "Zeitgrenze")
        pidfile = e.log + ".pid"
        self.assertTrue(os.path.exists(pidfile), "hc startete nicht vor der Zeitgrenze")
        self.assertTrue(gone(read_pid(pidfile)), "hc läuft nach der Zeitgrenze weiter")

    def test_task_with_quotes_newlines_and_dollar_arrives_unchanged(self):
        e = Env(self)
        task = ('Sag "hallo" und \'tschüss\'\nZeile 2: $HOME ${PATH} `touch pwned1` $(touch pwned2)\n'
                '; touch pwned3 && echo \\n --label studio.role=reviewer\n')
        res = e.run(["implementer", "n1", e.work, "-", task, "EX-1"])
        self.assertEqual(res.returncode, 0, res.stderr)
        argv = e.call()
        self.assertTrue(argv[-1].endswith("\n## Auftrag\n" + task))
        self.assertEqual(labels(argv).count("studio.role=implementer"), 1)
        self.assertNotIn("studio.role=reviewer", labels(argv))
        for root, _, files in os.walk(e.tmp):
            self.assertFalse([f for f in files if f.startswith("pwned")], root)

    def test_task_that_looks_like_an_option(self):
        e = Env(self)
        res = e.run(["implementer", "n1", e.work, "-", "--model"])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(e.call()[-1].endswith("## Auftrag\n--model"))

    def test_tool_boundary_of_role_reaches_claude(self):
        e = Env(self)
        res = e.run(["--model", "sonnet", "reviewer", "rev-2", e.work, "-", "Prüfe PR 8.", "EX-8"])
        self.assertEqual(res.returncode, 0, res.stderr)
        argv = e.call()
        self.assertEqual(argv[-6:-1], ["claude", "--disallowedTools", "Write,NotebookEdit", "--model", "sonnet"])
        self.assertTrue(argv[-1].endswith("## Auftrag\nPrüfe PR 8."))

    def test_ctrl_c_also_stops_hc(self):
        e = Env(self)
        env = {"PATH": e.bin, "HOME": e.tmp, "FAKE_HC_LOG": e.log, "FAKE_HC_MODE": "hang"}
        # SIGINT auf Standard: läuft die Suite als Hintergrundjob, käme Strg-C sonst nie an.
        proc = subprocess.Popen([sys.executable, SCRIPT, "implementer", "n1", e.work, "-", "x"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        pidfile = e.log + ".pid"
        self.assertTrue(wait_for(lambda: os.path.exists(pidfile)), "hc startete nicht")
        hc_pid = read_pid(pidfile)
        proc.send_signal(signal.SIGINT)
        proc.communicate(timeout=60)
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(gone(hc_pid), "hc läuft nach Strg-C weiter")


if __name__ == "__main__":
    unittest.main()
