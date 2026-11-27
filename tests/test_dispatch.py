"""Prüft `decide(state) -> actions` aus `runtime/herdr/slickfab_dispatch.py`.

`decide` ist eine reine Funktion: Jeder Test baut einen Zustand als Fixture
(nur Dicts und Listen, so wie das Folgeticket ihn aus Linear und Herdr liest)
und prüft die geplanten Aktionen. Kein Netz, kein Herdr, kein Linear.
Die Form von `state` und `actions` steht in docs/features/slickfab-dispatch.md.
"""
import builtins
import copy
import os
import random
import socket
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "runtime", "herdr"))

from slickfab_dispatch import decide  # noqa: E402

BOT = "bot@example.com"
KIM = "kim@example.com"


def ticket(id, **kw):
    t = {
        "id": id,
        "project": "slickfab",
        "spec": "EX-100",
        "status": "Todo",
        "assignee": BOT,
        "labels": ["S"],
        "blockers": [],
        "files": [],
        "rework_rounds": 0,
        "pr": None,
    }
    t.update(kw)
    return t


def terminal(id, issue, role="implementer", status="working", report=None, seq=1, **labels):
    lab = {"slickfab.dispatch": "1", "studio.role": role, "studio.issue": issue}
    lab.update(labels)
    return {"id": id, "labels": lab, "status": status, "report": report, "seq": seq}


def project(**kw):
    p = {"enabled": True, "auto_merge": True, "max_parallel": 3,
         "main": {"sha": "m1", "ci": "green", "checked_sha": "m1", "debugged_sha": None},
         "merges": 0, "retro_at": 0}
    p.update(kw)
    return p


def state(tickets=(), terminals=(), projects=None, specs=None):
    return {
        "assignee": BOT,
        "projects": projects if projects is not None else {"slickfab": project()},
        "specs": specs if specs is not None else {"EX-100": {"project": "slickfab", "verified": False}},
        "tickets": list(tickets),
        "terminals": list(terminals),
    }


def pr(number=7, ci="green", paths=("src/app.py",), head="abc123", merged=False, mergeable="MERGEABLE"):
    return {"number": number, "ci": ci, "paths": list(paths), "head": head, "merged": merged,
            "mergeable": mergeable}


def kinds(actions, ticket_id=None):
    return [a["action"] for a in actions if ticket_id is None or a.get("ticket") == ticket_id]


def starts(actions):
    return [a["ticket"] for a in actions if a["action"] == "start_implementer"]


def needs_human(actions, ticket_id):
    return [a for a in actions if a["action"] == "needs_human" and a.get("ticket") == ticket_id]


class StartRule(unittest.TestCase):
    def test_free_todo_ticket_of_bot_starts_with_model_by_size(self):
        # Kim, 24.11.: S = Sonnet 5.5, M und L = Opus 5.5
        acts = decide(state([ticket("EX-1", labels=["S"]), ticket("EX-2", labels=["L"]),
                             ticket("EX-3", labels=["M"])]))
        by = {a["ticket"]: a for a in acts if a["action"] == "start_implementer"}
        self.assertEqual(by["EX-1"]["model"], "sonnet")
        self.assertEqual(by["EX-2"]["model"], "opus")
        self.assertEqual(by["EX-3"]["model"], "opus")
        self.assertIsNone(by["EX-1"]["effort"])
        self.assertEqual(by["EX-1"]["worktree"], "ex-1")
        self.assertEqual(by["EX-1"]["project"], "slickfab")
        self.assertFalse(by["EX-1"]["fresh"])

    def test_blocked_ticket_never_starts(self):
        t = ticket("EX-1", blockers=[{"id": "EX-9", "state_type": "started"}])
        self.assertEqual(starts(decide(state([t]))), [])

    def test_blocker_done_or_canceled_frees_ticket(self):
        t = ticket("EX-1", blockers=[{"id": "EX-9", "state_type": "completed"},
                                      {"id": "EX-8", "state_type": "canceled"},
                                      {"id": "EX-7", "state_type": "duplicate"}])
        self.assertEqual(starts(decide(state([t]))), ["EX-1"])

    def test_ticket_of_kim_or_without_assignee_never_starts(self):
        acts = decide(state([ticket("EX-1", assignee=KIM), ticket("EX-2", assignee=None)]))
        self.assertEqual(acts, [])

    def test_not_todo_never_starts(self):
        acts = decide(state([ticket("EX-1", status="Backlog"), ticket("EX-2", status="Done")]))
        self.assertEqual(starts(acts), [])

    def test_two_free_tickets_sharing_a_file_only_one_starts(self):
        acts = decide(state([ticket("EX-2", files=["a.py", "b.py"]), ticket("EX-1", files=["b.py"])]))
        self.assertEqual(starts(acts), ["EX-1"])  # deterministisch: kleinere Nummer zuerst

    def test_disjoint_files_both_start(self):
        acts = decide(state([ticket("EX-1", files=["a.py"]), ticket("EX-2", files=["b.py"])]))
        self.assertEqual(starts(acts), ["EX-1", "EX-2"])

    def test_file_overlap_with_running_ticket_blocks_start(self):
        running = ticket("EX-1", status="In Progress", files=["a.py"])
        acts = decide(state([running, ticket("EX-2", files=["a.py"])],
                            [terminal("t1", "EX-1")]))
        self.assertEqual(starts(acts), [])

    def test_parallel_limit_reached_blocks_start(self):
        running = [ticket("EX-%d" % i, status="In Progress") for i in (1, 2)]
        terms = [terminal("t%d" % i, "EX-%d" % i) for i in (1, 2)]
        todo = [ticket("EX-3"), ticket("EX-4")]
        acts = decide(state(running + todo, terms, {"slickfab": project(max_parallel=3)}))
        self.assertEqual(starts(acts), ["EX-3"])

    def test_running_implementer_means_no_second_start(self):
        # Ticket steht noch auf Todo, aber der Umsetzer läuft schon (Status nicht nachgezogen)
        acts = decide(state([ticket("EX-1")], [terminal("t1", "EX-1")]))
        self.assertEqual(starts(acts), [])

    def test_started_ticket_still_on_todo_counts_as_running(self):
        # Tick 1 hat EX-1 gestartet, Linear steht noch auf Todo (Pre-Push-Review A1)
        acts = decide(state([ticket("EX-1", files=["a.py"]), ticket("EX-2", files=["a.py"])],
                            [terminal("t1", "EX-1")]))
        self.assertEqual(acts, [])
        acts = decide(state([ticket("EX-1"), ticket("EX-2")], [terminal("t1", "EX-1")],
                            {"slickfab": project(max_parallel=1)}))
        self.assertEqual(acts, [])

    def test_done_ticket_with_leftover_terminal_frees_slot_and_files(self):
        # Re-Review PR #8 R-neu-3: Statusfilter der Belegung
        for status in ("Done", "Canceled", "Backlog"):
            old = ticket("EX-1", status=status, files=["a.py"], pr=pr(merged=True))
            acts = decide(state([old, ticket("EX-2", files=["a.py"])],
                                [terminal("t1", "EX-1", status="done", report=DONE)],
                                {"slickfab": project(max_parallel=1)}))
            self.assertEqual(starts(acts), ["EX-2"], status)

    def test_halted_ticket_with_terminal_counts_for_files_and_limit(self):
        # PR #8 Review A2: needs-human/ready halten das Ticket an, es läuft aber weiter bzw. hat einen PR
        for label, status in (("slickfab:needs-human", "blocked"), ("slickfab:ready", "done")):
            halted = ticket("EX-1", status="In Review", labels=["S", label], files=["a.py"], pr=pr())
            term = terminal("t1", "EX-1", status=status, report=DONE)
            acts = decide(state([halted, ticket("EX-2", files=["a.py"])], [term]))
            self.assertEqual(starts(acts), [], label)
            acts = decide(state([halted, ticket("EX-2")], [term], {"slickfab": project(max_parallel=1)}))
            self.assertEqual(starts(acts), [], label)
        garbled_term = decide(state([ticket("EX-1", status="In Progress"), ticket("EX-2")],
                                    [terminal("t1", "EX-1", seq="x")], {"slickfab": project(max_parallel=1)}))
        self.assertEqual(starts(garbled_term), [])
        broken = ticket("EX-1", status="In Progress", labels="S", files=["a.py"])
        acts = decide(state([broken, ticket("EX-2")], [terminal("t1", "EX-1")],
                            {"slickfab": project(max_parallel=1)}))
        self.assertEqual(starts(acts), [])

    def test_dead_implementer_on_todo_ticket_is_watched(self):
        acts = decide(state([ticket("EX-1")], [terminal("t1", "EX-1", status="dead")]))
        self.assertEqual(kinds(acts), ["restart_agent"])

    def test_unknown_or_missing_size_needs_human_instead_of_start(self):
        for labels in ([], ["XL"], ["S", "M"]):
            acts = decide(state([ticket("EX-1", labels=labels)]))
            self.assertEqual(starts(acts), [], labels)
            self.assertEqual(len(needs_human(acts, "EX-1")), 1, labels)
            self.assertIn("Größe", needs_human(acts, "EX-1")[0]["reason"])


DONE = "Fertig, PR offen.\nSLICKFAB-STATUS: DONE"


def review_verdict(verdict, status="DONE"):
    return "Review.\nSLICKFAB-VERDICT: %s\nSLICKFAB-STATUS: %s" % (verdict, status)


class ReviewRule(unittest.TestCase):
    def run_impl(self, report, pr_=None, status="done"):
        t = ticket("EX-1", status="In Review", pr=pr_ if pr_ is not None else pr())
        return decide(state([t], [terminal("t1", "EX-1", status=status, report=report)]))

    def test_done_with_open_pr_starts_reviewer_at_pr_head(self):
        for report in (DONE, "x\nSLICKFAB-STATUS: DONE_WITH_CONCERNS"):
            acts = self.run_impl(report)
            self.assertEqual(acts, [{"action": "start_reviewer", "ticket": "EX-1", "project": "slickfab",
                                     "pr": 7, "head": "abc123", "worktree": "pr-7"}], report)

    def test_idle_counts_like_done(self):
        self.assertEqual(kinds(self.run_impl(DONE, status="idle")), ["start_reviewer"])

    def test_still_working_means_wait(self):
        self.assertEqual(self.run_impl(None, status="working"), [])

    def test_permission_prompt_is_never_answered(self):
        self.assertEqual(self.run_impl(DONE, status="blocked"), [])

    def test_done_without_pr_needs_human(self):
        t = ticket("EX-1", status="In Progress", pr=None)
        acts = decide(state([t], [terminal("t1", "EX-1", status="done", report=DONE)]))
        self.assertEqual(kinds(acts), ["needs_human"])
        self.assertIn("Pull Request", acts[0]["reason"])

    def test_merged_or_closed_pr_is_not_reviewed(self):
        acts = self.run_impl(DONE, pr_=pr(merged=True))
        self.assertNotIn("start_reviewer", kinds(acts))

    def test_running_reviewer_means_no_second_reviewer(self):
        t = ticket("EX-1", status="In Review", pr=pr())
        acts = decide(state([t], [terminal("t1", "EX-1", status="done", report=DONE, seq=1),
                                  terminal("t2", "EX-1", role="reviewer", status="working", seq=2)]))
        self.assertEqual(acts, [])


class Markers(unittest.TestCase):
    def finished(self, report, role="implementer"):
        t = ticket("EX-1", status="In Review", pr=pr())
        return decide(state([t], [terminal("t1", "EX-1", role=role, status="done", report=report)]))

    def assert_needs_human(self, acts, word):
        self.assertEqual(kinds(acts), ["needs_human"], acts)
        self.assertIn(word, acts[0]["reason"])

    def test_missing_marker_needs_human(self):
        for report in (None, "", "Fertig, alles gut."):
            self.assert_needs_human(self.finished(report), "Marker")

    def test_unknown_status_value_needs_human(self):
        for report in ("SLICKFAB-STATUS: FINE", "SLICKFAB-STATUS: done", "SLICKFAB-STATUS: DONE|BLOCKED",
                       "SLICKFAB-STATUS: DONE\nNoch ein Satz danach"):
            self.assert_needs_human(self.finished(report), "Marker")

    def test_implementer_with_verdict_line_is_contradictory(self):
        self.assert_needs_human(self.finished(review_verdict("MERGE")), "Marker")

    def test_reviewer_finished_without_verdict_needs_human(self):
        for report in ("Stopp.\nSLICKFAB-STATUS: BLOCKED", "SLICKFAB-STATUS: DONE", None):
            self.assert_needs_human(self.finished(report, role="reviewer"), "VERDICT" if report else "Marker")

    def test_reviewer_unknown_verdict_needs_human(self):
        self.assert_needs_human(self.finished(review_verdict("SHIP"), role="reviewer"), "Marker")

    def test_marker_with_trailing_whitespace_is_read(self):
        self.assertEqual(kinds(self.finished(DONE + "\n\n  ")), ["start_reviewer"])


def reviewed(verdict, status="DONE", rounds=0, labels=("S",), pr_=None, impl_status="done",
             with_impl=True, head="abc123", projects=None):
    """Ticket nach dem Review: Umsetzer t1 fertig, Reviewer t2 hat zuletzt gemeldet."""
    t = ticket("EX-1", status="In Review", labels=list(labels), rework_rounds=rounds,
               pr=pr_ if pr_ is not None else pr())
    terms = [terminal("t2", "EX-1", role="reviewer", status="done", report=review_verdict(verdict, status),
                      seq=2, **({"slickfab.head": head} if head else {}))]
    if with_impl:
        terms.insert(0, terminal("t1", "EX-1", status=impl_status, report=DONE, seq=1))
    return decide(state([t], terms, projects))


class ReworkRule(unittest.TestCase):
    def test_rework_sequence_1_2_3_4(self):
        r1, r2, r3, r4 = (reviewed("REWORK", rounds=n) for n in (1, 2, 3, 4))
        for n, acts in ((1, r1), (2, r2)):
            self.assertEqual(acts, [{"action": "send_rework", "ticket": "EX-1", "project": "slickfab",
                                     "terminal": "t1", "round": n, "pr": 7}], n)
        self.assertEqual(r3, [{"action": "start_implementer", "ticket": "EX-1", "project": "slickfab",
                               "model": "opus", "effort": "high", "worktree": "ex-1", "fresh": True,
                               "round": 3, "pr": 7}])
        self.assertEqual(kinds(r4), ["needs_human"])
        self.assertNotIn("send_rework", kinds(r4))
        self.assertNotIn("start_implementer", kinds(r4))

    def test_round_3_is_opus_with_higher_effort_for_every_size(self):
        # Kim, 24.11.: Runde 3 = frischer Umsetzer auf Opus mit höherer Effort
        for size in ("S", "M", "L"):
            acts = reviewed("REWORK", rounds=3, labels=(size,))
            self.assertEqual([(a["model"], a["effort"], a["fresh"]) for a in acts], [("opus", "high", True)], size)

    def test_finished_implementer_in_state_done_gets_rework_like_idle(self):
        # Herdr meldet nach beendetem Turn `done`, nicht `idle` (Kommentar am Ticket)
        for st in ("done", "idle"):
            self.assertEqual(kinds(reviewed("REWORK", rounds=1, impl_status=st)), ["send_rework"], st)

    def test_rework_never_typed_into_blocked_terminal(self):
        self.assertEqual(reviewed("REWORK", rounds=1, impl_status="blocked"), [])

    def test_implementer_gone_starts_fresh_one_on_same_model(self):
        acts = reviewed("REWORK", rounds=1, with_impl=False)
        self.assertEqual(kinds(acts), ["start_implementer"])
        self.assertEqual((acts[0]["model"], acts[0]["effort"], acts[0]["fresh"], acts[0]["round"]),
                         ("sonnet", None, True, 1))

    def test_dead_old_implementer_gets_fresh_one_for_rework(self):
        acts = reviewed("REWORK", rounds=1, impl_status="dead")
        self.assertEqual([(a["action"], a["fresh"], a["model"]) for a in acts],
                         [("start_implementer", True, "sonnet")])

    def test_fresh_implementer_takes_over_round_count(self):
        # Master, Runde 2: der Rundenzähler hängt am Ticket, ein frischer Umsetzer setzt ihn nicht zurück
        def tick(rounds, terms):
            t = ticket("EX-1", status="In Review", rework_rounds=rounds, pr=pr())
            return decide(state([t], terms))
        rev = lambda id, seq: terminal(id, "EX-1", role="reviewer", status="done",
                                       report=review_verdict("REWORK"), seq=seq)
        # Runde 1: alter Umsetzer tot (oder weg) -> frischer, Runde 1
        r1 = tick(1, [terminal("t1", "EX-1", status="dead", seq=1), rev("t2", 2)])
        self.assertEqual([(a["action"], a["round"]) for a in r1], [("start_implementer", 1)])
        # Runde 2: der frische t3 ist jetzt "derselbe Umsetzer"
        r2 = tick(2, [terminal("t1", "EX-1", status="dead", seq=1), rev("t2", 2),
                      terminal("t3", "EX-1", status="done", report=DONE, seq=3), rev("t4", 4)])
        self.assertEqual([(a["action"], a.get("terminal"), a["round"]) for a in r2], [("send_rework", "t3", 2)])
        # Runde 4 mit lauter neuen Terminals ohne Vorgeschichte: Deckel greift trotzdem
        r4 = tick(4, [terminal("t9", "EX-1", status="idle", report=DONE, seq=1), rev("t10", 2)])
        self.assertEqual(kinds(r4), ["needs_human"])
        self.assertIn("erschöpft", r4[0]["reason"])

    def test_rework_without_round_count_needs_human(self):
        self.assertEqual(kinds(reviewed("REWORK", rounds=0)), ["needs_human"])


class ReplanRule(unittest.TestCase):
    def test_replan_sets_label_and_nothing_else(self):
        acts = reviewed("REPLAN")
        self.assertEqual(len(acts), 1)
        self.assertEqual((acts[0]["action"], acts[0]["label"]), ("label", "slickfab:replan"))

    def test_ticket_with_replan_label_gets_no_action(self):
        t = ticket("EX-1", status="In Review", labels=["S", "slickfab:replan"], pr=pr())
        acts = decide(state([t], [terminal("t2", "EX-1", role="reviewer", status="done",
                                           report=review_verdict("REPLAN"))]))
        self.assertEqual(acts, [])


class MergeRule(unittest.TestCase):
    def assert_ready(self, acts, word):
        self.assertEqual([(a["action"], a.get("label")) for a in acts], [("label", "slickfab:ready")], acts)
        self.assertIn(word, acts[0]["reason"])

    def test_all_conditions_met_auto_merges_at_reviewed_head(self):
        self.assertEqual(reviewed("MERGE"), [{"action": "merge", "ticket": "EX-1", "project": "slickfab",
                                              "pr": 7, "head": "abc123"}])

    def test_each_single_violation_leads_to_ready(self):
        self.assert_ready(reviewed("MERGE", labels=("M",)), "Größe")
        self.assert_ready(reviewed("MERGE", labels=("S", "door:one-way")), "door:one-way")
        self.assert_ready(reviewed("MERGE", projects={"slickfab": project(auto_merge=False)}), "auto_merge")
        self.assert_ready(reviewed("MERGE", projects={"slickfab": project(auto_merge="yes")}), "auto_merge")
        unset = project()
        del unset["auto_merge"]
        self.assert_ready(reviewed("MERGE", projects={"slickfab": unset}), "auto_merge")
        self.assert_ready(reviewed("MERGE", status="DONE_WITH_CONCERNS"), "Bedenken")

    def test_ci_pending_or_unknown_waits_instead_of_ready(self):
        # Entscheidung des Masters (Nachbesserung PR #8): sonst landet fast jeder S-PR beim Menschen
        for ci in ("pending", None):
            self.assertEqual(reviewed("MERGE", pr_=pr(ci=ci)), [], ci)

    def test_ci_value_outside_contract_needs_human(self):
        # Entscheidung des Masters (Runde 2): ein Lesefehler wartet nicht still ohne Ende
        for ci in ("queued", "failure", "GREEN", ""):
            acts = reviewed("MERGE", pr_=pr(ci=ci))
            self.assertEqual(kinds(acts), ["needs_human"], ci)
            self.assertIn("ci", acts[0]["reason"])
        # Ist Auto-Merge ohnehin ausgeschlossen, wartet nichts auf CI: sofort ready
        self.assert_ready(reviewed("MERGE", labels=("M",), pr_=pr(ci="pending")), "Größe")

    def test_sensitive_paths_lead_to_ready(self):
        for path in ("src/auth/login.ts", "supabase/migrations/001.sql", ".env.example", "apps/web/.env",
                     "db/rls_policies.sql", ".github/workflows/ci.yml", "lib/OAuth.py",
                     ".githooks/pre-push", ".slickrails/config.sh", "hooks/hooks.json",
                     ".claude/settings.json", ".codex/config.toml", "sub/.claude/agents/x.md",
                     "hooks/docs_lookup_guard.py", "hooks/other.json", "plugin/hooks/x.sh",
                     "runtime/herdr/slickfab_dispatch.py"):
            self.assert_ready(reviewed("MERGE", pr_=pr(paths=["README.md", path])), "sensibl")

    def test_executing_part_of_autopilot_is_never_auto_merged(self):
        # auch der ausführende Teil des Autopiloten ist eine Bremse
        # dazu, was der Autopilot ausführt und das selbst Bremse ist: Baseline/Vergleich und
        # die Übersetzung der Werkzeuggrenzen (Pre-Push-Review)
        for path in ("runtime/herdr/slickfab-dispatch", "runtime/herdr/slickfab-run",
                     "runtime/herdr/slickfab-worktree", "runtime/herdr/slickfab_templates.py",
                     "runtime/herdr/gen-templates",
                     # Rollen mit ihren Werkzeuggrenzen (disallowedTools) und die daraus erzeugten
                     # Herdr-Vorlagen (Entscheidung des Masters)
                     "agents/implementer.md", "agents/reviewer.md", "runtime/herdr/templates/implementer.md",
                     "runtime/herdr/templates/reviewer.md"):
            self.assert_ready(reviewed("MERGE", pr_=pr(paths=[path])), "sensibl")

    def test_merge_condition_and_checks_are_never_auto_merged(self):
        # Entscheidung des Masters (Review PR #18): wann der Reviewer MERGE schreibt, der Prüfbefehl
        # und seine Prüfskripte sowie die Projektkonfiguration der Fabrik
        for path in ("skills/review/SKILL.md", "tests/run.sh", "tests/check_structure.py",
                     "tests/check_fab.py", ".slickfab/config", "sub/.slickfab/config"):
            self.assert_ready(reviewed("MERGE", pr_=pr(paths=[path])), "sensibl")

    def test_harmless_paths_are_not_sensitive(self):
        for path in ("src/urls.py", "docs/environment.md", "src/controls.ts", "src/webhooks.py",
                     "docs/claude.md", "runtime/herdr/slickfab_other.py", "tests/test_dispatch.py",
                     "src/agents/chat.ts", "tests/test_check_steps.py", "tests/fixtures/run.sh",
                     "skills/implement/SKILL.md", "src/skills/review/x.md", "docs/tests/check_x.py",
                     "apps/web/tests/run.sh"):
            self.assertEqual(kinds(reviewed("MERGE", pr_=pr(paths=[path]))), ["merge"], path)

    def test_unknown_paths_lead_to_ready(self):
        p = pr()
        p["paths"] = None
        self.assert_ready(reviewed("MERGE", pr_=p), "Pfade")

    def test_head_moved_since_review_is_not_merged(self):
        self.assert_ready(reviewed("MERGE", head="old999"), "Head")
        self.assert_ready(reviewed("MERGE", head=None), "Head")
        # Head fehlt auf beiden Seiten (PR #8 Review R1): None == None ist kein geprüfter Head
        self.assert_ready(reviewed("MERGE", head=None, pr_=pr(head=None)), "Head")

    def test_reviewer_blocked_with_verdict_needs_human(self):
        self.assertEqual(kinds(reviewed("MERGE", status="BLOCKED")), ["needs_human"])

    def test_ticket_already_ready_or_merged_gets_no_action(self):
        self.assertEqual(reviewed("MERGE", pr_=pr(merged=True)), [])
        t = ticket("EX-1", status="In Review", labels=["M", "slickfab:ready"], pr=pr())
        acts = decide(state([t], [terminal("t2", "EX-1", role="reviewer", status="done",
                                           report=review_verdict("MERGE"))]))
        self.assertEqual(acts, [])


class GithubCiIgnore(unittest.TestCase):
    """github_ci = ignore. GitHub-Checks am PR gelten als nicht vorhanden, es zählt das Review."""

    def test_red_or_missing_ci_is_no_rework_and_merges_on_review(self):
        for ci in ("red", "pending", None, "seltsam"):
            with self.subTest(ci=ci):
                acts = reviewed("MERGE", pr_=pr(ci=ci), projects={"slickfab": project(github_ci="ignore")})
                self.assertEqual(acts, [{"action": "merge", "ticket": "EX-1", "project": "slickfab",
                                         "pr": 7, "head": "abc123"}])

    def test_other_brakes_still_hold(self):
        ign = {"slickfab": project(github_ci="ignore")}
        acts = reviewed("MERGE", labels=("M",), pr_=pr(ci="red"), projects=ign)
        self.assertEqual([(a["action"], a.get("label")) for a in acts], [("label", "slickfab:ready")])
        acts = reviewed("MERGE", pr_=pr(ci="red", mergeable="CONFLICTING"), projects=ign)
        self.assertEqual([(a["action"], a["cause"]) for a in acts], [("send_rework", ["conflict"])])
        self.assertEqual(reviewed("MERGE", pr_=pr(ci="red", mergeable="UNKNOWN"), projects=ign), [])

    def test_use_and_default_keep_ci(self):
        for projects in ({"slickfab": project(github_ci="use")}, None):
            acts = reviewed("MERGE", pr_=pr(ci="red"), projects=projects)
            self.assertEqual([(a["action"], a["cause"]) for a in acts], [("send_rework", ["ci"])])
            self.assertEqual(reviewed("MERGE", pr_=pr(ci="pending"), projects=projects), [])

    def test_value_outside_contract_needs_human(self):
        for value in ("aus", None, True):
            with self.subTest(value=value):
                acts = reviewed("MERGE", projects={"slickfab": project(github_ci=value)})
                self.assertEqual(kinds(acts), ["needs_human"])
                self.assertIn("github_ci", acts[0]["reason"])


class PrWatch(unittest.TestCase):
    """was /ship am PR beobachtet, ohne dass ein kaputter PR beim Menschen landet."""

    def test_merge_with_red_ci_is_reworked_not_ready(self):
        # Kein Rework-Verdict am Ticket: die CI-Runde ist die erste
        acts = reviewed("MERGE", rounds=0, pr_=pr(ci="red"))
        self.assertEqual(acts, [{"action": "send_rework", "ticket": "EX-1", "project": "slickfab",
                                 "terminal": "t1", "round": 1, "pr": 7, "cause": ["ci"]}])

    def test_red_ci_rework_even_when_auto_merge_is_excluded_anyway(self):
        # Größe M: früher ready mit „CI red“, jetzt bekommt der Mensch keinen roten PR
        acts = reviewed("MERGE", rounds=1, labels=("M",), pr_=pr(ci="red"))
        self.assertEqual([(a["action"], a["round"], a["cause"]) for a in acts], [("send_rework", 2, ["ci"])])
        self.assertNotIn("label", kinds(acts))

    def test_red_ci_rework_respects_the_rework_cap(self):
        # Runde 3 = frischer Umsetzer auf Opus, danach ist Schluss (needs_human statt ready)
        r3 = reviewed("MERGE", rounds=2, pr_=pr(ci="red"))
        self.assertEqual([(a["action"], a["model"], a["effort"], a["round"], a["cause"]) for a in r3],
                         [("start_implementer", "opus", "high", 3, ["ci"])])
        r4 = reviewed("MERGE", rounds=3, pr_=pr(ci="red"))
        self.assertEqual(kinds(r4), ["needs_human"])
        self.assertIn("erschöpft", r4[0]["reason"])


    def test_conflicting_pr_is_brought_onto_main_whatever_else_holds(self):
        for labels in (("S",), ("M",), ("S", "door:one-way")):
            acts = reviewed("MERGE", rounds=0, labels=labels, pr_=pr(mergeable="CONFLICTING"))
            self.assertEqual([(a["action"], a["round"], a["cause"]) for a in acts],
                             [("send_rework", 1, ["conflict"])], labels)

    def test_red_ci_and_conflict_are_one_round(self):
        acts = reviewed("MERGE", rounds=0, pr_=pr(ci="red", mergeable="CONFLICTING"))
        self.assertEqual([(a["action"], a["round"], a["cause"]) for a in acts], [("send_rework", 1, ["ci", "conflict"])])

    def test_unclear_mergeability_is_never_merged(self):
        missing = pr()
        del missing["mergeable"]
        for p in (pr(mergeable="UNKNOWN"), pr(mergeable=None), missing):
            acts = reviewed("MERGE", pr_=p)
            self.assertEqual(acts, [], p)   # GitHub rechnet noch: warten wie bei CI pending
            # Ist Auto-Merge ohnehin ausgeschlossen, wartet nichts: ready, aber nie merge
            self.assertEqual([(a["action"], a.get("label")) for a in reviewed("MERGE", labels=("M",), pr_=p)],
                             [("label", "slickfab:ready")], p)

    def test_mergeable_outside_contract_needs_human(self):
        for value in ("mergeable", "DIRTY", "", 1, True):
            acts = reviewed("MERGE", pr_=pr(mergeable=value))
            self.assertEqual(kinds(acts), ["needs_human"], value)
            self.assertIn("mergeable", acts[0]["reason"])


def gh_comment(author="Lokl97", at=5, body="Bitte den Button anders benennen.", n=1):
    return {"author": author, "at": at, "url": "https://github.com/o/r/pull/7#c%d" % n, "body": body}


def with_comments(*comments, rounds=0, verdict="MERGE", labels=("S",), authors=("lokl97",), **kw):
    """Wie reviewed(), Umsetzer t1 (seq 1), Reviewer t2 (seq 2), dazu PR-Kommentare und erlaubte Autoren."""
    p = pr(**kw)
    p["comments"] = list(comments)
    return reviewed(verdict, rounds=rounds, labels=labels, pr_=p,
                    projects={"slickfab": project(comment_authors=list(authors))})


class PrComments(unittest.TestCase):
    """Kommentare erlaubter Autoren (Factory-Konfiguration) am PR, nie ein Merge daraus."""

    def test_comment_of_allowed_author_goes_back_to_implementer_instead_of_merge(self):
        acts = with_comments(gh_comment())
        self.assertEqual(acts, [{"action": "send_rework", "ticket": "EX-1", "project": "slickfab",
                                 "terminal": "t1", "round": 1, "pr": 7, "cause": ["comment"],
                                 "comments": ["https://github.com/o/r/pull/7#c1"]}])

    def test_author_match_ignores_case(self):
        self.assertEqual(kinds(with_comments(gh_comment(author="LOKL97"))), ["send_rework"])
        self.assertEqual(kinds(with_comments(gh_comment(author="lokl97"), authors=("Lokl97",))), ["send_rework"])

    def test_comment_during_review_is_not_lost_behind_the_reviewer(self):
        # nach dem Umsetzer (seq 1), vor dem Start des Reviewers (seq 2): der Umsetzer kennt ihn nicht
        self.assertEqual(kinds(with_comments(gh_comment(at=2))), ["send_rework"])

    def test_replan_keeps_its_label_despite_a_comment(self):
        acts = with_comments(gh_comment(), verdict="REPLAN")
        self.assertEqual([(a["action"], a.get("label")) for a in acts], [("label", "slickfab:replan")])

    def test_comment_on_merged_pr_does_nothing(self):
        self.assertEqual(with_comments(gh_comment(), merged=True), [])

    def test_comment_with_red_ci_or_conflict_names_every_cause(self):
        acts = with_comments(gh_comment(), ci="red", mergeable="CONFLICTING")
        self.assertEqual([(a["action"], a["round"], a["cause"]) for a in acts],
                         [("send_rework", 1, ["ci", "conflict", "comment"])])

    def test_comments_of_other_authors_are_ignored(self):
        for c in (gh_comment(author="mallory"), gh_comment(author=None), gh_comment(author="lokl97-bot"),
                  gh_comment(author="github-actions[bot]")):
            self.assertEqual(kinds(with_comments(c)), ["merge"], c)
        # ohne erlaubte Autoren in der Konfiguration zählt niemand, auch kein Feld am Ticket
        self.assertEqual(kinds(with_comments(gh_comment(), authors=())), ["merge"])
        unset = reviewed("MERGE", pr_=dict(pr(), comments=[gh_comment()]))
        self.assertEqual(kinds(unset), ["merge"])
        # Review R4: ein Feld am Ticket oder PR erlaubt niemanden
        t = ticket("EX-1", status="In Review", comment_authors=["lokl97"],
                   pr=dict(pr(), comments=[gh_comment()], comment_authors=["lokl97"]))
        terms = [terminal("t1", "EX-1", status="done", report=DONE, seq=1),
                 terminal("t2", "EX-1", role="reviewer", status="done", report=review_verdict("MERGE"), seq=2,
                          **{"slickfab.head": "abc123", "comment_authors": "lokl97"})]
        self.assertEqual(kinds(decide(state([t], terms))), ["merge"])

    def test_agent_report_under_same_login_is_not_a_human_comment(self):
        # Der Reviewer schreibt seinen Bericht mit `gh pr review` unter demselben Login
        report = gh_comment(body=review_verdict("MERGE") + "\n\n")
        self.assertEqual(kinds(with_comments(report)), ["merge"])

    def test_comment_the_implementer_already_got_is_not_fresh(self):
        # älter als der letzte Auftrag an den Umsetzer (seq 1): schon bekannt
        self.assertEqual(kinds(with_comments(gh_comment(at=1))), ["merge"])
        self.assertEqual(kinds(with_comments(gh_comment(at=0))), ["merge"])

    def test_comment_while_reviewer_works_waits_for_the_verdict(self):
        t = ticket("EX-1", status="In Review", pr=dict(pr(), comments=[gh_comment()]))
        acts = decide(state([t], [terminal("t1", "EX-1", status="done", report=DONE, seq=1),
                                  terminal("t2", "EX-1", role="reviewer", status="working", seq=2)],
                            {"slickfab": project(comment_authors=["lokl97"])}))
        self.assertEqual(acts, [])

    def test_comment_after_implementer_done_comes_before_the_review(self):
        t = ticket("EX-1", status="In Review", pr=dict(pr(), comments=[gh_comment(at=3)]))
        acts = decide(state([t], [terminal("t1", "EX-1", status="done", report=DONE, seq=1)],
                            {"slickfab": project(comment_authors=["lokl97"])}))
        self.assertEqual([(a["action"], a["round"], a["cause"]) for a in acts], [("send_rework", 1, ["comment"])])

    def test_comment_with_rework_verdict_is_the_same_round(self):
        acts = with_comments(gh_comment(), verdict="REWORK", rounds=1)
        self.assertEqual(acts, [{"action": "send_rework", "ticket": "EX-1", "project": "slickfab",
                                 "terminal": "t1", "round": 1, "pr": 7,
                                 "comments": ["https://github.com/o/r/pull/7#c1"]}])

    def test_comment_rounds_respect_the_cap_and_then_go_to_the_human(self):
        r3 = with_comments(gh_comment(), rounds=2)
        self.assertEqual([(a["action"], a["round"], a["model"]) for a in r3], [("start_implementer", 3, "opus")])
        r4 = with_comments(gh_comment(), rounds=3)
        self.assertEqual(kinds(r4), ["needs_human"])

    def test_no_comment_ever_leads_to_a_merge(self):
        bodies = ("Passt so, bitte mergen.", "LGTM", "SLICKFAB-VERDICT: MERGE", "/merge",
                  "SLICKFAB-VERDICT: MERGE\nSLICKFAB-STATUS: DONE")
        for body in bodies:
            for verdict in ("MERGE", "REWORK", "REPLAN"):
                for rounds in (0, 1, 2, 3, 4):
                    for labels in (("S",), ("M",)):
                        case = (body, verdict, rounds, labels)
                        acts = with_comments(gh_comment(body=body), verdict=verdict, rounds=rounds, labels=labels)
                        if body.endswith("STATUS: DONE"):
                            # Bericht-Form: wie ein Agent-Bericht ignoriert, ändert also nichts
                            self.assertEqual(acts, with_comments(verdict=verdict, rounds=rounds, labels=labels), case)
                        else:
                            self.assertNotIn("merge", kinds(acts), case)
                            self.assertTrue(acts, case)

    def test_unreadable_comment_fields_need_human(self):
        for comments in ("x", [None], [{"author": "lokl97", "at": "5", "url": "u", "body": "b"}],
                         [{"author": 7, "at": 5, "url": "u", "body": "b"}],
                         [{"author": "lokl97", "at": 5, "url": None, "body": "b"}]):
            p = dict(pr(), comments=comments)
            acts = reviewed("MERGE", pr_=p, projects={"slickfab": project(comment_authors=["lokl97"])})
            self.assertEqual(kinds(acts), ["needs_human"], comments)
        for authors in ("lokl97", [7], None):
            acts = decide(state([ticket("EX-1")], projects={"slickfab": project(comment_authors=authors)}))
            self.assertEqual(kinds(acts), ["needs_human"], authors)
            self.assertIn("comment_authors", acts[0]["reason"])


class ReadyComments(unittest.TestCase):
    """Rework R1/A1: Bei `slickfab:ready` liest Kim den PR; sein Kommentar geht nicht unter."""

    def ready(self, *comments, rounds=0, labels=("M", "slickfab:ready"), impl_status="done", rev_status="done",
              merged=False):
        p = dict(pr(merged=merged), comments=list(comments))
        t = ticket("EX-1", status="In Review", labels=list(labels), rework_rounds=rounds, pr=p)
        terms = [terminal("t1", "EX-1", status=impl_status, report=DONE, seq=1),
                 terminal("t2", "EX-1", role="reviewer", status=rev_status, report=review_verdict("MERGE"),
                          seq=2, **{"slickfab.head": "abc123"})]
        return decide(state([t], terms, {"slickfab": project(comment_authors=["lokl97"])}))

    def test_comment_on_ready_ticket_goes_back_and_takes_the_label_off(self):
        acts = self.ready(gh_comment(at=5))
        self.assertEqual(acts, [{"action": "send_rework", "ticket": "EX-1", "project": "slickfab",
                                 "terminal": "t1", "round": 1, "pr": 7, "cause": ["comment"],
                                 "comments": ["https://github.com/o/r/pull/7#c1"], "unlabel": "slickfab:ready"}])

    def test_ready_ticket_without_fresh_comment_stays_with_the_human(self):
        for comments in ((), (gh_comment(at=1),), (gh_comment(author="mallory"),),
                         (gh_comment(body=review_verdict("MERGE")),)):
            self.assertEqual(self.ready(*comments), [], comments)

    def test_ready_comment_respects_the_cap_and_never_merges(self):
        r3 = self.ready(gh_comment(), rounds=2)
        self.assertEqual([(a["action"], a["round"], a["model"], a["unlabel"]) for a in r3],
                         [("start_implementer", 3, "opus", "slickfab:ready")])
        r4 = self.ready(gh_comment(), rounds=3)
        self.assertEqual(kinds(r4), ["needs_human"])
        for labels in (("S", "slickfab:ready"), ("M", "slickfab:ready")):
            for rounds in range(5):
                self.assertNotIn("merge", kinds(self.ready(gh_comment(), rounds=rounds, labels=labels)))

    def test_ready_comment_waits_while_an_agent_works_and_ignores_merged_prs(self):
        self.assertEqual(self.ready(gh_comment(), rev_status="working"), [])
        # Review R6: wartet das jüngste Terminal auf eine Berechtigung, plant der Dispatcher nichts
        self.assertEqual(self.ready(gh_comment(), rev_status="blocked"), [])
        self.assertEqual(self.ready(gh_comment(), rounds=2, rev_status="blocked"), [])
        self.assertEqual(self.ready(gh_comment(), merged=True), [])

    def test_ticket_back_from_ready_by_comment_never_auto_merges(self):
        # Review A3, Ruling des Masters: S-Ticket stand bei ready (Bedenken des Reviewers), Kim kommentiert,
        # Ticket kommt zurück. Nach Nachbesserung und neuem MERGE/DONE geht es wieder auf ready.
        step1 = self.ready(gh_comment(at=5), labels=("S", "slickfab:ready"))
        self.assertEqual([(a["action"], a["unlabel"]) for a in step1], [("send_rework", "slickfab:ready")])
        # Ausführung: Label ab, Runde gebucht (rework_rounds 1), Markierung am Ticket (human_gate)
        def after(gate):
            t = ticket("EX-1", status="In Review", labels=["S"], rework_rounds=1, human_gate=gate,
                       pr=dict(pr(), comments=[gh_comment(at=5)]))
            terms = [terminal("t1", "EX-1", status="done", report=DONE, seq=6),
                     terminal("t2", "EX-1", role="reviewer", status="done", report=review_verdict("MERGE"), seq=7,
                              **{"slickfab.head": "abc123"})]
            return decide(state([t], terms, {"slickfab": project(comment_authors=["lokl97"])}))
        acts = after(True)
        self.assertEqual([(a["action"], a.get("label")) for a in acts], [("label", "slickfab:ready")])
        self.assertIn("beim Menschen", acts[0]["reason"])
        self.assertEqual(kinds(after(False)), ["merge"])   # Gegenprobe: ohne Markierung wie bisher

    def test_unreadable_human_gate_needs_human(self):
        for gate in ("ja", 1, None, []):
            t = ticket("EX-1", human_gate=gate)
            self.assertEqual(kinds(decide(state([t]))), ["needs_human"], gate)

    def test_other_halt_labels_stay_halted(self):
        for halt in ("slickfab:needs-human", "slickfab:replan"):
            self.assertEqual(self.ready(gh_comment(), labels=("M", halt)), [], halt)


class Watcher(unittest.TestCase):
    def run_term(self, status="dead", report=None, restarts=None, role="implementer"):
        extra = {} if restarts is None else {"slickfab.restarts": str(restarts)}
        t = ticket("EX-1", status="In Progress", pr=pr())
        return decide(state([t], [terminal("t1", "EX-1", role=role, status=status, report=report, **extra)]))

    def test_dead_agent_first_restart_then_needs_human(self):
        first = self.run_term(restarts=None)
        self.assertEqual(first, [{"action": "restart_agent", "ticket": "EX-1", "project": "slickfab",
                                  "terminal": "t1", "role": "implementer", "handoff": True, "restarts": 1,
                                  "reason": "Agent tot"}])
        second = self.run_term(restarts=1)
        self.assertEqual(kinds(second), ["needs_human"])
        self.assertNotIn("restart_agent", kinds(second))

    def test_restart_cap_counts_per_ticket_and_role(self):
        # PR #8 Review A1, Fehlerfall 1: altes totes Terminal ohne Zähler neben neuem mit Zähler
        t = ticket("EX-1", status="In Progress", pr=pr())
        acts = decide(state([t], [terminal("t1", "EX-1", status="dead", seq=1),
                                  terminal("t9", "EX-1", status="dead", seq=2, **{"slickfab.restarts": "1"})]))
        self.assertEqual(kinds(acts), ["needs_human"])
        # Zähler am alten Terminal, das neue ist tot: auch kein zweiter Neustart
        acts = decide(state([t], [terminal("t1", "EX-1", status="dead", seq=1, **{"slickfab.restarts": "1"}),
                                  terminal("t9", "EX-1", status="dead", seq=2)]))
        self.assertEqual(kinds(acts), ["needs_human"])

    def test_obsolete_dead_terminal_is_never_restarted(self):
        # PR #8 Review A1, Fehlerfall 2: nach Runde 3 arbeitet t3, das alte t1 meldet dead
        t = ticket("EX-1", status="In Review", rework_rounds=3, pr=pr())
        terms = [terminal("t1", "EX-1", status="dead", seq=1),
                 terminal("t2", "EX-1", role="reviewer", status="done", report=review_verdict("REWORK"), seq=2),
                 terminal("t3", "EX-1", status="working", seq=3)]
        self.assertEqual(decide(state([t], terms)), [])
        terms[2] = terminal("t3", "EX-1", status="done", report=DONE, seq=3)
        self.assertEqual(kinds(decide(state([t], terms))), ["start_reviewer"])

    def test_restart_cap_is_per_role(self):
        # Umsetzer schon einmal neu gestartet; der Reviewer hat seinen eigenen Deckel
        t = ticket("EX-1", status="In Review", pr=pr())
        acts = decide(state([t], [terminal("t1", "EX-1", status="done", report=DONE, seq=1,
                                           **{"slickfab.restarts": "1"}),
                                  terminal("t2", "EX-1", role="reviewer", status="dead", seq=2)]))
        self.assertEqual([(a["action"], a["terminal"]) for a in acts], [("restart_agent", "t2")])

    def test_dead_reviewer_is_restarted_too(self):
        acts = self.run_term(role="reviewer")
        self.assertEqual((acts[0]["action"], acts[0]["role"]), ("restart_agent", "reviewer"))

    def test_garbled_restart_counter_needs_human(self):
        for raw in ("x", "-1", ""):
            acts = self.run_term(restarts=raw)
            self.assertEqual(len(needs_human(acts, "EX-1")), 1, raw)
            self.assertIn("Neustart-Zähler", acts[0]["reason"])

    def test_blocked_marker_needs_human(self):
        acts = self.run_term(status="done", report="Kein Zugriff.\nSLICKFAB-STATUS: BLOCKED")
        self.assertEqual(kinds(acts), ["needs_human"])
        self.assertIn("BLOCKED", acts[0]["reason"])

    def test_needs_context_restarts_once_with_handoff(self):
        report = "Spec fehlt.\nSLICKFAB-STATUS: NEEDS_CONTEXT"
        first = self.run_term(status="done", report=report)
        self.assertEqual([(a["action"], a["handoff"], a["restarts"]) for a in first],
                         [("restart_agent", True, 1)])
        self.assertEqual(kinds(self.run_term(status="done", report=report, restarts=1)), ["needs_human"])

    def test_living_agent_is_not_restarted(self):
        for status in ("working", "blocked"):
            self.assertEqual(self.run_term(status=status), [], status)

    def test_unknown_role_on_ticket_needs_human(self):
        acts = self.run_term(status="done", report=DONE, role="debug")
        self.assertEqual(len(needs_human(acts, "EX-1")), 1)
        self.assertIn("Rolle", acts[0]["reason"])

    def test_unknown_terminal_status_needs_human(self):
        self.assertEqual(kinds(self.run_term(status="zombie")), ["needs_human"])


class Labels(unittest.TestCase):
    def test_contradictory_labels_need_human(self):
        for labels in (["S", "slickfab:ready", "slickfab:rework"], ["S", "slickfab:replan", "slickfab:ready"]):
            acts = decide(state([ticket("EX-1", labels=labels)]))
            self.assertEqual(kinds(acts), ["needs_human"], labels)
            self.assertIn("widersprüchlich", acts[0]["reason"])

    def test_needs_human_label_silences_ticket(self):
        t = ticket("EX-1", labels=["S", "slickfab:needs-human", "slickfab:ready"])
        self.assertEqual(decide(state([t])), [])

    def test_needs_human_label_silences_unreadable_ticket(self):
        # Pre-Push-Review nach dem Rebase: ein schon geparktes Ticket mit kaputten Daten
        # bekommt nicht bei jedem Tick erneut needs_human (Kommentar-Spam)
        broken_term = terminal("t1", "EX-1", seq="x")
        for labels in (["S", "slickfab:needs-human"], ["slickfab:needs-human"]):
            t = ticket("EX-1", status="In Progress", labels=labels)
            self.assertEqual(decide(state([t], [broken_term])), [], labels)
            bad = ticket("EX-1", status="In Progress", labels=labels)
            bad["files"] = "x"
            self.assertEqual(decide(state([bad], [terminal("t1", "EX-1")])), [], labels)
            bad = ticket("EX-1", status="In Progress", labels=labels)
            bad["rework_rounds"] = "zwei"
            self.assertEqual(decide(state([bad])), [], labels)
        # Ohne das Label bleibt es laut, und ein unlesbares labels-Feld zählt nicht als geparkt
        t = ticket("EX-1", status="In Progress", labels=["S"])
        self.assertEqual(kinds(decide(state([t], [broken_term]))), ["needs_human"])
        bad = ticket("EX-1", status="In Progress")
        bad["labels"] = "slickfab:needs-human"
        self.assertEqual(kinds(decide(state([bad]))), ["needs_human"])
        bad["labels"] = ["S", 7, "slickfab:needs-human"]
        self.assertEqual(kinds(decide(state([bad]))), ["needs_human"])
        # Nur needs-human schweigt: ready/replan mit kaputten Daten bleiben laut
        for halt in ("slickfab:ready", "slickfab:replan"):
            t = ticket("EX-1", status="In Progress", labels=["S", halt])
            self.assertEqual(kinds(decide(state([t], [broken_term]))), ["needs_human"], halt)
        # Geparkt und kaputt belegt weiter Platz und Dateien
        parked = ticket("EX-1", status="In Progress", labels=["S", "slickfab:needs-human"], files=["a.py"])
        todo = ticket("EX-2", files=["a.py"])
        self.assertEqual(decide(state([parked, todo], [broken_term])), [])

    def test_unknown_size_on_running_ticket_needs_human(self):
        t = ticket("EX-1", status="In Review", labels=[], pr=pr())
        acts = decide(state([t], [terminal("t1", "EX-1", status="done", report=DONE)]))
        self.assertEqual(kinds(acts), ["needs_human"])


def main_(sha="m2", ci="green", checked="m1", debugged=None):
    return {"sha": sha, "ci": ci, "checked_sha": checked, "debugged_sha": debugged}


class AfterMerge(unittest.TestCase):
    def test_new_main_commit_gets_post_merge_check_once(self):
        acts = decide(state(projects={"slickfab": project(main=main_())}))
        self.assertEqual(acts, [{"action": "post_merge_check", "project": "slickfab", "sha": "m2"}])
        checked = decide(state(projects={"slickfab": project(main=main_(checked="m2"))}))
        self.assertEqual(checked, [])
        running = decide(state(terminals=[terminal("c1", "slickfab", role="check")],
                               projects={"slickfab": project(main=main_())}))
        self.assertEqual(running, [])

    def test_merged_blocker_frees_waiting_ticket(self):
        waiting = ticket("EX-2", blockers=[{"id": "EX-1", "state_type": "started"}])
        self.assertEqual(starts(decide(state([waiting]))), [])
        waiting["blockers"][0]["state_type"] = "completed"
        self.assertEqual(starts(decide(state([waiting]))), ["EX-2"])

    def test_every_tenth_merge_starts_retro(self):
        acts = decide(state(projects={"slickfab": project(merges=20, retro_at=10)}))
        self.assertEqual(acts, [{"action": "start_retro", "project": "slickfab", "merges": 20}])
        self.assertEqual(decide(state(projects={"slickfab": project(merges=19, retro_at=10)})), [])
        running = decide(state(terminals=[terminal("r1", "slickfab", role="retro")],
                               projects={"slickfab": project(merges=20, retro_at=10)}))
        self.assertEqual(running, [])

    def test_all_tickets_of_spec_done_starts_verify(self):
        done = [ticket("EX-1", status="Done"), ticket("EX-2", status="Canceled", assignee=KIM),
                ticket("EX-3", status="Done", assignee=KIM)]
        self.assertEqual(decide(state(done)), [{"action": "start_verify", "project": "slickfab", "spec": "EX-100"}])

    def test_verify_waits_for_open_tickets_and_runs_once(self):
        open_ = [ticket("EX-1", status="Done"), ticket("EX-2", status="In Review", assignee=KIM)]
        self.assertNotIn("start_verify", kinds(decide(state(open_))))
        done = [ticket("EX-1", status="Done")]
        verified = {"EX-100": {"project": "slickfab", "verified": True}}
        self.assertEqual(decide(state(done, specs=verified)), [])
        self.assertEqual(decide(state(done, [terminal("v1", "EX-100", role="verify")])), [])
        only_canceled = [ticket("EX-1", status="Canceled")]
        self.assertEqual(decide(state(only_canceled)), [])

    def test_dead_verify_agent_of_foreign_project_is_not_restarted(self):
        # Re-Review PR #8 R-neu-1: Wächter-Projektfilter
        specs = {"EX-100": {"project": "slickfab", "verified": False},
                 "EX-9": {"project": "other", "verified": False}}
        projects = {"slickfab": project(), "other": project(enabled=False)}
        acts = decide(state(terminals=[terminal("v", "EX-9", role="verify", status="dead")],
                            projects=projects, specs=specs))
        self.assertEqual(acts, [])

    def test_verify_only_for_specs_of_own_project(self):
        # PR #8 Review R1: Spec eines abgeschalteten Projekts bekommt kein Verify
        other_done = [ticket("EX-5", project="other", spec="EX-200", status="Done")]
        specs = {"EX-200": {"project": "other", "verified": False}}
        projects = {"slickfab": project(), "other": project(enabled=False)}
        self.assertEqual(decide(state(other_done, projects=projects, specs=specs)), [])

    def test_red_main_starts_debug_once_per_commit(self):
        red = {"slickfab": project(main=main_(sha="m1", ci="red", checked="m1"))}
        self.assertEqual(decide(state(projects=red)),
                         [{"action": "start_debug", "project": "slickfab", "sha": "m1"}])
        red["slickfab"]["main"]["debugged_sha"] = "m1"
        self.assertEqual(decide(state(projects=red)), [])
        for ci in ("green", "pending"):
            self.assertEqual(decide(state(projects={"slickfab": project(main=main_("m1", ci, "m1"))})), [], ci)

    def test_dead_project_agent_is_watched_even_without_due_work(self):
        # main geprüft, grün, keine Retro fällig: der tote Agent wird trotzdem gemeldet (Review A2)
        for role, issue in (("check", "slickfab"), ("debug", "slickfab"), ("retro", "slickfab"),
                            ("verify", "EX-100")):
            acts = decide(state(terminals=[terminal("c1", issue, role=role, status="dead")]))
            self.assertEqual([(a["action"], a["terminal"]) for a in acts], [("restart_agent", "c1")], role)

    def test_garbled_project_agent_reported_once(self):
        bad = terminal("c1", "slickfab", role="check", seq="x")
        acts = decide(state(terminals=[bad], projects={"slickfab": project(main=main_(ci="red"),
                                                                           merges=10)}))
        self.assertEqual(kinds(acts), ["needs_human"])

    def test_project_agent_restart_cap_and_obsolete_terminals(self):
        capped = [terminal("c1", "slickfab", role="check", status="dead", seq=1, **{"slickfab.restarts": "1"}),
                  terminal("c2", "slickfab", role="check", status="dead", seq=2)]
        self.assertEqual(kinds(decide(state(terminals=capped))), ["needs_human"])
        obsolete = [terminal("c1", "slickfab", role="check", status="dead", seq=1),
                    terminal("c2", "slickfab", role="check", status="done", seq=2)]
        self.assertEqual(decide(state(terminals=obsolete)), [])
        # ein überholtes totes Terminal hält neue Arbeit nicht auf
        due = decide(state(terminals=obsolete, projects={"slickfab": project(main=main_())}))
        self.assertEqual(kinds(due), ["post_merge_check"])

    def test_dead_project_agent_restarts_once(self):
        p = {"slickfab": project(main=main_())}
        first = decide(state(terminals=[terminal("c1", "slickfab", role="check", status="dead")], projects=p))
        self.assertEqual([(a["action"], a["terminal"], a["ticket"]) for a in first],
                         [("restart_agent", "c1", None)])
        second = decide(state(terminals=[terminal("c1", "slickfab", role="check", status="dead",
                                                  **{"slickfab.restarts": "1"})], projects=p))
        self.assertEqual([(a["action"], a["ticket"]) for a in second], [("needs_human", None)])


KNOWN_ACTIONS = {"start_implementer", "start_reviewer", "send_rework", "label", "merge", "needs_human",
                 "restart_agent", "post_merge_check", "start_debug", "start_retro", "start_verify"}


def busy_state():
    """Ein Zustand, in dem jede Regel etwas zu tun hätte."""
    return state(
        [ticket("EX-1"), ticket("EX-2", status="In Review", pr=pr()),
         ticket("EX-3", status="In Progress", pr=pr(8)), ticket("EX-4", status="Done", spec="EX-200"),
         ticket("EX-5", status="In Review", rework_rounds=1, pr=pr(9))],
        [terminal("t2", "EX-2", status="done", report=DONE),
         terminal("t3", "EX-3", status="dead"),
         terminal("t5a", "EX-5", status="done", report=DONE, seq=1),
         terminal("t5b", "EX-5", role="reviewer", status="done", report=review_verdict("REWORK"), seq=2)],
        {"slickfab": project(main=main_(ci="red"), merges=10, max_parallel=5)},
        {"EX-100": {"project": "slickfab", "verified": False},
         "EX-200": {"project": "slickfab", "verified": False}})


class Boundaries(unittest.TestCase):
    def test_busy_state_has_work_for_every_rule(self):
        self.assertEqual(set(kinds(decide(busy_state()))),
                         {"start_implementer", "start_reviewer", "restart_agent", "send_rework",
                          "post_merge_check", "start_debug", "start_retro", "start_verify"})

    def test_project_without_enabled_gets_no_action(self):
        for enabled in (False, None, "yes", 1):
            st = busy_state()
            st["projects"]["slickfab"]["enabled"] = enabled
            self.assertEqual(decide(st), [], enabled)
        st = busy_state()
        del st["projects"]["slickfab"]["enabled"]
        self.assertEqual(decide(st), [])

    def test_ticket_of_unknown_project_gets_no_action(self):
        self.assertEqual(decide(state([ticket("EX-1", project="other")])), [])

    def test_terminals_without_dispatch_label_get_no_action(self):
        foreign = [terminal("x2", "EX-2", status="done", report=DONE),
                   terminal("x3", "EX-3", status="dead"),
                   terminal("x5", "EX-5", role="reviewer", status="done", report=review_verdict("MERGE"))]
        for term in foreign:
            term["labels"]["slickfab.dispatch"] = "0"
        del foreign[1]["labels"]["slickfab.dispatch"]
        tickets = [ticket("EX-2", status="In Review", pr=pr()), ticket("EX-3", status="In Progress"),
                   ticket("EX-5", status="In Review", pr=pr())]
        acts = decide(state(tickets, foreign))
        self.assertEqual(acts, [])
        self.assertFalse([a for a in acts if a.get("terminal", "").startswith("x")])

    def test_foreign_terminal_with_odd_labels_is_ignored(self):
        odd = {"id": "x9", "labels": {"studio.issue": ["EX-1"], "slickfab.dispatch": "0"}, "status": "idle"}
        odd2 = {"id": "x8", "labels": {"studio.issue": {"a": 1}}, "status": "idle"}
        self.assertEqual(starts(decide(state([ticket("EX-1")], [odd, odd2]))), ["EX-1"])

    def test_foreign_terminal_on_todo_ticket_blocks_start(self):
        term = terminal("x1", "EX-1")
        del term["labels"]["slickfab.dispatch"]
        self.assertEqual(decide(state([ticket("EX-1")], [term])), [])


class Idempotence(unittest.TestCase):
    def test_same_state_twice_gives_same_actions(self):
        self.assertEqual(decide(busy_state()), decide(busy_state()))

    def test_order_of_input_lists_does_not_matter(self):
        st = busy_state()
        expected = decide(st)
        rnd = random.Random(7)
        for _ in range(10):
            shuffled = copy.deepcopy(st)
            rnd.shuffle(shuffled["tickets"])
            rnd.shuffle(shuffled["terminals"])
            self.assertEqual(decide(shuffled), expected)

    def test_state_is_not_modified(self):
        st = busy_state()
        before = copy.deepcopy(st)
        decide(st)
        self.assertEqual(st, before)

    def test_started_actions_are_not_planned_again(self):
        # Der Zustand nach Ausführung der Aktionen aus busy_state: alles läuft.
        st = busy_state()
        st["terminals"] = [terminal("t1", "EX-1"), terminal("t2", "EX-2"),
                           terminal("t2r", "EX-2", role="reviewer", seq=2),
                           terminal("t3", "EX-3", **{"slickfab.restarts": "1"}),
                           terminal("t5a", "EX-5", seq=3),
                           terminal("c", "slickfab", role="check"), terminal("d", "slickfab", role="debug"),
                           terminal("r", "slickfab", role="retro"), terminal("v", "EX-200", role="verify")]
        self.assertEqual(decide(st), [])


class Robustness(unittest.TestCase):
    def assert_safe(self, st):
        acts = decide(st)
        self.assertIsInstance(acts, list)
        for a in acts:
            self.assertIn(a["action"], KNOWN_ACTIONS)
        return acts

    def test_broken_state_needs_human_instead_of_exception(self):
        for st in (None, [], "x", {"projects": "x"}, {"projects": {"slickfab": None}},
                   {"assignee": BOT, "projects": {"slickfab": project()}, "tickets": "x"}):
            acts = self.assert_safe(st)
            self.assertEqual(kinds(acts), ["needs_human"], st)
            self.assertIn("Zustand", acts[0]["reason"])

    def test_duplicate_ticket_ids_need_human(self):
        acts = self.assert_safe(state([ticket("EX-1"), ticket("EX-1", files=["x"])]))
        self.assertEqual(kinds(acts), ["needs_human"])
        self.assertIn("doppelt", acts[0]["reason"])
        self.assertEqual(acts[0]["project"], "slickfab")

    def test_error_inside_one_project_does_not_stop_another(self):
        # Re-Review PR #8 R-neu-2: das Netz je Projekt, nicht nur der Filter davor
        class Boom(str):
            def isdigit(self):
                raise RuntimeError("kaputtes Label")
        for raw in ("²", Boom("0")):  # "²".isdigit() ist wahr, int("²") wirft ValueError
            projects = {"a": project(), "b": project()}
            tickets = [ticket("EX-1", project="a", status="In Progress"), ticket("EX-2", project="b")]
            terms = [terminal("t1", "EX-1", status="dead", **{"slickfab.restarts": raw})]
            acts = self.assert_safe(state(tickets, terms, projects, specs={}))
            self.assertEqual(starts(acts), ["EX-2"], raw)
            self.assertEqual([(a["action"], a["project"], a["ticket"]) for a in acts if a["action"] == "needs_human"],
                             [("needs_human", "a", None)], raw)

    def test_broken_foreign_project_does_not_stop_others(self):
        # PR #8 Review R2: Fehler bleiben im betroffenen Projekt
        for broken in ("broken", None, ["x"]):
            acts = self.assert_safe(state([ticket("EX-1")], projects={"slickfab": project(), "other": broken}))
            self.assertEqual(starts(acts), ["EX-1"], broken)
            self.assertEqual(kinds(acts), ["start_implementer"], broken)

    def test_duplicate_ids_stay_in_their_project(self):
        projects = {"slickfab": project(), "other": project(enabled=False), "third": project()}
        dup_other = [ticket("EX-1"), ticket("EX-5", project="other"), ticket("EX-5", project="other")]
        self.assertEqual(starts(decide(state(dup_other, projects=projects))), ["EX-1"])
        dup_third = [ticket("EX-1"), ticket("EX-5", project="third"), ticket("EX-5", project="third")]
        acts = decide(state(dup_third, projects=projects))
        self.assertEqual(starts(acts), ["EX-1"])
        self.assertEqual([(a["action"], a["project"]) for a in acts if a["action"] == "needs_human"],
                         [("needs_human", "third")])

    def test_broken_ticket_needs_human_others_continue(self):
        broken = ticket("EX-1", labels="S", blockers=[None], files=7)
        acts = self.assert_safe(state([broken, ticket("EX-2")]))
        self.assertEqual(starts(acts), ["EX-2"])
        self.assertEqual(len(needs_human(acts, "EX-1")), 1)

    def test_random_garbage_never_raises(self):
        rnd = random.Random(1234)
        junk = [None, "", "x", 0, -1, 3.5, [], {}, [None], {"a": None}, True]
        for i in range(400):
            st = busy_state()
            for _ in range(rnd.randint(1, 4)):
                target = rnd.choice(st["tickets"] + st["terminals"] + [st["projects"]["slickfab"]])
                key = rnd.choice(sorted(target))
                target[key] = rnd.choice(junk)
            self.assert_safe(st)

    def test_no_network_no_processes_no_files(self):
        def forbidden(*a, **k):
            raise AssertionError("externer Aufruf aus decide")
        with mock.patch.object(socket, "socket", forbidden), \
                mock.patch.object(subprocess, "Popen", forbidden), \
                mock.patch.object(builtins, "open", forbidden):
            self.assertTrue(decide(busy_state()))


if __name__ == "__main__":
    unittest.main()
