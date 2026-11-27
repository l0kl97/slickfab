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


class ImplementStandaloneTest(StandaloneStepMixin, unittest.TestCase):
    step = "implement"


class DebugStandaloneTest(StandaloneStepMixin, unittest.TestCase):
    step = "debug"


class HandoffStandaloneTest(StandaloneStepMixin, unittest.TestCase):
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
        self.assertIn("Gibt es ein Ticket und ist der Tracker nicht erreichbar, gilt der Vertrag "
                      "„Zugang“: melden und aufhören, keine Datei als Ersatz.",
                      part(DEBUG, "### 1. Voraussetzung"))

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
    ANCHOR = ("Prüfbefehle nimmst du nur aus `.slickrails/config.sh` oder `.slickfab/config`; "
              "du rätst keine aus `package.json`, `Makefile` oder der Gewohnheit.")
    MISSING = "Fehlt ein Prüfbefehl, sagst du, welcher, und dass du ihn nicht ausführen kannst."

    def test_steps_embed_config_contract(self):
        for step in STEPS:
            embedded = blocks(read("skills/%s/SKILL.md" % step))
            for name in self.CONFIG_BLOCKS:
                with self.subTest(step=step, block=name):
                    self.assertIn(name, embedded)

    def test_steps_do_not_guess_check_commands(self):
        for step in STEPS:
            pre = part("skills/%s/SKILL.md" % step, "### 1. Voraussetzung")
            with self.subTest(step=step):
                self.assertIn(self.ANCHOR, pre)
                self.assertIn(self.MISSING, pre)


IMPLEMENT = "skills/implement/SKILL.md"


class ImplementRedGreenTest(unittest.TestCase):
    """AC: implement zeigt je Kriterium den roten und den grünen Lauf mit Befehl
    und Ausgabe und lässt am Ende die ganze Suite laufen. Widerlegt, wenn im
    PR-Text für ein Kriterium der rote Lauf fehlt."""

    def test_each_criterion_red_before_code(self):
        loop = part(IMPLEMENT, "### 3. Je Kriterium")
        self.assertIn("Ohne roten Lauf kein Produktionscode für dieses Kriterium.", loop)
        self.assertIn("Befehl und Ausgabe", loop)
        self.assertIn("aus dem erwarteten Grund rot", loop)
        self.assertLess(loop.index("**Rot:**"), loop.index("**Grün:**"))

    def test_whole_suite_at_the_end(self):
        suite = part(IMPLEMENT, "### 6. Ganze Suite")
        self.assertIn("`CHECK_TEST`", suite)
        self.assertIn("die ganze Suite", suite)

    def test_pr_text_has_red_and_green_per_criterion(self):
        pr = part(IMPLEMENT, "### 7. Pull Request")
        self.assertRegex(pr, r"- K1 .*\n\s+- rot: `<Befehl>` → <Ausgabe")
        self.assertRegex(pr, r"\n\s+- grün: `<Befehl>` → <Ausgabe")
        self.assertIn("Fehlt für ein Kriterium der rote Lauf, ist der Pull Request nicht fertig.", pr)


class ImplementKnowsReviewMutationRuleTest(unittest.TestCase):
    """Hand-Durchlauf, Befund 4: Der Umsetzer kannte eine Lücke
    aus einem früheren Review-Kommentar und ließ sie offen, weil das Ticket sie nicht
    nannte; review machte daraus REWORK. implement nennt die Mutationsregel des Reviews."""

    def test_every_changed_behaviour_needs_a_test_even_if_ticket_is_silent(self):
        rule = part(IMPLEMENT, "### 2. Kriterien in Tests")
        self.assertIn("Jedes Verhalten, das dein Diff einführt oder ändert, braucht einen Test, "
                      "auch wenn das Ticket es nicht nennt.", rule)
        self.assertIn("/slickfab:review", rule)

    def test_known_gap_from_earlier_review_is_closed_or_justified(self):
        rule = part(IMPLEMENT, "### 2. Kriterien in Tests")
        self.assertIn("Eine bekannte Lücke aus einem früheren Review-Kommentar am Ticket oder am "
                      "Pull Request schließt du mit rotem und grünem Lauf, oder du begründest im "
                      "Pull Request unter „Nicht angefasst“ ausdrücklich, warum sie offen bleibt.", rule)
        # Die Review-Kommentare liest implement schon in der Voraussetzung.
        self.assertIn("Review-Kommentare", part(IMPLEMENT, "### 1. Voraussetzung"))


class ImplementKeepsTestsTest(unittest.TestCase):
    """AC: implement schwächt keine bestehenden Tests ab (kein Überspringen,
    keine gelöschten Assertions, keine gesenkten Schwellen). Widerlegt, wenn
    im Fall „bestehender Test steht im Weg“ der Test verändert statt gemeldet wird."""

    def setUp(self):
        self.loop = part(IMPLEMENT, "### 3. Je Kriterium")

    def test_rule_names_the_three_weakenings(self):
        self.assertIn("Bestehende Tests schwächst du nicht ab, um grün zu werden:", self.loop)
        for way in ("kein Überspringen", "keine gelöschten oder gelockerten Assertions",
                    "keine gesenkten Schwellen"):
            self.assertIn(way, self.loop)

    def test_blocking_test_is_reported_not_changed(self):
        self.assertIn("Steht ein bestehender Test im Weg, änderst du ihn nicht, sondern hörst auf "
                      "und meldest ihn", self.loop)
        self.assertIn("`BLOCKED`", self.loop)

    def test_no_exception_when_ticket_changes_behaviour(self):
        # Hand-Durchlauf D: Mit der Ausnahme „verlangt das Ticket ausdrücklich …“
        # schrieb der Agent den im Weg stehenden Test um und meldete ihn nicht.
        self.assertIn("Das gilt auch, wenn das Ticket das Verhalten, das der Test festhält, "
                      "ausdrücklich ändern will", self.loop)
        self.assertNotIn("ist die Änderung dieses Tests Teil des Kriteriums", self.loop)
        self.assertIn("„Das Ticket verlangt doch genau dieses neue Verhalten.“", self.loop)

    def test_excuses_are_answered(self):
        self.assertIn("| Ausrede | Realität |", self.loop)
        self.assertIn("„Der alte Test ist sowieso falsch.“", self.loop)


class ImplementStopsTest(unittest.TestCase):
    """AC: Trifft implement auf einen Punkt der Stopp-Liste oder eine
    Architekturfrage, hält er an und meldet BLOCKED mit Begründung. Widerlegt,
    wenn im Fall „Ticket verlangt destruktive Migration“ ohne Rückfrage gebaut wird."""

    STOP_LIST = ("Auth und Berechtigungen", "destruktive Migrationen", "Zahlungen",
                 "Löschungen", "Deploys", "Secrets", "alles, was ein Revert nicht zurückholt")

    def test_stop_list_complete(self):
        stop = part(IMPLEMENT, "### 5. Stopp-Liste")
        for item in self.STOP_LIST:
            self.assertIn(item, stop)

    def test_stop_list_halts_even_when_ticket_asks(self):
        stop = part(IMPLEMENT, "### 5. Stopp-Liste")
        self.assertIn("hörst du auf, bevor du ihn baust, und meldest `BLOCKED` mit Begründung", stop)
        self.assertIn("Das gilt auch, wenn das Ticket es ausdrücklich verlangt", stop)

    def test_stop_list_checked_before_first_test(self):
        self.assertIn("Prüf vor dem ersten Test, ob das Ticket die Stopp-Liste (Schritt 5) berührt.",
                      part(IMPLEMENT, "### 1. Voraussetzung"))

    def test_architecture_question_stops(self):
        dev = part(IMPLEMENT, "### 4. Abweichungen")
        self.assertIn("**Regel 4, Architekturfrage:** Hier hörst du auf und meldest `BLOCKED` mit Begründung.", dev)

    def test_small_deviations_fixed_and_named(self):
        dev = part(IMPLEMENT, "### 4. Abweichungen")
        for rule in ("**Regel 1, Fehler:**", "**Regel 2, fehlende kritische Funktion:**",
                     "**Regel 3, Blocker:**"):
            self.assertIn(rule, dev)
        self.assertIn("Die Stopp-Liste geht den Regeln 1–3 vor.", dev)


class ImplementAttemptCapTest(unittest.TestCase):
    """AC: Nach 3 gescheiterten Fix-Versuchen an derselben Stelle stoppt
    implement. Widerlegt, wenn ein vierter Versuch startet."""

    def setUp(self):
        self.loop = part(IMPLEMENT, "### 3. Je Kriterium")

    def test_three_attempts_then_stop(self):
        self.assertIn("Nach 3 gescheiterten Fix-Versuchen an derselben Stelle hörst du auf. "
                      "Einen vierten Versuch startest du nicht.", self.loop)

    def test_attempt_is_defined_and_counted(self):
        self.assertIn("Ein Fix-Versuch ist eine Änderung am Produktionscode, nach der derselbe Test "
                      "wieder rot ist.", self.loop)
        self.assertIn("Versuch 1/3", self.loop)

    def test_stop_hands_over_to_debug(self):
        self.assertRegex(self.loop, r"vierten Versuch startest du nicht\.[^\n]*`BLOCKED`[^\n]*`/slickfab:debug")


class ImplementFinishesTest(unittest.TestCase):
    """Kommentar am Ticket (Master, 24.11.): Ein Umsetzer rief `/security-review`
    auf und beendete danach den Turn ohne PR. Ein Pflicht-Review ist ein
    Zwischenschritt; der Schritt endet erst mit dem Ergebnis."""

    def test_mandatory_review_is_intermediate(self):
        suite = part(IMPLEMENT, "### 6. Ganze Suite")
        self.assertIn("Ein Pflicht-Review vor dem Pull Request (etwa `/security-review`) ist ein "
                      "Zwischenschritt: Danach machst du mit Commit, Push und Pull Request weiter.", suite)

    def test_hooks_only_bypassed_with_documented_approval(self):
        # Pre-Push-Review: „außer der Mensch sagt es“ ließ eine Chat-Zusage gelten.
        suite = part(IMPLEMENT, "### 6. Ganze Suite")
        self.assertIn("Hooks umgehst du nie (`--no-verify` und Ähnliches), außer der Mensch hat es "
                      "für genau diesen Push am Ticket festgehalten; dann steht der Grund im Commit.", suite)
        self.assertNotIn("außer der Mensch sagt es ausdrücklich", suite)

    def test_ticket_to_in_review_and_result_last(self):
        done = part(IMPLEMENT, "### 8. Abschluss")
        self.assertIn("`In Review`", done)
        self.assertIn("Der Schritt endet erst mit dem „Ergebnis implement“", done)


class NextStepAlsoWhenBlockedTest(unittest.TestCase):
    """AC 1, Hand-Durchlauf A: Bei BLOCKED nannte implement den nächsten Schritt
    nur im Fließtext. Die Zeile steht in jedem Ausgang."""

    def test_next_step_line_never_missing(self):
        for step in STEPS:
            with self.subTest(step=step):
                self.assertIn("Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei `BLOCKED` "
                              "oder `NEEDS_CONTEXT`.", section(read("skills/%s/SKILL.md" % step), "Ergebnis"))


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
        pr = part(IMPLEMENT, "### 7. Pull Request")
        positions = [pr.find("\n" + s + "\n") for s in self.SECTIONS]
        for name, pos in zip(self.SECTIONS, positions):
            self.assertNotEqual(pos, -1, name)
        self.assertEqual(positions, sorted(positions))

    def test_door_names_both_values(self):
        self.assertIn("`one-way` | `two-way`", part(IMPLEMENT, "### 7. Pull Request"))

    def test_empty_sections_stay(self):
        self.assertIn("Jeder Abschnitt steht im Text, auch wenn er leer ist; dann steht darunter „keine“.",
                      part(IMPLEMENT, "### 7. Pull Request"))


DEBUG = "skills/debug/SKILL.md"


class DebugRedLoopFirstTest(unittest.TestCase):
    """AC: debug beginnt keine Ursachensuche ohne einen Befehl, der rot wird.
    Widerlegt, wenn im Fall ohne reproduzierbaren Fehler eine Korrektur
    vorgeschlagen wird."""

    def setUp(self):
        self.loop = part(DEBUG, "### 2. Rote Schleife")

    def test_red_command_gates_everything(self):
        self.assertIn("Ohne einen Befehl, der auf genau diesen Fehler rot wird, keine Ursachensuche "
                      "und keine Korrektur.", self.loop)
        self.assertIn("schon einmal ausgeführt", self.loop)

    def test_no_loop_means_stop_without_fix(self):
        self.assertIn("Gelingt dir kein roter Befehl, hörst du auf: Du nennst, was du versucht hast, "
                      "und fragst nach dem, was fehlt. Du schlägst keine Korrektur vor.", self.loop)
        self.assertIn("`NEEDS_CONTEXT`", self.loop)

    def test_loop_comes_before_hypotheses(self):
        text = section(read(DEBUG), "Ablauf")
        self.assertLess(text.index("### 2. Rote Schleife"), text.index("### 4. Hypothesen"))

    def test_hypotheses_are_falsifiable_and_three_to_five(self):
        hyp = part(DEBUG, "### 4. Hypothesen")
        self.assertIn("3 bis 5", hyp)
        self.assertIn("Wenn <X> die Ursache ist, dann", hyp)


class DebugCleanupTest(unittest.TestCase):
    """AC: debug entfernt seine getaggten Logs am Ende und hinterlässt einen
    Regressionstest; fehlt die Teststelle dafür, ist das ein eigener Befund.
    Widerlegt, wenn nach dem Lauf noch ein Log-Tag im Code steht."""

    def test_every_probe_is_tagged(self):
        probe = part(DEBUG, "### 5. Messen")
        self.assertIn("`[DEBUG-<tag>]`", probe)
        self.assertIn("Jeder Messpunkt trägt den Tag", probe)

    def test_cleanup_greps_tag_to_zero(self):
        clean = part(DEBUG, "### 7. Aufräumen")
        self.assertIn("`grep -rn \"DEBUG-<tag>\" .`", clean)
        self.assertIn("Solange der Tag irgendwo steht, bist du nicht fertig.", clean)

    def test_regression_test_red_before_fix(self):
        reg = part(DEBUG, "### 6. Regressionstest")
        self.assertLess(reg.index("rot"), reg.index("Dann die Korrektur"))

    def test_early_stop_cleans_up_or_names_leftovers(self):
        # Review PR #7, A2: Im Lauf B blieb /tmp/debug-a4f2/loop.py nach NEEDS_CONTEXT
        # liegen; „Wegwerf-Gerüste löschen“ stand nur in Schritt 7, den ein früher Stopp nie erreicht.
        rule = ("Hörst du vor Schritt 7 auf (`NEEDS_CONTEXT`, `BLOCKED`), räumst du trotzdem auf: "
                "Messpunkte und Wegwerf-Gerüste, auch außerhalb des Repos, löschst du, oder du nennst "
                "im Ergebnis jeden Pfad, der bleibt, und warum.")
        self.assertIn(rule, part(DEBUG, "### 7. Aufräumen"))
        self.assertIn("Vor dem Aufhören gilt Schritt 7.", part(DEBUG, "### 2. Rote Schleife"))
        self.assertIn("**Liegen geblieben:**", section(read(DEBUG), "Ergebnis"))

    def test_missing_seam_is_a_finding(self):
        self.assertIn("Fehlt eine Teststelle, die den Fehler so trifft, wie er entsteht, ist das "
                      "ein eigener Befund", part(DEBUG, "### 6. Regressionstest"))

    def test_fix_has_same_guardrails_as_implement(self):
        # Pre-Push-Review: implement schickt nach 3 Versuchen zu debug; ohne
        # diese Regeln stünde dort das in Hand-Durchlauf D geschlossene Loch offen.
        reg = part(DEBUG, "### 6. Regressionstest")
        self.assertIn("Für die Korrektur gelten dieselben Grenzen wie in `/slickfab:implement`:", reg)
        for item in ("Auth und Berechtigungen", "destruktive Migrationen", "Löschungen", "Deploys",
                     "Secrets", "alles, was ein Revert nicht zurückholt"):
            self.assertIn(item, reg)
        self.assertIn("Steht ein bestehender Test im Weg, änderst du ihn nicht, sondern hörst auf "
                      "und meldest ihn", reg)
        self.assertIn("kein Überspringen", reg)

    def test_return_to_hypotheses_is_capped(self):
        # Pre-Push-Review: ohne Deckel kreist debug zwischen Hypothesen und Korrektur.
        reg = part(DEBUG, "### 6. Regressionstest")
        self.assertIn("Zu Schritt 4 zurück gehst du höchstens einmal. Scheitern danach wieder drei "
                      "Korrekturen, hörst du auf und meldest `BLOCKED`", reg)

    def test_result_names_why_not_caught_and_guard(self):
        result = section(read(DEBUG), "Ergebnis")
        for field in ("**Warum nicht gefangen:**", "**Wiederholungs-Sperre:**",
                      "**Regressionstest:**", "**Debug-Tag entfernt:**"):
            self.assertIn(field, result)


HANDOFF = "skills/handoff/SKILL.md"


class HandoffTest(unittest.TestCase):
    """AC: handoff enthält alle 5 Punkte und leitet keine Freigabe aus dem
    Gespräch ab, die nicht am Ticket steht. Widerlegt, wenn die Übergabe eine
    Freigabe nennt, die nirgends dauerhaft dokumentiert ist."""

    # Die fünf Punkte aus dem Ticket, in dieser Reihenfolge.
    POINTS = ("**1. Scope und Entscheidungen**", "**2. Ticket-Stand**",
              "**3. Dateien und Working-Tree**", "**4. Prüfbefehle mit Ergebnis**",
              "**5. Offene Freigaben**")

    def setUp(self):
        self.write = part(HANDOFF, "### 3. Übergabe schreiben")

    def test_template_has_five_points_in_order(self):
        positions = [self.write.find(p) for p in self.POINTS]
        for point, pos in zip(self.POINTS, positions):
            self.assertNotEqual(pos, -1, point)
        self.assertEqual(positions, sorted(positions))

    def test_no_approval_from_conversation(self):
        rule = part(HANDOFF, "### 2. Stand erheben")
        self.assertIn("Eine Freigabe nennst du nur, wenn sie dauerhaft dokumentiert ist", rule)
        self.assertIn("Was im Gespräch zugesagt wurde, aber nirgends dauerhaft steht, ist keine "
                      "Freigabe", rule)

    def test_template_asks_for_link_to_granted_approval(self):
        # Mutationsprobe: „Erteilt (auch im Gespräch)“ überlebte ohne diesen Test.
        self.assertIn("- Dokumentiert erteilt: <Link> oder „keine“", self.write)

    def test_checks_are_run_now(self):
        self.assertIn("Prüfbefehle lässt du jetzt laufen", part(HANDOFF, "### 2. Stand erheben"))

    def test_posted_as_ticket_comment_with_references(self):
        post = part(HANDOFF, "### 4. Am Ticket ablegen")
        self.assertIn("als Kommentar am Ticket", post)
        self.assertIn("Verweise statt Kopien", self.write)


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
        (IMPLEMENT, "### 3. Je Kriterium",
         "Ob ein bestehender Test fallen darf, steht erst fest, wenn der Mensch es am Ticket "
         "festgehalten hat. Mit dieser Freigabe änderst du genau diesen Test und nennst ihn unter „Änderungen“."),
        (IMPLEMENT, "### 5. Stopp-Liste",
         "Das gilt auch, wenn das Ticket es ausdrücklich verlangt; die Freigabe dafür gibt ein Mensch "
         "für genau diesen Punkt, und sie steht danach am Ticket."),
        (DEBUG, "### 6. Regressionstest", "Gebaut wird erst mit einer Freigabe am Ticket."),
        (IMPLEMENT, "### 6. Ganze Suite", "Eine Zusage im Gespräch reicht nicht."),
        (HANDOFF, "### 2. Stand erheben", "Du hältst sie nicht selbst als erteilt fest."),
        # Der Schritt endet erst mit dem Ergebnis (Kommentar am Ticket)
        (IMPLEMENT, "### 8. Abschluss",
         "Der Schritt endet erst mit dem „Ergebnis implement“ (unten); ein Review-Bericht, eine "
         "Testausgabe oder ein offener Pull Request ohne dieses Ergebnis ist kein Ende."),
        # Nicht mergen
        (IMPLEMENT, "### 7. Pull Request",
         "Push den Branch und öffne einen Pull Request gegen den Hauptzweig. Nicht mergen."),
        (DEBUG, "### 8. Warum nicht gefangen",
         "sonst öffnest du einen Pull Request gegen den Hauptzweig, nicht mergen."),
        # Voraussetzungen und Stopps in implement
        (IMPLEMENT, "### 1. Voraussetzung",
         "- Steht das Ticket nicht auf `Todo` oder `In Progress`, ist es nicht zum Bauen freigegeben: "
         "hör auf und sag das."),
        (IMPLEMENT, "### 1. Voraussetzung",
         "- Sind im Arbeitsbaum fremde Änderungen offen, hör auf und sag es. Du verschiebst oder "
         "versteckst keine fremde Arbeit."),
        (IMPLEMENT, "### 5. Stopp-Liste", "Prüf vor jeder Änderung, ob sie einen dieser Punkte berührt:"),
        (IMPLEMENT, "### 5. Stopp-Liste",
         "Beim Anhalten (Regel 4, Stopp-Liste, Test im Weg) schreibst du einen Kommentar am Ticket mit "
         "Grund und bisherigem Stand und setzt `slickfab:needs-human`."),
        # Test-Disziplin in implement
        (IMPLEMENT, "### 3. Je Kriterium",
         "Ist er sofort grün, ist das Kriterium schon erfüllt oder der Test prüft nichts: klär das, "
         "bevor du weitermachst."),
        (IMPLEMENT, "### 3. Je Kriterium",
         "keine neuen Unterdrückungen (`@ts-ignore`, `eslint-disable`, `noqa`)."),
        (IMPLEMENT, "### 3. Je Kriterium",
         "| „Der Test ist flaky, ich setze ihn kurz auf skip.“ | Ein übersprungener Test ist ein "
         "gelöschter Test, den niemand bemerkt. Melden. |"),
        (IMPLEMENT, "### 4. Abweichungen",
         "- **Regel 1, Fehler:** Bestehender Code tut nicht, was er soll, und hindert dein Kriterium "
         "(falsche Abfrage, Logikfehler, kaputte Prüfung). Du behebst ihn mit eigenem rotem und grünem Lauf."),
        (IMPLEMENT, "### 6. Ganze Suite", "Halte Befehl und Ergebnis fest. Rot heißt nicht fertig."),
        # debug
        (DEBUG, "### 2. Rote Schleife",
         "| „Ich kann es nicht nachstellen, aber diese Änderung schadet nicht.“ | Eine Korrektur ohne "
         "roten Befehl ist geraten. Melden, nicht raten. |"),
        (DEBUG, "### 6. Regressionstest",
         "Steht ein bestehender Test im Weg, änderst du ihn nicht, sondern hörst auf und meldest ihn "
         "(Status `BLOCKED`), auch wenn du sicher bist, dass er falsch ist."),
        (DEBUG, "### 6. Regressionstest",
         "Du schreibst keinen flachen Test, der nur so tut, sondern nennst, welche Teststelle fehlt und warum."),
        (DEBUG, "### 7. Aufräumen",
         "- Lösch Wegwerf-Gerüste und Hilfsdateien, die nicht zum Regressionstest gehören."),
        (DEBUG, "### 8. Warum nicht gefangen",
         "schlag sie als Vorschlag vor (für `/slickfab:retro`), statt sie ungefragt einzubauen."),
        # handoff
        (HANDOFF, "### 2. Stand erheben",
         "Prüfbefehle lässt du jetzt laufen und notierst Befehl und Ergebnis; ein Ergebnis von vor einer "
         "Stunde ist keins."),
        (HANDOFF, "### 2. Stand erheben",
         "| „Das war doch klar gemeint.“ | Eine abgeleitete Freigabe ist eine Entscheidung, die niemand "
         "getroffen hat. |"),
        (HANDOFF, "### 3. Übergabe schreiben",
         "Geheimnisse (Schlüssel, Passwörter, persönliche Daten) ersetzt du durch `<REDACTED>`."),
        (HANDOFF, "### 4. Am Ticket ablegen", "Den Status des Tickets änderst du nicht."),
        (HANDOFF, "### 4. Am Ticket ablegen",
         "Ist der Tracker nicht erreichbar, zeigst du die Übergabe vollständig im Chat und sagst das; "
         "du legst keine Übergabe-Datei im Repo an."),
    )

    def test_rule_sentences_in_place(self):
        for rel, scope, sentence in self.SENTENCES:
            with self.subTest(file=rel, scope=scope, satz=sentence[:50]):
                text = part(rel, scope)
                self.assertTrue(text, "%s: Abschnitt '%s' fehlt" % (rel, scope))
                self.assertIn(sentence, text)


if __name__ == "__main__":
    unittest.main()
