"""Tests für tests/pressure/auszug.py: macht aus einem Lauf die drei Auswertungsdateien."""
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
AUSZUG = os.path.join(HERE, "pressure", "auszug.py")
TMP_ROOT = os.path.join(os.path.dirname(HERE), ".test-tmp")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


class AuszugTest(unittest.TestCase):
    def setUp(self):
        os.makedirs(TMP_ROOT, exist_ok=True)
        self.run_dir = tempfile.mkdtemp(dir=TMP_ROOT)
        self.addCleanup(shutil.rmtree, self.run_dir, True)
        repo = os.path.join(self.run_dir, "repo")
        os.makedirs(repo)
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.invalid")
        git(repo, "config", "user.name", "T")
        with open(os.path.join(repo, "a.txt"), "w") as f:
            f.write("a\n")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "start")
        with open(os.path.join(self.run_dir, "start-commit"), "w") as f:
            f.write(git(repo, "rev-parse", "HEAD"))
        with open(os.path.join(repo, "a.txt"), "w") as f:
            f.write("b\n")
        git(repo, "commit", "-qam", "nachher")
        with open(os.path.join(repo, "neu.txt"), "w") as f:
            f.write("x\n")
        self.repo = repo

    def write_transcript(self, lines):
        with open(os.path.join(self.run_dir, "transcript.jsonl"), "w", encoding="utf-8") as f:
            for line in lines:
                f.write((line if isinstance(line, str) else json.dumps(line)) + "\n")

    def run_auszug(self):
        res = subprocess.run([sys.executable, AUSZUG, self.run_dir], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)

    def read(self, name):
        with open(os.path.join(self.run_dir, name), encoding="utf-8") as f:
            return f.read()

    def test_ergebnis_befehle_und_zustand(self):
        self.write_transcript([
            {"type": "system", "subtype": "init"},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Ich prüfe."},
                {"type": "tool_use", "name": "Bash", "input": {"command": "git commit --no-verify -m x"}},
                {"type": "tool_use", "name": "mcp__linear__save_issue", "input": {"title": "T"}},
            ]}},
            {"type": "result", "result": "Fertig.\n\nSLICKFAB-STATUS: BLOCKED", "total_cost_usd": 1.25,
             "num_turns": 7},
        ])
        with open(os.path.join(self.run_dir, "linear.json.calls"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"tool": "save_issue", "arguments": {"title": "T"}}) + "\n")
        self.run_auszug()
        ergebnis = self.read("ergebnis.md")
        self.assertIn("SLICKFAB-STATUS: BLOCKED", ergebnis)
        self.assertIn("1.25", ergebnis)
        befehle = self.read("befehle.md")
        self.assertIn("git commit --no-verify -m x", befehle)
        self.assertIn("mcp__linear__save_issue", befehle)
        nachher = self.read("nachher.md")
        self.assertIn("nachher", nachher)       # Commit seit dem Start
        self.assertNotIn("start\n", nachher.split("## Commits seit dem Start")[1].split("##")[0])
        self.assertIn("neu.txt", nachher)       # ungetrackte Datei
        self.assertIn("save_issue", nachher)    # Tracker-Schreibzugriff

    def test_lauf_ohne_ergebnis_und_ohne_tracker(self):
        self.write_transcript(["kein json", {"type": "assistant", "message": {"content": []}}])
        self.run_auszug()
        self.assertIn("kein Ergebnis", self.read("ergebnis.md"))
        self.assertIn("keine", self.read("nachher.md").split("## Tracker-Schreibzugriffe")[1])

    def test_ablage_bereinigt_und_kuerzt(self):
        home = os.path.expanduser("~")
        self.write_transcript([
            {"type": "system", "subtype": "init", "session_id": "sitzung-xyz", "cwd": self.repo},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Lese %s/geheim und %s/datei, Mail an info@firma.example.org" % (home, self.repo)},
                {"type": "tool_use", "name": "Bash", "input": {"command": "cat /private/tmp/claude-501/abc/x; echo ghp_%s; echo lin_api_%s" % ("A" * 36, "B" * 40)}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": [{"type": "text", "text": "y" * 3000}]}]}},
            {"type": "result", "result": "Ende in %s\n\nSLICKFAB-STATUS: DONE" % self.repo, "total_cost_usd": 0.25, "num_turns": 2},
        ])
        with open(os.path.join(self.run_dir, "lauf.md"), "w", encoding="utf-8") as f:
            f.write("# Laufparameter\n- Aufruf: claude --mcp-config %s/mcp.json\n" % self.run_dir)
        ablage = os.path.join(self.run_dir, "ablage")
        res = subprocess.run([sys.executable, AUSZUG, self.run_dir, "--ablage", ablage, "--root", os.path.dirname(HERE)],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        names = sorted(os.listdir(ablage))
        self.assertEqual(names, ["befehle.md", "ergebnis.md", "lauf.md", "nachher.md", "transkript.md"])
        alles = ""
        for n in names:
            with open(os.path.join(ablage, n), encoding="utf-8") as f:
                alles += f.read()
        for verboten in (home, self.run_dir, "/private/tmp/claude-501", "sitzung-xyz", "info@firma.example.org",
                         "ghp_" + "A" * 36, "lin_api_" + "B" * 40, "y" * 1000):
            self.assertNotIn(verboten, alles)
        self.assertIn("<lauf>/repo", alles)
        self.assertIn("SLICKFAB-STATUS: DONE", alles)
        self.assertIn("Kosten: 0.25 USD", alles)
        with open(os.path.join(ablage, "lauf.md"), encoding="utf-8") as f:
            self.assertIn("Kosten: 0.25 USD", f.read())
        with open(os.path.join(ablage, "transkript.md"), encoding="utf-8") as f:
            t = f.read()
        self.assertIn("gekürzt", t)
        self.assertIn("Bash", t)

    def test_branch_aus_dem_setup_ist_kein_neuer_commit(self):
        # setup.sh legt oft einen Feature-Branch an; dessen Commits gab es schon vor dem Lauf.
        git(self.repo, "checkout", "-qb", "feature")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "aus dem setup")
        git(self.repo, "checkout", "-q", "main" if "main" in git(self.repo, "branch") else "master")
        with open(os.path.join(self.run_dir, "start-refs"), "w") as f:
            f.write(git(self.repo, "for-each-ref", "--format=%(objectname)", "refs/heads"))
        self.write_transcript([{"type": "result", "result": "x", "total_cost_usd": 0, "num_turns": 1}])
        self.run_auszug()
        commits = self.read("nachher.md").split("## Commits seit dem Start")[1].split("##")[0]
        self.assertNotIn("aus dem setup", commits)

    def test_pfad_an_der_kuerzgrenze_wird_trotzdem_ersetzt(self):
        root = os.path.dirname(HERE)
        self.write_transcript([
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                                                            "input": {"command": "b" * 1960 + root}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "a" * 560 + root + "/tests/x.py"}]}},
            {"type": "result", "result": "x", "total_cost_usd": 0, "num_turns": 1},
        ])
        ablage = os.path.join(self.run_dir, "ablage")
        res = subprocess.run([sys.executable, AUSZUG, self.run_dir, "--ablage", ablage, "--root", root],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        with open(os.path.join(ablage, "transkript.md"), encoding="utf-8") as f:
            t = f.read()
        rest = root.replace(os.path.expanduser("~"), "")[:15]  # Pfad hinter dem Home-Ordner
        self.assertNotIn(rest, t)
        self.assertIn("<slickfab>", t)
        with open(os.path.join(ablage, "befehle.md"), encoding="utf-8") as f:
            self.assertNotIn(rest, f.read())

    def test_lokaler_nutzername_aus_ls_wird_ersetzt(self):
        # `ls -la` im Wegwerf-Repo zeigt den lokalen Nutzer als Besitzer; der darf nicht ins Repo.
        import getpass
        user = getpass.getuser()
        ls = "drwxr-xr-x@  7 %s  staff  224 Nov 28 01:17 .\n-rw-r--r--@  1 %s  staff  12 Nov 28 a.txt" % (user, user)
        self.write_transcript([
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                                                            "input": {"command": "ls -la; stat -f %Su ."}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": ls}]}},
            {"type": "result", "result": "Besitzer " + user + ".", "total_cost_usd": 0, "num_turns": 1},
        ])
        ablage = os.path.join(self.run_dir, "ablage")
        res = subprocess.run([sys.executable, AUSZUG, self.run_dir, "--ablage", ablage,
                              "--root", os.path.dirname(HERE)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        for name in ("transkript.md", "ergebnis.md"):
            with open(os.path.join(ablage, name), encoding="utf-8") as f:
                t = f.read()
            with self.subTest(datei=name):
                self.assertIsNone(re.search(r"\b%s\b" % re.escape(user), t), t)
                self.assertIn("<nutzer>", t)
        with open(os.path.join(ablage, "transkript.md"), encoding="utf-8") as f:
            self.assertIn("staff", f.read())  # nur der Name fällt weg, nicht die Zeile

    def test_kurzer_nutzername_und_wortteile_bleiben(self):
        # Grenzfälle: ein Login unter 3 Zeichen wird nicht ersetzt (träfe sonst Wörter), und ein
        # längerer Name als ganzes Wort (auch vor .txt), nicht als Teil eines längeren Worts.
        import importlib.util
        import unittest.mock
        spec = importlib.util.spec_from_file_location("auszug_modul", AUSZUG)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with unittest.mock.patch("getpass.getuser", return_value="ab"), \
                unittest.mock.patch.dict(os.environ, {"HOME": "/nirgends/ab"}):
            self.assertEqual(mod.nutzernamen(), [])
            self.assertEqual(mod.bereinige("ab abc", "/x/lauf", "/x/root"), "ab abc")
        with unittest.mock.patch("getpass.getuser", return_value="kimtest"), \
                unittest.mock.patch.dict(os.environ, {"HOME": "/nirgends/kimtest"}):
            out = mod.bereinige("1 kimtest staff; kimtester; kimtest.txt; an kimtest.", "/x/lauf", "/x/root")
            self.assertEqual(out, "1 <nutzer> staff; kimtester; <nutzer>.txt; an <nutzer>.")

    def test_datei_in_latin1_bricht_den_auszug_nicht(self):
        with open(os.path.join(self.repo, "export.csv"), "wb") as f:
            f.write("Müller;Größe\n".encode("cp1252"))
        git(self.repo, "add", "export.csv")
        git(self.repo, "commit", "-qm", "csv")
        self.write_transcript([{"type": "result", "result": "x", "total_cost_usd": 0, "num_turns": 1}])
        self.run_auszug()
        self.assertIn("export.csv", self.read("nachher.md"))

    def test_diff_zeigt_setup_branch_nicht_als_aenderung(self):
        git(self.repo, "checkout", "-qb", "feature")
        with open(os.path.join(self.repo, "setup_datei.txt"), "w") as f:
            f.write("aus dem setup\n")
        git(self.repo, "add", "setup_datei.txt")
        git(self.repo, "commit", "-qm", "aus dem setup")
        git(self.repo, "checkout", "-q", "-")
        with open(os.path.join(self.run_dir, "start-refs"), "w") as f:
            f.write(git(self.repo, "for-each-ref", "--format=%(objectname) %(refname:short)", "refs/heads"))
        self.write_transcript([{"type": "result", "result": "x", "total_cost_usd": 0, "num_turns": 1}])
        self.run_auszug()
        nachher = self.read("nachher.md")
        self.assertNotIn("setup_datei.txt", nachher)

    def test_fehlender_lauf_ordner_ist_fehler(self):
        res = subprocess.run([sys.executable, AUSZUG, os.path.join(self.run_dir, "fehlt")],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
