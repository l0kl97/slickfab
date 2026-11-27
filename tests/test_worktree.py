"""Prüft `runtime/herdr/slickfab-worktree` über die Befehlszeile.

Jeder Test baut im Temp-Ordner ein Wegwerf-Projekt: ein nacktes Repo als
`origin` und daneben den Haupt-Checkout mit `.slickrails/config.sh`, einem
Hook und einer lokalen `.env`. Worktrees landen unter einem eigenen Temp-Root
(`--root`), nie unter ~/.herdr/worktrees. `gh` wird als Systemgrenze durch ein
kleines Skript im PATH ersetzt.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "runtime", "herdr", "slickfab-worktree")


def default_sigint():
    """Strg-C-Tests starten den Befehl mit SIGINT auf Standard. Läuft die Suite als
    Hintergrundjob (z. B. aus dem Stop-Hook), erbt der Kindprozess sonst ein ignoriertes
    SIGINT, und das Strg-C der Tests käme nie an."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def wait_for(cond, limit=60):
    """Wartet auf einen Zustand statt eine feste Zeit; die Obergrenze greift nur, wenn er nie kommt."""
    deadline = time.monotonic() + limit
    while not cond():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)
    return True


def contains(path, text):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return text in f.read()
    except FileNotFoundError:
        return False


def pid_gone(pid, limit=30):
    """True, sobald der Prozess weg ist; lebt er nach der Obergrenze noch, wird er beendet
    (kein Rest für die nächsten Tests) und das Ergebnis ist False."""
    def dead():
        try:
            os.kill(pid, 0)
            return False
        except ProcessLookupError:
            return True
    if wait_for(dead, limit):
        return True
    os.kill(pid, signal.SIGKILL)
    return False


# Shell-Schleife für Prüf-/Installationsskripte: wartet bis zu 60 s, bis BEDINGUNG gilt.
SH_WAIT = 'i=0; until %s; do i=$((i+1)); [ $i -gt 600 ] && break; sleep 0.1; done'

# "Hängt", bis der Prozess beendet wird. Bleibt er bei einem Testfehler übrig, endet er von selbst,
# sobald der Test seinen Temp-Ordner aufgeräumt hat (spätestens nach 10 min); kein verwaistes sleep.
SH_HANG = 'i=0; while [ -d "%s" ] && [ $i -lt 6000 ]; do i=$((i+1)); sleep 0.1; done'

GREEN_TEST = textwrap.dedent("""\
    import unittest
    class T(unittest.TestCase):
        def test_ok(self):
            self.assertTrue(True)
    """)

RED_TEST = textwrap.dedent("""\
    import unittest
    class T(unittest.TestCase):
        def test_broken(self):
            self.fail("absichtlich rot")
    """)

# Braucht eine nicht eingecheckte Datei; fehlt sie, wird der Test übersprungen.
DATA_TEST = textwrap.dedent("""\
    import os, unittest
    DATA = os.path.join(os.path.dirname(__file__), "data.txt")
    class T(unittest.TestCase):
        @unittest.skipUnless(os.path.exists(DATA), "Testdaten fehlen")
        def test_with_data(self):
            self.assertTrue(True)
    """)

HOOK = "#!/bin/sh\necho 'hook-lief' >&2\nexit 1\n"


def git_env(extra_path=None):
    env = dict(os.environ)
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "GIT_TERMINAL_PROMPT": "0",
    })
    if extra_path:
        env["PATH"] = extra_path + os.pathsep + env["PATH"]
    return env


class Project:
    """Wegwerf-Projekt mit origin, Haupt-Checkout und Worktree-Root."""

    def __init__(self, test=GREEN_TEST, check='CHECK_TEST="python3 -m unittest discover -s tests"'):
        self.tmp = tempfile.mkdtemp(prefix="slickfab-wt-")
        self.origin = os.path.join(self.tmp, "origin.git")
        self.main = os.path.join(self.tmp, "demo")
        self.root = os.path.join(self.tmp, "worktrees")
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        self.env = git_env(self.bin)
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", self.origin)
        self.git(self.tmp, "clone", "-q", self.origin, self.main)
        self.git(self.main, "checkout", "-q", "-b", "main")
        self.write(".gitignore", ".env\n.env.*\n!.env.example\ntests/data.txt\n")
        self.write("tests/test_demo.py", test)
        if check is not None:
            self.write(".slickrails/config.sh", check + "\n")
        self.write(".githooks/pre-commit", HOOK, mode=0o755)
        self.write(".env.example", "KEY=\n")
        self.git(self.main, "add", "-A")
        self.git(self.main, "commit", "-q", "--no-verify", "-m", "init")
        self.git(self.main, "push", "-q", "-u", "origin", "main")
        # lokal, nicht in git
        self.write(".env", "KEY=geheim\n")
        self.write(".env.local", "LOCAL=1\n")

    def write(self, rel, content, mode=None, base=None):
        path = os.path.join(base or self.main, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if mode:
            os.chmod(path, mode)
        return path

    def git(self, cwd, *args, check=True):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, capture_output=True,
                              text=True, timeout=60, check=check)

    def run(self, *args, cwd=None):
        return subprocess.run([sys.executable, SCRIPT, *args, "--root", self.root],
                              cwd=cwd or self.main, env=self.env, capture_output=True,
                              text=True, timeout=120)

    def wt(self, name):
        return os.path.join(self.root, "demo", name)

    def worktrees(self):
        out = self.git(self.main, "worktree", "list", "--porcelain").stdout
        return [os.path.realpath(l.split(" ", 1)[1]) for l in out.splitlines()
                if l.startswith("worktree ")]

    def branches(self):
        out = self.git(self.main, "branch", "--format=%(refname:short)").stdout
        return out.split()

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class WorktreeTest(unittest.TestCase):
    def project(self, **kw):
        p = Project(**kw)
        self.addCleanup(p.cleanup)
        return p

    def assertOk(self, r):
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def assertFails(self, r, *needles):
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, "erwartet Fehler, war 0:\n" + out)
        for n in needles:
            self.assertIn(n, out)

    def assertNoTrace(self, p, name, branch=None):
        """Kein halber Zustand: weder Ordner noch Worktree-Eintrag noch Branch."""
        self.assertFalse(os.path.exists(p.wt(name)), "Ordner blieb zurück: " + p.wt(name))
        self.assertNotIn(os.path.realpath(p.wt(name)), p.worktrees())
        self.assertNotIn(branch or name, p.branches())

    # --- add ---------------------------------------------------------------

    def test_add_green_baseline_prints_path_with_env_and_active_hooks(self):
        p = self.project()
        r = p.run("add", "ex-1")
        self.assertOk(r)
        path = p.wt("ex-1")
        self.assertEqual(r.stdout.strip().splitlines()[-1], path)
        self.assertIn(os.path.realpath(path), p.worktrees())
        self.assertEqual(p.git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), "ex-1")
        with open(os.path.join(path, ".env"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "KEY=geheim\n")
        self.assertTrue(os.path.exists(os.path.join(path, ".env.local")))
        # Hook ist aktiv: er lehnt jeden Commit ab.
        p.write("neu.txt", "x\n", base=path)
        p.git(path, "add", "neu.txt")
        c = p.git(path, "commit", "-m", "probe", check=False)
        self.assertNotEqual(c.returncode, 0, "Commit ging ohne Hook durch")
        self.assertIn("hook-lief", c.stderr)

    def test_add_red_baseline_fails_clearly_and_leaves_nothing(self):
        p = self.project(test=RED_TEST)
        r = p.run("add", "ex-2")
        self.assertFails(r, "Baseline rot", "absichtlich rot")
        self.assertNoTrace(p, "ex-2")

    def test_add_fails_when_worktree_skips_tests_that_run_in_main_checkout(self):
        p = self.project(test=DATA_TEST)
        p.write("tests/data.txt", "nur lokal\n")  # gitignored: fehlt im Worktree
        r = p.run("add", "ex-3")
        self.assertFails(r, "übersprungen")
        self.assertNoTrace(p, "ex-3")

    def test_skip_detection_for_pytest_and_node_output(self):
        formats = {
            "pytest": ("3 passed in 0.1s", "2 passed, 1 skipped in 0.1s"),
            "node": ("# pass 3\n# skipped 0", "# pass 2\n# skipped 1"),
        }
        for fmt, (full, skipped) in formats.items():
            with self.subTest(fmt=fmt):
                p = self.project()
                p.write("tests/data.txt", "nur lokal\n")
                script = ("#!/bin/sh\nif [ -f tests/data.txt ]; then printf '%s\\n' '" + full +
                          "'; else printf '%s\\n' '" + skipped + "'; fi\n")
                p.write("count.sh", script)
                p.git(p.main, "add", "count.sh")
                p.git(p.main, "commit", "-q", "--no-verify", "-m", "count")
                p.git(p.main, "push", "-q", "origin", "main")
                r = p.run("add", "ex-" + fmt, "--check", "sh count.sh")
                self.assertFails(r, "übersprungen")
                self.assertNoTrace(p, "ex-" + fmt)

    # --- review ------------------------------------------------------------

    def make_pr(self, p, number=7):
        """Legt im origin einen PR-Head an und ein falsches `gh`, das ihn meldet."""
        p.git(p.main, "checkout", "-q", "-b", "feature")
        p.write("feature.txt", "neu\n")
        p.git(p.main, "add", "feature.txt")
        p.git(p.main, "commit", "-q", "--no-verify", "-m", "feature")
        head = p.git(p.main, "rev-parse", "HEAD").stdout.strip()
        p.git(p.main, "push", "-q", "origin", "HEAD:refs/pull/%d/head" % number)
        p.git(p.main, "checkout", "-q", "main")
        p.git(p.main, "branch", "-q", "-D", "feature")
        gh = textwrap.dedent("""\
            #!/bin/sh
            if [ "$1 $2 $3" = "pr view %d" ]; then
              echo '%s'
              exit 0
            fi
            echo "GraphQL: Could not resolve to a PullRequest with the number of $3." >&2
            exit 1
            """) % (number, json.dumps({"headRefOid": head}))
        p.write("gh", gh, mode=0o755, base=p.bin)
        return head

    def test_review_checks_out_exact_pr_head_detached(self):
        p = self.project()
        head = self.make_pr(p)
        r = p.run("review", "7")
        self.assertOk(r)
        path = r.stdout.strip().splitlines()[-1]
        self.assertEqual(path, p.wt("pr-7"))
        self.assertEqual(p.git(path, "rev-parse", "HEAD").stdout.strip(), head)
        self.assertEqual(p.git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(), "HEAD")

    def test_review_unknown_pr_fails_and_leaves_nothing(self):
        p = self.project()
        self.make_pr(p)
        r = p.run("review", "99")
        self.assertFails(r, "99")
        self.assertNoTrace(p, "pr-99")

    # --- rm / doppelt ---------------------------------------------------------

    def test_rm_removes_worktree_and_branch_second_rm_fails_clearly(self):
        p = self.project()
        self.assertOk(p.run("add", "ex-5"))
        self.assertOk(p.run("rm", "ex-5"))
        self.assertNoTrace(p, "ex-5")
        r = p.run("rm", "ex-5")
        self.assertFails(r, "ex-5", "kein Worktree")

    def test_rm_review_worktree(self):
        p = self.project()
        self.make_pr(p)
        self.assertOk(p.run("review", "7"))
        self.assertOk(p.run("rm", "pr-7"))
        self.assertNoTrace(p, "pr-7")

    def test_rm_review_worktree_keeps_local_commit_without_force(self):
        p = self.project()
        self.make_pr(p)
        self.assertOk(p.run("review", "7"))
        path = p.wt("pr-7")
        p.write("notiz.txt", "x\n", base=path)
        p.git(path, "add", "notiz.txt")
        p.git(path, "commit", "-q", "--no-verify", "-m", "review-notiz")
        self.assertFails(p.run("rm", "pr-7"), "nicht gepusht")
        self.assertTrue(os.path.exists(os.path.join(path, "notiz.txt")))

    # --- ungültige Eingaben ---------------------------------------------------

    def test_not_a_git_repo_fails(self):
        p = self.project()
        empty = os.path.join(p.tmp, "leer")
        os.makedirs(empty)
        for args in (("add", "ex-10"), ("review", "7"), ("rm", "ex-10")):
            with self.subTest(cmd=args[0]):
                r = p.run(*args, "--repo", empty)
                self.assertFails(r, "kein Git-Repo")
        self.assertFalse(os.path.exists(p.root))

    def test_missing_check_commands_fails_without_worktree(self):
        p = self.project(check=None)
        r = p.run("add", "ex-11")
        self.assertFails(r, "Prüfbefehle")
        self.assertNoTrace(p, "ex-11")

    def test_failing_install_fails_and_cleans_up(self):
        p = self.project()
        r = p.run("add", "ex-12", "--install", "echo install-kaputt; exit 3")
        self.assertFails(r, "Installation", "install-kaputt")
        self.assertNoTrace(p, "ex-12")

    def test_install_timeout_fails_and_cleans_up(self):
        p = self.project()
        r = p.run("add", "ex-13", "--install", "sleep 30", "--timeout", "1")
        self.assertFails(r, "Zeitgrenze")
        self.assertNoTrace(p, "ex-13")

    def test_ctrl_c_during_install_stops_child_and_leaves_nothing(self):
        p = self.project()
        pidfile = os.path.join(p.tmp, "install-pid")
        # Die Installation meldet ihre PID (atomar per mv) und schläft dann; erst danach kommt Strg-C.
        install = 'echo $$ > "{0}.tmp" && mv "{0}.tmp" "{0}"; {1}'.format(pidfile, SH_HANG % p.tmp)
        proc = subprocess.Popen(
            [sys.executable, SCRIPT, "add", "ex-17", "--root", p.root, "--install", install],
            cwd=p.main, env=p.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            preexec_fn=default_sigint)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        self.assertTrue(wait_for(lambda: os.path.exists(pidfile)), "Installation startete nicht")
        with open(pidfile) as f:
            install_pid = int(f.read())
        proc.send_signal(signal.SIGINT)
        proc.communicate(timeout=60)
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(pid_gone(install_pid), "Installation läuft nach Strg-C weiter")
        self.assertNoTrace(p, "ex-17")

    def slow_worktree_add(self, p):
        """`git` im PATH, das nach `worktree add` eine Markerdatei anlegt und dann hängt
        (langsamer Checkout). Gibt den Pfad der Markerdatei zurück."""
        real = shutil.which("git")
        marker = os.path.join(p.tmp, "worktree-add-fertig")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            "%s" "$@"
            code=$?
            if [ "$1" = worktree ] && [ "$2" = add ]; then touch "%s"; %s; fi
            exit $code
            """) % (real, marker, SH_HANG % p.tmp), mode=0o755, base=p.bin)
        return marker

    def interrupt_when_exists(self, p, args, marker):
        proc = subprocess.Popen([sys.executable, SCRIPT, *args, "--root", p.root], cwd=p.main,
                                env=p.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, preexec_fn=default_sigint)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        self.assertTrue(wait_for(lambda: os.path.exists(marker)), "worktree add lief nicht")
        proc.send_signal(signal.SIGINT)
        out, _ = proc.communicate(timeout=60)
        return proc.returncode, out

    def test_ctrl_c_during_worktree_add_leaves_nothing(self):
        p = self.project()
        marker = self.slow_worktree_add(p)
        code, out = self.interrupt_when_exists(p, ("add", "ex-30"), marker)
        self.assertEqual(code, 130, out)
        self.assertNotIn("Traceback", out)
        self.assertNoTrace(p, "ex-30")

    def test_ctrl_c_during_review_worktree_add_leaves_nothing(self):
        p = self.project()
        self.make_pr(p)
        marker = self.slow_worktree_add(p)
        code, out = self.interrupt_when_exists(p, ("review", "7"), marker)
        self.assertEqual(code, 130, out)
        self.assertNotIn("Traceback", out)
        self.assertNoTrace(p, "pr-7")

    def test_review_fails_when_worktree_is_not_at_pr_head(self):
        p = self.project()
        self.make_pr(p)
        real = shutil.which("git")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            case "$(pwd -P)" in "%s"/*)
              if [ "$1 $2" = "rev-parse HEAD" ]; then echo %s; exit 0; fi;;
            esac
            exec "%s" "$@"
            """) % (os.path.realpath(p.root), "0" * 40, real), mode=0o755, base=p.bin)
        r = p.run("review", "7")
        self.assertFails(r, "PR-Head")
        self.assertNoTrace(p, "pr-7")

    def test_env_copy_does_not_overwrite_checked_in_file(self):
        p = self.project()
        # .envrc ist auf origin eingecheckt; im veralteten Haupt-Checkout liegt eine lokale,
        # nicht eingecheckte .envrc mit anderem Inhalt.
        self.push_from_other_clone(p, {".envrc": "AUS_ORIGIN=1\n"})
        p.write(".envrc", "LOKAL=1\n")
        r = p.run("add", "ex-33", "--no-compare")
        self.assertOk(r)
        with open(os.path.join(p.wt("ex-33"), ".envrc"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "AUS_ORIGIN=1\n")

    def test_install_detected_from_lockfile(self):
        p = self.project()
        p.write("package-lock.json", "{}\n")
        p.git(p.main, "add", "package-lock.json")
        p.git(p.main, "commit", "-q", "--no-verify", "-m", "lock")
        p.git(p.main, "push", "-q", "origin", "main")
        p.write("npm", '#!/bin/sh\necho "$@" > npm-aufruf.txt\n', mode=0o755, base=p.bin)
        r = p.run("add", "ex-14")
        self.assertOk(r)
        with open(os.path.join(p.wt("ex-14"), "npm-aufruf.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "ci")

    def test_relative_root_resolves_from_caller_directory(self):
        p = self.project()
        caller = os.path.join(p.tmp, "aufrufer")
        os.makedirs(caller)
        r = subprocess.run([sys.executable, SCRIPT, "add", "ex-15", "--repo", p.main,
                            "--root", "wt-rel"], cwd=caller, env=p.env, capture_output=True,
                           text=True, timeout=120)
        self.assertOk(r)
        expected = os.path.join(caller, "wt-rel", "demo", "ex-15")
        self.assertEqual(os.path.realpath(r.stdout.strip().splitlines()[-1]),
                         os.path.realpath(expected))
        self.assertIn(os.path.realpath(expected), p.worktrees())

    def test_invalid_names_are_rejected(self):
        p = self.project()
        for bad in ("../raus", "a/b", ".versteckt", ""):
            with self.subTest(name=bad):
                self.assertFails(p.run("add", bad), "ungültig")
        self.assertFails(p.run("review", "abc"), "ungültig")
        for bad_base in ("--upload-pack=touch x", "main..x", "a b"):
            with self.subTest(base=bad_base):
                self.assertFails(p.run("add", "ex-16", "--base=" + bad_base), "ungültig")
        self.assertFalse(os.path.exists(p.root))

    def test_second_add_fails_clearly_and_keeps_first(self):
        p = self.project()
        self.assertOk(p.run("add", "ex-6"))
        marker = p.write("arbeit.txt", "halb fertig\n", base=p.wt("ex-6"))
        r = p.run("add", "ex-6")
        self.assertFails(r, "existiert schon")
        self.assertEqual(os.listdir(os.path.join(p.root, "demo")), ["ex-6"])
        self.assertTrue(os.path.exists(marker), "erster Worktree wurde beschädigt")
        self.assertIn("ex-6", p.branches())

    def test_add_keeps_foreign_registration_whose_folder_is_missing(self):
        # Re-Review R4: am Pfad ist ein fremder Worktree registriert, sein Ordner wurde verschoben.
        p = self.project()
        path = p.wt("x")
        os.makedirs(os.path.dirname(path))
        p.git(p.main, "worktree", "add", "-q", "-b", "fremd", path)
        moved = os.path.join(p.tmp, "verschoben")
        os.rename(path, moved)
        # ein zweiter, ebenfalls verwaister Worktree darf von keinem prune erfasst werden
        other = p.wt("y")
        p.git(p.main, "worktree", "add", "-q", "-b", "fremd2", other)
        shutil.rmtree(other)
        r = p.run("add", "x")
        self.assertFails(r, "registriert")
        self.assertIn(os.path.realpath(path), p.worktrees())
        self.assertIn(os.path.realpath(other), p.worktrees())
        self.assertIn("fremd", p.branches())
        self.assertEqual(p.git(p.main, "worktree", "repair", moved, check=False).returncode, 0)

    def test_rollback_does_not_prune_other_missing_worktrees(self):
        p = self.project(test=RED_TEST)
        other = p.wt("y")
        os.makedirs(os.path.dirname(other))
        p.git(p.main, "worktree", "add", "-q", "-b", "fremd2", other)
        shutil.rmtree(other)  # verwaist, aber registriert (z. B. Laufwerk abgezogen)
        r = p.run("add", "ex-26")
        self.assertFails(r, "Baseline rot")
        self.assertNoTrace(p, "ex-26")
        self.assertIn(os.path.realpath(other), p.worktrees())

    def test_add_fails_when_branch_already_exists(self):
        p = self.project()
        p.git(p.main, "branch", "ex-7")
        r = p.run("add", "ex-7")
        self.assertFails(r, "existiert schon")
        self.assertFalse(os.path.exists(p.wt("ex-7")))
        self.assertIn("ex-7", p.branches())

    def test_rm_keeps_uncommitted_changes_without_force(self):
        p = self.project()
        self.assertOk(p.run("add", "ex-8"))
        work = p.write("wichtig.txt", "nicht committet\n", base=p.wt("ex-8"))
        r = p.run("rm", "ex-8")
        self.assertFails(r, "--force", "wichtig.txt")
        self.assertTrue(os.path.exists(work))
        self.assertIn("ex-8", p.branches())
        self.assertOk(p.run("rm", "ex-8", "--force"))
        self.assertNoTrace(p, "ex-8")

    def test_rm_keeps_unpushed_commits_without_force(self):
        p = self.project()
        self.assertOk(p.run("add", "ex-9"))
        path = p.wt("ex-9")
        p.write("neu.txt", "x\n", base=path)
        p.git(path, "add", "neu.txt")
        p.git(path, "commit", "-q", "--no-verify", "-m", "lokal")
        r = p.run("rm", "ex-9")
        self.assertFails(r, "--force", "nicht gepusht")
        self.assertTrue(os.path.exists(os.path.join(path, "neu.txt")))
        self.assertIn("ex-9", p.branches())
        # gepusht = gesichert: dann darf rm ohne --force
        p.git(path, "push", "-q", "origin", "ex-9")
        self.assertOk(p.run("rm", "ex-9"))
        self.assertNoTrace(p, "ex-9")

    # --- Vergleichbarkeit des Haupt-Checkouts (Review A1) ----------------------

    def push_from_other_clone(self, p, files):
        """Neuer Commit auf origin/main, ohne den Haupt-Checkout zu bewegen (er veraltet)."""
        other = os.path.join(p.tmp, "anderer-klon")
        if not os.path.exists(other):
            p.git(p.tmp, "clone", "-q", p.origin, other)
        p.git(other, "pull", "-q", "origin", "main")
        for rel, content in files.items():
            p.write(rel, content, base=other)
        p.git(other, "add", "-A")
        p.git(other, "commit", "-q", "--no-verify", "-m", "weiter")
        p.git(other, "push", "-q", "origin", "HEAD:main")

    def test_stale_main_checkout_is_not_used_as_reference(self):
        # Falsch grün aus dem Review: origin/main bekommt einen Datentest, der Haupt-Checkout
        # ist veraltet und hat die Daten. Im Worktree wird der Datentest übersprungen.
        p = self.project()
        p.write("tests/data.txt", "nur lokal\n")
        self.push_from_other_clone(p, {"tests/test_data.py": DATA_TEST})
        r = p.run("add", "ex-20")
        self.assertFails(r, "Haupt-Checkout", "--no-compare")
        self.assertNoTrace(p, "ex-20")

    def test_main_checkout_on_other_branch_fails_without_misleading_hint(self):
        p = self.project()
        p.git(p.main, "checkout", "-q", "-b", "feature")
        p.write("tests/test_mehr.py", GREEN_TEST)
        p.git(p.main, "add", "-A")
        p.git(p.main, "commit", "-q", "--no-verify", "-m", "mehr")
        r = p.run("add", "ex-21")
        self.assertFails(r, "--no-compare")
        self.assertNotIn("Testdaten", r.stdout + r.stderr)
        self.assertNoTrace(p, "ex-21")

    def test_dirty_main_checkout_is_not_used_as_reference(self):
        p = self.project()
        p.write("tests/test_demo.py", GREEN_TEST + "# lokal geändert\n")
        r = p.run("add", "ex-22")
        self.assertFails(r, "Änderungen", "--no-compare")
        self.assertNoTrace(p, "ex-22")

    def test_fetch_between_check_and_create_does_not_change_start_commit(self):
        # Re-Review A1': ein paralleler fetch direkt vor `worktree add` schiebt origin/main
        # weiter (Datentest + normaler Test). Der Worktree muss am geprüften Commit starten.
        p = self.project()
        p.write("tests/data.txt", "nur lokal\n")
        checked = p.git(p.main, "rev-parse", "HEAD").stdout.strip()
        other = os.path.join(p.tmp, "anderer-klon")
        p.git(p.tmp, "clone", "-q", p.origin, other)
        p.write("tests/test_data.py", DATA_TEST, base=other)
        p.write("tests/test_mehr.py", GREEN_TEST, base=other)
        p.git(other, "add", "-A")
        p.git(other, "commit", "-q", "--no-verify", "-m", "weiter")
        real = shutil.which("git")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1" = worktree ] && [ "$2" = add ] && [ ! -e "%(flag)s" ]; then
              touch "%(flag)s"
              "%(git)s" -C "%(other)s" push -q origin HEAD:main
              "%(git)s" -C "%(main)s" fetch -q origin
            fi
            exec "%(git)s" "$@"
            """) % {"flag": os.path.join(p.tmp, "fetch-lief"), "git": real, "other": other,
                    "main": p.main}, mode=0o755, base=p.bin)
        r = p.run("add", "ex-24")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fetch-lief")), "Rennen nicht ausgelöst")
        self.assertOk(r)
        self.assertEqual(p.git(p.wt("ex-24"), "rev-parse", "HEAD").stdout.strip(), checked)

    def test_main_checkout_moving_during_baseline_is_detected(self):
        p = self.project()
        move = 'git -C "%s" commit -q --allow-empty --no-verify -m bewegt' % p.main
        r = p.run("add", "ex-25", "--install", move)
        self.assertFails(r, "Haupt-Checkout steht auf", "--no-compare")
        self.assertNotIn("Testdaten", r.stdout + r.stderr)
        self.assertNoTrace(p, "ex-25")

    def test_main_checkout_moving_during_reference_run_is_detected(self):
        # Re-Review PR #3, A1'': wird der Haupt-Checkout während des Vergleichslaufs
        # umgestellt, zählte er einen anderen Stand als den Startcommit (falsch grün).
        p = self.project()
        check = ('python3 -m unittest discover -s tests && case "$(pwd -P)" in "%s") '
                 'git commit -q --allow-empty --no-verify -m umgestellt;; esac' % os.path.realpath(p.main))
        r = p.run("add", "ex-26", "--check", check)
        self.assertFails(r, "Haupt-Checkout steht auf", "--no-compare")
        self.assertNoTrace(p, "ex-26")

    def test_no_compare_skips_reference_run_with_warning(self):
        p = self.project()
        marker = os.path.join(p.tmp, "lief-im-haupt-checkout")
        p.write("tests/test_demo.py", GREEN_TEST + "# lokal geändert\n")
        check = 'case "$(pwd -P)" in "%s") touch "%s";; esac; python3 -m unittest discover -s tests' % (
            os.path.realpath(p.main), marker)
        r = p.run("add", "ex-23", "--no-compare", "--check", check)
        self.assertOk(r)
        self.assertIn("WARNUNG", r.stderr)
        self.assertFalse(os.path.exists(marker), "Vergleichslauf lief trotz --no-compare")

    def start_logged(self, p, args, log, sigint=False):
        """Startet slickfab-worktree mit Ausgabe in eine Datei. Prüf- und Installationsskripte
        können so lesen, wie weit ein paralleler Aufruf ist (z. B. "warte auf Sperre")."""
        with open(log, "w") as f:
            proc = subprocess.Popen([sys.executable, SCRIPT, *args, "--root", p.root],
                                    cwd=p.main, env=p.env, stdout=f, stderr=subprocess.STDOUT,
                                    preexec_fn=default_sigint if sigint else None)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        return proc

    def finish(self, proc, log):
        proc.wait(timeout=120)
        with open(log, encoding="utf-8", errors="replace") as f:
            return proc.returncode, f.read()

    def test_parallel_adds_do_not_test_in_main_checkout_at_the_same_time(self):
        p = self.project()
        running = os.path.join(p.tmp, "laeuft")
        overlap = os.path.join(p.tmp, "ueberlappt")
        timeout = os.path.join(p.tmp, "zeitgrenze")
        logs = [os.path.join(p.tmp, n + ".log") for n in ("ex-31", "ex-32")]
        # Der erste Vergleichslauf im Haupt-Checkout hält an, bis der andere Aufruf entweder an
        # der Vergleichssperre wartet (richtig) oder selbst im Haupt-Checkout testet (Überlappung).
        until = ('[ -e "%s" ] || grep -qs "warte auf Sperre (Vergleichslauf)" "%s" "%s"'
                 % (overlap, logs[0], logs[1]))
        probe = p.write("probe.sh", textwrap.dedent("""\
            #!/bin/sh
            if [ "$(pwd -P)" = "%s" ]; then
              if mkdir "%s" 2>/dev/null; then
                %s
                [ $i -gt 600 ] && touch "%s"
                rmdir "%s"
              else
                touch "%s"
              fi
            fi
            echo "1 passed"
            """) % (os.path.realpath(p.main), running, SH_WAIT % until, timeout, running, overlap),
            base=p.tmp)
        procs = [self.start_logged(p, ("add", n, "--check", "sh " + probe), log)
                 for n, log in zip(("ex-31", "ex-32"), logs)]
        for proc, log in zip(procs, logs):
            code, out = self.finish(proc, log)
            self.assertEqual(code, 0, out)
        self.assertFalse(os.path.exists(overlap), "Vergleichsläufe liefen gleichzeitig")
        self.assertFalse(os.path.exists(timeout), "der zweite Aufruf kam nie beim Vergleich an")

    def test_rm_does_not_wait_for_reference_run_of_another_add(self):
        p = self.project()
        self.assertOk(p.run("add", "ex-34"))
        started = os.path.join(p.tmp, "vergleich-laeuft")
        rm_done = os.path.join(p.tmp, "rm-fertig")
        timeout = os.path.join(p.tmp, "zeitgrenze")
        # Der Vergleichslauf hält die Vergleichssperre, bis rm fertig ist (höchstens 60 s).
        probe = p.write("probe.sh", textwrap.dedent("""\
            #!/bin/sh
            if [ "$(pwd -P)" = "%s" ]; then
              touch "%s"
              %s
              [ $i -gt 600 ] && touch "%s"
            fi
            echo "1 passed"
            """) % (os.path.realpath(p.main), started, SH_WAIT % ('[ -e "%s" ]' % rm_done), timeout),
            base=p.tmp)
        log = os.path.join(p.tmp, "ex-35.log")
        slow = self.start_logged(p, ("add", "ex-35", "--check", "sh " + probe), log)
        self.assertTrue(wait_for(lambda: os.path.exists(started)), "Vergleichslauf startete nicht")
        r = p.run("rm", "ex-34")
        open(rm_done, "w").close()
        self.assertOk(r)
        self.assertFalse(os.path.exists(timeout), "rm wartete auf den Vergleichslauf eines anderen add")
        code, out = self.finish(slow, log)
        self.assertEqual(code, 0, out)

    def test_parallel_add_with_same_name_does_not_destroy_the_first(self):
        p = self.project()
        real = shutil.which("git")
        flag = os.path.join(p.tmp, "erster-add")
        log1, log2 = (os.path.join(p.tmp, n) for n in ("erster.log", "zweiter.log"))
        # Der erste Aufruf legt erst an, wenn der zweite seine Vorprüfung bestanden hat und an
        # der Sperre wartet; seine Installation endet erst, wenn der zweite abgelehnt wurde.
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1" = worktree ] && [ "$2" = add ] && [ ! -e "%s" ]; then
              touch "%s"
              %s
            fi
            exec "%s" "$@"
            """) % (flag, flag, SH_WAIT % ('grep -qs "warte auf Sperre (Worktree anlegen)" "%s"' % log2),
                    real), mode=0o755, base=p.bin)
        install = SH_WAIT % ('grep -qs "existiert schon" "%s"' % log2)
        first = self.start_logged(p, ("add", "ex-40", "--install", install), log1)
        self.assertTrue(wait_for(lambda: os.path.exists(flag)), "erster Aufruf legte nicht an")
        second = self.start_logged(p, ("add", "ex-40", "--install", "true"), log2)
        code1, out1 = self.finish(first, log1)
        code2, out2 = self.finish(second, log2)
        self.assertEqual(code1, 0, out1)
        self.assertNotEqual(code2, 0, out2)
        self.assertIn("existiert schon", out2)
        self.assertIn("warte auf Sperre (Worktree anlegen)", out2)  # der Wettlauf fand wirklich statt
        self.assertIn(os.path.realpath(p.wt("ex-40")), p.worktrees())
        self.assertIn("ex-40", p.branches())

    def race_aborted_first(self, p, args_a, args_b):
        """A bricht mitten in `worktree add` ab, bevor git etwas angelegt hat; B wartet
        derweil an der Sperre und legt danach denselben Pfad an. Gibt (A, B) zurück."""
        real = shutil.which("git")
        flag = os.path.join(p.tmp, "erster-add")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1" = worktree ] && [ "$2" = add ] && [ ! -e "%s" ]; then
              touch "%s"; %s
            fi
            exec "%s" "$@"
            """) % (flag, flag, SH_HANG % p.tmp, real), mode=0o755, base=p.bin)
        log_a, log_b = (os.path.join(p.tmp, n) for n in ("a.log", "b.log"))
        a = self.start_logged(p, args_a, log_a, sigint=True)
        self.assertTrue(wait_for(lambda: os.path.exists(flag)), "A kam nicht bis worktree add")
        b = self.start_logged(p, args_b, log_b, sigint=True)
        self.assertTrue(wait_for(lambda: contains(log_b, "warte auf Sperre (Worktree anlegen)")),
                        "B wartete nie an der Sperre")
        a.send_signal(signal.SIGINT)
        return self.finish(a, log_a), self.finish(b, log_b)

    def test_aborted_add_does_not_remove_worktree_of_waiting_add(self):
        p = self.project()
        (code_a, out_a), (code_b, out_b) = self.race_aborted_first(
            p, ("add", "ex-41"), ("add", "ex-41", "--install", "sleep 2"))
        self.assertEqual(code_a, 130, out_a)
        self.assertEqual(code_b, 0, out_b)
        self.assertIn(os.path.realpath(p.wt("ex-41")), p.worktrees())
        self.assertIn("ex-41", p.branches())

    def test_aborted_review_does_not_remove_worktree_of_waiting_review(self):
        p = self.project()
        self.make_pr(p)
        (code_a, out_a), (code_b, out_b) = self.race_aborted_first(p, ("review", "7"), ("review", "7"))
        self.assertEqual(code_a, 130, out_a)
        self.assertEqual(code_b, 0, out_b)
        self.assertIn(os.path.realpath(p.wt("pr-7")), p.worktrees())

    def before_worktree_add(self, p, script):
        """`git` im PATH, das direkt vor `worktree add` einmal `script` ausführt: jemand
        außerhalb der Sperre (von Hand, IDE) legt im Millisekunden-Fenster etwas an."""
        real = shutil.which("git")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1" = worktree ] && [ "$2" = add ] && [ ! -e "%(flag)s" ]; then
              touch "%(flag)s"
              %(script)s
            fi
            exec "%(git)s" "$@"
            """) % {"flag": os.path.join(p.tmp, "fremd-lief"), "git": real, "script": script},
            mode=0o755, base=p.bin)

    def test_foreign_folder_created_in_the_window_is_not_deleted(self):
        # Re-Review PR #3, A1: `git worktree add` scheitert am fremden Ordner; das Aufräumen
        # darf ihn nicht löschen. Den Branch, den git dabei schon angelegt hat, schon.
        p = self.project()
        folder = p.wt("ex-50")
        self.before_worktree_add(p, 'mkdir -p "%s" && echo arbeit > "%s/notiz.txt"' % (folder, folder))
        r = p.run("add", "ex-50")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        with open(os.path.join(folder, "notiz.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "arbeit\n")
        self.assertNotIn(os.path.realpath(folder), p.worktrees())
        self.assertNotIn("ex-50", p.branches())

    def test_foreign_worktree_registered_in_the_window_is_not_removed(self):
        # A1: jemand legt per IDE/Hand im Fenster einen Worktree am selben Pfad an
        p = self.project()
        folder = p.wt("ex-53")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q --detach "%s" HEAD && echo arbeit > "%s/notiz.txt"'
                                 % (shutil.which("git"), p.main, folder, folder))
        r = p.run("add", "ex-53")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        self.assertIn(os.path.realpath(folder), p.worktrees())
        self.assertTrue(os.path.exists(os.path.join(folder, "notiz.txt")))
        self.assertNotIn("ex-53", p.branches())

    def test_foreign_worktree_at_review_path_in_the_window_is_not_removed(self):
        # A1 für review: ein fremder detached Worktree am Pfad pr-<n> (anderer Commit als der PR-Head)
        p = self.project()
        self.make_pr(p)
        folder = p.wt("pr-7")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q --detach "%s" main && echo arbeit > "%s/notiz.txt"'
                                 % (shutil.which("git"), p.main, folder, folder))
        r = p.run("review", "7")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        self.assertIn(os.path.realpath(folder), p.worktrees())
        self.assertTrue(os.path.exists(os.path.join(folder, "notiz.txt")))

    def assertForeignWorktreeKept(self, p, r, folder):
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        self.assertIn(os.path.realpath(folder), p.worktrees())
        with open(os.path.join(folder, "notiz.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "arbeit\n")

    def test_p1_foreign_worktree_with_same_branch_on_other_commit_is_not_removed(self):
        # Review PR #18, P1: gleicher Branchname belegt kein Eigentum
        p = self.project()
        p.git(p.main, "commit", "-q", "--allow-empty", "--no-verify", "-m", "fremde Arbeit")
        other = p.git(p.main, "rev-parse", "HEAD").stdout.strip()
        p.git(p.main, "reset", "-q", "--hard", "HEAD~1")
        folder = p.wt("ex-60")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b ex-60 "%s" %s && echo arbeit > "%s/notiz.txt"'
                                 % (shutil.which("git"), p.main, folder, other, folder))
        r = p.run("add", "ex-60")
        self.assertForeignWorktreeKept(p, r, folder)
        self.assertEqual(p.git(p.main, "rev-parse", "refs/heads/ex-60").stdout.strip(), other)

    def test_p1b_foreign_worktree_with_same_branch_at_start_commit_and_work_is_not_removed(self):
        # Review PR #18, P1b: auch am Startcommit nicht, wenn darin ungesicherte Arbeit liegt
        p = self.project()
        folder = p.wt("ex-61")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b ex-61 "%s" HEAD && echo arbeit > "%s/notiz.txt"'
                                 % (shutil.which("git"), p.main, folder, folder))
        r = p.run("add", "ex-61")
        self.assertForeignWorktreeKept(p, r, folder)
        self.assertIn("ex-61", p.branches())

    def assertCleanForeignKept(self, p, r, folder, name):
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        self.assertIn(os.path.realpath(folder), p.worktrees())
        self.assertTrue(os.path.exists(os.path.join(folder, "tests", "test_demo.py")), name)

    def test_clean_foreign_worktree_with_same_branch_on_other_commit_is_not_removed(self):
        # Mutationsprobe Rework PR #18: ohne ungesicherte Arbeit entscheidet allein der Commit
        p = self.project()
        p.git(p.main, "commit", "-q", "--allow-empty", "--no-verify", "-m", "fremd")
        other = p.git(p.main, "rev-parse", "HEAD").stdout.strip()
        p.git(p.main, "reset", "-q", "--hard", "HEAD~1")
        folder = p.wt("ex-62")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b ex-62 "%s" %s'
                                 % (shutil.which("git"), p.main, folder, other))
        self.assertCleanForeignKept(p, p.run("add", "ex-62"), folder, "ex-62")

    def test_clean_foreign_worktree_on_other_branch_at_start_commit_is_not_removed(self):
        # Mutationsprobe Rework PR #18: ohne ungesicherte Arbeit entscheidet allein der Branch
        p = self.project()
        folder = p.wt("ex-63")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b fremd-63 "%s" HEAD'
                                 % (shutil.which("git"), p.main, folder))
        self.assertCleanForeignKept(p, p.run("add", "ex-63"), folder, "ex-63")
        self.assertIn("fremd-63", p.branches())

    def test_clean_foreign_worktree_behind_symlink_at_review_path_is_not_removed(self):
        # Mutationsprobe Rework PR #18: P3 ohne ungesicherte Arbeit; Symlink- und Pfadprüfung
        # decken sich gegenseitig, gemeinsam entfernt muss das auffallen
        p = self.project()
        head = self.make_pr(p)
        elsewhere = os.path.join(p.tmp, "anderswo", "pr-7")
        link = p.wt("pr-7")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q --detach "%s" %s && mkdir -p "%s" && ln -s "%s" "%s"'
                                 % (shutil.which("git"), p.main, elsewhere, head, os.path.dirname(link),
                                    elsewhere, link))
        self.assertCleanForeignKept(p, p.run("review", "7"), elsewhere, "pr-7")

    def test_p5_foreign_worktree_with_only_an_ignored_env_is_not_removed(self):
        # Re-Review PR #18, P5: ignorierte Dateien sind auch Arbeit (.env mit Geheimnissen)
        p = self.project()
        folder = p.wt("ex-80")
        # gleiche Länge und gleiche Änderungszeit wie die Quelle: nur der Inhalt unterscheidet sich
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b ex-80 "%s" HEAD && echo KEY=fremdX > "%s/.env" '
                                 '&& touch -r "%s/.env" "%s/.env"'
                                 % (shutil.which("git"), p.main, folder, folder, p.main, folder))
        r = p.run("add", "ex-80")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        with open(os.path.join(folder, ".env"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "KEY=fremdX\n")

    def symlinked_repo_folder(self, p, head, env):
        """Im Fenster: <root>/demo ist ein Symlink auf einen fremden Ordner mit einem sauberen,
        detached Review-Worktree pr-7 am PR-Head (Re-Review PR #18, P6)."""
        foreign = os.path.join(p.tmp, "fremd")
        target = os.path.join(foreign, "pr-7")
        script = '"%s" -C "%s" worktree add -q --detach "%s" %s && mkdir -p "%s" && ln -s "%s" "%s"' % (
            shutil.which("git"), p.main, target, head, p.root, foreign, os.path.dirname(p.wt("pr-7")))
        if env:
            script += ' && echo KEY=fremd > "%s/.env"' % target
        self.before_worktree_add(p, script)
        return target

    def test_p6_symlinked_repo_folder_with_foreign_review_worktree_and_env_is_not_removed(self):
        p = self.project()
        target = self.symlinked_repo_folder(p, self.make_pr(p), env=True)
        r = p.run("review", "7")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        self.assertIn(os.path.realpath(target), p.worktrees())
        self.assertTrue(os.path.exists(os.path.join(target, ".env")))

    def test_clean_foreign_review_worktree_behind_symlinked_repo_folder_is_not_removed(self):
        # Re-Review PR #18: ein Symlink im Elternordner unter dem Root belegt kein Eigentum,
        # auch wenn der fremde Worktree sauber ist
        p = self.project()
        target = self.symlinked_repo_folder(p, self.make_pr(p), env=False)
        self.assertCleanForeignKept(p, p.run("review", "7"), target, "pr-7")

    def test_failing_git_status_in_started_worktree_means_not_own(self):
        # Re-Review PR #18, N7: scheitert `git status` im angefangenen Worktree, ist nichts belegt
        self.assert_failing_git_command_means_not_own("status", "ex-81")

    def test_failing_git_ls_files_in_started_worktree_means_not_own(self):
        # Rework PR #18, Runde 3: dasselbe für die Prüfung auf versteckte Änderungen
        self.assert_failing_git_command_means_not_own("ls-files", "ex-92")

    def test_failing_git_reflog_in_started_worktree_means_not_own(self):
        self.assert_failing_git_command_means_not_own("reflog", "ex-96")

    def test_failing_git_for_each_ref_in_started_worktree_means_not_own(self):
        self.assert_failing_git_command_means_not_own("for-each-ref", "ex-97")

    def assert_failing_git_command_means_not_own(self, command, name):
        p = self.project()
        folder = p.wt(name)
        real = shutil.which("git")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1 $2" = "worktree add" ] && [ ! -e "%(flag)s" ]; then
              touch "%(flag)s"
              "%(git)s" -C "%(main)s" worktree add -q -b %(name)s "%(folder)s" HEAD
            fi
            if [ "$1" = %(command)s ] && [ "$(pwd -P)" = "$(cd "%(folder)s" 2>/dev/null && pwd -P)" ]; then
              exit 128  # stumm: eine leere Ausgabe darf nicht als "sauber" gelten
            fi
            exec "%(git)s" "$@"
            """) % {"flag": os.path.join(p.tmp, "fremd-lief"), "git": real, "main": p.main, "folder": folder,
                    "name": name, "command": command},
            mode=0o755, base=p.bin)
        self.assertCleanForeignKept(p, p.run("add", name), folder, name)

    def test_byte_equal_env_copies_do_not_prevent_recognising_own_worktree(self):
        # Rework PR #18, Runde 2: Kopien, wie add sie anlegt, verhindern die eigene Erkennung nicht.
        # Nachgestellt: ein Worktree wie dieser Aufruf ihn anlegt, mit byte-gleichen .env-Kopien.
        p = self.project()
        folder = p.wt("ex-83")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b ex-83 "%s" HEAD && cp "%s/.env" "%s/.env.local" "%s/"'
                                 % (shutil.which("git"), p.main, folder, p.main, p.main, folder))
        r = p.run("add", "ex-83")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "Worktree anlegen fehlgeschlagen")
        self.assertNotIn("nicht gelöscht", r.stderr)
        self.assertNoTrace(p, "ex-83")

    def test_byte_equal_ignored_file_that_add_does_not_copy_makes_worktree_foreign(self):
        # Rework PR #18, Runde 2: nur .env* kopiert add; andere ignorierte Dateien sind fremd,
        # auch wenn sie der Datei im Haupt-Checkout gleichen
        p = self.project()
        p.write("tests/data.txt", "nur lokal\n")
        folder = p.wt("ex-84")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b ex-84 "%s" HEAD && cp "%s/tests/data.txt" "%s/tests/"'
                                 % (shutil.which("git"), p.main, folder, p.main, folder))
        self.assertCleanForeignKept(p, p.run("add", "ex-84"), folder, "ex-84")
        self.assertTrue(os.path.exists(os.path.join(folder, "tests", "data.txt")))

    def test_env_that_is_not_an_ignored_copy_makes_worktree_foreign(self):
        # Rework PR #18, Runde 2: erlaubt sind nur ignorierte, byte-gleiche Kopien als normale Datei.
        # Fremd bleibt: eine nicht ignorierte .envrc (auch wenn byte-gleich) und eine .env als Symlink.
        for name, script in (
                ("ex-85", 'cp "{main}/.envrc" "{wt}/.envrc"'),
                ("ex-86", 'ln -s "{main}/.env" "{wt}/.env"')):
            p = self.project()
            p.write(".envrc", "export X=1\n")
            folder = p.wt(name)
            self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b %s "%s" HEAD && %s' % (
                shutil.which("git"), p.main, name, folder, script.format(main=p.main, wt=folder)))
            self.assertCleanForeignKept(p, p.run("add", name), folder, name)

    def test_p7_p8_hidden_change_to_tracked_file_makes_worktree_foreign(self):
        # Re-Review PR #18, Runde 2, P7/P8: `git status` verschweigt Änderungen an Dateien mit
        # skip-worktree bzw. assume-unchanged; die Arbeit darf trotzdem nicht verloren gehen
        for name, flag in (("ex-90", "--skip-worktree"), ("ex-91", "--assume-unchanged")):
            p = self.project()
            folder = p.wt(name)
            self.before_worktree_add(p, '"%s" -C "%s" worktree add -q -b %s "%s" HEAD && echo ARBEIT >> "%s/tests/test_demo.py" '
                                     '&& "%s" -C "%s" update-index %s tests/test_demo.py'
                                     % (shutil.which("git"), p.main, name, folder, folder,
                                        shutil.which("git"), folder, flag))
            self.assertCleanForeignKept(p, p.run("add", name), folder, name)
            with open(os.path.join(folder, "tests", "test_demo.py"), encoding="utf-8") as f:
                self.assertTrue(f.read().endswith("ARBEIT\n"), name)

    def test_commit_only_in_worktree_head_reflog_makes_worktree_foreign(self):
        # Rework PR #18, Runde 3: Commit im fremden Review-Worktree, danach `reset --hard` auf den
        # PR-Head. git status ist leer, der Commit hängt nur noch am HEAD-Reflog dieses Worktrees.
        p = self.project()
        head = self.make_pr(p)
        folder = p.wt("pr-7")
        g = shutil.which("git")
        self.before_worktree_add(p, '"{g}" -C "{main}" worktree add -q --detach "{wt}" {head} && echo x > "{wt}/arbeit" '
                                    '&& "{g}" -C "{wt}" add arbeit && "{g}" -C "{wt}" commit -q --no-verify -m arbeit '
                                    '&& "{g}" -C "{wt}" reset -q --hard {head}'
                                 .format(g=g, main=p.main, wt=folder, head=head))
        self.assertCleanForeignKept(p, p.run("review", "7"), folder, "pr-7")
        self.assertEqual(p.git(folder, "log", "-1", "--format=%s", "HEAD@{1}").stdout.strip(), "arbeit")

    def test_refs_of_only_this_worktree_make_it_foreign(self):
        # Rework PR #18, Runde 3: refs/worktree/* und refs/bisect/* gehören nur diesem Worktree
        # und verschwinden mit ihm; ein Commit, der nur dort hängt, ginge verloren
        for name, ref in (("ex-93", "refs/worktree/sicher"), ("ex-94", "refs/bisect/bad")):
            p = self.project()
            folder = p.wt(name)
            g = shutil.which("git")
            self.before_worktree_add(p, '"{g}" -C "{main}" worktree add -q -b {name} "{wt}" HEAD '
                                        '&& "{g}" -C "{wt}" commit -q --allow-empty --no-verify -m arbeit '
                                        '&& "{g}" -C "{wt}" update-ref {ref} HEAD '
                                        '&& "{g}" -C "{wt}" reset -q --hard HEAD~1 && "{g}" -C "{wt}" reflog expire --expire=all --all'
                                     .format(g=g, main=p.main, wt=folder, name=name, ref=ref))
            self.assertCleanForeignKept(p, p.run("add", name), folder, name)
            self.assertEqual(p.git(folder, "log", "-1", "--format=%s", ref).stdout.strip(), "arbeit", name)

    def test_initialized_submodule_makes_worktree_foreign(self):
        # Rework PR #18, Runde 3: mit `ignore = all` verschweigt git status das Submodul ganz.
        # Ein frischer Worktree hat nie ein initialisiertes Submodul; Arbeit darin bleibt.
        p = self.project()
        sub = os.path.join(p.tmp, "subsrc")
        p.git(p.tmp, "init", "-q", "-b", "main", sub)
        p.write("s.txt", "s\n", base=sub)
        p.git(sub, "add", "s.txt")
        p.git(sub, "commit", "-q", "-m", "s")
        p.git(p.main, "-c", "protocol.file.allow=always", "submodule", "add", "-q", sub, "sub")
        p.git(p.main, "config", "-f", ".gitmodules", "submodule.sub.ignore", "all")
        p.git(p.main, "add", "-A")
        p.git(p.main, "commit", "-q", "--no-verify", "-m", "submodul")
        p.git(p.main, "push", "-q")
        folder = p.wt("ex-95")
        g = shutil.which("git")
        self.before_worktree_add(p, '"{g}" -C "{main}" worktree add -q -b ex-95 "{wt}" HEAD '
                                    '&& "{g}" -C "{wt}" -c protocol.file.allow=always submodule -q update --init '
                                    '&& echo ARBEIT > "{wt}/sub/neu" && "{g}" -C "{wt}/sub" add neu '
                                    '&& "{g}" -C "{wt}/sub" commit -q --no-verify -m arbeit'
                                 .format(g=g, main=p.main, wt=folder))
        r = p.run("add", "ex-95", "--no-compare")
        self.assertCleanForeignKept(p, r, folder, "ex-95")
        self.assertEqual(p.git(os.path.join(folder, "sub"), "log", "-1", "--format=%s").stdout.strip(), "arbeit")

    def test_rollback_of_own_worktree_with_copied_env_still_cleans_up(self):
        # Rework PR #18, Runde 2: die von add kopierten .env* dürfen das Aufräumen nicht verhindern
        p = self.project()
        r = p.run("add", "ex-82", "--install", 'test -f .env && test -f .env.local && exit 3')
        self.assertFails(r, "Installation fehlgeschlagen (Exit 3)")
        copied = [l for l in r.stderr.splitlines() if ".env* kopiert:" in l]
        self.assertTrue(copied, r.stderr)
        self.assertEqual(set(copied[0].split(": ", 2)[-1].split(", ")), {".env", ".env.local"})
        self.assertNoTrace(p, "ex-82")

    def test_p2_foreign_review_worktree_at_pr_head_with_work_is_not_removed(self):
        # Review PR #18, P2: detached am PR-Head belegt kein Eigentum
        p = self.project()
        head = self.make_pr(p)
        folder = p.wt("pr-7")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q --detach "%s" %s && echo arbeit > "%s/notiz.txt"'
                                 % (shutil.which("git"), p.main, folder, head, folder))
        r = p.run("review", "7")
        self.assertForeignWorktreeKept(p, r, folder)

    def test_p3_symlink_at_review_path_to_foreign_worktree_is_not_followed(self):
        # Review PR #18, P3: <root>/demo/pr-7 ist ein Symlink auf einen fremden Review-Worktree
        p = self.project()
        head = self.make_pr(p)
        elsewhere = os.path.join(p.tmp, "anderswo", "pr-7")
        link = p.wt("pr-7")
        self.before_worktree_add(p, '"%s" -C "%s" worktree add -q --detach "%s" %s && echo arbeit > "%s/notiz.txt" '
                                 '&& mkdir -p "%s" && ln -s "%s" "%s"'
                                 % (shutil.which("git"), p.main, elsewhere, head, elsewhere,
                                    os.path.dirname(link), elsewhere, link))
        r = p.run("review", "7")
        self.assertForeignWorktreeKept(p, r, elsewhere)
        self.assertTrue(os.path.islink(link))

    def test_foreign_branch_created_in_the_window_is_not_deleted(self):
        # Re-Review PR #3, A1: `git worktree add -b` scheitert am fremden Branch (mit eigenem
        # Commit); das Aufräumen darf ihn nicht löschen.
        p = self.project()
        p.git(p.main, "commit", "-q", "--allow-empty", "--no-verify", "-m", "fremde Arbeit")
        foreign = p.git(p.main, "rev-parse", "HEAD").stdout.strip()
        p.git(p.main, "reset", "-q", "--hard", "HEAD~1")
        self.before_worktree_add(p, '"%s" -C "%s" branch ex-51 %s' % (shutil.which("git"), p.main, foreign))
        r = p.run("add", "ex-51")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "nicht gelöscht")
        self.assertEqual(p.git(p.main, "rev-parse", "refs/heads/ex-51").stdout.strip(), foreign)
        self.assertFalse(os.path.exists(p.wt("ex-51")))

    def test_add_aborted_after_registration_leaves_no_registration(self):
        # Re-Review PR #3, R5: bricht `git worktree add` nach der Registrierung, aber vor der
        # .git-Datei im Ordner ab, scheitert `git worktree remove`; die Registrierung darf
        # trotzdem nicht hängen bleiben (gezielt, ohne repo-weites prune).
        p = self.project()
        real = shutil.which("git")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1" = worktree ] && [ "$2" = add ]; then
              "%s" "$@" || exit $?
              for a; do case "$a" in */ex-52) rm -f "$a/.git";; esac; done
              exit 1
            fi
            exec "%s" "$@"
            """) % (real, real), mode=0o755, base=p.bin)
        r = p.run("add", "ex-52")
        self.assertFails(r, "Worktree anlegen")
        self.assertNoTrace(p, "ex-52")

    def test_git_failing_during_cleanup_keeps_everything_and_reports_original_error(self):
        # Pre-Push-Review: scheitert `git worktree list` beim Aufräumen, darf das weder
        # die eigentliche Ursache verdecken noch ungeprüft löschen.
        p = self.project()
        real = shutil.which("git")
        flag = os.path.join(p.tmp, "add-lief")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1 $2" = "worktree add" ]; then touch "%(flag)s"; echo "fatal: kaputt beim Anlegen" >&2; exit 1; fi
            if [ "$1 $2" = "worktree list" ] && [ -e "%(flag)s" ]; then echo "fatal: list kaputt" >&2; exit 1; fi
            exec "%(git)s" "$@"
            """) % {"flag": flag, "git": real}, mode=0o755, base=p.bin)
        r = p.run("add", "ex-54")
        self.assertFails(r, "kaputt beim Anlegen", "nicht gelöscht")
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_unreadable_foreign_folder_keeps_everything_and_reports_original_error(self):
        # Review PR #18, A1-Fehlerweg (P4): ein fremder Ordner mit chmod 000 im Fenster; das
        # Lesen beim Aufräumen scheitert mit OSError, das darf die Ursache nicht verdecken.
        p = self.project()
        folder = p.wt("ex-70")
        self.addCleanup(lambda: os.path.isdir(folder) and os.chmod(folder, 0o755))
        self.before_worktree_add(p, 'mkdir -p "%s" && echo x > "%s/f" && chmod 000 "%s"' % (folder, folder, folder))
        r = p.run("add", "ex-70")
        self.assertTrue(os.path.exists(os.path.join(p.tmp, "fremd-lief")), "Rennen nicht ausgelöst")
        self.assertFails(r, "Worktree anlegen fehlgeschlagen", "nicht gelöscht")
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        self.assertTrue(os.path.isdir(folder))

    def test_add_aborted_after_mkdir_before_registration_leaves_no_folder(self):
        # Pre-Push-Review: bricht `git worktree add` nach dem Anlegen des (leeren) Ordners,
        # aber vor der Registrierung ab, bleibt kein Ordner liegen, der jedes spätere add blockiert.
        p = self.project()
        real = shutil.which("git")
        p.write("git", textwrap.dedent("""\
            #!/bin/sh
            if [ "$1 $2" = "worktree add" ]; then
              for a; do case "$a" in */ex-55) mkdir -p "$a";; esac; done
              exit 1
            fi
            exec "%s" "$@"
            """) % real, mode=0o755, base=p.bin)
        r = p.run("add", "ex-55")
        self.assertFails(r, "Worktree anlegen")
        self.assertNoTrace(p, "ex-55")

    def test_add_is_green_when_test_is_skipped_in_main_checkout_too(self):
        p = self.project(test=DATA_TEST)
        self.assertOk(p.run("add", "ex-4"))


if __name__ == "__main__":
    unittest.main()
