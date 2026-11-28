"""Bau-Schritte implement, debug, handoff an ihrer öffentlichen
Schnittstelle: den Texten, die ein Agent liest, wenn er `/slickfab:<schritt>`
ausführt.

Erwartete Sätze und Begriffe stammen aus den Akzeptanzkriterien des Tickets
(und der Spec), nicht aus den Dateien selbst. Ob ein Agent sich daran
hält, prüft das nicht (dafür Hand-Durchlauf und später Pressure-Szenarien);
es fängt aber, wenn eine Regel verschwindet, umgedreht oder verschoben wird
(Mutationsprobe, siehe docs/features/bau-schritte.md).
"""
import unittest

from test_contract_blocks import blocks
from test_planning_steps import StandaloneStepMixin, read, section, subsection

STEPS = ("implement", "debug", "handoff")


def part(rel, scope):
    """'### <Anfang>' → Unterabschnitt, '## <Name>' → Abschnitt."""
    text = read(rel)
    return subsection(text, scope[4:]) if scope.startswith("### ") else section(text, scope[3:])


class EnglishStepMixin(StandaloneStepMixin):
    """Wie StandaloneStepMixin, aber mit der englischen Überschrift des ersten Schritts.
    Die festen `## `-Überschriften (Wann, Ablauf, Ergebnis, Nächster Schritt) bleiben deutsch,
    weil tests/check_structure.py sie verlangt."""

    precondition = "### 1. Check the precondition"

    def test_checks_its_precondition(self):
        self.assertIn(self.precondition, section(self.text, "Ablauf"))


class ImplementStandaloneTest(EnglishStepMixin, unittest.TestCase):
    step = "implement"


class DebugStandaloneTest(EnglishStepMixin, unittest.TestCase):
    step = "debug"


class HandoffStandaloneTest(EnglishStepMixin, unittest.TestCase):
    step = "handoff"


class RequiredContractBlocksTest(unittest.TestCase):
    """Ruling: Vertragsteile wörtlich einbetten. Welche ein Schritt
    braucht, steht hier; die Gleichheit mit der Quelle prüft
    tests/test_contract_blocks.py für alle Schritte."""

    REQUIRED = {
        # setzt Status, Labels (needs-human, door:one-way), schreibt Rulings
        "implement": ("zugang", "status", "labels", "rulings", "marker"),
        # Ticket optional; gibt es eins, liest und kommentiert debug es (Review PR #7, A1)
        "debug": ("zugang", "marker"),
        # Kommentar am Ticket
        "handoff": ("zugang", "marker"),
    }

    def test_debug_follows_access_contract_when_ticket_given(self):
        # Review PR #7, A1: mit Ticket, aber ohne erreichbares Linear war offen,
        # ob debug aufhört, eine Datei schreibt oder still weitermacht.
        self.assertIn("If there is a ticket and the tracker is unreachable, the contract “access” "
                      "applies: report and stop, no file as a substitute.",
                      part(DEBUG, "### 1. Check the precondition"))

    def test_steps_embed_required_blocks(self):
        for step, names in self.REQUIRED.items():
            embedded = blocks(read("skills/%s/SKILL.md" % step))
            for name in names:
                with self.subTest(step=step, block=name):
                    self.assertIn(name, embedded)


class CheckCommandsFromConfigTest(unittest.TestCase):
    """AC: Prüfbefehle kommen aus der Projektkonfiguration; fehlt sie, meldet
    der Schritt das. Widerlegt, wenn ein Schritt Prüfbefehle rät."""

    CONFIG_BLOCKS = ("config-format", "config-slickrails", "config-fehlt")
    ANCHOR = ("You take check commands only from `.slickrails/config.sh` or `.slickfab/config`; "
              "you do not guess any from `package.json`, `Makefile` or habit.")
    MISSING = "If a check command is missing, you say which one, and that you cannot run it."

    def test_steps_embed_config_contract(self):
        for step in STEPS:
            embedded = blocks(read("skills/%s/SKILL.md" % step))
            for name in self.CONFIG_BLOCKS:
                with self.subTest(step=step, block=name):
                    self.assertIn(name, embedded)

    def test_steps_do_not_guess_check_commands(self):
        for step in STEPS:
            pre = part("skills/%s/SKILL.md" % step, "### 1. Check the precondition")
            with self.subTest(step=step):
                self.assertIn(self.ANCHOR, pre)
                self.assertIn(self.MISSING, pre)


IMPLEMENT = "skills/implement/SKILL.md"


class ImplementRedGreenTest(unittest.TestCase):
    """AC: implement zeigt je Kriterium den roten und den grünen Lauf mit Befehl
    und Ausgabe und lässt am Ende die ganze Suite laufen. Widerlegt, wenn im
    PR-Text für ein Kriterium der rote Lauf fehlt."""

    def test_each_criterion_red_before_code(self):
        loop = part(IMPLEMENT, "### 3. Per criterion")
        self.assertIn("No production code for this criterion without a red run.", loop)
        self.assertIn("Record command and output.", loop)
        self.assertIn("red for the expected reason", loop)
        self.assertLess(loop.index("**Red:**"), loop.index("**Green:**"))

    def test_whole_suite_at_the_end(self):
        suite = part(IMPLEMENT, "### 6. Whole suite")
        self.assertIn("`CHECK_TEST`", suite)
        self.assertIn("the whole suite", suite)

    def test_pr_text_has_red_and_green_per_criterion(self):
        pr = part(IMPLEMENT, "### 7. Pull request")
        self.assertRegex(pr, r"- K1 .*\n\s+- red: `<command>` → <output")
        self.assertRegex(pr, r"\n\s+- green: `<command>` → <output")
        self.assertIn("If the red run is missing for a criterion, the pull request is not done.", pr)


class ImplementKnowsReviewMutationRuleTest(unittest.TestCase):
    """Hand-Durchlauf, Befund 4: Der Umsetzer kannte eine Lücke
    aus einem früheren Review-Kommentar und ließ sie offen, weil das Ticket sie nicht
    nannte; review machte daraus REWORK. implement nennt die Mutationsregel des Reviews."""

    def test_every_changed_behaviour_needs_a_test_even_if_ticket_is_silent(self):
        rule = part(IMPLEMENT, "### 2. Translate criteria into tests")
        self.assertIn("Every behaviour that your diff introduces or changes needs a test, "
                      "even if the ticket does not mention it.", rule)
        self.assertIn("/slickfab:review", rule)

    def test_known_gap_from_earlier_review_is_closed_or_justified(self):
        rule = part(IMPLEMENT, "### 2. Translate criteria into tests")
        self.assertIn("You close a known gap from an earlier review comment on the ticket or on the "
                      "pull request with a red and a green run, or you explicitly justify in the "
                      "pull request under “Nicht angefasst” why it stays open.", rule)
        # Die Review-Kommentare liest implement schon in der Voraussetzung.
        self.assertIn("you also read its review comments", part(IMPLEMENT, "### 1. Check the precondition"))


class ImplementKeepsTestsTest(unittest.TestCase):
    """AC: implement schwächt keine bestehenden Tests ab (kein Überspringen,
    keine gelöschten Assertions, keine gesenkten Schwellen). Widerlegt, wenn
    im Fall „bestehender Test steht im Weg“ der Test verändert statt gemeldet wird."""

    def setUp(self):
        self.loop = part(IMPLEMENT, "### 3. Per criterion")

    def test_rule_names_the_three_weakenings(self):
        self.assertIn("You do not weaken existing tests to get green:", self.loop)
        for way in ("no skipping", "no deleted or loosened assertions",
                    "no lowered thresholds"):
            self.assertIn(way, self.loop)

    def test_blocking_test_is_reported_not_changed(self):
        self.assertIn("If an existing test is in the way, you do not change it; you stop "
                      "and report it", self.loop)
        self.assertIn("`BLOCKED`", self.loop)

    def test_no_exception_when_ticket_changes_behaviour(self):
        # Hand-Durchlauf D: Mit der Ausnahme „verlangt das Ticket ausdrücklich …“
        # schrieb der Agent den im Weg stehenden Test um und meldete ihn nicht.
        self.assertIn("This applies even if the ticket explicitly wants to change the behaviour "
                      "that the test pins down", self.loop)
        self.assertNotIn("changing this test is part of the criterion", self.loop)
        self.assertIn("“The ticket asks for exactly this new behaviour.”", self.loop)

    def test_excuses_are_answered(self):
        self.assertIn("| Excuse | Reality |", self.loop)
        self.assertIn("“The old test is wrong anyway.”", self.loop)


class ImplementStopsTest(unittest.TestCase):
    """AC: Trifft implement auf einen Punkt der Stopp-Liste oder eine
    Architekturfrage, hält er an und meldet BLOCKED mit Begründung. Widerlegt,
    wenn im Fall „Ticket verlangt destruktive Migration“ ohne Rückfrage gebaut wird."""

    STOP_LIST = ("auth and permissions", "destructive migrations", "payments",
                 "deletions", "deploys", "secrets", "anything a revert does not bring back")

    def test_stop_list_complete(self):
        stop = part(IMPLEMENT, "### 5. Stop list")
        for item in self.STOP_LIST:
            self.assertIn(item, stop)

    def test_stop_list_halts_even_when_ticket_asks(self):
        stop = part(IMPLEMENT, "### 5. Stop list")
        self.assertIn("you stop before you build it and report `BLOCKED` with a reason", stop)
        self.assertIn("This applies even if the ticket explicitly demands it", stop)

    def test_stop_list_checked_before_first_test(self):
        self.assertIn("Before the first test, check whether the ticket touches the stop list (step 5).",
                      part(IMPLEMENT, "### 1. Check the precondition"))

    def test_architecture_question_stops(self):
        dev = part(IMPLEMENT, "### 4. Deviations")
        self.assertIn("**Rule 4, architecture question:** Here you stop and report `BLOCKED` with a reason.", dev)

    def test_small_deviations_fixed_and_named(self):
        dev = part(IMPLEMENT, "### 4. Deviations")
        for rule in ("**Rule 1, bug:**", "**Rule 2, missing critical function:**",
                     "**Rule 3, blocker:**"):
            self.assertIn(rule, dev)
        self.assertIn("The stop list takes precedence over rules 1–3.", dev)


class ImplementAttemptCapTest(unittest.TestCase):
    """AC: Nach 3 gescheiterten Fix-Versuchen an derselben Stelle stoppt
    implement. Widerlegt, wenn ein vierter Versuch startet."""

    def setUp(self):
        self.loop = part(IMPLEMENT, "### 3. Per criterion")

    def test_three_attempts_then_stop(self):
        self.assertIn("After 3 failed fix attempts at the same place, you stop. "
                      "You do not start a fourth attempt.", self.loop)

    def test_attempt_is_defined_and_counted(self):
        self.assertIn("A fix attempt is a change to the production code after which the same test "
                      "is red again.", self.loop)
        self.assertIn("Attempt 1/3", self.loop)

    def test_stop_hands_over_to_debug(self):
        self.assertRegex(self.loop, r"do not start a fourth attempt\.[^\n]*`BLOCKED`[^\n]*`/slickfab:debug")


class ImplementFinishesTest(unittest.TestCase):
    """Kommentar am Ticket (Master, 24.11.): Ein Umsetzer rief `/security-review`
    auf und beendete danach den Turn ohne PR. Ein Pflicht-Review ist ein
    Zwischenschritt; der Schritt endet erst mit dem Ergebnis."""

    def test_mandatory_review_is_intermediate(self):
        suite = part(IMPLEMENT, "### 6. Whole suite")
        self.assertIn("A mandatory review before the pull request (such as `/security-review`) is an "
                      "intermediate step: Afterwards you continue with commit, push and pull request.", suite)

    def test_hooks_only_bypassed_with_documented_approval(self):
        # Pre-Push-Review: „außer der Mensch sagt es“ ließ eine Chat-Zusage gelten.
        suite = part(IMPLEMENT, "### 6. Whole suite")
        self.assertIn("You never bypass hooks (`--no-verify` and the like), unless the human has recorded it "
                      "on the ticket for exactly this push; then the reason is in the commit.", suite)
        self.assertNotIn("unless the human says so explicitly", suite)

    def test_ticket_to_in_review_and_result_last(self):
        done = part(IMPLEMENT, "### 8. Wrap-up")
        self.assertIn("`In Review`", done)
        self.assertIn("The step only ends with the “Ergebnis implement”", done)


class NextStepAlsoWhenBlockedTest(unittest.TestCase):
    """AC 1, Hand-Durchlauf A: Bei BLOCKED nannte implement den nächsten Schritt
    nur im Fließtext. Die Zeile steht in jedem Ausgang."""

    def test_next_step_line_never_missing(self):
        for step in STEPS:
            with self.subTest(step=step):
                self.assertIn("The line “Nächster Schritt” is never missing, not even with `BLOCKED` "
                              "or `NEEDS_CONTEXT`.", section(read("skills/%s/SKILL.md" % step), "Ergebnis"))


class StatusLastInResultTest(unittest.TestCase):
    """Hand-Durchlauf B: Der Agent schrieb SLICKFAB-STATUS und danach noch
    „Nächster Schritt“, weil die Vorlage den Status davor hatte. Der Marker-
    Vertrag verlangt den Status als letzte Zeile."""

    def test_status_is_last_line_of_result_template(self):
        for step in STEPS:
            result = section(read("skills/%s/SKILL.md" % step), "Ergebnis")
            block = result.split("```")[1].strip().splitlines()
            with self.subTest(step=step):
                self.assertTrue(block[-1].startswith("SLICKFAB-STATUS: "), block[-1])
                self.assertTrue(any(l.startswith("Nächster Schritt: `/slickfab:") for l in block[:-1]))


class ImplementPrFormatTest(unittest.TestCase):
    """AC: Der PR-Text enthält alle Abschnitte des Formats; „nicht angefasst“
    und „Bedenken“ dürfen leer sein, fehlen aber nicht."""

    # Reihenfolge und Namen aus dem Ticket: Änderungen, nicht angefasst, Bedenken,
    # Door (one-way / two-way), Blast Radius, Nachweise vorher/nachher.
    SECTIONS = ("## Änderungen", "## Nicht angefasst", "## Bedenken", "## Door",
                "## Blast Radius", "## Nachweise")

    def test_template_has_all_sections_in_order(self):
        pr = part(IMPLEMENT, "### 7. Pull request")
        positions = [pr.find("\n" + s + "\n") for s in self.SECTIONS]
        for name, pos in zip(self.SECTIONS, positions):
            self.assertNotEqual(pos, -1, name)
        self.assertEqual(positions, sorted(positions))

    def test_door_names_both_values(self):
        self.assertIn("`one-way` | `two-way`", part(IMPLEMENT, "### 7. Pull request"))

    def test_empty_sections_stay(self):
        self.assertIn("Every section is in the text, even if it is empty; then it says “none” below it.",
                      part(IMPLEMENT, "### 7. Pull request"))


DEBUG = "skills/debug/SKILL.md"


class DebugRedLoopFirstTest(unittest.TestCase):
    """AC: debug beginnt keine Ursachensuche ohne einen Befehl, der rot wird.
    Widerlegt, wenn im Fall ohne reproduzierbaren Fehler eine Korrektur
    vorgeschlagen wird."""

    def setUp(self):
        self.loop = part(DEBUG, "### 2. Build a red loop")

    def test_red_command_gates_everything(self):
        self.assertIn("Without a command that turns red on exactly this bug, no search for the cause "
                      "and no fix.", self.loop)
        self.assertIn("that you have already run once", self.loop)

    def test_no_loop_means_stop_without_fix(self):
        self.assertIn("If you do not manage to get a red command, you stop: You name what you have tried "
                      "and ask for what is missing. You do not suggest a fix.", self.loop)
        self.assertIn("`NEEDS_CONTEXT`", self.loop)

    def test_loop_comes_before_hypotheses(self):
        text = section(read(DEBUG), "Ablauf")
        self.assertLess(text.index("### 2. Build a red loop"), text.index("### 4. Hypotheses"))

    def test_hypotheses_are_falsifiable_and_three_to_five(self):
        hyp = part(DEBUG, "### 4. Hypotheses")
        self.assertIn("3 to 5", hyp)
        self.assertIn("If <X> is the cause, then", hyp)


class DebugCleanupTest(unittest.TestCase):
    """AC: debug entfernt seine getaggten Logs am Ende und hinterlässt einen
    Regressionstest; fehlt die Teststelle dafür, ist das ein eigener Befund.
    Widerlegt, wenn nach dem Lauf noch ein Log-Tag im Code steht."""

    def test_every_probe_is_tagged(self):
        probe = part(DEBUG, "### 5. Measure")
        self.assertIn("`[DEBUG-<tag>]`", probe)
        self.assertIn("Every measurement point carries the tag", probe)

    def test_cleanup_greps_tag_to_zero(self):
        clean = part(DEBUG, "### 7. Clean up")
        self.assertIn("`grep -rn \"DEBUG-<tag>\" .`", clean)
        self.assertIn("As long as the tag appears anywhere, you are not done.", clean)

    def test_regression_test_red_before_fix(self):
        reg = part(DEBUG, "### 6. Regression test")
        self.assertLess(reg.index("red"), reg.index("Then the fix"))

    def test_early_stop_cleans_up_or_names_leftovers(self):
        # Review PR #7, A2: Im Lauf B blieb /tmp/debug-a4f2/loop.py nach NEEDS_CONTEXT
        # liegen; „Wegwerf-Gerüste löschen“ stand nur in Schritt 7, den ein früher Stopp nie erreicht.
        rule = ("If you stop before step 7 (`NEEDS_CONTEXT`, `BLOCKED`), you still clean up: "
                "You delete measurement points and throwaway harnesses, also outside the repo, or you name "
                "in the result every path that remains, and why.")
        self.assertIn(rule, part(DEBUG, "### 7. Clean up"))
        self.assertIn("Before stopping, step 7 applies.", part(DEBUG, "### 2. Build a red loop"))
        self.assertIn("**Left behind:**", section(read(DEBUG), "Ergebnis"))

    def test_missing_seam_is_a_finding(self):
        self.assertIn("If there is no test seam that hits the bug the way it arises, that is "
                      "a finding of its own", part(DEBUG, "### 6. Regression test"))

    def test_fix_has_same_guardrails_as_implement(self):
        # Pre-Push-Review: implement schickt nach 3 Versuchen zu debug; ohne
        # diese Regeln stünde dort das in Hand-Durchlauf D geschlossene Loch offen.
        reg = part(DEBUG, "### 6. Regression test")
        self.assertIn("The fix is subject to the same limits as in `/slickfab:implement`:", reg)
        for item in ("auth and permissions", "destructive migrations", "deletions", "deploys",
                     "secrets", "anything a revert does not bring back"):
            self.assertIn(item, reg)
        self.assertIn("If an existing test is in the way, you do not change it; you stop "
                      "and report it", reg)
        self.assertIn("no skipping", reg)

    def test_return_to_hypotheses_is_capped(self):
        # Pre-Push-Review: ohne Deckel kreist debug zwischen Hypothesen und Korrektur.
        reg = part(DEBUG, "### 6. Regression test")
        self.assertIn("You go back to step 4 at most once. If three fixes fail again after that, "
                      "you stop and report `BLOCKED`", reg)

    def test_result_names_why_not_caught_and_guard(self):
        result = section(read(DEBUG), "Ergebnis")
        for field in ("**Why not caught:**", "**Recurrence guard:**",
                      "**Regression test:**", "**Debug tag removed:**"):
            self.assertIn(field, result)


HANDOFF = "skills/handoff/SKILL.md"


class HandoffTest(unittest.TestCase):
    """AC: handoff enthält alle 5 Punkte und leitet keine Freigabe aus dem
    Gespräch ab, die nicht am Ticket steht. Widerlegt, wenn die Übergabe eine
    Freigabe nennt, die nirgends dauerhaft dokumentiert ist."""

    # Die fünf Punkte aus dem Ticket, in dieser Reihenfolge.
    POINTS = ("**1. Scope and decisions**", "**2. Ticket state**",
              "**3. Files and working tree**", "**4. Check commands with result**",
              "**5. Open approvals**")

    def setUp(self):
        self.write = part(HANDOFF, "### 3. Write the handoff")

    def test_template_has_five_points_in_order(self):
        positions = [self.write.find(p) for p in self.POINTS]
        for point, pos in zip(self.POINTS, positions):
            self.assertNotEqual(pos, -1, point)
        self.assertEqual(positions, sorted(positions))

    def test_no_approval_from_conversation(self):
        rule = part(HANDOFF, "### 2. Gather the state")
        self.assertIn("You name an approval only if it is documented permanently", rule)
        self.assertIn("What was promised in the conversation but is not recorded anywhere permanently "
                      "is not an approval", rule)

    def test_template_asks_for_link_to_granted_approval(self):
        # Mutationsprobe: „Erteilt (auch im Gespräch)“ überlebte ohne diesen Test.
        self.assertIn("- Documented as granted: <link> or “none”", self.write)

    def test_checks_are_run_now(self):
        self.assertIn("You run the check commands now", part(HANDOFF, "### 2. Gather the state"))

    def test_posted_as_ticket_comment_with_references(self):
        post = part(HANDOFF, "### 4. Post it on the ticket")
        self.assertIn("as a comment on the ticket", post)
        self.assertIn("References instead of copies", self.write)


class RuleSentencesTest(unittest.TestCase):
    """Review PR #7, R1: Die Tests prüften Stichworte. Wer eine Regel strich
    oder ihre Bedingung abschwächte, blieb grün (29 von 29 Mutationen überlebten).
    Hier steht je Regel der ganze Satz an seiner Stelle; Streichen, Abschwächen
    oder Verschieben wird rot. Am schwersten wiegen die Bedingungen der
    Ausnahmen: Freigabe durch den Menschen, am Ticket, für genau diesen Test oder
    Punkt."""

    # (Datei, '### <Anfang>', Satz)
    SENTENCES = (
        # Freigabe-Bedingungen der Ausnahmen
        (IMPLEMENT, "### 3. Per criterion",
         "Whether an existing test may go is only settled once the human has recorded it on the ticket. "
         "With this approval, you change exactly this test and name it under “Änderungen”."),
        (IMPLEMENT, "### 5. Stop list",
         "This applies even if the ticket explicitly demands it; the approval for it is given by a human "
         "for exactly this point, and it is recorded on the ticket afterwards."),
        (DEBUG, "### 6. Regression test", "It is only built with an approval on the ticket."),
        (IMPLEMENT, "### 6. Whole suite", "A promise in the conversation is not enough."),
        (HANDOFF, "### 2. Gather the state", "You do not record it as granted yourself."),
        # Der Schritt endet erst mit dem Ergebnis (Kommentar am Ticket)
        (IMPLEMENT, "### 8. Wrap-up",
         "The step only ends with the “Ergebnis implement” (below); a review report, a "
         "test output or an open pull request without this result is not an end."),
        # Nicht mergen
        (IMPLEMENT, "### 7. Pull request",
         "Push the branch and open a pull request against the main branch. Do not merge."),
        (DEBUG, "### 8. Why not caught",
         "otherwise you open a pull request against the main branch, do not merge."),
        # Voraussetzungen und Stopps in implement
        (IMPLEMENT, "### 1. Check the precondition",
         "- If the ticket is not in `Todo` or `In Progress`, it is not approved for building: "
         "stop and say so."),
        (IMPLEMENT, "### 1. Check the precondition",
         "- If someone else's changes are open in the working tree, stop and say so. You do not move or "
         "hide anyone else's work."),
        (IMPLEMENT, "### 5. Stop list", "Before each change, check if it touches one of these points:"),
        (IMPLEMENT, "### 5. Stop list",
         "When you stop (rule 4, stop list, test in the way), you write a comment on the ticket with "
         "the reason and the state so far, and set `slickfab:needs-human`."),
        # Test-Disziplin in implement
        (IMPLEMENT, "### 3. Per criterion",
         "If it is green right away, the criterion is already met or the test checks nothing: clear that up "
         "before you continue."),
        (IMPLEMENT, "### 3. Per criterion",
         "no new suppressions (`@ts-ignore`, `eslint-disable`, `noqa`)."),
        (IMPLEMENT, "### 3. Per criterion",
         "| “The test is flaky, I'll set it to skip for a moment.” | A skipped test is a "
         "deleted test that nobody notices. Report it. |"),
        (IMPLEMENT, "### 4. Deviations",
         "- **Rule 1, bug:** Existing code does not do what it should and gets in the way of your criterion "
         "(wrong query, logic error, broken check). You fix it with its own red and green run."),
        (IMPLEMENT, "### 6. Whole suite", "Record command and result. Red means not done."),
        # debug
        (DEBUG, "### 2. Build a red loop",
         "| “I can't reproduce it, but this change does no harm.” | A fix without a "
         "red command is a guess. Report, don't guess. |"),
        (DEBUG, "### 6. Regression test",
         "If an existing test is in the way, you do not change it; you stop and report it "
         "(status `BLOCKED`), even if you are sure that it is wrong."),
        (DEBUG, "### 6. Regression test",
         "You do not write a shallow test that only pretends; you name which test seam is missing and why."),
        (DEBUG, "### 7. Clean up",
         "- Delete throwaway harnesses and helper files that do not belong to the regression test."),
        (DEBUG, "### 8. Why not caught",
         "put it forward as a proposal (for `/slickfab:retro`), instead of building it in unasked."),
        # handoff
        (HANDOFF, "### 2. Gather the state",
         "You run the check commands now and note command and result; a result from an hour ago "
         "is no result."),
        (HANDOFF, "### 2. Gather the state",
         "| “It was clearly meant that way.” | A derived approval is a decision that nobody "
         "made. |"),
        (HANDOFF, "### 3. Write the handoff",
         "You replace secrets (keys, passwords, personal data) with `<REDACTED>`."),
        (HANDOFF, "### 4. Post it on the ticket", "You do not change the ticket's status."),
        (HANDOFF, "### 4. Post it on the ticket",
         "If the tracker is unreachable, you show the handoff in full in the chat and say so; "
         "you create no handoff file in the repo."),
    )

    def test_rule_sentences_in_place(self):
        for rel, scope, sentence in self.SENTENCES:
            with self.subTest(file=rel, scope=scope, satz=sentence[:50]):
                text = part(rel, scope)
                self.assertTrue(text, "%s: Abschnitt '%s' fehlt" % (rel, scope))
                self.assertIn(sentence, text)


if __name__ == "__main__":
    unittest.main()
