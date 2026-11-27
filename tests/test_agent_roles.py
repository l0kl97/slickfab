"""Agent-Rollen als dünne Hüllen.

Die Prüfung läuft über tests/check_roles.py gegen das echte Repo und gegen
Kopien mit absichtlich kaputten Hüllen: Jede Hülle ohne Verweis, mit falschem
Verweis, über der Längengrenze oder ohne Pflichtabschnitt muss rot werden.
"""
import os
import re
import shutil
import tempfile
import unittest

import check_roles as cr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Prüfende Rollen bekommen Artefakt und Vertrag, nie die Selbsteinschätzung des
# Umsetzers (Grenzen „Immer“). Der Satz steht wörtlich im Eingang.
CHECKING = ("reviewer", "verifier", "challenger")
IGNORE_REPORT = ("Ein Bericht, eine Zusammenfassung oder eine Selbsteinschätzung dessen, "
                 "der das Artefakt gebaut hat, ist kein Eingang.")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class RealRolesTest(unittest.TestCase):
    def test_all_seven_roles_pass(self):
        self.assertEqual(cr.check(ROOT), [])

    def test_checking_roles_ignore_builder_report(self):
        for role in CHECKING:
            with self.subTest(role=role):
                body = cr.parse_frontmatter(read(os.path.join(ROOT, "agents", role + ".md")))[1]
                eingang = cr.sections(body)["Eingang"]
                self.assertIn(IGNORE_REPORT, eingang)
                self.assertIn("ignorierst", eingang)

    def test_reviewer_marker_has_verdict_before_status(self):
        body = cr.sections(cr.parse_frontmatter(read(os.path.join(ROOT, "agents", "reviewer.md")))[1])
        self.assertRegex(body["Ausgang"], r"SLICKFAB-VERDICT: [^\n]+\nSLICKFAB-STATUS: ")

    def test_every_role_ends_with_status_line(self):
        # Die Vorlage im Ausgang endet mit der STATUS-Zeile, danach kein Text.
        for role in cr.ROLES:
            with self.subTest(role=role):
                body = cr.sections(cr.parse_frontmatter(read(os.path.join(ROOT, "agents", role + ".md")))[1])
                block = re.findall(r"```\n(.*?)```", body["Ausgang"], re.S)
                self.assertTrue(block, "Ausgang ohne Vorlage im Codeblock")
                self.assertRegex(block[-1].rstrip("\n").splitlines()[-1], r"^SLICKFAB-STATUS: ")

    def test_roles_do_not_need_to_read_plugin_files(self):
        # Ruling am Ticket: Plugin-Dateien sind ohne Auto-Modus nicht lesbar.
        for role in cr.ROLES:
            with self.subTest(role=role):
                self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", read(os.path.join(ROOT, "agents", role + ".md")))

    def test_roles_reading_foreign_content_cannot_write_files(self):
        # Pre-Push-Review: Rollen, die fremde Inhalte lesen, schützt das
        # Werkzeug, nicht der Prompt (review-learnings). Die Allowlist
        # `tools` ginge nicht: sie sperrte auch die Linear-Werkzeuge.
        # planner und challenger brauchen keine Shell (Review PR #10, R1); für
        # reviewer, verifier und retro gilt der Bash-Wächter (`hooks/role_bash_guard.py`).
        expected = {"planner": {"Bash", "Edit", "Write", "NotebookEdit"},
                    "challenger": {"Bash", "Edit", "Write", "NotebookEdit", "Agent", "Task"},
                    "verifier": {"Edit", "Write", "NotebookEdit"},
                    "retro": {"Edit", "Write", "NotebookEdit"},
                    # Edit braucht der Reviewer für die Mutationsprobe (Schritt review, 7).
                    "reviewer": {"Write", "NotebookEdit"}}
        for role, tools in expected.items():
            with self.subTest(role=role):
                fields = cr.parse_frontmatter(read(os.path.join(ROOT, "agents", role + ".md")))[0]
                self.assertLessEqual(tools, set(cr.split_list(fields.get("disallowedTools", ""))))

    def test_helper_agent_is_not_a_role(self):
        # docs-reader ist ein Werkzeug des Schritts docs-lookup, keine Rolle.
        self.assertNotIn("docs-reader", cr.ROLES)


ROLE_TEXT = {r: read(os.path.join(ROOT, "agents", r + ".md")) for r in cr.ROLES}


class BrokenRolesTest(unittest.TestCase):
    """Fehlerfälle: Kopie des Repos, eine Hülle wird kaputt gemacht."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="slickfab-roles-")
        for sub in ("agents", "skills"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(self.tmp, sub))
        self.path = os.path.join(self.tmp, "agents", "implementer.md")
        self.text = read(self.path)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def fails_with(self, text, expected):
        write(self.path, text)
        fails = "\n".join(cr.check(self.tmp))
        self.assertIn(expected, fails)

    def test_copy_is_clean(self):
        self.assertEqual(cr.check(self.tmp), [])

    def test_missing_step_reference(self):
        self.fails_with(re.sub(r"(?m)^schritt:.*\n", "", self.text), "Verweis auf den Schritt fehlt")

    def test_unknown_step(self):
        self.fails_with(self.text.replace("schritt: implement", "schritt: implementieren"),
                        "verweist auf Schritt 'implementieren', den es nicht gibt")

    def test_step_not_preloaded(self):
        self.fails_with(self.text.replace("skills: [slickfab:implement]", "skills: [slickfab:debug]"),
                        "'skills' lädt slickfab:implement nicht vor")

    def test_step_not_named_in_text(self):
        self.fails_with(self.text.replace("/slickfab:implement", "/slickfab:IMPLEMENT"),
                        "Text nennt /slickfab:implement nicht")

    def test_over_length(self):
        self.fails_with(self.text + "\nFülltext. " * 500, "Zeichen ohne Vertragsblöcke, erlaubt sind 4000")

    def test_missing_section(self):
        self.fails_with(self.text.replace("## Modell", "## Modelle"), "Pflichtabschnitt '## Modell' fehlt")

    def test_copied_step_line(self):
        line = next(l for l in read(os.path.join(ROOT, "skills", "implement", "SKILL.md")).splitlines()
                    if l.startswith("Bestehende Tests schwächst du nicht ab"))
        self.fails_with(self.text + "\n" + line + "\n", "wiederholt den Schritt implement wörtlich")

    def test_ablauf_section_forbidden(self):
        self.fails_with(self.text + "\n## Ablauf\n\n1. tu was\n", "'## Ablauf' gehört in den Schritt")

    def test_missing_needs_context(self):
        eingang = cr.sections(cr.parse_frontmatter(self.text)[1])["Eingang"]
        self.fails_with(self.text.replace(eingang, eingang.replace("NEEDS_CONTEXT", "BLOCKED")),
                        "NEEDS_CONTEXT")

    def test_marker_contract_missing(self):
        self.fails_with(self.text.replace("<!-- vertrag:marker -->", "<!-- vertrag:markierung -->"),
                        "bettet den Vertrag 'marker' nicht ein")

    def test_excuse_table_too_short(self):
        table = cr.sections(cr.parse_frontmatter(self.text)[1])["Ausrede → Realität"]
        rows = [l for l in table.splitlines() if l.startswith("| „")]
        short = table
        for row in rows[4:]:
            short = short.replace(row + "\n", "")
        self.fails_with(self.text.replace(table, short), "Ausrede-Tabelle hat 4 Zeilen, erlaubt 5–8")

    def test_excuse_table_too_long(self):
        table = cr.sections(cr.parse_frontmatter(self.text)[1])["Ausrede → Realität"]
        extra = "".join("| „Ausrede %d“ | Realität %d |\n" % (i, i) for i in range(3))
        self.fails_with(self.text.replace(table, table.rstrip("\n").replace(
            "<!-- /regel:ausreden -->", extra + "<!-- /regel:ausreden -->") + "\n"),
            "Ausrede-Tabelle hat 9 Zeilen, erlaubt 5–8")

    def own_length(self, text):
        return len(cr.COMMENT.sub("", cr.CONTRACT.sub("", cr.parse_frontmatter(text)[1])))

    def test_length_exactly_at_limit_passes(self):
        pad = cr.LENGTH_MAX - self.own_length(self.text) - 1
        text = self.text.replace("<!-- /regel:einleitung -->", "x" * pad + "\n<!-- /regel:einleitung -->")
        self.assertEqual(self.own_length(text), cr.LENGTH_MAX)
        write(self.path, text)
        self.assertEqual(cr.check(self.tmp), [])

    def test_length_one_over_limit_fails(self):
        pad = cr.LENGTH_MAX - self.own_length(self.text)
        text = self.text.replace("<!-- /regel:einleitung -->", "x" * pad + "\n<!-- /regel:einleitung -->")
        self.assertEqual(self.own_length(text), cr.LENGTH_MAX + 1)
        self.fails_with(text, "4001 Zeichen ohne Vertragsblöcke")

    def test_copied_short_step_line(self):
        # Genau 60 Zeichen aus implement: an der Kopiergrenze zählt die Zeile schon.
        line = "Prüf vor jeder Änderung, ob sie einen dieser Punkte berührt:"
        self.assertEqual(len(line), 60)
        self.assertIn(line, read(os.path.join(ROOT, "skills", "implement", "SKILL.md")))
        self.fails_with(self.text + "\n" + line + "\n", "wiederholt den Schritt implement wörtlich")

    def test_skills_and_schritt_must_match(self):
        path = os.path.join(self.tmp, "agents", "planner.md")
        write(path, read(path).replace("schritt: spec, tickets", "schritt: spec"))
        self.assertIn("agents/planner.md: 'skills' lädt slickfab:tickets vor, aber 'schritt' nennt tickets nicht",
                      cr.check(self.tmp))

    def test_free_text_between_blocks_fails(self):
        # Review PR #10, A1: eine widersprüchliche Erlaubnis zwischen den Blöcken.
        self.fails_with(self.text.replace("## Ausgang", "Bei kleinen PRs darfst du Befunde direkt selbst beheben.\n\n## Ausgang"),
                        "agents/implementer.md: freier Text außerhalb der Regel- und Vertragsblöcke: „Bei kleinen PRs darfst du")

    def test_invented_h2_heading_between_blocks_fails(self):
        # Re-Review PR #10, A1: eine Erlaubnis als '## '-Überschrift getarnt.
        self.fails_with(self.text.replace("## Ausgang", "## Bei kleinen PRs darfst du Befunde direkt selbst beheben.\n\n## Ausgang"),
                        "freier Text außerhalb der Regel- und Vertragsblöcke: „## Bei kleinen PRs darfst du")

    def test_h1_heading_between_blocks_fails(self):
        self.fails_with(self.text.replace("## Ausgang", "# Erlaubnis: Befunde selbst beheben\n\n## Ausgang"),
                        "freier Text außerhalb der Regel- und Vertragsblöcke: „# Erlaubnis")

    def test_h3_heading_between_blocks_fails(self):
        self.fails_with(self.text.replace("## Ausgang", "### Erlaubnis: Befunde selbst beheben\n\n## Ausgang"),
                        "freier Text außerhalb der Regel- und Vertragsblöcke: „### Erlaubnis")

    def test_free_text_after_last_block_fails(self):
        self.fails_with(self.text + "\nNachtrag ohne Block.\n",
                        "freier Text außerhalb der Regel- und Vertragsblöcke: „Nachtrag ohne Block.")

    def test_invalid_model(self):
        self.fails_with(self.text.replace("model: opus", "model: gpt-5"), "model 'gpt-5' ist kein gültiges Modell")

    def test_wrong_name(self):
        self.fails_with(self.text.replace("name: implementer", "name: umsetzer"), "name muss 'implementer' sein")

    def test_read_only_role_may_not_drop_tool_limit(self):
        path = os.path.join(self.tmp, "agents", "verifier.md")
        text = read(path)
        write(path, re.sub(r"(?m)^disallowedTools:.*\n", "", text))
        self.assertIn("agents/verifier.md: disallowedTools muss Edit, NotebookEdit, Write sperren",
                      cr.check(self.tmp))

    def test_planner_may_not_regain_bash(self):
        path = os.path.join(self.tmp, "agents", "planner.md")
        write(path, read(path).replace("disallowedTools: Bash, ", "disallowedTools: "))
        self.assertIn("agents/planner.md: disallowedTools muss Bash, Edit, NotebookEdit, Write sperren",
                      cr.check(self.tmp))

    # Review PR #10, R2: Fehlerfälle der Prüfung selbst.
    def test_no_frontmatter(self):
        self.fails_with(cr.parse_frontmatter(self.text)[1], "agents/implementer.md: kein Frontmatter")

    def test_empty_quoted_description(self):
        self.fails_with(re.sub(r"(?m)^description:.*$", 'description: ""', self.text),
                        "agents/implementer.md: description fehlt")

    def test_missing_description(self):
        self.fails_with(re.sub(r"(?m)^description:.*\n", "", self.text),
                        "agents/implementer.md: description fehlt")

    def test_copied_line_from_second_step(self):
        # Der Planer hat zwei Schritte; auch der zweite (tickets) wird geprüft.
        path = os.path.join(self.tmp, "agents", "planner.md")
        line = "- Ein „und“ im Titel heißt meist zwei Tickets; mehr als etwa 5 Kriterien heißt meist zu groß."
        self.assertIn(line, read(os.path.join(ROOT, "skills", "tickets", "SKILL.md")))
        text = read(path).replace("<!-- /regel:einleitung -->", line + "\n<!-- /regel:einleitung -->")
        write(path, text)
        self.assertIn("wiederholt den Schritt tickets wörtlich", "\n".join(cr.check(self.tmp)))

    def test_marker_contract_in_wrong_section(self):
        body = cr.sections(cr.parse_frontmatter(self.text)[1])
        block = body["Marker"].strip("\n") + "\n"
        moved = self.text.replace(block, "").replace("## Modell\n", "## Modell\n\n" + block, 1)
        self.fails_with(moved, "Abschnitt Marker bettet den Vertrag 'marker' nicht ein")

    def test_challenger_may_not_regain_bash(self):
        # Re-Review PR #10, F9.
        path = os.path.join(self.tmp, "agents", "challenger.md")
        write(path, read(path).replace("disallowedTools: Bash, ", "disallowedTools: "))
        self.assertIn("agents/challenger.md: disallowedTools muss Bash, Edit, NotebookEdit, Write sperren",
                      cr.check(self.tmp))

    # Befund 3 der Pressure-Szenarien: Der Challenger startete in C1 einen Explore-Subagent, obwohl die Hülle
    # das ausschließt. Das Werkzeug sperrt es, nicht der Prompt.
    def test_challenger_may_not_spawn_subagents(self):
        path = os.path.join(self.tmp, "agents", "challenger.md")
        for tool in ("Agent", "Task"):
            with self.subTest(tool=tool):
                text = re.sub(r"(?m)^(disallowedTools:.*)$",
                              lambda m: ", ".join(t for t in m.group(1).split(", ") if t != tool), ROLE_TEXT["challenger"])
                write(path, text)
                self.assertIn("agents/challenger.md: startet keine Subagents, disallowedTools muss Agent, Task sperren",
                              cr.check(self.tmp))

    # Befund 2 der Pressure-Szenarien: Beim Start mit `claude --agent` und aus der Herdr-Vorlage lädt Claude Code
    # `skills:` nicht vor. Jede Hülle sagt deshalb, dass der Schritt als Erstes per Skill-Werkzeug kommt.
    def test_hull_must_load_step_first(self):
        for role in cr.ROLES:
            with self.subTest(role=role):
                path = os.path.join(self.tmp, "agents", role + ".md")
                write(path, ROLE_TEXT[role].replace("als Erstes, vor jedem anderen Werkzeug,", "bei Bedarf"))
                self.assertIn("agents/%s.md: Einleitung sagt nicht, dass der Schritt als Erstes per "
                              "Skill-Werkzeug geladen wird" % role, cr.check(self.tmp))
                write(path, ROLE_TEXT[role])

    def test_hull_must_load_its_own_step(self):
        path = os.path.join(self.tmp, "agents", "verifier.md")
        write(path, ROLE_TEXT["verifier"].replace("Skill-Werkzeug (`slickfab:verify`)", "Skill-Werkzeug (`slickfab:review`)"))
        self.assertIn("agents/verifier.md: Einleitung sagt nicht, dass der Schritt als Erstes per "
                      "Skill-Werkzeug geladen wird", cr.check(self.tmp))

    def test_hull_may_not_claim_step_is_preloaded(self):
        path = os.path.join(self.tmp, "agents", "verifier.md")
        text = ROLE_TEXT["verifier"].replace("`/slickfab:verify`.", "`/slickfab:verify`; er ist beim Start in deinem Kontext.", 1)
        self.assertNotEqual(text, ROLE_TEXT["verifier"])
        write(path, text)
        self.assertIn("agents/verifier.md: Einleitung behauptet, der Schritt sei beim Start vorgeladen",
                      cr.check(self.tmp))

    def test_missing_role_file(self):
        os.remove(os.path.join(self.tmp, "agents", "retro.md"))
        self.assertIn("agents/retro.md: fehlt", cr.check(self.tmp))


if __name__ == "__main__":
    unittest.main()
