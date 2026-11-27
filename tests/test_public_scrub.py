"""Das Repo enthält keine privaten Bezüge (Vorbereitung auf das öffentliche Repo).

Durchsucht jede getrackte Datei (`git ls-files`) nach privaten Mustern: Name und
Adressen des Maintainers, Linear-Werte und Ticket-IDs des privaten Trackers,
private Pfade, interne Terminals und Projekte. Jeder Treffer macht den Test rot.

Einzige feste Ausnahme: `LICENSE` und `NOTICE` nennen den Rechteinhaber. Dort ist
nur sein Name erlaubt, alle anderen Muster gelten auch dort.

Die Muster sind so geschrieben, dass diese Datei sich selbst nicht findet
(`jon[a]h` statt des Namens), damit sie keine weitere Ausnahme braucht.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (Name, Muster). Groß- und Kleinschreibung zählt nicht.
PATTERNS = [
    ("Name des Maintainers", r"jon[a]h"),
    ("Nachname des Maintainers", r"jeschk[e]it"),
    ("Kontaktadresse", r"kontak[t]@"),
    ("Linear-User des Agents", r"\bat[l]as\b"),
    ("Ticket-ID des privaten Trackers", r"\bsl[i]-[0-9]"),
    ("privater Ordner", r"claude[ _-]ar[e]a"),
    ("privates Master-Repo", r"herdr-mast[e]r"),
    ("privates Wissensrepo", r"slick-a[i]\b"),
    ("internes Projekt", r"oki[d]o"),
    ("internes Projekt (Ticket)", r"\bok[i]-[0-9]"),
    ("Firma", r"vetstag[e]"),
    ("internes Projekt", r"cv-agen[t]"),
    ("internes Projekt", r"tam-katal[o]g"),
    ("interne Terminal-Adresse", r"\bt(?:1[1]|4[g]|5[y])\b"),
    ("GitHub-noreply-Adresse", r"users\.norepl[y]\.github\.com"),
    ("privater Home-Pfad", r"/users/jon[a]h|/home/jon[a]h"),
    ("Linear-Team als Beispielwert", r"team[ „\"':=]+jon[a]h"),
    ("Linear-Projekt als Beispielwert", r"projekt[ „\"':]+slickf[a]b\b"),
]
COMPILED = [(name, re.compile(rx, re.I)) for name, rx in PATTERNS]

# Rechteinhaber: in LICENSE und NOTICE ist genau sein Name erlaubt, sonst nichts.
OWNER_FILES = ("LICENSE", "NOTICE")
OWNER_PATTERNS = ("Name des Maintainers", "Nachname des Maintainers")


def tracked_files(root):
    r = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError("git ls-files: %s" % r.stderr.decode(errors="replace").strip())
    return [p for p in r.stdout.decode("utf-8").split("\0") if p]


def scan_text(path, text):
    """Alle Treffer in einem Text als (pfad, zeile, mustername, fundstelle)."""
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        for name, rx in COMPILED:
            if path in OWNER_FILES and name in OWNER_PATTERNS:
                continue
            m = rx.search(line)
            if m:
                hits.append((path, no, name, m.group(0)))
    return hits


def scan(root):
    hits = []
    for path in tracked_files(root):
        full = os.path.join(root, path)
        if not os.path.isfile(full):  # gelöscht, aber noch im Index
            continue
        with open(full, "rb") as f:
            data = f.read()
        # Auch Dateinamen zählen (etwa belege/…-<ticket>.md).
        hits += [(path, 0, n, s) for _, _, n, s in scan_text(path, path.replace("/", " "))]
        hits += scan_text(path, data.decode("utf-8", errors="replace"))
    return hits


class RepoIsPublicTest(unittest.TestCase):
    def test_no_private_references_in_tracked_files(self):
        hits = scan(ROOT)
        report = "\n".join("%s:%d: %s (%r)" % h for h in hits[:50])
        self.assertEqual(hits, [], "private Bezüge gefunden (%d):\n%s" % (len(hits), report))


class ScannerFindsTest(unittest.TestCase):
    """Fehlerfälle: Der Scanner muss eingefügte private Werte finden."""

    def setUp(self):
        base = os.path.join(ROOT, ".test-tmp")
        os.makedirs(base, exist_ok=True)
        self.repo = tempfile.mkdtemp(prefix="scrub-", dir=base)
        subprocess.run(["git", "init", "-q", self.repo], check=True, timeout=30)

    def tearDown(self):
        shutil.rmtree(self.repo)

    def add(self, path, text):
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.run(["git", "-C", self.repo, "add", path], check=True, timeout=30)

    def names(self):
        return sorted({(h[0], h[2]) for h in scan(self.repo)})

    def test_clean_repo_has_no_hits(self):
        self.add("a.md", "Team Example, Ticket EX-12, Terminal t9z, example@example.com\n")
        self.assertEqual(self.names(), [])

    def test_ticket_id_and_name_in_any_file(self):
        self.add("docs/x.md", "seit " + "SLI" + "-123 gebaut\n")
        self.add("tests/deep/y.py", "# von " + "Jo" + "nah entschieden\n")
        self.assertEqual(self.names(), [("docs/x.md", "Ticket-ID des privaten Trackers"),
                                        ("tests/deep/y.py", "Name des Maintainers")])

    def test_each_pattern_is_found(self):
        samples = {
            "Kontaktadresse": "kontakt" + "@example.org",
            "Linear-User des Agents": "Assignee " + "At" + "las",
            "privater Ordner": "~/Claude " + "Area/x",
            "privates Master-Repo": "herdr-" + "master/bin",
            "privates Wissensrepo": "slick-" + "ai",
            "internes Projekt": "use" + "ok" + "ido",
            "Firma": "Vet" + "Stage",
            "interne Terminal-Adresse": "Freigabe von t" + "4g",
            "GitHub-noreply-Adresse": "1+x@users." + "noreply.github.com",
            "privater Home-Pfad": "/Users/" + "jo" + "nah/x",
            "Name des Maintainers": "JO" + "NAH",
            "Nachname des Maintainers": "Jeschk" + "eit",
            "Ticket-ID des privaten Trackers": "sl" + "i-9",
            "internes Projekt (Ticket)": "OK" + "I-12",
            "Linear-Team als Beispielwert": 'TRACKER_' + 'TEAM="Jo' + 'nah"',
            "Linear-Projekt als Beispielwert": "Projekt „Slick" + "fab“",
        }
        # Jedes Muster hat ein Beispiel; ein neues Muster ohne Beispiel fällt hier auf.
        self.assertEqual(set(samples), {name for name, _ in PATTERNS})
        extra = {"internes Projekt": ["cv-" + "agent", "tam-" + "katalog"],
                 "interne Terminal-Adresse": ["t" + "11", "t" + "5y"]}
        for name, texts in extra.items():
            for text in texts:
                with self.subTest(name=name, text=text):
                    self.assertIn(name, [h[2] for h in scan_text("f.md", text + "\n")])
        for name, text in samples.items():
            with self.subTest(name=name):
                hits = scan_text("f.md", text + "\n")
                self.assertIn(name, [h[2] for h in hits])

    def test_ticket_id_lowercase_in_branch_name(self):
        self.add("b.md", "git push origin at" + "las/" + "sli" + "-132\n")
        self.assertIn(("b.md", "Ticket-ID des privaten Trackers"), self.names())

    def test_private_value_in_file_name(self):
        self.add("docs/belege/hand-" + "sli" + "-139.md", "neutral\n")
        self.assertIn(("docs/belege/hand-" + "sli" + "-139.md", "Ticket-ID des privaten Trackers"),
                      self.names())

    def test_license_and_notice_allow_only_the_owner_name(self):
        owner = "Copyright (c) 2026 " + "Jo" + "nah Jeschk" + "eit\n"
        self.add("LICENSE", owner)
        self.add("NOTICE", "siehe LICENSE: " + owner)
        self.assertEqual(self.names(), [])
        self.add("NOTICE", owner + "Ticket " + "SLI" + "-1\n")
        self.assertEqual(self.names(), [("NOTICE", "Ticket-ID des privaten Trackers")])

    def test_root_readmes_are_scanned_like_any_file(self):
        # Die vorübergehende Ausnahme für die README im Wurzelordner ist gestrichen: README.md
        # und README.de.md werden geprüft wie jede andere Datei, ebenso READMEs darunter.
        name = "Gebaut von " + "Jo" + "nah\n"
        for path in ("README.md", "README.de.md", "docs/README.md", "tests/pressure/README.de.md"):
            self.add(path, name)
        self.assertEqual(sorted(self.names()), sorted([
            ("README.md", "Name des Maintainers"), ("README.de.md", "Name des Maintainers"),
            ("docs/README.md", "Name des Maintainers"), ("tests/pressure/README.de.md", "Name des Maintainers")]))

    def test_not_a_git_repo_is_an_error_not_a_clean_result(self):
        plain = tempfile.mkdtemp(prefix="scrub-plain-", dir=os.path.dirname(self.repo))
        self.addCleanup(shutil.rmtree, plain)
        env = dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(plain))
        with unittest.mock.patch.dict(os.environ, env):
            with self.assertRaises(RuntimeError):
                scan(plain)

    def test_owner_name_elsewhere_is_a_hit(self):
        self.add("docs/LICENSE.md", "Copyright (c) 2026 " + "Jo" + "nah\n")
        self.assertEqual(self.names(), [("docs/LICENSE.md", "Name des Maintainers")])


if __name__ == "__main__":
    unittest.main()
