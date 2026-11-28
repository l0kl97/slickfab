"""Nutzer-Doku englisch, Entwicklungsprotokoll deutsch.

Die Nutzer-Doku (docs/*.md ohne Unterordner) ist englisch und hat englische
Dateinamen. Kein Verweis im Repo nennt noch die alten deutschen Dateinamen.
Die Schlüssel der Projekt- und der Factory-Konfiguration stehen in der
englischen Doku; verglichen wird mit dem Code, der sie liest
(`runtime/herdr/slickfab-dispatch`, `load_config`; `runtime/herdr/slickfab-worktree`,
`read_checks`) und mit der Prüfung der Projektkonfiguration (`test_repo_config`).
Die Feature-Dossiers unter docs/features/ bleiben deutsch; beide READMEs sagen das.
"""
import ast
import glob
import os
import re
import unittest

import test_repo_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_CONFIG = os.path.join("docs", "project-config.md")
OPERATING_MODES = os.path.join("docs", "operating-modes.md")
AUTOPILOT = os.path.join("docs", "autopilot.md")
# Alte Namen zusammengesetzt, damit dieser Test sich nicht selbst findet.
OLD_NAMES = ("docs/" + "projektkonfiguration.md", "docs/" + "betriebsarten.md")
# Datierte Historie in den Dossiers ist Protokoll: Sie nennt den Namen, den die Datei damals hatte.
HISTORY_LINE = re.compile(r"^- \d{4}-\d{2}-\d{2}")
# Häufige deutsche Funktionswörter; in englischer Doku kommt keines davon als Wort vor.
GERMAN = re.compile(r"\b(und|oder|nicht|der|das|ist|wird|mit|für|eine|auch|wenn|bei)\b")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
CODE = re.compile(r"`[^`\n]*`")
SKIP_DIRS = {".git"}


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def text_files():
    """Alle Textdateien des Repos (relativ), ohne .git und ohne diesen Test."""
    me = os.path.relpath(os.path.abspath(__file__), ROOT)
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            rel = os.path.relpath(os.path.join(base, name), ROOT)
            if rel == me:
                continue
            try:
                with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                    yield rel, f.read()
            except (UnicodeDecodeError, OSError):
                continue


def stale_references(files):
    """[(datei, zeile, alter name)] für jeden Verweis auf einen alten Dateinamen."""
    out = []
    for rel, text in files:
        dossier = rel.startswith(os.path.join("docs", "features") + os.sep)
        for no, line in enumerate(text.splitlines(), 1):
            if dossier and HISTORY_LINE.match(line):
                continue
            for old in OLD_NAMES:
                if old in line:
                    out.append((rel, no, old))
    return out


def german_words(text):
    """Deutsche Funktionswörter außerhalb von Code (Blöcke und `…`)."""
    prose = CODE.sub("", FENCE.sub("", text))
    return sorted(set(GERMAN.findall(prose)))


def factory_keys():
    """Schlüssel, die load_config in slickfab-dispatch liest: (oben, je Projekt)."""
    tree = ast.parse(read(os.path.join("runtime", "herdr", "slickfab-dispatch")))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "load_config")
    top, project = set(), set()
    target = {"cfg": top, "p": project}

    def const(node):
        return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

    for node in ast.walk(fn):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("get", "setdefault") and isinstance(node.func.value, ast.Name)
                and node.func.value.id in target and node.args and const(node.args[0])):
            target[node.func.value.id].add(const(node.args[0]))
        elif (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
              and node.value.id in target):
            key = const(node.slice) or const(getattr(node.slice, "value", None))
            if key:
                target[node.value.id].add(key)
        elif (isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.In)
              and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id in target
              and const(node.left)):
            target[node.comparators[0].id].add(const(node.left))
        elif isinstance(node, ast.For) and isinstance(node.iter, ast.Tuple):
            # for key in ("assignee", …): cfg.get(key) — Schlüssel der obersten Ebene
            names = [const(e) for e in node.iter.elts]
            if all(names):
                top.update(names)
    return top, project


def worktree_check_keys():
    """Schlüssel, die slickfab-worktree aus .slickrails/config.sh liest."""
    src = read(os.path.join("runtime", "herdr", "slickfab-worktree"))
    m = re.search(r'\^\\s\*\(((?:CHECK_[A-Z]+\|?)+)\)=', src)
    return tuple(m.group(1).split("|")) if m else ()


class StaleReferenceTest(unittest.TestCase):
    """Kein Verweis zeigt auf eine deutsche Nutzer-Doku."""

    def test_new_user_docs_exist(self):
        for rel in (PROJECT_CONFIG, OPERATING_MODES, AUTOPILOT):
            with self.subTest(file=rel):
                self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)))

    def test_old_file_names_are_gone(self):
        for old in OLD_NAMES:
            with self.subTest(file=old):
                self.assertFalse(os.path.exists(os.path.join(ROOT, old)))

    def test_no_reference_to_an_old_file_name(self):
        self.assertEqual(stale_references(text_files()), [])

    def test_check_finds_a_planted_old_reference(self):
        # Gegenprobe: Der Scanner findet einen alten Namen, aber nicht in datierter Dossier-Historie.
        files = [("README.md", "see `%s`\n" % OLD_NAMES[0]),
                 (os.path.join("docs", "features", "x.md"), "- 2026-11-01: `%s` war …\n" % OLD_NAMES[1]),
                 (os.path.join("docs", "features", "y.md"), "Wo es lebt: `%s`\n" % OLD_NAMES[1])]
        self.assertEqual(stale_references(files),
                         [("README.md", 1, OLD_NAMES[0]),
                          (os.path.join("docs", "features", "y.md"), 1, OLD_NAMES[1])])

    def test_user_docs_are_english(self):
        docs = sorted(glob.glob(os.path.join(ROOT, "docs", "*.md")))
        self.assertTrue(docs)
        for path in docs:
            rel = os.path.relpath(path, ROOT)
            with self.subTest(file=rel):
                self.assertEqual(german_words(read(rel)), [])

    def test_language_check_sees_german_prose_but_not_code(self):
        self.assertEqual(german_words("The steps und the roles."), ["und"])
        self.assertEqual(german_words("Use `oder` here.\n```\nwenn das\n```\n"), [])

    def test_readmes_point_to_the_user_doc_for_the_factory_configuration(self):
        for rel in ("README.md", "README.de.md", OPERATING_MODES):
            with self.subTest(file=rel):
                text = read(rel)
                self.assertIn("`docs/autopilot.md`", text)
                self.assertNotIn("`docs/features/slickfab-dispatch.md`", text)

    def test_dispatch_dossier_points_to_the_user_doc(self):
        self.assertIn("`docs/autopilot.md`", read(os.path.join("docs", "features", "slickfab-dispatch.md")))


class KeysTest(unittest.TestCase):
    """Jeder Schlüssel aus dem Code steht in der englischen Doku."""

    def test_factory_keys_are_read_from_the_code(self):
        # Gegenprobe des Lesers: Er findet die bekannten Schlüssel beider Ebenen.
        top, project = factory_keys()
        self.assertTrue({"assignee", "projects", "timeout", "linear_api"} <= top, top)
        self.assertTrue({"enabled", "github_ci", "space", "max_parallel"} <= project, project)

    def test_every_factory_key_is_documented(self):
        doc = read(AUTOPILOT)
        top, project = factory_keys()
        for key in sorted(top | project):
            with self.subTest(key=key):
                self.assertIn("`%s`" % key, doc)

    def test_every_project_config_key_is_documented(self):
        doc = read(PROJECT_CONFIG)
        for key in test_repo_config.KNOWN:
            with self.subTest(key=key):
                self.assertIn("`%s=`" % key, doc)

    def test_runtime_check_keys_are_named(self):
        # slickfab-worktree (Baseline, Post-Merge-Prüfung) liest nur diese Schlüssel aus
        # .slickrails/config.sh; die Doku nennt sie ausdrücklich, außerhalb der Vertragsblöcke.
        keys = worktree_check_keys()
        self.assertEqual(keys, ("CHECK_TYPECHECK", "CHECK_TEST"))
        outside = re.sub(r"<!-- vertrag:([a-z-]+) -->.*?<!-- /vertrag:\1 -->", "",
                         read(PROJECT_CONFIG), flags=re.S)
        line = [l for l in outside.splitlines() if "slickfab-worktree" in l]
        self.assertTrue(line, "kein Satz zu slickfab-worktree")
        for key in keys:
            with self.subTest(key=key):
                self.assertTrue(any("`%s`" % key in l for l in line), line)


class ReadmeLanguageNoteTest(unittest.TestCase):
    """Beide READMEs: Nur noch das Entwicklungsprotokoll ist deutsch."""

    CASES = (("README.md", ("currently still in German",), "Only the development record"),
             ("README.de.md", ("derzeit noch deutsch",), "Nur noch das Entwicklungsprotokoll"))

    def test_note_says_only_the_development_record_is_german(self):
        for rel, old, new in self.CASES:
            with self.subTest(file=rel):
                text = read(rel)
                for phrase in old:
                    self.assertNotIn(phrase, text)
                note = [l for l in text.splitlines() if new in l]
                self.assertEqual(len(note), 1, note)
                self.assertIn("`docs/features/`", note[0])


if __name__ == "__main__":
    unittest.main()
