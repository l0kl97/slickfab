"""Verträge der Planungs-Schritte an ihrer öffentlichen Schnittstelle:
den Texten, die ein Agent liest, wenn er `/slickfab:<schritt>` ausführt.

Erwartete Schreibweisen stammen aus der Spec bzw. dem Ticket,
nicht aus den Dateien selbst. Ob ein Agent sich daran hält, prüft das nicht
(dafür Hand-Durchlauf und später Pressure-Szenarien); es fängt aber, wenn ein
Vertragsbegriff verschwindet oder anders geschrieben wird.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def section(text, name):
    """Inhalt unter '## <name>' bis zur nächsten '## '-Überschrift; Überschriften
    in Codeblöcken (``` oder ~~~) zählen nicht, sie gehören zum Inhalt."""
    out, inside, fence = [], False, None
    for line in text.splitlines():
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~"):
            fence = marker if fence is None else (None if marker == fence else fence)
        elif fence is None and line.startswith("## "):
            inside = line[3:].strip() == name
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


def subsection(text, prefix):
    """Inhalt unter der '### <prefix>…'-Überschrift bis zur nächsten '##'/'###'."""
    out, inside, fence = [], False, None
    for line in text.splitlines():
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~"):
            fence = marker if fence is None else (None if marker == fence else fence)
        elif fence is None and line.startswith("#"):
            if line.startswith("### "):
                inside = line[4:].startswith(prefix)
                continue
            if line.startswith("## "):
                inside = False
        if inside:
            out.append(line)
    return "\n".join(out)


class TrackerContractTest(unittest.TestCase):
    """Schreibweisen exakt wie in der Spec, Abschnitt Entscheidungen."""

    def setUp(self):
        self.text = read("tracker/linear.md")

    def test_labels(self):
        for label in ("slickfab:rework", "slickfab:ready", "slickfab:needs-human",
                      "slickfab:replan", "door:one-way"):
            self.assertIn("`%s`" % label, self.text)

    def test_linear_name_of_group_labels(self):
        # Review PR #2, A3: in Linear heißt das Label nur `rework` usw., in der Gruppe `slickfab`.
        self.assertIn("When searching and setting via the Linear tools, the label is called `rework`, "
                      "`ready`, `needs-human` or `replan` in the group `slickfab`",
                      section(self.text, "Labels"))

    def test_size_labels(self):
        for size in ("`S`", "`M`", "`L`"):
            self.assertIn(size, self.text)

    def test_markers(self):
        self.assertIn("SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT", self.text)
        self.assertIn("SLICKFAB-VERDICT: MERGE|REWORK|REPLAN", self.text)

    def test_marker_position_is_unambiguous(self):
        # Review PR #2, A2: STATUS ist immer die letzte Zeile, VERDICT (nur Reviewer) die vorletzte.
        marker = section(self.text, "Marker")
        self.assertIn("- Last line, always: `SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`", marker)
        self.assertIn("- Second-to-last line, only for the reviewer: `SLICKFAB-VERDICT: MERGE|REWORK|REPLAN`", marker)
        self.assertNotIn("exactly one marker line", marker)
        # STATUS beschreibt den Review-Lauf; ein vollständiges REWORK-Review ist DONE.
        self.assertRegex(marker, r"SLICKFAB-VERDICT: REWORK\nSLICKFAB-STATUS: DONE\n```",
                         "Reviewer-Beispiel: VERDICT direkt über STATUS, STATUS zuletzt")

    def test_ruling_format(self):
        self.assertIn("Ruling: what — why — cost if wrong", self.text)

    def test_status_sequence(self):
        self.assertRegex(self.text, r"Backlog.*Todo.*In Progress.*In Review.*Done")


class ProjectConfigTest(unittest.TestCase):
    """Projektkonfiguration je Repo: Tracker, Team, Projekt, Prüfbefehle."""

    def setUp(self):
        self.text = read("docs/projektkonfiguration.md")

    def test_names_file_and_keys(self):
        self.assertIn("`.slickfab/config`", self.text)
        for key in ("TRACKER", "TRACKER_TEAM", "TRACKER_PROJECT", "CHECK_TEST"):
            self.assertIn(key + "=", self.text)

    def test_checks_come_from_slickrails_when_present(self):
        self.assertIn("`.slickrails/config.sh`", self.text)

    def test_missing_config_writes_no_replacement_file(self):
        missing = section(self.text, "Wenn die Konfiguration fehlt")
        self.assertIn("no plan", missing)
        self.assertRegex(missing, r"plan, ledger or state file")


class StandaloneStepMixin:
    """AC: läuft allein per Slash-Befehl, prüft seine Voraussetzung, nennt den nächsten Schritt."""
    step = None
    # Überschrift von Schritt 1 in der Sprache des Schritts. test_build_steps und test_check_steps
    # nutzen diesen Mixin für Schritte, die noch deutsch sind; die englischen setzen ihn selbst.
    precondition = "### 1. Voraussetzung prüfen"

    def setUp(self):
        self.text = read("skills/%s/SKILL.md" % self.step)

    def test_checks_its_precondition(self):
        self.assertIn(self.precondition, section(self.text, "Ablauf"))

    def test_names_next_step(self):
        self.assertRegex(section(self.text, "Nächster Schritt"), r"`/slickfab:[a-z-]+")

    def test_result_ends_with_next_step(self):
        self.assertIn("Nächster Schritt: `/slickfab:", section(self.text, "Ergebnis"))

    def test_carries_contract_inline(self):
        # Inhalt und Gleichheit mit der Quelle prüft tests/test_contract_blocks.py.
        self.assertIn("<!-- vertrag:marker -->", section(self.text, "Vertrag"))

    def test_does_not_depend_on_herdr(self):
        self.assertNotIn("hc send", self.text)


class SpecStepTest(StandaloneStepMixin, unittest.TestCase):
    step = "spec"
    precondition = "### 1. Check the precondition"

    # Überschriften des Spec-Issues bleiben wörtlich: verify, implement und der Dispatcher
    # lesen sie unter diesen Namen, auch in schon angelegten Issues.
    SECTIONS = ("Bitte (wörtlich)", "Problem", "Lösung", "User Stories", "Entscheidungen",
                "Muss wahr sein", "Kritische Verbindungen", "Grenzen", "Global Constraints",
                "Review-Fokus", "Teststellen", "Nicht im Umfang")

    def test_template_has_all_sections(self):
        for name in self.SECTIONS:
            self.assertIn("## " + name, self.text, name)

    def test_boundaries_have_three_tiers(self):
        for tier in ("**Immer:**", "**Erst fragen:**", "**Nie:**"):
            self.assertIn(tier, self.text)

    def test_seams_name_what_they_catch_and_miss(self):
        self.assertRegex(self.text, r"fängt.*verpasst")

    def test_open_decision_goes_back_to_grill(self):
        self.assertIn("`/slickfab:grill`", section(self.text, "Ablauf"))


class PrototypeStepTest(StandaloneStepMixin, unittest.TestCase):
    step = "prototype"
    precondition = "### 1. Check the precondition"

    def test_two_shapes_ui_variants_and_logic_script(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("?variant=", flow)
        self.assertIn("throwaway script", flow)

    def test_always_on_throwaway_branch(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("prototype/", flow)
        self.assertIn("throwaway branch", flow)


class PrototypeEndingsTest(unittest.TestCase):
    """Hand-Durchlauf (UI und Logik, je frische Session per `claude -p`): Beide Läufe
    endeten in Schritt 5 beim Warten auf das Urteil, ohne „Nächster Schritt“ und ohne Marker,
    und der Prototyp lag uncommittet auf dem Wegwerf-Branch. Auch die Vorlage nach dem Urteil
    hatte keine STATUS-Zeile."""

    def setUp(self):
        self.text = read("skills/prototype/SKILL.md")
        result = section(self.text, "Ergebnis")
        self.templates = {}
        for block in re.findall(r"^```\n(.*?)^```", result, re.S | re.M):
            self.templates[block.splitlines()[0][len("## "):]] = block

    def test_templates_for_waiting_and_after_verdict(self):
        self.assertEqual(set(self.templates),
                         {"Ergebnis prototype", "Ergebnis prototype (awaiting verdict)",
                          "Ergebnis prototype (branch question)", "Ergebnis prototype (halt)"})

    def test_every_template_ends_with_next_step_and_status(self):
        expected = {"Ergebnis prototype": ("DONE",),
                    "Ergebnis prototype (awaiting verdict)": ("NEEDS_CONTEXT",),
                    "Ergebnis prototype (branch question)": ("NEEDS_CONTEXT",),
                    "Ergebnis prototype (halt)": ("NEEDS_CONTEXT", "BLOCKED")}
        for name, block in self.templates.items():
            with self.subTest(template=name):
                lines = block.strip().splitlines()
                self.assertTrue(lines[-1].startswith("SLICKFAB-STATUS: "), lines[-1])
                self.assertEqual(tuple(re.findall(r"[A-Z_]{4,}", lines[-1][len("SLICKFAB-STATUS: "):])),
                                 expected[name])
                self.assertTrue(any(l.startswith("Nächster Schritt: ") for l in lines[:-1]))

    def test_waiting_template_says_how_to_continue_and_where_the_repo_stands(self):
        waiting = self.templates["Ergebnis prototype (awaiting verdict)"]
        self.assertIn("**Start:**", waiting)
        self.assertIn("**Compare:**", waiting)
        self.assertIn("**Repo is on:** prototype/<slug> (prototype committed, created from <branch>) "
                      "— back with `git switch <branch>`", waiting)
        # Pre-Push-Review: Die neue Session braucht Wegwerf- und Ausgangs-Branch im Argument.
        self.assertIn("Nächster Schritt: give the verdict here, then prototype records it; in a "
                      "new session `/slickfab:prototype Question: <…> Verdict: <…> "
                      "Branch: prototype/<slug> from <branch>`", waiting)

    def test_step_five_commits_before_waiting_and_uses_the_template(self):
        five = subsection(section(self.text, "Ablauf"), "5.")
        self.assertIn("Before you demonstrate, commit the prototype on the throwaway branch; the "
                      "commit message names the question and the starting branch", five)
        self.assertIn("template “awaiting verdict”", five)
        self.assertIn("If the session ends before the verdict", five)

    def test_step_six_continues_with_verdict_from_argument(self):
        six = subsection(section(self.text, "Ablauf"), "6.")
        self.assertIn("If the verdict comes in a new session", six)
        # Pre-Push-Review: sonst Commit auf main und Rückkehr auf einen geratenen Branch.
        self.assertIn("switch to the throwaway branch from the argument", six)
        self.assertIn("you take the starting branch from the argument or from the prototype's "
                      "commit message", six)
        self.assertIn("If one of the two is missing or the throwaway branch does not exist, stop", six)
        # Pre-Push-Review 2: auch dieses Warten braucht eine Vorlage mit nächstem Schritt.
        self.assertIn("template “branch question”", six)
        self.assertIn("You never commit on a branch that does not start with `prototype/`.", six)

    def test_branch_question_template_names_what_is_missing_and_the_command(self):
        ask = self.templates["Ergebnis prototype (branch question)"]
        self.assertIn("**Missing:** <throwaway branch | starting branch | `prototype/<slug>` does not exist>", ask)
        self.assertIn("**Nothing changed:** no commit, no branch switch", ask)
        self.assertIn("Nächster Schritt: `/slickfab:prototype Question: <…> Verdict: <…> "
                      "Branch: prototype/<slug> from <branch>`", ask)


class PrototypeHaltTest(unittest.TestCase):
    """Review PR #21, A3: Die Enden in Schritt 1 (keine Frage, Ein-Satz-Frage, offene Änderungen)
    hatten keine Vorlage mit nächstem Schritt und Marker."""

    def setUp(self):
        self.text = read("skills/prototype/SKILL.md")
        self.result = section(self.text, "Ergebnis")
        self.rows = set()
        for line in self.result.splitlines():
            cells = tuple(c.strip() for c in line.strip().strip("|").split("|"))
            if len(cells) == 4 and cells[0].startswith("Step "):
                self.rows.add(cells)

    def test_every_halt_has_a_row_with_next_step_and_status(self):
        self.assertEqual(self.rows, {
            ("Step 1", "no question", "`/slickfab:prototype <question>`", "`NEEDS_CONTEXT`"),
            ("Step 1", "question can be settled with one sentence", "`/slickfab:grill <question>`", "`NEEDS_CONTEXT`"),
            ("Step 1", "open changes in the repo",
             "the human commits or sets them aside themselves, then `/slickfab:prototype <question>` again",
             "`BLOCKED`"),
            # Review PR #21, A1: Commit in Schritt 5 nur auf prototype/.
            ("Step 5", "not on `prototype/<slug>`",
             "the human checks the branch, then `/slickfab:prototype <question>` again", "`BLOCKED`"),
        })

    def test_step_five_checks_the_branch_before_committing(self):
        five = subsection(section(self.text, "Ablauf"), "5.")
        self.assertIn("Before this commit, check with `git branch --show-current` that you are on "
                      "`prototype/<slug>`. Otherwise you commit nothing and end with the "
                      "template “halt”.", five)

    def test_step_one_points_to_the_template(self):
        one = subsection(section(self.text, "Ablauf"), "1.")
        self.assertIn("If you stop here, you end with the template “halt” (below).", one)

    def test_template_says_nothing_changed(self):
        self.assertIn("**State:** repo on <branch>, no commit; <no branch created | "
                      "uncommitted prototype files: …>", self.result)


class ChallengeStepTest(StandaloneStepMixin, unittest.TestCase):
    step = "challenge"
    precondition = "### 1. Check the precondition"

    def test_fresh_view_gets_only_the_spec(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("start a fresh subagent", flow)
        self.assertIn("only the spec", flow)

    def test_at_most_seven_objections_and_a_verdict(self):
        self.assertIn("at most 7 objections", self.text)
        # Die Urteilswerte bleiben wörtlich: fab und tickets lesen sie aus Kommentaren am Spec-Issue.
        for verdict in ("`bauen`", "`kleiner bauen`", "`nicht bauen`"):
            self.assertIn(verdict, self.text)

    def test_buildability_sorts_into_three_piles(self):
        for pile in ("already answered", "small stuff", "only the human"):
            self.assertIn(pile, self.text)

    def test_decomposition_check_stops_after_round_two(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("at most 2 rounds", flow)
        self.assertIn("does not go down", flow)
        self.assertIn("There is no third round", flow)


class TicketsStepTest(StandaloneStepMixin, unittest.TestCase):
    step = "tickets"
    precondition = "### 1. Check the precondition"

    def test_tracer_first_blocks_all_others(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("Tracer", flow)
        self.assertIn("blocks all other tickets", flow)
        # Beide Stellen tragen die Regel: das Schneiden und das Setzen der Relationen
        # (Mutationsprobe: der Satz in Schritt 3 allein gestrichen blieb grün).
        self.assertIn("It blocks all other tickets.", subsection(flow, "3. Cut"))
        self.assertIn("- The tracer blocks all other tickets.", subsection(flow, "4. Set dependencies"))

    def test_file_overlap_gets_blocked_by_relation(self):
        self.assertIn("the same file", section(self.text, "Ablauf"))
        self.assertIn("blocked-by relation", section(self.text, "Ablauf"))
        # Mutationsprobe: die Regel selbst gestrichen blieb grün, die Wörter standen auch anderswo.
        self.assertIn("If two tickets name the same file, the later one gets a blocked-by relation on "
                      "the earlier one, even if they need nothing from each other in content",
                      subsection(section(self.text, "Ablauf"), "4. Set dependencies"))

    def test_rejects_deferral_phrases(self):
        flow = section(self.text, "Ablauf")
        for phrase in ("“v1”", "“simplified”", "“placeholder”", "“will be wired later”",
                       "`vereinfacht`", "`Platzhalter`", "`wird später verdrahtet`"):
            self.assertIn(phrase, flow)

    def test_confirmation_and_duplicate_check_before_creating(self):
        flow = section(self.text, "Ablauf")
        confirm = flow.index("numbered list")
        dupes = flow.index("Check for duplicates")
        create = flow.index("### 7. Create")
        self.assertLess(confirm, create)
        self.assertLess(dupes, create)

    def test_ticket_template_fields(self):
        # Felder des Tickets bleiben wörtlich: der Dispatcher liest „Betroffene Dateien“,
        # implement, review und verify lesen „Widerlegt, wenn“.
        for field in ("Widerlegt, wenn", "Verbraucht:", "Liefert:", "Betroffene Dateien",
                      "`door:one-way`", "Expand–Migrate–Contract"):
            self.assertIn(field, self.text)

    def test_decomposition_is_challenged_before_human_sees_it(self):
        self.assertIn("/slickfab:challenge", section(self.text, "Ablauf"))

    def test_question_ending_keeps_next_step_and_marker_outside_code_block(self):
        # Hand-Durchlauf, Befund 1: Bei einer Rückfrage (Dublette,
        # NEEDS_CONTEXT) fehlte „Nächster Schritt“, und der Marker stand in einem Codeblock.
        result = section(self.text, "Ergebnis")
        self.assertIn("The line `Nächster Schritt` is never missing, not even for a question "
                      "(`NEEDS_CONTEXT`).", result)
        self.assertIn("The marker line is the last line of your answer and stands outside "
                      "any code block.", result)
        templates = re.findall(r"^```\n(.*?)^```", result, re.S | re.M)
        self.assertEqual(len(templates), 3, "Vorlagen: angelegt, Rückfrage, Abbruch")
        for block in templates:
            lines = block.strip().splitlines()
            with self.subTest(template=lines[0]):
                self.assertTrue(lines[-1].startswith("SLICKFAB-STATUS: "), lines[-1])
                self.assertTrue(any(l.startswith("Nächster Schritt: `/slickfab:") for l in lines[:-1]))
        self.assertIn("SLICKFAB-STATUS: NEEDS_CONTEXT", templates[1])
        self.assertIn("SLICKFAB-STATUS: BLOCKED", templates[2])

    def result_templates(self):
        return re.findall(r"^```\n(.*?)^```", section(self.text, "Ergebnis"), re.S | re.M)

    def test_question_next_step_matches_the_reason(self):
        # Review PR #17, A1: Die Rückfrage-Vorlage empfahl fest `tickets` erneut, Schritt 1
        # verlangt bei fehlender Spec oder einer Entscheidung, die nicht in der Spec steht, `spec`.
        question = [t for t in self.result_templates() if "(question)" in t][0]
        self.assertIn("if the spec is missing or a decision is not yet in it: "
                      "`/slickfab:spec [spec issue]`", question)
        self.assertIn("if the check is missing: `/slickfab:challenge <spec issue>`", question)
        self.assertIn("question about the cut (duplicate, list waiting for the yes, findings open after round 2): "
                      "`/slickfab:tickets <spec issue>` again", question)
        # Schritt 1 nennt dieselben Wege.
        pre = subsection(self.text, "1. Check the precondition")
        self.assertIn("If it is missing, recommend `/slickfab:spec`.", pre)
        self.assertIn("`/slickfab:spec <spec issue>` first", pre)

    def test_tracker_abort_while_creating_has_blocked_template(self):
        # Review PR #17, A1: Bricht der Tracker beim Anlegen ab, gab es keine Vorlage mit BLOCKED.
        aborted = [t for t in self.result_templates() if "(abort)" in t]
        self.assertEqual(len(aborted), 1)
        lines = aborted[0].strip().splitlines()
        self.assertEqual(lines[-1], "SLICKFAB-STATUS: BLOCKED")
        self.assertTrue(any(l.startswith("Nächster Schritt: `/slickfab:") for l in lines[:-1]))
        self.assertIn("**Already created:**", aborted[0])
        self.assertIn("**Not created:**", aborted[0])
        self.assertIn("**Error message:**", aborted[0])
        main = [t for t in self.result_templates() if t.startswith("## Ergebnis tickets\n")][0]
        self.assertNotIn("BLOCKED", main)


STOP = re.compile(r"\b[Ss]top\b|recommend|you wait|you put to the human")


class TicketsEveryEndingHasTemplateTest(unittest.TestCase):
    """Review PR #17, Re-Review: Der Abbruch in Schritt 1 (Konfiguration fehlt, Tracker nicht
    erreichbar) hatte keine Vorlage mehr. Jede Stelle, an der tickets enden kann, steht in der
    Tabelle „Wo tickets endet“ und zeigt auf eine Vorlage mit STATUS und nächstem Schritt."""

    def setUp(self):
        self.text = read("skills/tickets/SKILL.md")
        result = section(self.text, "Ergebnis")
        self.templates = {}
        for block in re.findall(r"^```\n(.*?)^```", result, re.S | re.M):
            head = block.splitlines()[0]
            self.templates[head[len("## "):]] = block
        self.rows = []
        for line in result.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0].startswith("Step "):
                self.rows.append(cells)

    def test_every_stop_in_the_flow_has_a_row(self):
        flow = section(self.text, "Ablauf")
        stops = sorted({int(m.group(1)) for m in re.finditer(r"^### (\d+)\.", flow, re.M)
                        if STOP.search(subsection(flow, m.group(1) + "."))})
        self.assertEqual(stops, [1, 6, 7])
        covered = {int(r[0].split()[1].rstrip(":")) for r in self.rows}
        for step in stops:
            with self.subTest(step=step):
                self.assertIn(step, covered, "Schritt %d kann enden, hat aber keine Zeile" % step)

    def test_expected_endings(self):
        expected = {
            ("Step 1", "`.slickfab/config` missing or tracker unreachable", "Ergebnis tickets (abort)", "`BLOCKED`"),
            ("Step 1", "spec issue missing", "Ergebnis tickets (question)", "`NEEDS_CONTEXT`"),
            ("Step 1", "`challenge` comment missing", "Ergebnis tickets (question)", "`NEEDS_CONTEXT`"),
            ("Step 1", "decision not yet in the spec", "Ergebnis tickets (question)", "`NEEDS_CONTEXT`"),
            ("Step 1", "last `challenge` verdict `nicht bauen`", "Ergebnis tickets (question)", "`NEEDS_CONTEXT`"),
            ("Step 6", "tracker answers the duplicate search with an error", "Ergebnis tickets (abort)", "`BLOCKED`"),
            ("Step 6", "duplicate, list waiting for the yes, or findings open after round 2", "Ergebnis tickets (question)", "`NEEDS_CONTEXT`"),
            ("Step 7", "tracker breaks off while creating", "Ergebnis tickets (abort)", "`BLOCKED`"),
            ("Step 7", "all tickets created", "Ergebnis tickets", "`DONE` or `DONE_WITH_CONCERNS`"),
        }
        self.assertEqual({tuple(r) for r in self.rows}, expected)

    def test_each_row_points_to_a_template_with_status_and_next_step(self):
        for step, case, template, status in self.rows:
            with self.subTest(case=case):
                self.assertIn(template, self.templates)
                lines = self.templates[template].strip().splitlines()
                self.assertTrue(lines[-1].startswith("SLICKFAB-STATUS: "))
                for value in re.findall(r"`([A-Z_]+)`", status):
                    self.assertIn(value, lines[-1])
                self.assertTrue(any(l.startswith("Nächster Schritt: `/slickfab:") for l in lines[:-1]))

    def test_abort_template_covers_step_one_and_names_what_the_human_does(self):
        abort = self.templates["Ergebnis tickets (abort)"]
        # Schritt 7 verweist beim Abbruch auf die Vorlage (überlebende Mutation, Rework 2).
        self.assertIn("(template “abort” below, `BLOCKED`)", subsection(self.text, "7. Create"))
        self.assertIn("**Where:** step 1 (configuration or tracker) | step 6 (duplicate search) "
                      "| step 7 (while creating)", abort)
        self.assertIn("**Already created:** <IDs with title and relations set> (in steps 1 and 6: none)", abort)
        self.assertIn("Nächster Schritt: `/slickfab:tickets <spec issue>` again, after you have "
                      "<created `.slickfab/config` | checked the tracker (tools loaded, logged in, "
                      "team and project exist)>", abort)


# Stellen im Ablauf, an denen tickets den Tracker anspricht (lesen, suchen, anlegen).
TRACKER_CALL = re.compile(r"Read the spec issue|search the project|sub-issue of the spec, status|comment on the spec issue")


class TicketsTrackerErrorTest(unittest.TestCase):
    """Review PR #17, O1: Der Vertrag „Zugang“ sagt, bei jeder Fehlerantwort des
    Trackers hört der Schritt auf. Die Tabelle „Wo tickets endet“ kannte das nur für Schritt 1
    und 7; die Dublettensuche in Schritt 6 hatte kein Ende. Der alte Ankertest sah das nicht,
    weil er nur Stoppwörter im Ablauf las, nicht das „hört auf“ des Vertrags."""

    def setUp(self):
        self.text = read("skills/tickets/SKILL.md")
        self.ending = TicketsEveryEndingHasTemplateTest("test_expected_endings")
        self.ending.setUp()

    def tracker_steps(self):
        flow = section(self.text, "Ablauf")
        return sorted({int(m.group(1)) for m in re.finditer(r"^### (\d+)\.", flow, re.M)
                       if TRACKER_CALL.search(subsection(flow, m.group(1) + "."))})

    def test_contract_stops_on_any_tracker_error(self):
        # Der Zugang-Block ist englisch: „Fehlerantwort“ = error response, „hört auf“ = stops.
        # Ganzer Satz im Block 'zugang' (Review PR #1): „and stops“ steht auch in config-fehlt,
        # „and stops.“ → „and continues.“ blieb sonst grün.
        contract = section(self.text, "Vertrag")
        access = re.search(r"<!-- vertrag:zugang -->\n(.*?)<!-- /vertrag:zugang -->", contract, re.S)
        self.assertIsNotNone(access, "tickets bettet den Block 'zugang' nicht ein")
        self.assertIn("error response", access.group(1))
        self.assertIn("the step reports exactly that, with the error message, and stops.", access.group(1))

    def test_steps_that_use_the_tracker(self):
        self.assertEqual(self.tracker_steps(), [1, 6, 7])

    def test_every_tracker_step_has_an_abort_row(self):
        for step in self.tracker_steps():
            with self.subTest(step=step):
                rows = [r for r in self.ending.rows if r[0] == "Step %d" % step
                        and "tracker" in r[1] and r[2] == "Ergebnis tickets (abort)" and r[3] == "`BLOCKED`"]
                self.assertTrue(rows, "Schritt %d spricht den Tracker an, hat aber keine Abbruch-Zeile" % step)

    def test_step_six_names_the_abort(self):
        self.assertIn("If the tracker answers the search with an error, stop (template “abort” "
                      "below, `BLOCKED`).", subsection(self.text, "6. Check the split"))


class ChallengeNotBuildEndsWithCanceledTest(unittest.TestCase):
    """Review PR #19, A1: challenge nannte bei `nicht bauen` nur „endet die Planung hier“."""

    def test_next_step_names_canceled(self):
        self.assertIn("If the verdict is `nicht bauen` and the human agrees, planning ends "
                      "here: the human sets the spec to `Canceled`.",
                      section(read("skills/challenge/SKILL.md"), "Nächster Schritt"))


class TicketsAbortFieldsTest(unittest.TestCase):
    """Review PR #19, A2: Die Abbruch-Vorlage gilt für Schritt 1, 6 und 7; zwei davon sind
    Fehlerantworten des Trackers, das Feld Fehlermeldung kannte nur Datei oder Schlüssel."""

    def setUp(self):
        ending = TicketsEveryEndingHasTemplateTest("test_expected_endings")
        ending.setUp()
        self.abort = ending.templates["Ergebnis tickets (abort)"]

    def test_error_field_takes_tracker_errors(self):
        self.assertIn("**Error message:** <verbatim: missing file or missing key, or "
                      "the tracker's error response>", self.abort)

    def test_not_created_fits_step_six(self):
        self.assertIn("in step 6: all titles of the not yet confirmed list", self.abort)


class TicketsNotBuildVerdictTest(unittest.TestCase):
    """Review PR #17, O2: Bei challenge-Urteil `nicht bauen` hatte tickets keine
    Regel aufzuhören und kein Ende mit Vorlage."""

    def setUp(self):
        self.text = read("skills/tickets/SKILL.md")

    def test_step_one_stops_on_not_build(self):
        self.assertIn("If the last verdict is `nicht bauen`, stop here and put the question to the "
                      "human (template “question” below), unless they have explicitly said "
                      "that the spec is to be split anyway.", subsection(self.text, "1. Check the precondition"))

    def test_question_template_names_next_step_without_tickets(self):
        question = [b for b in re.findall(r"^```\n(.*?)^```", section(self.text, "Ergebnis"), re.S | re.M)
                    if b.startswith("## Ergebnis tickets (question)")][0]
        self.assertIn("if the verdict is `nicht bauen`: `/slickfab:spec <spec issue>` if you change the spec "
                      "(after that `/slickfab:challenge <spec issue>`); if you agree with the verdict, "
                      "the work ends and you set the spec to `Canceled`", question)


class GrillAdrRuleTest(unittest.TestCase):
    """Hand-Durchlauf, Befund 3: Runde 1 wollte für dieselbe
    Entscheidung einen ADR, Runde 2 nicht. Wann ein ADR fällig ist, steht als feste
    Regel mit genau zwei Kriterien, die beide zutreffen müssen."""

    def setUp(self):
        self.rule = subsection(read("skills/grill/SKILL.md"), "6. Take notes")

    def test_adr_rule_has_two_fixed_criteria(self):
        self.assertIn("**ADR:** An ADR is due if both apply: (1) The decision is hard to "
                      "reverse. (2) Without a reason, a later reader would find it surprising "
                      "or reopen it.", self.rule)
        self.assertIn("If both apply, you create the ADR; if one does not apply, you create none.",
                      self.rule)

    def test_no_third_criterion_left_to_judgement(self):
        # Widerlegt, wenn die Regel ein Ermessen ohne diese zwei Kriterien lässt.
        self.assertNotIn("real trade-off", self.rule)
        self.assertNotIn("Only if", self.rule)


class RuleAnchorsTest(unittest.TestCase):
    """Review PR #2, R1: Die Sätze, die die „Widerlegt, wenn“-Fälle des Tickets
    tragen, müssen an ihrer Stelle stehen. Fehlt einer oder wird er umgedreht,
    wird es rot (Mutationsprobe). Das prüft den Text, nicht das Verhalten."""

    # (Datei, Abschnitt '### <Anfang>' oder '## <Name>', Ankersatz)
    ANCHORS = (
        # Fehlende Konfiguration / Tracker: melden, keine Ersatzdatei
        ("skills/tickets/SKILL.md", "### 1. Check the precondition", "stop here and report exactly that"),
        ("skills/tickets/SKILL.md", "### 1. Check the precondition", "you write no ticket, plan or state file into the repo as a substitute"),
        ("skills/tickets/SKILL.md", "### 7. Create", "You create no file as a substitute."),
        ("skills/spec/SKILL.md", "### 6. Create in the tracker", "You create no spec, plan or ticket file in the repo."),
        ("skills/challenge/SKILL.md", "### 5. Record", "No file in the repo as a substitute."),
        ("tracker/linear.md", "## Access", "It writes **no** plan, ledger, state or ticket file into the repo as a substitute."),
        ("docs/projektkonfiguration.md", "## Wenn die Konfiguration fehlt", "It writes no plan, ledger or state file and no ticket list into the repo as a substitute"),
        # Anlegen erst nach Bestätigung, Dubletten vorher
        ("skills/tickets/SKILL.md", "### 6. Check the split", "Nothing is created until there is an explicit yes to the list"),
        ("skills/tickets/SKILL.md", "### 7. Create", "Only after the yes"),
        ("skills/tickets/SKILL.md", "### 6. Check the split", "Check for duplicates"),
        ("tracker/linear.md", "## Issues", "Before creating anything, check for duplicates"),
        # Vertagende Formulierungen
        ("skills/tickets/SKILL.md", "### 5. Check for silent", "A ticket with such a phrase you do not create."),
        # Keine stille Annahme in spec, keine Pfade
        ("skills/spec/SKILL.md", "### 1. Check the precondition", "you stop here"),
        ("skills/spec/SKILL.md", "### 3. Check every statement", "**Product question or hard to reverse:** Here you stop."),
        ("skills/spec/SKILL.md", "### 5. Self-check", "no file path, no file name, no code in the text"),
        # challenge: frischer Blick
        ("skills/challenge/SKILL.md", "### 2. Establish the fresh eye", "Do not check yourself in a session that knows the conversation."),
        # Freigabe bleibt beim Menschen
        ("skills/tickets/SKILL.md", "### 7. Create", "You set no ticket to `Todo`"),
        ("tracker/linear.md", "## Status flow", "No step sets a ticket to `Todo` by itself."),
        # Konfiguration nie ausführen
        ("docs/projektkonfiguration.md", "## Format", "not executed as a shell script (no `source`)"),
        # prototype: fremde Arbeit und Hauptzweig unangetastet
        ("skills/prototype/SKILL.md", "### 1. Check the precondition", "If changes are open, stop and say so. You do not move or hide anyone else's changes."),
        ("skills/prototype/SKILL.md", "### 6. Record", "Nothing from the prototype goes into the main branch"),
        ("tracker/linear.md", "## Labels", "a step does not create new ones"),
    )

    def test_anchors(self):
        for rel, scope, sentence in self.ANCHORS:
            with self.subTest(file=rel, scope=scope, anchor=sentence[:40]):
                text = read(rel)
                part = subsection(text, scope[4:]) if scope.startswith("### ") else section(text, scope[3:])
                self.assertTrue(part, "%s: Abschnitt '%s' fehlt" % (rel, scope))
                self.assertIn(sentence, part)


# Die Planungs-Schritte sind englisch (öffentliches Repo). Deutsch bleiben nur Namen, die andere
# Dateien, der Dispatcher oder schon angelegte Issues lesen; sie stehen in `Code`, in Codeblöcken,
# in Vertragsblöcken oder als feste Überschrift (check_structure.py).
PLANNING_STEPS = ("fab", "grill", "spec", "prototype", "challenge", "tickets")
GERMAN = re.compile(r"[äöüÄÖÜß„]|\b(und|oder|nicht|der|die|das|ist|wird|eine?|keine?|du|dich|wenn|mit|auf|sie)\b", re.I)
FIXED = re.compile(r"^## (Wann|Ablauf|Vertrag|Ergebnis|Nächster Schritt)$", re.M)


def prose(text):
    """Fließtext ohne Frontmatter-Schlüssel, Vertragsblöcke, Codeblöcke, `Code`, Marker und feste Überschriften."""
    text = re.sub(r"<!-- vertrag:([a-z-]+) -->.*?<!-- /vertrag:\1 -->", "", text, flags=re.S)
    text = re.sub(r"(?ms)^```.*?^```", "", text)
    text = re.sub(r"<!--.*?-->", "", text)
    text = FIXED.sub("", text)
    return re.sub(r"`[^`\n]*`", "", text)


class EnglishPlanningStepsTest(unittest.TestCase):
    def test_planning_steps_are_english(self):
        for step in PLANNING_STEPS:
            with self.subTest(step=step):
                text = prose(read("skills/%s/SKILL.md" % step))
                found = GERMAN.search(text)
                self.assertIsNone(found, found and text[max(0, found.start() - 40):found.end() + 40])

    def test_german_guard_is_sharp(self):
        # Mutationsprobe des Wächters: ein deutscher Satz im Fließtext fällt auf, Namen in `Code` nicht.
        self.assertIsNotNone(GERMAN.search(prose("You read it. Du liest es selbst.")))
        self.assertIsNotNone(GERMAN.search(prose("Name it under „Bedenken“.")))
        self.assertIsNone(GERMAN.search(prose("Name it under `Nicht im Umfang`.\n## Nächster Schritt\n")))
        self.assertIsNotNone(GERMAN.search(prose("## Nächster Schritt: weiter\n")))

    def test_every_step_carries_the_language_rule(self):
        for step in PLANNING_STEPS:
            with self.subTest(step=step):
                intro = read("skills/%s/SKILL.md" % step).split("<!-- /regel:einleitung -->")[0]
                self.assertIn("Answer in the user's language.", intro)


class GlossedGermanValuesTest(unittest.TestCase):
    """Review: Die deutschen Werte bleiben (fab liest sie aus Kommentaren), dahinter steht
    eine kurze englische Erklärung in Klammern, damit englische Leser sie verstehen."""

    def test_verify_statuses_in_fab_are_glossed(self):
        fab = read("skills/fab/SKILL.md")
        tracker = fab.split("<!-- regel:tracker-lesen -->")[1].split("<!-- /regel:tracker-lesen -->")[0]
        self.assertIn("(with status `bestanden` (passed), `Lücken gefunden` (gaps found) or "
                      "`Mensch nötig` (human needed))", tracker)
        rows = fab.split("<!-- regel:entscheiden -->")[1].split("<!-- /regel:entscheiden -->")[0]
        for value, gloss in (("bestanden", "passed"), ("Lücken gefunden", "gaps found"),
                             ("Mensch nötig", "human needed")):
            with self.subTest(value=value):
                self.assertIn("last `verify` result `%s` (%s) |" % (value, gloss), rows)

    def test_challenge_verdicts_in_template_are_glossed(self):
        result = section(read("skills/challenge/SKILL.md"), "Ergebnis")
        self.assertIn("**Verdict:** bauen (build) | kleiner bauen (build smaller) | "
                      "nicht bauen (don't build) — <carrying reason>", result)


if __name__ == "__main__":
    unittest.main()
