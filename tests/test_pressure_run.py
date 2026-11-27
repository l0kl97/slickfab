"""Sicherheitsrahmen und Ablage von tests/pressure/run.sh (Review PR #20 R1).

run.sh läuft hier mit einem nachgestellten `claude` im PATH, der seine Argumente und den Prompt
aufschreibt und eine stream-json-Zeile ausgibt. Geprüft wird, was run.sh an claude übergibt
(kein echtes Linear, Sandbox an, keine Nutzer-Einstellungen, Kontrolle ohne Plugin) und was es
ablegt (bereinigt, ohne Home-Pfade). Es läuft kein echtes Modell.
"""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUN_SH = os.path.join(HERE, "pressure", "run.sh")
TMP_ROOT = os.path.join(ROOT, ".test-tmp")

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys, time
if sys.argv[1:] == ["--version"]:
    print("0.0.0 (Fake)")
    sys.exit(0)
log = os.environ["FAKE_CLAUDE_LOG"]
with open(log + ".argv", "w") as f:
    json.dump(sys.argv[1:], f)
with open(log + ".prompt", "w") as f:
    f.write(sys.stdin.read())
with open(log + ".cwd", "w") as f:
    f.write(os.getcwd())
if os.environ.get("FAKE_CLAUDE_ENKEL"):
    import subprocess
    enkel = subprocess.Popen(["sh", "-c", "while :; do echo x >> \"$0\"; sleep 0.2; done", log + ".enkel"])
    with open(log + ".enkel.pid", "w") as f:
        f.write(str(enkel.pid))
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
home = os.environ.get("HOME", "")
print(json.dumps({"type": "system", "subtype": "init", "cwd": os.getcwd(), "session_id": "geheim-123"}))
print(json.dumps({"type": "assistant", "message": {"content": [
    {"type": "text", "text": "Ich lese %s/notizen.txt und %s" % (home, os.getcwd())},
    {"type": "tool_use", "name": "Bash", "input": {"command": "cat %s/.ssh/id_rsa; echo sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWX" % home}}]}}))
print(json.dumps({"type": "user", "message": {"content": [
    {"type": "tool_result", "content": "x" * 5000}]}}))
print(json.dumps({"type": "result", "result": "Fertig.\n\nSLICKFAB-STATUS: BLOCKED", "total_cost_usd": 0.5, "num_turns": 3}))
'''


class RunShTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TMP_ROOT, exist_ok=True)
        self.work = tempfile.mkdtemp(dir=TMP_ROOT)
        self.addCleanup(shutil.rmtree, self.work, True)
        self.bin = os.path.join(self.work, "bin")
        os.makedirs(self.bin)
        fake = os.path.join(self.bin, "claude")
        with open(fake, "w") as f:
            f.write(FAKE_CLAUDE)
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        self.log = os.path.join(self.work, "claude")
        self.ablage = os.path.join(self.work, "ablage")
        self.env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"],
                        FAKE_CLAUDE_LOG=self.log,
                        PRESSURE_TMP=os.path.join(self.work, "tmp"),
                        PRESSURE_ABLAGE=self.ablage)

    def run_sh(self, szenario, arm, **extra):
        env = dict(self.env, **extra)
        return subprocess.run(["sh", RUN_SH, szenario, arm], env=env, capture_output=True, text=True,
                              timeout=120)

    def argv(self):
        with open(self.log + ".argv") as f:
            return json.load(f)

    def prompt(self):
        with open(self.log + ".prompt") as f:
            return f.read()

    def opt(self, argv, name):
        """Werte nach einer Option bis zur nächsten Option."""
        self.assertIn(name, argv)
        i = argv.index(name) + 1
        out = []
        while i < len(argv) and not argv[i].startswith("--"):
            out.append(argv[i])
            i += 1
        return out

    def assertRahmen(self, argv):
        self.assertIn("-p", argv)
        self.assertIn("--strict-mcp-config", argv)
        with open(self.opt(argv, "--mcp-config")[0]) as f:
            servers = json.load(f)["mcpServers"]
        self.assertEqual(list(servers), ["linear"])
        self.assertTrue(servers["linear"]["args"][0].endswith("tests/pressure/fake_linear_mcp.py"))
        self.assertEqual(self.opt(argv, "--setting-sources"), ["project,local"])
        sandbox = json.loads(self.opt(argv, "--settings")[0])["sandbox"]
        self.assertIs(sandbox["enabled"], True)
        self.assertIs(sandbox["allowUnsandboxedCommands"], False)
        self.assertNotIn("excludedCommands", sandbox)
        self.assertEqual(self.opt(argv, "--permission-mode"), ["acceptEdits"])
        self.assertEqual(self.opt(argv, "--allowedTools"), ["mcp__linear"])
        self.assertTrue({"WebFetch", "WebSearch"} <= set(self.opt(argv, "--disallowedTools")))
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertEqual(len(self.opt(argv, "--max-budget-usd")), 1)
        self.assertEqual(self.opt(argv, "--model"), ["opus"])

    def test_neu_rahmen_und_plugin(self):
        res = self.run_sh("debugger/1-nicht-reproduzierbar", "neu")
        self.assertEqual(res.returncode, 0, res.stderr)
        argv = self.argv()
        self.assertRahmen(argv)
        self.assertEqual(self.opt(argv, "--agent"), ["slickfab:debugger"])
        plugin = self.opt(argv, "--plugin-dir")[0]
        self.assertTrue(os.path.isfile(os.path.join(plugin, "agents", "debugger.md")))
        with open(self.log + ".cwd") as f:
            cwd = f.read()
        self.assertFalse(cwd.startswith(plugin + os.sep), "Wegwerf-Repo liegt im Plugin-Ordner")

    def test_kontrolle_ohne_plugin_mit_versionierter_vorlage(self):
        res = self.run_sh("implementer/2-test-im-weg", "kontrolle")
        self.assertEqual(res.returncode, 0, res.stderr)
        argv = self.argv()
        self.assertRahmen(argv)
        self.assertNotIn("--plugin-dir", argv)
        self.assertNotIn("--agent", argv)
        with open(os.path.join(HERE, "pressure", "kontrolle", "implementer.md")) as f:
            vorlage = f.read()
        body = vorlage.split("---\n", 2)[2].strip()
        prompt = self.prompt()
        self.assertTrue(prompt.startswith(body[:200]), prompt[:300])
        with open(os.path.join(HERE, "pressure", "implementer", "2-test-im-weg", "auftrag.md")) as f:
            auftrag = f.read().strip()
        self.assertIn("## Auftrag\n" + auftrag, prompt)

    def test_kontrolle_ohne_vorlage_nur_auftrag(self):
        res = self.run_sh("debugger/1-nicht-reproduzierbar", "kontrolle")
        self.assertEqual(res.returncode, 0, res.stderr)
        with open(os.path.join(HERE, "pressure", "debugger", "1-nicht-reproduzierbar", "auftrag.md")) as f:
            auftrag = f.read().strip()
        self.assertTrue(self.prompt().startswith(auftrag))
        self.assertNotIn("--plugin-dir", self.argv())

    def test_beide_arme_gleicher_rahmen(self):
        self.run_sh("reviewer/1-nicht-melden", "neu")
        neu = self.argv()
        self.run_sh("reviewer/1-nicht-melden", "kontrolle")
        kontrolle = self.argv()

        def ohne_plugin(argv):
            out, skip = [], 0
            for a in argv:
                if skip:
                    skip -= 1
                    continue
                if a in ("--plugin-dir", "--agent"):
                    skip = 1
                    continue
                out.append(a)
            return [a for a in out if not a.endswith("mcp.json")]

        self.assertEqual(ohne_plugin(neu), ohne_plugin(kontrolle))

    def test_fehlende_vorlage_bricht_ab_statt_still_ohne_anleitung(self):
        leer = os.path.join(self.work, "keine-vorlagen")
        os.makedirs(leer)
        res = self.run_sh("reviewer/1-nicht-melden", "kontrolle", PRESSURE_VORLAGEN=leer)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Vorlage", res.stderr)
        self.assertFalse(os.path.exists(self.log + ".argv"), "claude lief trotz fehlender Vorlage")

    def test_ablage_bereinigt(self):
        res = self.run_sh("implementer/1-gate-rot-schnell", "neu")
        self.assertEqual(res.returncode, 0, res.stderr)
        d = os.path.join(self.ablage, "implementer", "runs", "1-gate-rot-schnell-neu")
        for name in ("ergebnis.md", "befehle.md", "nachher.md", "transkript.md", "lauf.md"):
            self.assertTrue(os.path.isfile(os.path.join(d, name)), name)
        alles = ""
        for name in os.listdir(d):
            with open(os.path.join(d, name), encoding="utf-8") as f:
                alles += f.read()
        self.assertIn("SLICKFAB-STATUS: BLOCKED", alles)
        self.assertNotIn(os.environ["HOME"], alles)
        self.assertNotIn(ROOT, alles)
        self.assertNotIn("sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWX", alles)
        self.assertNotIn("geheim-123", alles)
        self.assertNotIn("x" * 2000, alles)  # Rohausgaben gekürzt
        with open(os.path.join(d, "lauf.md"), encoding="utf-8") as f:
            lauf = f.read()
        for teil in ("neue Rolle slickfab:implementer", "opus", "--strict-mcp-config", "0.5"):
            self.assertIn(teil, lauf)
        self.assertRegex(lauf, r"Plugin-Prüfsumme [0-9a-f]{16}")

    def test_kontrolle_vermerkt_vorlage_mit_pruefsumme(self):
        self.run_sh("planner/1-egal-mach-du", "kontrolle")
        with open(os.path.join(self.ablage, "planner", "runs", "1-egal-mach-du-kontrolle", "lauf.md")) as f:
            lauf = f.read()
        self.assertIn("tests/pressure/kontrolle/planner.md", lauf)
        self.assertRegex(lauf, r"sha256 [0-9a-f]{64}")

    def test_neuer_lauf_ersetzt_alte_bewertung(self):
        d = os.path.join(self.ablage, "debugger", "runs", "2-falsche-theorie-neu")
        os.makedirs(d)
        with open(os.path.join(d, "bewertung.md"), "w") as f:
            f.write("alt")
        self.run_sh("debugger/2-falsche-theorie", "neu")
        self.assertFalse(os.path.exists(os.path.join(d, "bewertung.md")))

    def test_haengender_lauf_endet_mit_zeitgrenze(self):
        start = time.time()
        res = self.run_sh("retro/2-unbelegtes-muster", "neu", PRESSURE_TIMEOUT="2", FAKE_CLAUDE_SLEEP="60")
        self.assertLess(time.time() - start, 40)
        self.assertEqual(res.returncode, 0, res.stderr)
        with open(os.path.join(self.ablage, "retro", "runs", "2-unbelegtes-muster-neu", "lauf.md")) as f:
            self.assertIn("Zeitgrenze", f.read())

    def test_zeitgrenze_beendet_auch_kindprozesse(self):
        res = self.run_sh("retro/2-unbelegtes-muster", "neu", PRESSURE_TIMEOUT="2", FAKE_CLAUDE_SLEEP="60",
                          FAKE_CLAUDE_ENKEL="1")
        self.assertEqual(res.returncode, 0, res.stderr)
        with open(self.log + ".enkel.pid") as f:
            pid = int(f.read())
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
            lebt = True
            os.kill(pid, 9)
        except ProcessLookupError:
            lebt = False
        self.assertFalse(lebt, "Kindprozess von claude läuft nach der Zeitgrenze weiter")

    def test_abbruch_mit_strg_c_beendet_auch_claude_und_kinder(self):
        import signal
        alt = os.path.join(self.ablage, "retro", "runs", "2-unbelegtes-muster-neu")
        os.makedirs(alt)
        with open(os.path.join(alt, "bewertung.md"), "w") as f:
            f.write("gewerteter Lauf")
        env = dict(self.env, FAKE_CLAUDE_SLEEP="60", FAKE_CLAUDE_ENKEL="1")
        proc = subprocess.Popen(["sh", RUN_SH, "retro/2-unbelegtes-muster", "neu"], env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        pidfile = self.log + ".enkel.pid"
        for _ in range(200):
            if os.path.exists(pidfile) and os.path.getsize(pidfile):
                break
            time.sleep(0.1)
        with open(pidfile) as f:
            enkel = int(f.read())
        os.killpg(proc.pid, signal.SIGINT)  # wie Strg-C: an die Vordergrundgruppe (sh, perl)
        proc.wait(timeout=30)
        time.sleep(0.5)
        try:
            os.kill(enkel, 0)
            lebt = True
            os.kill(enkel, 9)
        except ProcessLookupError:
            lebt = False
        self.assertFalse(lebt, "claude-Kindprozess läuft nach Strg-C weiter")
        self.assertNotEqual(proc.returncode, 0)
        with open(os.path.join(alt, "bewertung.md")) as f:
            self.assertEqual(f.read(), "gewerteter Lauf", "abgebrochener Lauf hat die Ablage ersetzt")

    def test_ungueltige_zeitgrenze(self):
        for wert in ("30m", "0", "-5", "007x"):
            res = self.run_sh("debugger/1-nicht-reproduzierbar", "neu", PRESSURE_TIMEOUT=wert)
            self.assertEqual(res.returncode, 2, wert)
            self.assertIn("PRESSURE_TIMEOUT", res.stderr)
        self.assertFalse(os.path.exists(self.log + ".argv"))

    def test_falscher_aufruf(self):
        self.assertEqual(self.run_sh("debugger/1-nicht-reproduzierbar", "beide").returncode, 2)
        self.assertEqual(self.run_sh("debugger/gibtsnicht", "neu").returncode, 2)
        self.assertEqual(self.run_sh("implementer/../reviewer/1-nicht-melden", "neu").returncode, 2)
        self.assertEqual(self.run_sh("reviewer/1-nicht-melden/extra", "neu").returncode, 2)
        self.assertFalse(os.path.exists(self.log + ".argv"))

    def test_schraegstrich_am_ende_landet_am_richtigen_ort(self):
        res = self.run_sh("debugger/1-nicht-reproduzierbar/", "neu")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(os.path.isdir(os.path.join(self.ablage, "debugger", "runs", "1-nicht-reproduzierbar-neu")))
        self.assertEqual(os.listdir(os.path.join(self.ablage, "debugger", "runs")), ["1-nicht-reproduzierbar-neu"])


if __name__ == "__main__":
    unittest.main()
