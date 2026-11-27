"""Prüft den context-guard über seine Hook-Schnittstelle: JSON auf stdin wie von
Claude Code (PostToolBatch), zusätzlicher Kontext als JSON auf stdout.

Nachgestellt werden nur Systemgrenzen: die Statuszeilen-Datei unter
$HOME/.config/studio-board/sessions/<terminal>.json (aus der anonymisierten
Fixture), das Herdr-Terminal über HC_TERMINAL_ID und die Herdr-CLI `hc`
(ein Skript im PATH, das das Label studio.role liefert).
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
HOOK = os.path.join(ROOT, "hooks", "context_guard.py")
FIXTURE = os.path.join(HERE, "fixtures", "statusline", "session.json")
TERMINAL = "t9z"


class Studio:
    """Wegwerf-HOME mit Statuszeilen-Datei und einer nachgestellten `hc`-CLI."""

    def __init__(self, tc):
        self.home = tempfile.mkdtemp(prefix="slickfab-cg-")
        tc.addCleanup(shutil.rmtree, self.home, True)
        self.bin = os.path.join(self.home, "bin")
        os.makedirs(self.bin)
        self.sessions = os.path.join(self.home, ".config", "studio-board", "sessions")
        os.makedirs(self.sessions)
        with open(FIXTURE, encoding="utf-8") as f:
            self.status = json.load(f)
        self.session_id = self.status["session_id"]
        self.role("implementer")

    def role(self, role):
        labels = {"studio.issue": "EX-1"}
        if role is not None:
            labels["studio.role"] = role
        self.hc_script('cat <<\'J\'\n%s\nJ\n' % json.dumps(
            {"address": TERMINAL, "labels": labels, "state": "live"}))

    def hc_script(self, body):
        path = os.path.join(self.bin, "hc")
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n" + body)
        os.chmod(path, 0o755)

    def context(self, percent):
        self.status["context_window"]["used_percentage"] = percent
        self.status["context_window"]["remaining_percentage"] = 100 - percent
        self.write_status(json.dumps(self.status))

    def write_status(self, text):
        with open(os.path.join(self.sessions, TERMINAL + ".json"), "w", encoding="utf-8") as f:
            f.write(text)

    def run(self, event=None, terminal=TERMINAL, **env_extra):
        if event is None:
            event = {"session_id": self.session_id, "hook_event_name": "PostToolBatch",
                     "cwd": "/home/user/repo", "tool_calls": []}
        env = {k: v for k, v in os.environ.items() if not k.startswith("HC_")}
        env.update(HOME=self.home, PATH=self.bin + os.pathsep + env.get("PATH", ""))
        env.pop("XDG_STATE_HOME", None)
        if terminal is not None:
            env["HC_TERMINAL_ID"] = terminal
        env.update(env_extra)
        data = event if isinstance(event, str) else json.dumps(event)
        r = subprocess.run([sys.executable, HOOK], input=data, capture_output=True,
                           text=True, timeout=30, env=env)
        return r

    def warning(self, **kw):
        r = self.run(**kw)
        assert r.returncode == 0, (r.returncode, r.stderr)
        if not r.stdout.strip():
            return ""
        out = json.loads(r.stdout)["hookSpecificOutput"]
        assert out["hookEventName"] == "PostToolBatch", out
        return out["additionalContext"]


class WarningTest(unittest.TestCase):
    def test_role_terminal_at_65_gets_the_wrap_up_warning(self):
        s = Studio(self)
        s.context(65)
        text = s.warning()
        self.assertIn("65", text)
        self.assertIn("Teilaufgabe", text)

    def test_role_terminal_at_80_gets_the_handoff_warning(self):
        s = Studio(self)
        s.context(80)
        text = s.warning()
        self.assertIn("80 % voll", text)
        self.assertIn("NEEDS_CONTEXT", text)

    def test_79_is_still_the_wrap_up_warning(self):
        s = Studio(self)
        s.context(79)
        text = s.warning()
        self.assertIn("79 % voll", text)
        self.assertIn("Teilaufgabe", text)
        self.assertNotIn("NEEDS_CONTEXT", text)

    def test_fractional_percentage_is_shown_rounded(self):
        s = Studio(self)
        s.context(81.6)
        self.assertIn("82 % voll", s.warning())

    def test_warning_texts_match_the_reference_word_for_word(self):
        # Referenz der beiden Warnungen. Jede Änderung am Wortlaut ist hier im Diff sichtbar.
        s = Studio(self)
        s.context(70)
        self.assertEqual(s.warning(), (
            "slickfab context-guard: Dein Kontext ist zu 70 % voll (Schwelle 65 %). "
            "Schließ die laufende Teilaufgabe ab und fang nichts Neues an. "
            "Ab 80 % schreibst du die Übergabe."))
        s.context(86)
        self.assertEqual(s.warning(), (
            "slickfab context-guard: Dein Kontext ist zu 86 % voll (Schwelle 80 %). "
            "Hör jetzt auf zu bauen und schreib die Übergabe mit dem Schritt `handoff` "
            "(/slickfab:handoff <Ticket>). Danach endest du mit dem Marker `NEEDS_CONTEXT` "
            "als letzter Zeile: `SLICKFAB-STATUS: NEEDS_CONTEXT`. Eine frische Session macht weiter."))

    def test_handoff_warning_names_step_and_marker(self):
        s = Studio(self)
        s.context(91)
        text = s.warning()
        self.assertIn("`handoff`", text)
        self.assertIn("NEEDS_CONTEXT", text)
        self.assertIn("SLICKFAB-STATUS: NEEDS_CONTEXT", text)

    def test_wrap_up_warning_does_not_ask_for_the_handoff_yet(self):
        s = Studio(self)
        s.context(65)
        self.assertNotIn("NEEDS_CONTEXT", s.warning())


class OnceTest(unittest.TestCase):
    def test_each_threshold_warns_once_per_session(self):
        s = Studio(self)
        s.context(70)
        self.assertIn("65 %", s.warning())
        self.assertEqual(s.warning(), "")
        s.context(85)
        self.assertIn("80 %", s.warning())
        self.assertEqual(s.warning(), "")
        s.context(72)  # nach einer Kompaktierung: 65 % kam schon
        self.assertEqual(s.warning(), "")

    def test_jump_straight_past_80_gives_only_the_handoff_warning(self):
        s = Studio(self)
        s.context(83)
        text = s.warning()
        self.assertIn("80 %", text)
        self.assertNotIn("Teilaufgabe", text)
        s.context(84)
        self.assertEqual(s.warning(), "")
        s.context(70)  # nach Kompaktierung: kein 65-%-Hinweis nach der Übergabe-Aufforderung
        self.assertEqual(s.warning(), "")

    def test_new_session_in_the_same_terminal_warns_again(self):
        s = Studio(self)
        s.context(70)
        self.assertIn("65 %", s.warning())
        s.session_id = s.status["session_id"] = "00000000-0000-4000-8000-000000000002"
        s.context(70)
        self.assertIn("65 %", s.warning())

    def test_after_both_warnings_hc_is_not_asked_again(self):
        # Ein hängendes hc würde jeden weiteren Aufruf um 2 s aufhalten.
        s = Studio(self)
        s.context(85)
        self.assertIn("80 %", s.warning())
        s.hc_script("sleep 30\n")
        for p in (85, 90, 70):
            with self.subTest(p=p):
                s.context(p)
                start = time.monotonic()
                self.assertEqual(s.warning(), "")
                self.assertLess(time.monotonic() - start, 1.5)

    def test_after_the_wrap_up_warning_hc_is_not_asked_below_80(self):
        s = Studio(self)
        s.context(66)
        self.assertIn("65 %", s.warning())
        s.hc_script("sleep 30\n")
        s.context(75)
        start = time.monotonic()
        self.assertEqual(s.warning(), "")
        self.assertLess(time.monotonic() - start, 1.5)

    def test_terminal_without_role_asks_hc_only_once_per_session(self):
        s = Studio(self)
        s.role(None)
        s.context(70)
        self.assertEqual(s.warning(), "")
        s.hc_script("sleep 30\n")
        for p in (70, 85):
            with self.subTest(p=p):
                s.context(p)
                start = time.monotonic()
                self.assertEqual(s.warning(), "")
                self.assertLess(time.monotonic() - start, 1.5)

    def test_failing_hc_is_asked_again_next_time(self):
        # Ein Fehler von hc ist keine Antwort „keine Rolle“; beim nächsten Mal wird neu gefragt.
        s = Studio(self)
        s.context(70)
        s.hc_script("exit 1\n")
        self.assertEqual(s.warning(), "")
        s.role("implementer")
        self.assertIn("65 %", s.warning())

    def test_parallel_calls_warn_only_once(self):
        s = Studio(self)
        s.context(70)
        # Ein langsames hc hält alle Aufrufe gleichzeitig zwischen Vorprüfung und Merken.
        s.hc_script('sleep 0.3; echo \'{"labels": {"studio.role": "implementer"}}\'\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith("HC_")}
        env.update(HOME=s.home, PATH=s.bin + os.pathsep + env.get("PATH", ""),
                   HC_TERMINAL_ID=TERMINAL)
        env.pop("XDG_STATE_HOME", None)
        event = json.dumps({"session_id": s.session_id, "hook_event_name": "PostToolBatch"})
        procs = [subprocess.Popen([sys.executable, HOOK], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, env=env) for _ in range(8)]
        for p in procs:  # erst allen die Eingabe geben, damit sie wirklich gleichzeitig laufen
            p.stdin.write(event)
            p.stdin.close()
        outs = [p.stdout.read() for p in procs]
        for p in procs:
            p.wait(timeout=30)
            p.stdout.close()
        self.assertEqual(sum(1 for o in outs if "65 %" in o), 1, outs)

    def test_state_files_are_private(self):
        s = Studio(self)
        s.context(70)
        self.assertIn("65 %", s.warning())
        folder = os.path.join(s.home, ".local", "state", "slickfab", "context-guard")
        self.assertEqual(os.stat(folder).st_mode & 0o777, 0o700)
        marker = os.path.join(folder, s.session_id + ".65")
        self.assertEqual(os.stat(marker).st_mode & 0o777, 0o600)

    def test_unwritable_state_stays_silent_instead_of_repeating(self):
        s = Studio(self)
        s.context(70)
        blocker = os.path.join(s.home, "state-is-a-file")
        open(blocker, "w").close()
        for _ in range(2):
            r = s.run(XDG_STATE_HOME=blocker)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))


LIMIT_SECONDS = 0.5  # Grenze aus dem Dossier: je Aufruf höchstens eine halbe Sekunde


class CostTest(unittest.TestCase):
    def test_each_call_stays_under_the_limit(self):
        s = Studio(self)
        for p, terminal in ((10, TERMINAL), (70, TERMINAL), (90, TERMINAL), (90, None)):
            with self.subTest(p=p, terminal=terminal):
                s.context(p)
                start = time.monotonic()
                r = s.run(terminal=terminal)
                self.assertEqual(r.returncode, 0)
                self.assertLess(time.monotonic() - start, LIMIT_SECONDS)

    def test_hanging_hc_does_not_hold_the_session(self):
        s = Studio(self)
        s.context(90)
        s.hc_script("sleep 30\n")
        start = time.monotonic()
        r = s.run()
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertLess(time.monotonic() - start, 3)

    def test_warns_without_any_network(self):
        # Python-Sockets sind gesperrt; die Warnung kommt trotzdem.
        s = Studio(self)
        site = os.path.join(s.home, "nonet")
        os.makedirs(site)
        with open(os.path.join(site, "sitecustomize.py"), "w", encoding="utf-8") as f:
            f.write("import socket\n"
                    "def _no(*a, **k):\n    raise OSError('Netz gesperrt')\n"
                    "socket.socket.connect = _no\nsocket.getaddrinfo = _no\n"
                    "socket.create_connection = _no\n")
        s.context(90)
        self.assertIn("80 %", s.warning(PYTHONPATH=site))

    def test_plugin_registers_the_hook_with_a_short_timeout(self):
        entry = registered_command(self)
        self.assertEqual(entry["type"], "command")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/hooks/context_guard.py", entry["command"])
        self.assertLessEqual(entry["timeout"], 5)

    def test_registered_command_delivers_the_warning(self):
        # Der Befehl aus hooks.json, so wie Claude Code ihn per Shell startet.
        s = Studio(self)
        s.context(90)
        r = run_registered(self, s, ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("(Schwelle 80 %)",
                      json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_missing_script_never_stops_the_session(self):
        # Fehlt das Skript (Worktree weg, Plugin-Cache mitten im Update), endet python3 mit
        # Exit 2, und Exit 2 hält bei PostToolBatch die Agent-Schleife an. Der Befehl darf
        # deshalb nie mit einem Fehlercode enden; auch nicht in normalen Sitzungen.
        s = Studio(self)
        s.context(90)
        for root in (os.path.join(s.home, "gibt-es-nicht"), ""):
            with self.subTest(root=root):
                r = run_registered(self, s, root)
                self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)


def registered_command(tc):
    with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
        hooks = json.load(f)["hooks"]
    entries = [c for h in hooks.get("PostToolBatch", []) for c in h["hooks"]]
    tc.assertEqual(len(entries), 1, hooks)
    return entries[0]


def run_registered(tc, studio, plugin_root):
    env = {k: v for k, v in os.environ.items() if not k.startswith("HC_")}
    env.update(HOME=studio.home, PATH=studio.bin + os.pathsep + env.get("PATH", ""),
               HC_TERMINAL_ID=TERMINAL, CLAUDE_PLUGIN_ROOT=plugin_root)
    env.pop("XDG_STATE_HOME", None)
    event = json.dumps({"session_id": studio.session_id, "hook_event_name": "PostToolBatch"})
    return subprocess.run(["sh", "-c", registered_command(tc)["command"]], input=event,
                          capture_output=True, text=True, timeout=30, env=env)


class SilenceTest(unittest.TestCase):
    """Normale Sitzungen: nichts auf stdout, nichts auf stderr, Exit 0."""

    def assertSilent(self, r):
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_below_65_is_silent(self):
        s = Studio(self)
        for p in (0, 10, 64):
            with self.subTest(p=p):
                s.context(p)
                self.assertSilent(s.run())

    def test_terminal_without_role_label_is_silent(self):
        s = Studio(self)
        s.role(None)
        s.context(90)
        self.assertSilent(s.run())

    def test_empty_role_label_is_silent(self):
        s = Studio(self)
        s.role("")
        s.context(90)
        self.assertSilent(s.run())

    def test_session_outside_herdr_is_silent(self):
        s = Studio(self)
        s.context(90)
        self.assertSilent(s.run(terminal=None))

    def test_without_hc_cli_is_silent(self):
        s = Studio(self)
        s.context(90)
        os.remove(os.path.join(s.bin, "hc"))
        self.assertSilent(s.run(PATH=s.bin))

    def test_failing_or_garbled_hc_is_silent(self):
        # Je Fall ein frisches Studio: Ein früherer Fall darf „keine Rolle“ nicht für
        # die späteren vormerken und sie so verdecken.
        for body in ("echo 'no such terminal' >&2; exit 1\n",
                     "echo 'kein json'\n",
                     "echo '[1, 2]'\n",
                     "echo '{\"labels\": [\"studio.role\"]}'\n",
                     "echo '{\"labels\": {\"studio.role\": 7}}'\n",
                     "echo '{\"labels\": {\"studio.role\": \"implementer\"}}'; exit 3\n"):
            with self.subTest(body=body):
                s = Studio(self)
                s.context(90)
                s.hc_script(body)
                self.assertSilent(s.run())

    def test_subagent_is_silent(self):
        # Die Statuszeile misst die Hauptsession, nicht den Subagent; sein Kontext ist ein anderer.
        s = Studio(self)
        s.context(90)
        event = {"session_id": s.session_id, "hook_event_name": "PostToolBatch",
                 "agent_id": "a1", "agent_type": "Explore", "tool_calls": []}
        self.assertSilent(s.run(event=event))


def walk(root):
    """Alle Pfade unter root, ohne den Bytecode-Cache, den das System-Python von macOS
    unter $HOME/Library anlegt."""
    cache = os.path.join(root, "Library")
    for folder, dirs, files in os.walk(root):
        for name in dirs + files:
            path = os.path.join(folder, name)
            if path != cache and not path.startswith(cache + os.sep):
                yield path


class BrokenStatusTest(unittest.TestCase):
    """Fehlt die Statuszeilen-Datei, ist sie leer, veraltet oder kaputt: still, Exit 0."""

    def assertSilent(self, s, **kw):
        r = s.run(**kw)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_missing_file(self):
        s = Studio(self)
        self.assertSilent(s)

    def test_missing_sessions_folder(self):
        s = Studio(self)
        shutil.rmtree(s.sessions)
        self.assertSilent(s)

    def test_empty_or_garbled_file(self):
        s = Studio(self)
        for text in ("", " ", "{", "kein json", "[]", "null", "90", '"90"', "\x00\x00"):
            with self.subTest(text=text):
                s.write_status(text)
                self.assertSilent(s)

    def test_binary_file(self):
        s = Studio(self)
        with open(os.path.join(s.sessions, TERMINAL + ".json"), "wb") as f:
            f.write(b"\xff\xfe\x00garbage")
        self.assertSilent(s)

    def test_wrong_shape_or_value(self):
        # Je Fall ein frisches Studio: Eine fälschliche Warnung darf die nächsten Fälle
        # nicht über den „nur einmal“-Merker verdecken.
        for value in (None, "90", True, -5, 101, 1e309, float("nan"), [90], {"p": 90}):
            with self.subTest(value=value):
                s = Studio(self)
                s.status["context_window"]["used_percentage"] = value
                s.write_status(json.dumps(s.status))
                self.assertSilent(s)
        for broken in ({"context_window": None}, {"context_window": 90}, {"context_window": {}}):
            with self.subTest(broken=broken):
                s = Studio(self)
                s.write_status(json.dumps(dict(s.status, **broken)))
                self.assertSilent(s)

    def test_boundaries_0_and_100_are_valid(self):
        s = Studio(self)
        s.context(100)
        self.assertIn("100 %", s.warning())

    def test_file_of_another_session_is_stale(self):
        # Gleiches Terminal, aber die Datei stammt aus einer früheren Claude-Session.
        s = Studio(self)
        s.status["session_id"] = "00000000-0000-4000-8000-0000000000ff"
        s.context(90)
        self.assertSilent(s)

    def test_file_without_session_id_is_stale(self):
        s = Studio(self)
        del s.status["session_id"]
        s.context(90)
        self.assertSilent(s)

    def test_old_file_is_stale(self):
        s = Studio(self)
        s.context(90)
        path = os.path.join(s.sessions, TERMINAL + ".json")
        old = time.time() - 31 * 60
        os.utime(path, (old, old))
        self.assertSilent(s)

    def test_recent_file_still_counts(self):
        s = Studio(self)
        s.context(90)
        path = os.path.join(s.sessions, TERMINAL + ".json")
        recent = time.time() - 29 * 60
        os.utime(path, (recent, recent))
        self.assertIn("80 %", s.warning())

    def test_garbled_hook_input(self):
        s = Studio(self)
        s.context(90)
        for event in ("", "kein json", "[]", "null", json.dumps({"session_id": 5}),
                      json.dumps({"session_id": "../../etc/passwd"}), json.dumps({})):
            with self.subTest(event=event):
                self.assertSilent(s, event=event)

    def test_odd_session_id_never_becomes_a_path(self):
        # session_id steht in Hook-Eingabe und Statusdatei gleich, sonst greift schon die
        # Prüfung „andere Session“. Erwartet: still, und nichts entsteht außerhalb des Merkordners.
        for session in ("../x", "../../escaped", "a/b", "x.y", "a" * 129):
            with self.subTest(session=session):
                s = Studio(self)
                s.session_id = s.status["session_id"] = session
                s.context(90)
                before = set(walk(s.home))
                self.assertSilent(s)
                self.assertEqual(set(walk(s.home)) - before, set())

    def test_odd_terminal_id_never_becomes_a_path(self):
        s = Studio(self)
        s.context(90)
        # Eine gültige Datei liegt dort, wohin ein Ausbruch per ../ zeigen würde.
        with open(os.path.join(s.home, ".config", "studio-board", "evil.json"), "w") as f:
            json.dump(s.status, f)
        for terminal in ("../evil", "x/../../evil"):
            with self.subTest(terminal=terminal):
                r = s.run(terminal=terminal)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        for terminal in ("", "../t9z", "t9z/../t9z", "t9z\x00", "a" * 65):
            with self.subTest(terminal=terminal):
                try:
                    r = s.run(terminal=terminal)
                except ValueError:  # NUL im Env lässt subprocess selbst ablehnen
                    continue
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))


REAL_SESSIONS = os.path.join(os.path.expanduser("~"), ".config", "studio-board", "sessions")


def newest_real_status():
    try:
        names = [n for n in os.listdir(REAL_SESSIONS) if n.endswith(".json") and n[0] != "."]
    except OSError:
        return None
    paths = sorted((os.path.join(REAL_SESSIONS, n) for n in names), key=os.path.getmtime)
    for path in reversed(paths):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            continue
    return None


class FormatContractTest(unittest.TestCase):
    """Kritische Verbindung context-guard ↔ Statuszeilen-Dateien. Die Fixture ist der
    Vertrag; auf einem Rechner mit Studio wird sie gegen die neueste echte Datei geprüft
    (nur Schlüssel und Typen, kein Inhalt wird ausgegeben). Ohne Studio übersprungen."""

    def test_fixture_has_the_fields_the_hook_reads(self):
        with open(FIXTURE, encoding="utf-8") as f:
            status = json.load(f)
        self.assertIsInstance(status["session_id"], str)
        self.assertIsInstance(status["context_window"]["used_percentage"], int)

    def test_real_statusline_file_still_matches_the_fixture(self):
        real = newest_real_status()
        if real is None:
            self.skipTest("keine Statuszeilen-Datei auf diesem Rechner")
        self.assertIsInstance(real.get("session_id"), str, "session_id fehlt im echten Format")
        window = real.get("context_window")
        self.assertIsInstance(window, dict, "context_window fehlt im echten Format")
        self.assertIn("used_percentage", window, "context_window.used_percentage fehlt")
        self.assertIsInstance(window["used_percentage"], (int, float, type(None)))


if __name__ == "__main__":
    unittest.main()
