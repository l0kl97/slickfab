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

    def setUp(self):
        self.text = read("skills/%s/SKILL.md" % self.step)

    def test_checks_its_precondition(self):
        self.assertIn("### 1. Voraussetzung prüfen", section(self.text, "Ablauf"))

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

    def test_two_shapes_ui_variants_and_logic_script(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("?variant=", flow)
        self.assertIn("Wegwerfskript", flow)

    def test_always_on_throwaway_branch(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("prototype/", flow)
        self.assertIn("Wegwerf-Branch", flow)


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
                         {"Ergebnis prototype", "Ergebnis prototype (wartet auf Urteil)",
                          "Ergebnis prototype (Rückfrage Branch)", "Ergebnis prototype (Halt)"})

    def test_every_template_ends_with_next_step_and_status(self):
        expected = {"Ergebnis prototype": ("DONE",),
                    "Ergebnis prototype (wartet auf Urteil)": ("NEEDS_CONTEXT",),
                    "Ergebnis prototype (Rückfrage Branch)": ("NEEDS_CONTEXT",),
                    "Ergebnis prototype (Halt)": ("NEEDS_CONTEXT", "BLOCKED")}
        for name, block in self.templates.items():
            with self.subTest(template=name):
                lines = block.strip().splitlines()
                self.assertTrue(lines[-1].startswith("SLICKFAB-STATUS: "), lines[-1])
                self.assertEqual(tuple(re.findall(r"[A-Z_]{4,}", lines[-1][len("SLICKFAB-STATUS: "):])),
                                 expected[name])
                self.assertTrue(any(l.startswith("Nächster Schritt: ") for l in lines[:-1]))

    def test_waiting_template_says_how_to_continue_and_where_the_repo_stands(self):
        waiting = self.templates["Ergebnis prototype (wartet auf Urteil)"]
        self.assertIn("**Start:**", waiting)
        self.assertIn("**Vergleichen:**", waiting)
        self.assertIn("**Repo steht auf:** prototype/<slug> (Prototyp committet, angelegt von <Branch>) "
                      "— zurück mit `git switch <Branch>`", waiting)
        # Pre-Push-Review: Die neue Session braucht Wegwerf- und Ausgangs-Branch im Argument.
        self.assertIn("Nächster Schritt: Urteil hier geben, dann hält prototype es fest; in einer "
                      "neuen Session `/slickfab:prototype Frage: <…> Urteil: <…> "
                      "Branch: prototype/<slug> von <Branch>`", waiting)

    def test_step_five_commits_before_waiting_and_uses_the_template(self):
        five = subsection(section(self.text, "Ablauf"), "5.")
        self.assertIn("Bevor du vorführst, committe den Prototyp auf dem Wegwerf-Branch; der "
                      "Commit-Text nennt die Frage und den Ausgangs-Branch", five)
        self.assertIn("Vorlage „wartet auf Urteil“", five)
        self.assertIn("Endet die Sitzung vor dem Urteil", five)

    def test_step_six_continues_with_verdict_from_argument(self):
        six = subsection(section(self.text, "Ablauf"), "6.")
        self.assertIn("Kommt das Urteil in einer neuen Session", six)
        # Pre-Push-Review: sonst Commit auf main und Rückkehr auf einen geratenen Branch.
        self.assertIn("wechsle auf den Wegwerf-Branch aus dem Argument", six)
        self.assertIn("den Ausgangs-Branch nimmst du aus dem Argument oder dem Commit-Text des "
                      "Prototyps", six)
        self.assertIn("Fehlt einer der beiden oder gibt es den Wegwerf-Branch nicht, hör auf", six)
        # Pre-Push-Review 2: auch dieses Warten braucht eine Vorlage mit nächstem Schritt.
        self.assertIn("Vorlage „Rückfrage Branch“", six)
        self.assertIn("Du committest nie auf einem Branch, der nicht mit `prototype/` beginnt.", six)

    def test_branch_question_template_names_what_is_missing_and_the_command(self):
        ask = self.templates["Ergebnis prototype (Rückfrage Branch)"]
        self.assertIn("**Fehlt:** <Wegwerf-Branch | Ausgangs-Branch | `prototype/<slug>` gibt es nicht>", ask)
        self.assertIn("**Nichts geändert:** kein Commit, kein Branchwechsel", ask)
        self.assertIn("Nächster Schritt: `/slickfab:prototype Frage: <…> Urteil: <…> "
                      "Branch: prototype/<slug> von <Branch>`", ask)


class PrototypeHaltTest(unittest.TestCase):
    """Review PR #21, A3: Die Enden in Schritt 1 (keine Frage, Ein-Satz-Frage, offene Änderungen)
    hatten keine Vorlage mit nächstem Schritt und Marker."""

    def setUp(self):
        self.text = read("skills/prototype/SKILL.md")
        self.result = section(self.text, "Ergebnis")
        self.rows = set()
        for line in self.result.splitlines():
            cells = tuple(c.strip() for c in line.strip().strip("|").split("|"))
            if len(cells) == 4 and cells[0].startswith("Schritt "):
                self.rows.add(cells)

    def test_every_halt_has_a_row_with_next_step_and_status(self):
        self.assertEqual(self.rows, {
            ("Schritt 1", "keine Frage", "`/slickfab:prototype <Frage>`", "`NEEDS_CONTEXT`"),
            ("Schritt 1", "Frage mit einem Satz zu klären", "`/slickfab:grill <Frage>`", "`NEEDS_CONTEXT`"),
            ("Schritt 1", "offene Änderungen im Repo",
             "Mensch committet oder legt sie selbst beiseite, dann `/slickfab:prototype <Frage>` erneut",
             "`BLOCKED`"),
            # Review PR #21, A1: Commit in Schritt 5 nur auf prototype/.
            ("Schritt 5", "nicht auf `prototype/<slug>`",
             "Mensch prüft den Branch, dann `/slickfab:prototype <Frage>` erneut", "`BLOCKED`"),
        })

    def test_step_five_checks_the_branch_before_committing(self):
        five = subsection(section(self.text, "Ablauf"), "5.")
        self.assertIn("Prüf vor diesem Commit mit `git branch --show-current`, dass du auf "
                      "`prototype/<slug>` stehst. Sonst committest du nichts und endest mit der "
                      "Vorlage „Halt“.", five)

    def test_step_one_points_to_the_template(self):
        one = subsection(section(self.text, "Ablauf"), "1.")
        self.assertIn("Hörst du hier auf, endest du mit der Vorlage „Halt“ (unten).", one)

    def test_template_says_nothing_changed(self):
        self.assertIn("**Stand:** Repo auf <Branch>, kein Commit; <kein Branch angelegt | "
                      "uncommittete Prototyp-Dateien: …>", self.result)


class ChallengeStepTest(StandaloneStepMixin, unittest.TestCase):
    step = "challenge"

    def test_fresh_view_gets_only_the_spec(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("frischen Sub-Agent", flow)
        self.assertIn("nur die Spec", flow)

    def test_at_most_seven_objections_and_a_verdict(self):
        self.assertIn("höchstens 7 Einwände", self.text)
        for verdict in ("`bauen`", "`kleiner bauen`", "`nicht bauen`"):
            self.assertIn(verdict, self.text)

    def test_buildability_sorts_into_three_piles(self):
        for pile in ("schon beantwortet", "Kleinkram", "nur der Mensch"):
            self.assertIn(pile, self.text)

    def test_decomposition_check_stops_after_round_two(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("höchstens 2 Runden", flow)
        self.assertIn("nicht sinkt", flow)
        self.assertIn("keine dritte Runde", flow)


class TicketsStepTest(StandaloneStepMixin, unittest.TestCase):
    step = "tickets"

    def test_tracer_first_blocks_all_others(self):
        flow = section(self.text, "Ablauf")
        self.assertIn("Tracer", flow)
        self.assertIn("blockiert alle übrigen", flow)

    def test_file_overlap_gets_blocked_by_relation(self):
        self.assertIn("dieselbe Datei", section(self.text, "Ablauf"))
        self.assertIn("Blockiert-Relation", section(self.text, "Ablauf"))

    def test_rejects_deferral_phrases(self):
        flow = section(self.text, "Ablauf")
        for phrase in ("„v1“", "„vereinfacht“", "„Platzhalter“", "„wird später verdrahtet“"):
            self.assertIn(phrase, flow)

    def test_confirmation_and_duplicate_check_before_creating(self):
        flow = section(self.text, "Ablauf")
        confirm = flow.index("nummerierte Liste")
        dupes = flow.index("Dubletten")
        create = flow.index("### 7. Anlegen")
        self.assertLess(confirm, create)
        self.assertLess(dupes, create)

    def test_ticket_template_fields(self):
        for field in ("Widerlegt, wenn", "Verbraucht:", "Liefert:", "Betroffene Dateien",
                      "`door:one-way`", "Expand–Migrate–Contract"):
            self.assertIn(field, self.text)

    def test_decomposition_is_challenged_before_human_sees_it(self):
        self.assertIn("/slickfab:challenge", section(self.text, "Ablauf"))

    def test_question_ending_keeps_next_step_and_marker_outside_code_block(self):
        # Hand-Durchlauf, Befund 1: Bei einer Rückfrage (Dublette,
        # NEEDS_CONTEXT) fehlte „Nächster Schritt“, und der Marker stand in einem Codeblock.
        result = section(self.text, "Ergebnis")
        self.assertIn("Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei einer Rückfrage "
                      "(`NEEDS_CONTEXT`).", result)
        self.assertIn("Die Marker-Zeile ist die letzte Zeile deiner Antwort und steht außerhalb "
                      "jedes Codeblocks.", result)
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
        question = [t for t in self.result_templates() if "(Rückfrage)" in t][0]
        self.assertIn("fehlt die Spec oder steht eine Entscheidung noch nicht darin: "
                      "`/slickfab:spec [Spec-Issue]`", question)
        self.assertIn("fehlt die Prüfung: `/slickfab:challenge <Spec-Issue>`", question)
        self.assertIn("Frage zum Schnitt (Dublette, Liste wartet auf das Ja, Befunde offen nach Runde 2): "
                      "`/slickfab:tickets <Spec-Issue>` erneut", question)
        # Schritt 1 nennt dieselben Wege.
        pre = subsection(self.text, "1. Voraussetzung")
        self.assertIn("Fehlt es, empfiehl `/slickfab:spec`.", pre)
        self.assertIn("zuerst `/slickfab:spec <Spec-Issue>`", pre)

    def test_tracker_abort_while_creating_has_blocked_template(self):
        # Review PR #17, A1: Bricht der Tracker beim Anlegen ab, gab es keine Vorlage mit BLOCKED.
        aborted = [t for t in self.result_templates() if "(Abbruch)" in t]
        self.assertEqual(len(aborted), 1)
        lines = aborted[0].strip().splitlines()
        self.assertEqual(lines[-1], "SLICKFAB-STATUS: BLOCKED")
        self.assertTrue(any(l.startswith("Nächster Schritt: `/slickfab:") for l in lines[:-1]))
        self.assertIn("**Schon angelegt:**", aborted[0])
        self.assertIn("**Nicht angelegt:**", aborted[0])
        self.assertIn("**Fehlermeldung:**", aborted[0])
        main = [t for t in self.result_templates() if t.startswith("## Ergebnis tickets\n")][0]
        self.assertNotIn("BLOCKED", main)


STOP = re.compile(r"hör (hier |sofort )?auf|empfiehl|wartest du|legst du dem Menschen vor")


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
            if len(cells) == 4 and cells[0].startswith("Schritt "):
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
            ("Schritt 1", "`.slickfab/config` fehlt oder Tracker nicht erreichbar", "Ergebnis tickets (Abbruch)", "`BLOCKED`"),
            ("Schritt 1", "Spec-Issue fehlt", "Ergebnis tickets (Rückfrage)", "`NEEDS_CONTEXT`"),
            ("Schritt 1", "`challenge`-Kommentar fehlt", "Ergebnis tickets (Rückfrage)", "`NEEDS_CONTEXT`"),
            ("Schritt 1", "Entscheidung steht noch nicht in der Spec", "Ergebnis tickets (Rückfrage)", "`NEEDS_CONTEXT`"),
            ("Schritt 1", "letztes `challenge`-Urteil `nicht bauen`", "Ergebnis tickets (Rückfrage)", "`NEEDS_CONTEXT`"),
            ("Schritt 6", "Tracker antwortet bei der Dublettensuche mit einem Fehler", "Ergebnis tickets (Abbruch)", "`BLOCKED`"),
            ("Schritt 6", "Dublette, Liste wartet auf das Ja oder Befunde offen nach Runde 2", "Ergebnis tickets (Rückfrage)", "`NEEDS_CONTEXT`"),
            ("Schritt 7", "Tracker bricht beim Anlegen ab", "Ergebnis tickets (Abbruch)", "`BLOCKED`"),
            ("Schritt 7", "alle Tickets angelegt", "Ergebnis tickets", "`DONE` oder `DONE_WITH_CONCERNS`"),
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
        abort = self.templates["Ergebnis tickets (Abbruch)"]
        # Schritt 7 verweist beim Abbruch auf die Vorlage (überlebende Mutation, Rework 2).
        self.assertIn("(Vorlage „Abbruch“ unten, `BLOCKED`)", subsection(self.text, "7. Anlegen"))
        self.assertIn("**Wo:** Schritt 1 (Konfiguration oder Tracker) | Schritt 6 (Dublettensuche) "
                      "| Schritt 7 (beim Anlegen)", abort)
        self.assertIn("**Schon angelegt:** <IDs mit Titel und gesetzten Relationen> (in Schritt 1 und 6: keine)", abort)
        self.assertIn("Nächster Schritt: `/slickfab:tickets <Spec-Issue>` erneut, nachdem du "
                      "<`.slickfab/config` angelegt | den Tracker geprüft (Werkzeuge geladen, angemeldet, "
                      "Team und Projekt vorhanden)> hast", abort)


# Stellen im Ablauf, an denen tickets den Tracker anspricht (lesen, suchen, anlegen).
TRACKER_CALL = re.compile(r"Lies das Spec-Issue|Suche im Projekt|Sub-Issue der Spec, Status|Kommentar am Spec-Issue")


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
        self.assertIn("error response", section(self.text, "Vertrag"))
        self.assertIn("and stops", section(self.text, "Vertrag"))

    def test_steps_that_use_the_tracker(self):
        self.assertEqual(self.tracker_steps(), [1, 6, 7])

    def test_every_tracker_step_has_an_abort_row(self):
        for step in self.tracker_steps():
            with self.subTest(step=step):
                rows = [r for r in self.ending.rows if r[0] == "Schritt %d" % step
                        and "Tracker" in r[1] and r[2] == "Ergebnis tickets (Abbruch)" and r[3] == "`BLOCKED`"]
                self.assertTrue(rows, "Schritt %d spricht den Tracker an, hat aber keine Abbruch-Zeile" % step)

    def test_step_six_names_the_abort(self):
        self.assertIn("Antwortet der Tracker bei der Suche mit einem Fehler, hör auf (Vorlage „Abbruch“ "
                      "unten, `BLOCKED`).", subsection(self.text, "6. Zerlegung"))


class ChallengeNotBuildEndsWithCanceledTest(unittest.TestCase):
    """Review PR #19, A1: challenge nannte bei `nicht bauen` nur „endet die Planung hier“."""

    def test_next_step_names_canceled(self):
        self.assertIn("Lautet das Urteil `nicht bauen` und der Mensch stimmt zu, endet die Planung "
                      "hier: Der Mensch setzt die Spec auf `Canceled`.",
                      section(read("skills/challenge/SKILL.md"), "Nächster Schritt"))


class TicketsAbortFieldsTest(unittest.TestCase):
    """Review PR #19, A2: Die Abbruch-Vorlage gilt für Schritt 1, 6 und 7; zwei davon sind
    Fehlerantworten des Trackers, das Feld Fehlermeldung kannte nur Datei oder Schlüssel."""

    def setUp(self):
        ending = TicketsEveryEndingHasTemplateTest("test_expected_endings")
        ending.setUp()
        self.abort = ending.templates["Ergebnis tickets (Abbruch)"]

    def test_error_field_takes_tracker_errors(self):
        self.assertIn("**Fehlermeldung:** <wörtlich: fehlende Datei oder fehlender Schlüssel, oder "
                      "die Fehlerantwort des Trackers>", self.abort)

    def test_not_created_fits_step_six(self):
        self.assertIn("in Schritt 6: alle Titel der noch nicht bestätigten Liste", self.abort)


class TicketsNotBuildVerdictTest(unittest.TestCase):
    """Review PR #17, O2: Bei challenge-Urteil `nicht bauen` hatte tickets keine
    Regel aufzuhören und kein Ende mit Vorlage."""

    def setUp(self):
        self.text = read("skills/tickets/SKILL.md")

    def test_step_one_stops_on_not_build(self):
        self.assertIn("Lautet das letzte Urteil `nicht bauen`, hör hier auf und leg die Frage dem "
                      "Menschen vor (Vorlage „Rückfrage“ unten), außer er hat ausdrücklich gesagt, "
                      "dass trotzdem zerlegt wird.", subsection(self.text, "1. Voraussetzung"))

    def test_question_template_names_next_step_without_tickets(self):
        question = [b for b in re.findall(r"^```\n(.*?)^```", section(self.text, "Ergebnis"), re.S | re.M)
                    if b.startswith("## Ergebnis tickets (Rückfrage)")][0]
        self.assertIn("lautet das Urteil `nicht bauen`: `/slickfab:spec <Spec-Issue>`, wenn du die Spec "
                      "änderst (danach `/slickfab:challenge <Spec-Issue>`); stimmst du dem Urteil zu, "
                      "endet das Vorhaben und du setzt die Spec auf `Canceled`", question)


class GrillAdrRuleTest(unittest.TestCase):
    """Hand-Durchlauf, Befund 3: Runde 1 wollte für dieselbe
    Entscheidung einen ADR, Runde 2 nicht. Wann ein ADR fällig ist, steht als feste
    Regel mit genau zwei Kriterien, die beide zutreffen müssen."""

    def setUp(self):
        self.rule = subsection(read("skills/grill/SKILL.md"), "6. Nebenbei")

    def test_adr_rule_has_two_fixed_criteria(self):
        self.assertIn("**ADR:** Ein ADR ist fällig, wenn beides zutrifft: (1) Die Entscheidung "
                      "ist schwer umkehrbar. (2) Ohne Begründung würde ein späterer Leser sie "
                      "überraschend finden oder wieder aufrollen.", self.rule)
        self.assertIn("Trifft beides zu, legst du den ADR an; trifft eins nicht zu, legst du keinen an.",
                      self.rule)

    def test_no_third_criterion_left_to_judgement(self):
        # Widerlegt, wenn die Regel ein Ermessen ohne diese zwei Kriterien lässt.
        self.assertNotIn("echte Abwägung", self.rule)
        self.assertNotIn("Nur wenn", self.rule)


class RuleAnchorsTest(unittest.TestCase):
    """Review PR #2, R1: Die Sätze, die die „Widerlegt, wenn“-Fälle des Tickets
    tragen, müssen an ihrer Stelle stehen. Fehlt einer oder wird er umgedreht,
    wird es rot (Mutationsprobe). Das prüft den Text, nicht das Verhalten."""

    # (Datei, Abschnitt '### <Anfang>' oder '## <Name>', Ankersatz)
    ANCHORS = (
        # Fehlende Konfiguration / Tracker: melden, keine Ersatzdatei
        ("skills/tickets/SKILL.md", "### 1. Voraussetzung", "hör hier auf und melde genau das"),
        ("skills/tickets/SKILL.md", "### 1. Voraussetzung", "du schreibst keine Ticket-, Plan- oder State-Datei ins Repo als Ersatz"),
        ("skills/tickets/SKILL.md", "### 7. Anlegen", "Du legst keine Datei als Ersatz an."),
        ("skills/spec/SKILL.md", "### 6. Im Tracker", "Du legst keine Spec-, Plan- oder Ticket-Datei im Repo an."),
        ("skills/challenge/SKILL.md", "### 5. Festhalten", "Keine Datei im Repo als Ersatz."),
        ("tracker/linear.md", "## Access", "It writes **no** plan, ledger, state or ticket file into the repo as a substitute."),
        ("docs/projektkonfiguration.md", "## Wenn die Konfiguration fehlt", "It writes no plan, ledger or state file and no ticket list into the repo as a substitute"),
        # Anlegen erst nach Bestätigung, Dubletten vorher
        ("skills/tickets/SKILL.md", "### 6. Zerlegung", "Angelegt wird erst nach einem ausdrücklichen Ja zur Liste"),
        ("skills/tickets/SKILL.md", "### 7. Anlegen", "Erst nach dem Ja"),
        ("skills/tickets/SKILL.md", "### 6. Zerlegung", "Prüf auf Dubletten"),
        ("tracker/linear.md", "## Issues", "Before creating anything, check for duplicates"),
        # Vertagende Formulierungen
        ("skills/tickets/SKILL.md", "### 5. Auf stille", "Ein Ticket mit so einer Formulierung legst du nicht an."),
        # Keine stille Annahme in spec, keine Pfade
        ("skills/spec/SKILL.md", "### 1. Voraussetzung", "hörst du hier auf"),
        ("skills/spec/SKILL.md", "### 3. Jede Aussage", "**Produktfrage oder schwer umkehrbar:** Hier hörst du auf."),
        ("skills/spec/SKILL.md", "### 5. Selbstprüfung", "kein Dateipfad, kein Dateiname, kein Code im Text"),
        # challenge: frischer Blick
        ("skills/challenge/SKILL.md", "### 2. Frischen Blick", "Prüf nicht selbst in einer Session, die das Gespräch kennt."),
        # Freigabe bleibt beim Menschen
        ("skills/tickets/SKILL.md", "### 7. Anlegen", "Kein Ticket setzt du auf `Todo`"),
        ("tracker/linear.md", "## Status flow", "No step sets a ticket to `Todo` by itself."),
        # Konfiguration nie ausführen
        ("docs/projektkonfiguration.md", "## Format", "not executed as a shell script (no `source`)"),
        # prototype: fremde Arbeit und Hauptzweig unangetastet
        ("skills/prototype/SKILL.md", "### 1. Voraussetzung", "Sind Änderungen offen, hör auf und sag es. Du verschiebst oder versteckst keine fremden Änderungen."),
        ("skills/prototype/SKILL.md", "### 6. Festhalten", "Vom Prototyp kommt nichts in den Hauptzweig"),
        ("tracker/linear.md", "## Labels", "a step does not create new ones"),
    )

    def test_anchors(self):
        for rel, scope, sentence in self.ANCHORS:
            with self.subTest(file=rel, scope=scope, anchor=sentence[:40]):
                text = read(rel)
                part = subsection(text, scope[4:]) if scope.startswith("### ") else section(text, scope[3:])
                self.assertTrue(part, "%s: Abschnitt '%s' fehlt" % (rel, scope))
                self.assertIn(sentence, part)


if __name__ == "__main__":
    unittest.main()
