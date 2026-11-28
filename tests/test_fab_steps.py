"""Wegweiser fab kennt genau die vorhandenen Schritte.

Die Prüfung läuft über tests/check_fab.py gegen das echte Repo und gegen
Kopien, in denen ein Schritt umbenannt, gestrichen oder erfunden ist: Jede
dieser Kopien muss rot werden. Dazu: Jeder `/slickfab:<schritt>`-Befehl in
README und Doku existiert.
"""
import os
import re
import shutil
import tempfile
import unittest

import check_fab as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAB = os.path.join("skills", "fab", "SKILL.md")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class RealRepoTest(unittest.TestCase):
    def test_real_repo_passes(self):
        self.assertEqual(cf.check(ROOT), [])

    def test_fab_lists_thirteen_steps(self):
        # Spec: 13 Schritte von fab bis docs-lookup.
        self.assertEqual(sorted(cf.listed_steps(read(os.path.join(ROOT, FAB)))), sorted([
            "fab", "grill", "spec", "prototype", "challenge", "tickets", "implement",
            "review", "debug", "verify", "retro", "handoff", "docs-lookup"]))


def table_rows(text):
    """{Nummer: (Wenn, Dann)} aus der Tabelle in '### 3. Nächsten Schritt bestimmen'."""
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0].isdigit():
            rows[int(cells[0])] = (cells[1], cells[2])
    return rows


class RetroHasEndTest(unittest.TestCase):
    """Re-Review PR #14 (Punkt 5): Nach einer retro empfahl fab wieder retro.
    retro schreibt nichts in den Tracker; das sichtbare Ende ist die Spec auf `Done`."""

    def setUp(self):
        self.text = read(os.path.join(ROOT, FAB))
        self.rows = table_rows(self.text)

    def test_retro_row_needs_open_spec_and_names_the_end(self):
        retro = [n for n, (_, then) in self.rows.items() if "/slickfab:retro" in then]
        self.assertEqual(retro, [13])
        when, then = self.rows[13]
        self.assertIn("Spec issue still open", when)
        self.assertIn("after that the human sets the spec to `Done`", then)

    def test_done_spec_counts_as_finished(self):
        # Nach retro und Spec auf Done darf keine Zeile wieder retro oder verify nennen.
        # Review PR #19, A1: `Canceled` endet ebenso.
        self.assertIn("A spec in `Done` or `Canceled` is finished: it does not count as an "
                      "open spec, even if it is given as argument.", self.text)
        for n in (12, 14, 15):
            with self.subTest(row=n):
                self.assertIn("Spec issue still open", self.rows[n][0])


    def test_usual_path_in_docs_ends_with_spec_done(self):
        # Review PR #17 (Optional, vom Master mitgenommen): Die Doku endete bei `retro`; wer danach
        # arbeitet, setzt die Spec nicht auf Done, und fab empfiehlt wieder retro.
        path = [l for l in read(os.path.join(ROOT, "docs", "betriebsarten.md")).splitlines()
                if l.startswith("Der übliche Weg:")]
        self.assertEqual(len(path), 1)
        self.assertIn("→ `retro` → du setzt die Spec auf `Done`.", path[0])


class NotBuildVerdictTest(unittest.TestCase):
    """Review PR #17, O2: Eine Spec mit challenge-Urteil `nicht bauen` landete
    über „Spec ohne Tickets, `challenge`-Kommentar da“ bei tickets. Die erste zutreffende
    Zeile gilt; für dieses Urteil darf sie tickets nicht nennen."""

    def setUp(self):
        self.text = read(os.path.join(ROOT, FAB))
        self.rows = table_rows(self.text)

    def first_row(self, facts):
        """Erste Zeile, deren Wenn alle genannten Tatsachen enthält."""
        for n in sorted(self.rows):
            if all(f in self.rows[n][0] for f in facts):
                return n
        return None

    def test_not_build_verdict_has_own_row_without_tickets(self):
        n = self.first_row(["Spec without tickets", "`nicht bauen`", "no comment"])
        self.assertIsNotNone(n, "keine Zeile für das Urteil `nicht bauen`")
        when, then = self.rows[n]
        self.assertNotIn("/slickfab:tickets", then)
        self.assertTrue(then.startswith("no step: the human decides"), then)
        # Sie steht vor der Zeile, die tickets empfiehlt, sonst gälte die zuerst.
        tickets = [k for k, (_, t) in self.rows.items() if t.startswith("`/slickfab:tickets")
                   and "challenge" in self.rows[k][0]]
        self.assertTrue(tickets and all(n < k for k in tickets), (n, tickets))

    def test_tickets_row_names_the_verdicts_it_takes(self):
        rows = [w for w, t in self.rows.values() if t.startswith("`/slickfab:tickets")
                and "`challenge` comment present" in w]
        self.assertEqual(rows, ["Spec without tickets, `challenge` comment present, "
                                "last verdict `bauen` or `kleiner bauen`"])

    def test_canceled_spec_counts_as_finished(self):
        # Review PR #19, A1a: Nach Zeile 19 setzt der Mensch die Spec auf `Canceled`; als
        # Argument genannt, galt sie weiter als offen, und Zeile 19 kam wieder.
        self.assertIn("A spec in `Done` or `Canceled` is finished: it does not count as an "
                      "open spec, even if it is given as argument.", self.text)

    def test_changed_spec_after_not_build_goes_back_to_challenge(self):
        # Review PR #19, A1b: Nach „ändern“ (spec) blieb das letzte Urteil `nicht bauen`, und
        # fab empfahl wieder „ändern oder `Canceled`“ statt einer neuen Prüfung.
        n = self.first_row(["`nicht bauen`", "after it a comment"])
        self.assertIsNotNone(n)
        self.assertTrue(self.rows[n][1].startswith("`/slickfab:challenge <spec issue>`"), self.rows[n])
        human = self.first_row(["Spec without tickets", "`nicht bauen`", "no comment"])
        self.assertIsNotNone(human)
        self.assertLess(n, human)

    def test_change_is_detected_by_the_spec_comment(self):
        # Review PR #19, N1: „Verlauf des Issues“ zeigt Linear nicht, und updatedAt steigt bei
        # jedem Kommentar. Erkennbar ist nur der Änderungskommentar, den spec beim Überarbeiten
        # schreibt; seine erste Zeile kommt aus spec, nicht aus diesem Test.
        spec = read(os.path.join(ROOT, "skills", "spec", "SKILL.md"))
        head = re.search(r"a comment whose first line is exactly `([^`]+)`", spec)
        self.assertIsNotNone(head, "spec schreibt den Änderungskommentar nicht erkennbar")
        mark = "comment `%s`" % head.group(1)
        changed = self.first_row(["`nicht bauen`", "after it a " + mark])
        unchanged = self.first_row(["`nicht bauen`", "no " + mark + " after it"])
        self.assertIsNotNone(changed)
        self.assertIsNotNone(unchanged)
        self.assertIn("later than the last `challenge` comment", self.rows[changed][0])
        self.assertLess(changed, unchanged)
        self.assertNotIn("issue history", self.text)
        # fab liest diese Kommentare auch (Schritt 2), sonst sähe es sie nicht.
        tracker = self.text.split("<!-- regel:tracker-lesen -->")[1].split("<!-- /regel:tracker-lesen -->")[0]
        self.assertIn("`%s`" % head.group(1), tracker)

    def test_result_counts_the_row_as_human_decision(self):
        n = self.first_row(["Spec without tickets", "`nicht bauen`", "no comment"])
        result = self.text.split("<!-- regel:ergebnis -->")[1]
        decisions = re.search(r"decision by the human \(rows ([0-9, ]+)\)", result).group(1)
        self.assertIn(str(n), [d.strip() for d in decisions.split(",")])
        # Wie Zeile 17 (Mensch entscheidet, ob die Spec endet): Status NEEDS_CONTEXT.
        needs = re.search(r"`NEEDS_CONTEXT` if [^;]*?or row ([0-9, ]+?) or (\d+) applies", result)
        self.assertIn(str(n), [d.strip() for d in needs.group(1).split(",")] + [needs.group(2)])


class RowReferencesTest(unittest.TestCase):
    """Review PR #19, R3: Die Zeilennummern im Fließtext von fab waren nur durch die Referenz
    geschützt; `rules_golden.py --update` hätte einen falschen Verweis übernommen. Jede Nummer
    wird hier über den Inhalt der Zeile aufgelöst, nicht über eine feste Zahl."""

    def setUp(self):
        self.text = read(os.path.join(ROOT, FAB))
        self.rows = table_rows(self.text)

    def numbers(self, pattern):
        m = re.search(pattern, self.text)
        self.assertIsNotNone(m, pattern)
        return sorted(int(x) for x in re.findall(r"\d+", " ".join(g for g in m.groups() if g)))

    def where(self, test):
        return sorted(n for n, (when, then) in self.rows.items() if test(when, then))

    def test_pr_rows_without_tracker(self):
        first, last = self.numbers(r"for rows (\d+) to (\d+) if its title")
        self.assertEqual(list(range(first, last + 1)), self.where(lambda w, t: w.startswith("Open PR")))

    def test_grill_row_without_tracker(self):
        self.assertEqual(self.numbers(r"If you reach row (\d+) without the tracker"),
                         self.where(lambda w, t: t.startswith("`/slickfab:grill")))

    def test_unclassified_row(self):
        self.assertEqual(self.numbers(r"for row (\d+), that line states what you cannot place"),
                         self.where(lambda w, t: "no row fits" in w))

    def test_needs_context_rows(self):
        self.assertEqual(self.numbers(r"or row ([\d, ]+?) or (\d+) applies\."),
                         self.where(lambda w, t: "status `NEEDS_CONTEXT`" in t))

    def test_human_decision_rows(self):
        self.assertEqual(self.numbers(r"decision by the human \(rows ([\d, ]+)\)"),
                         self.where(lambda w, t: t.startswith("no step")))


# README.md ist englisch, README.de.md deutsch. Je README die Überschrift der
# Schritt-Tabelle; je Datei mit Autopilot-Abschnitt die Sätze „noch nicht live“ und
# „noch nicht nutzbar“ in ihrer Sprache.
READMES = (("README.md", "## Steps"), ("README.de.md", "## Schritte"))
AUTOPILOT_DOCS = (("README.md", "not yet live", "not yet usable"),
                  ("README.de.md", "noch nicht live", "noch nicht nutzbar"),
                  (os.path.join("docs", "betriebsarten.md"), "noch nicht live", "noch nicht nutzbar"))
# Autopilot-Abschnitt ohne ausführbaren Dispatcher, so wie er vor dem Dispatcher gültig war.
NOT_USABLE = {"README.md": "- **Autopilot:** not yet usable.",
              "README.de.md": "- **Autopilot:** noch nicht nutzbar.",
              os.path.join("docs", "betriebsarten.md"): "**Noch nicht nutzbar.**"}


def cap(phrase):
    return phrase[0].upper() + phrase[1:]


class BrokenCopyTest(unittest.TestCase):
    """Kopie des Repos (nur skills/, READMEs, docs/) mit einer absichtlichen Störung."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fab-check-")
        for part in ("skills", "docs", "agents", "runtime"):
            shutil.copytree(os.path.join(ROOT, part), os.path.join(self.tmp, part))
        for rel, _ in READMES:
            shutil.copy(os.path.join(ROOT, rel), self.tmp)
        self.assertEqual(cf.check(self.tmp), [], "Kopie ohne Störung muss grün sein")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def fab_text(self):
        return read(os.path.join(self.tmp, FAB))

    def set_fab(self, text):
        write(os.path.join(self.tmp, FAB), text)

    def test_renamed_step_is_red(self):
        os.rename(os.path.join(self.tmp, "skills", "verify"), os.path.join(self.tmp, "skills", "pruefen"))
        fails = cf.check(self.tmp)
        self.assertTrue(any("pruefen" in f and "fehlt im Wegweiser" in f for f in fails), fails)
        self.assertTrue(any("verify" in f and "existiert nicht" in f for f in fails), fails)

    def test_new_step_missing_in_fab_is_red(self):
        os.makedirs(os.path.join(self.tmp, "skills", "deploy"))
        write(os.path.join(self.tmp, "skills", "deploy", "SKILL.md"), "---\nname: deploy\n---\n")
        self.assertTrue(any("deploy" in f and "fehlt im Wegweiser" in f for f in cf.check(self.tmp)))

    def test_row_removed_from_table_is_red(self):
        lines = [l for l in self.fab_text().split("\n") if not l.startswith("| `retro` |")]
        self.set_fab("\n".join(lines))
        self.assertTrue(any("retro" in f and "fehlt im Wegweiser" in f for f in cf.check(self.tmp)))

    def test_invented_step_in_table_is_red(self):
        text = self.fab_text().replace("| `retro` |", "| `release` | erfunden |\n| `retro` |", 1)
        self.set_fab(text)
        self.assertTrue(any("release" in f and "existiert nicht" in f for f in cf.check(self.tmp)))

    def test_unknown_command_in_fab_text_is_red(self):
        # Auch außerhalb der Tabelle: jeder genannte Befehl muss ein Schritt sein.
        self.set_fab(self.fab_text() + "\n<!-- regel:x -->\n`/slickfab:ship`\n<!-- /regel:x -->\n")
        self.assertTrue(any("/slickfab:ship" in f for f in cf.check(self.tmp)))

    def test_missing_table_is_red(self):
        self.set_fab(self.fab_text().replace("<!-- regel:schritte -->", "<!-- regel:andere -->")
                     .replace("<!-- /regel:schritte -->", "<!-- /regel:andere -->"))
        self.assertTrue(any("Schritt-Tabelle" in f for f in cf.check(self.tmp)))

    def test_missing_fab_is_red(self):
        shutil.rmtree(os.path.join(self.tmp, "skills", "fab"))
        self.assertTrue(any("skills/fab/SKILL.md" in f for f in cf.check(self.tmp)))

    def test_unknown_command_in_readme_is_red(self):
        for rel, _ in READMES:
            with self.subTest(file=rel):
                path = os.path.join(self.tmp, rel)
                orig = read(path)
                write(path, orig + "\n`/slickfab:start`\n")
                self.assertTrue(any(f.startswith(rel + ":") and "/slickfab:start" in f
                                    for f in cf.check(self.tmp)))
                write(path, orig)

    def test_missing_readme_is_red(self):
        # Beide READMEs gehören dazu; fehlt eine, ist das ein Befund.
        for rel, _ in READMES:
            with self.subTest(file=rel):
                path = os.path.join(self.tmp, rel)
                orig = read(path)
                os.remove(path)
                self.assertIn(rel + ": fehlt", cf.check(self.tmp))
                write(path, orig)

    def test_table_heading_follows_the_language(self):
        # Die englische README hat „## Steps“, die deutsche „## Schritte“; die
        # Überschrift der anderen Sprache zählt nicht als Schritt-Tabelle.
        swap = {"## Steps": "## Schritte", "## Schritte": "## Steps"}
        for rel, heading in READMES:
            with self.subTest(file=rel):
                path = os.path.join(self.tmp, rel)
                orig = read(path)
                self.assertIn(heading + "\n", orig)
                write(path, orig.replace(heading + "\n", swap[heading] + "\n", 1))
                self.assertTrue(any(f.startswith(rel + ":") and heading in f for f in cf.check(self.tmp)))
                write(path, orig)

    # Review PR #14, R1: Rollenaufrufe und die Schritt-Tabelle der README waren ungeprüft.
    def doc(self, rel):
        return os.path.join(self.tmp, rel)

    def test_renamed_role_in_docs_is_red(self):
        path = self.doc(os.path.join("docs", "betriebsarten.md"))
        write(path, read(path).replace("`slickfab:reviewer`", "`slickfab:pruefer`", 1))
        self.assertTrue(any("slickfab:pruefer" in f for f in cf.check(self.tmp)))

    def readme_cases(self, change, expect):
        """Je README: Störung `change(text)` schreiben, `expect(fails, rel)` prüfen, zurücksetzen."""
        for rel, _ in READMES:
            with self.subTest(file=rel):
                path = self.doc(rel)
                orig = read(path)
                bad = change(orig)
                self.assertNotEqual(bad, orig)
                write(path, bad)
                expect(cf.check(self.tmp), rel)
                write(path, orig)

    def test_invented_role_in_readme_is_red(self):
        self.readme_cases(lambda t: t + "\nStarte den Agent slickfab:builder.\n",
                          lambda fails, rel: self.assertTrue(any(
                              f.startswith(rel + ":") and "slickfab:builder" in f for f in fails), fails))

    def test_known_labels_and_roles_are_green(self):
        self.readme_cases(lambda t: t + "\n`slickfab:needs-human`, `slickfab:rework`, slickfab:planner\n",
                          lambda fails, rel: self.assertEqual(fails, []))

    def test_invented_row_in_readme_table_is_red(self):
        self.readme_cases(lambda t: t.replace("| `retro` |", "| `ship` | erfunden |\n| `retro` |", 1),
                          lambda fails, rel: self.assertTrue(any(
                              f.startswith(rel + ":") and "ship" in f for f in fails), fails))

    def test_removed_row_in_readme_table_is_red(self):
        self.readme_cases(lambda t: "\n".join(l for l in t.split("\n") if not l.startswith("| `debug` |")),
                          lambda fails, rel: self.assertTrue(any(
                              f.startswith(rel + ":") and "debug" in f for f in fails), fails))

    def test_missing_runtime_tool_in_docs_is_red(self):
        # Review PR #14, A2: Die Doku nennt nur Werkzeuge, die es unter runtime/herdr gibt.
        path = self.doc(os.path.join("docs", "betriebsarten.md"))
        write(path, read(path) + "\n`runtime/herdr/slickfab-tick`\n")
        self.assertTrue(any("runtime/herdr/slickfab-tick" in f for f in cf.check(self.tmp)))

    def test_autopilot_promised_without_dispatcher_is_red(self):
        # Review PR #14, A2: Ohne ausführbaren Dispatcher sagen READMEs und Doku „noch nicht
        # nutzbar“, die englische README „not yet usable“.
        os.chmod(os.path.join(self.tmp, "runtime", "herdr", "slickfab-dispatch"), 0o644)  # nicht ausführbar
        fails = cf.check(self.tmp)
        for rel, _, usable in AUTOPILOT_DOCS:
            self.assertTrue(any(f.startswith(rel + ":") and usable in f for f in fails), (rel, fails))
        for rel, live, usable in AUTOPILOT_DOCS:
            path = self.doc(rel)
            write(path, read(path).replace(live, usable).replace(cap(live), cap(usable)))
        # Der Hinweis „noch nicht nutzbar“ reicht jetzt; übrig bleibt nur, dass der
        # Abschnitt ohne ausführbaren Dispatcher das Werkzeug nicht nennen darf.
        rest = cf.check(self.tmp)
        self.assertFalse(any(usable in f for _, _, usable in AUTOPILOT_DOCS for f in rest), rest)
        self.assertTrue(all("nennt slickfab-dispatch" in f for f in rest), rest)
        for rel, _, _ in AUTOPILOT_DOCS:
            self.assertTrue(any(f.startswith(rel + ":") for f in rest), (rel, rest))

    def test_autopilot_with_dispatcher_says_not_live_yet(self):
        # Der Dispatcher ist ausführbar, aber nicht eingeschaltet (Pilot steht aus).
        for rel, live, usable in AUTOPILOT_DOCS:
            path = self.doc(rel)
            orig = read(path)
            for bad in (orig.replace(live, "läuft").replace(cap(live), "Läuft"),
                        orig.replace(live, live + ", " + usable).replace(cap(live), cap(live) + ", " + usable)):
                with self.subTest(file=rel, text=bad[:0]):
                    self.assertNotEqual(bad, orig)
                    write(path, bad)
                    self.assertTrue(any(f.startswith(rel + ":") and live in f for f in cf.check(self.tmp)))
            write(path, orig)

    def non_executable_dispatcher(self):
        """Stand ohne ausführbaren Dispatcher nachbauen (inzwischen gibt es ihn): Datei ohne
        Ausführrecht, Autopilot-Abschnitte so, wie sie vor dem Dispatcher gültig waren."""
        tool = os.path.join(self.tmp, "runtime", "herdr", "slickfab-dispatch")
        os.chmod(tool, 0o644)
        for rel, _ in READMES:
            path = self.doc(rel)
            write(path, re.sub(r"^- \*\*Autopilot:\*\*[^\n]*", NOT_USABLE[rel] + " `docs/betriebsarten.md`.",
                               read(path), count=1, flags=re.M))
        path = self.doc(os.path.join("docs", "betriebsarten.md"))
        write(path, re.sub(r"^## Autopilot\n.*?(?=^## )", "## Autopilot\n\n**Noch nicht nutzbar.** Bis dahin "
                           "fährst du slickfab in den Modi Hand oder Assistiert.\n\n", read(path),
                           count=1, flags=re.S | re.M))
        return tool

    def test_non_executable_dispatcher_still_needs_autopilot_note(self):
        # Re-Review PR #14, Punkt 6: Eine Datei ohne Ausführrecht ist kein Dispatcher.
        self.non_executable_dispatcher()
        self.assertEqual(cf.check(self.tmp), [])
        for rel, _, usable in AUTOPILOT_DOCS[:2]:
            with self.subTest(file=rel):
                path = self.doc(rel)
                orig = read(path)
                write(path, orig.replace(NOT_USABLE[rel], "- **Autopilot:** läuft.", 1))
                self.assertTrue(any(f.startswith(rel + ":") and usable in f for f in cf.check(self.tmp)))
                write(path, orig)

    def test_autopilot_note_must_lead_the_section(self):
        # Punkt 6: Der Satz allein reicht nicht; er steht vorn, nicht irgendwo im Abschnitt.
        self.non_executable_dispatcher()
        for rel, old, new, usable in (
                ("README.md", NOT_USABLE["README.md"],
                 "- **Autopilot:** running already, long not yet usable.", "not yet usable"),
                ("README.de.md", NOT_USABLE["README.de.md"],
                 "- **Autopilot:** läuft schon, war lange noch nicht nutzbar.", "noch nicht nutzbar"),
                (os.path.join("docs", "betriebsarten.md"), "**Noch nicht nutzbar.**",
                 "**Nutzbar.** Früher hieß es hier: noch nicht nutzbar.", "noch nicht nutzbar")):
            with self.subTest(file=rel):
                path = self.doc(rel)
                orig = read(path)
                self.assertIn(old, orig)
                write(path, orig.replace(old, new, 1))
                self.assertTrue(any(f.startswith(rel + ":") and usable in f for f in cf.check(self.tmp)))
                write(path, orig)

    def test_autopilot_section_without_dispatcher_gives_no_start_command(self):
        # Punkt 6: „noch nicht nutzbar“ und daneben eine Startanleitung widersprechen sich.
        self.non_executable_dispatcher()
        for rel, anchor in NOT_USABLE.items():
            with self.subTest(file=rel):
                path = self.doc(rel)
                orig = read(path)
                for start in ("`runtime/herdr/slickfab-dispatch tick`",
                              "`${CLAUDE_PLUGIN_ROOT}/runtime/herdr/slickfab-dispatch tick`",
                              "`./slickfab-dispatch`", "herdr/slickfab-dispatch."):
                    with self.subTest(start=start):
                        write(path, orig.replace(anchor, anchor + " Start: %s" % start, 1))
                        self.assertTrue(any(f.startswith(rel + ":") and "slickfab-dispatch" in f
                                            for f in cf.check(self.tmp)))
                write(path, orig)

    def test_unknown_command_in_docs_is_red(self):
        path = os.path.join(self.tmp, "docs", "betriebsarten.md")
        write(path, read(path) + "\n`/slickfab:start`\n")
        self.assertTrue(any("betriebsarten.md" in f and "/slickfab:start" in f for f in cf.check(self.tmp)))


if __name__ == "__main__":
    unittest.main()
