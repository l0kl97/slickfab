"""Entscheidungslogik des Autopiloten: decide(state) -> actions.

Reine Funktion: liest nur das übergebene `state`, schreibt nichts, ruft nichts
Externes auf und verändert die Eingabe nicht. Gleicher Zustand ergibt dieselben
Aktionen in derselben Reihenfolge. Form von `state` und `actions`:
docs/features/slickfab-dispatch.md. Nur Python-Standardbibliothek (3.9).
"""
import re

SIZES = ("S", "M", "L")
# Vom Maintainer entschieden am 2026-11-24: S = Sonnet 5.5, M und L = Opus 5.5 (Aliase für slickfab-run).
# Runde 3 der Nachbesserung: frischer Umsetzer auf Opus mit höherer Reasoning-Effort.
MODEL_BY_SIZE = {"S": "sonnet", "M": "opus", "L": "opus"}
FRESH_MODEL = "opus"
FRESH_EFFORT = "high"  # None = Standard der Rolle
CI_VALUES = ("green", "red", "pending", None)  # None = noch kein Stand
# Projekt-Schalter: use = GitHub-Checks zählen (Standard); ignore = gelten als nicht vorhanden,
# für main zählt nur die lokale Prüfung (liefert die Ausführung), für PRs nur das Review.
GITHUB_CI_VALUES = ("use", "ignore")
# GitHub `mergeable` des PRs; UNKNOWN und None (fehlt) heißen: noch nicht berechnet, kein Merge
MERGEABLE_VALUES = ("MERGEABLE", "CONFLICTING", "UNKNOWN", None)
SAME_IMPLEMENTER_ROUNDS = 2
MAX_REWORK_ROUNDS = 3
DEFAULT_MAX_PARALLEL = 3
CLOSED_STATE_TYPES = ("completed", "canceled", "duplicate")
# Specs in diesen Linear-Statustypen bekommen keinen Verifier mehr (duplicate bewusst nicht)
CLOSED_SPEC_STATE_TYPES = ("completed", "canceled")
ACTIVE_STATUSES = ("In Progress", "In Review")
DISPATCH_LABEL = ("slickfab.dispatch", "1")
STATUSES = ("DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT")
VERDICTS = ("MERGE", "REWORK", "REPLAN")
FINISHED = ("done", "idle")
WAITING = ("working", "blocked")
DEAD = "dead"
MAX_RESTARTS = 1
RETRO_EVERY = 10
PROJECT_ROLES = ("check", "debug", "retro", "verify")
CLOSED_STATUSES = ("Done", "Canceled", "Duplicate")
GROUP_LABELS = ("slickfab:rework", "slickfab:ready", "slickfab:needs-human", "slickfab:replan")
HALT_LABELS = ("slickfab:ready", "slickfab:needs-human", "slickfab:replan")
ONE_WAY = "door:one-way"
# Pfade, die nie automatisch gemergt werden (Auth, Migration, .env, RLS, CI-Workflows,
# dazu die Bremsen selbst: Git-Hooks, slickrails-, Claude- und Codex-Konfiguration, das ganze
# Plugin-Verzeichnis hooks/ mit seinen Wächtern und der Autopilot selbst: diese Regeln, sein
# ausführender Teil slickfab-dispatch mit slickfab-run, slickfab-worktree mit Baseline und Vergleich
# und die Werkzeuggrenzen: Rollen in agents/ mit disallowedTools, deren Übersetzung in
# slickfab_templates.py/gen-templates und die erzeugten Vorlagen in runtime/herdr/templates/).
# agents/ nur auf Repo-Ebene: ein src/agents/ in einem App-Projekt ist keine Bremse. Dazu die
# Merge-Bedingung des Reviewers (skills/review/), der Prüfbefehl tests/run.sh mit seinen
# Prüfskripten tests/check_*.py und die Fabrik-Konfiguration .slickfab/; normale Testdateien
# bleiben nicht sensibel. Groß/klein egal.
SENSITIVE_PATHS = tuple(re.compile(p, re.I) for p in (
    r"auth", r"migrat", r"(^|/)\.env", r"(^|[/_.-])rls([/_.-]|$)", r"(^|/)\.github/workflows/",
    r"(^|/)\.githooks/", r"(^|/)\.slickrails/", r"(^|/)hooks/", r"(^|/)\.claude/",
    r"(^|/)\.codex/", r"(^|/)runtime/herdr/slickfab_dispatch\.py$",
    r"(^|/)runtime/herdr/slickfab-dispatch$", r"(^|/)runtime/herdr/slickfab-run$",
    r"(^|/)runtime/herdr/slickfab-worktree$", r"(^|/)runtime/herdr/slickfab_templates\.py$",
    r"(^|/)runtime/herdr/gen-templates$", r"^agents/", r"(^|/)runtime/herdr/templates/",
    r"^skills/review/", r"^tests/run\.sh$", r"^tests/check_[^/]*\.py$", r"(^|/)\.slickfab/",
))
STATUS_RE = re.compile(r"^SLICKFAB-STATUS: ([A-Z_]+)$")
VERDICT_RE = re.compile(r"^SLICKFAB-VERDICT: ([A-Z_]+)$")


def _num(ticket_id):
    m = re.search(r"(\d+)$", str(ticket_id))
    return (str(ticket_id).rsplit("-", 1)[0], int(m.group(1)) if m else 0, str(ticket_id))


def _size(labels):
    found = [l for l in labels if l in SIZES]
    return found[0] if len(found) == 1 else None


def _open_blockers(ticket):
    return [b["id"] for b in ticket.get("blockers") or [] if b.get("state_type") not in CLOSED_STATE_TYPES]


def _is_dispatch(term):
    labels = term.get("labels") or {}
    return labels.get(DISPATCH_LABEL[0]) == DISPATCH_LABEL[1]


def parse_marker(report, role):
    """(status, verdict, fehler). Genau die Zeilen aus tracker/linear.md, nichts danach."""
    lines = (report or "").rstrip().splitlines()
    if not lines:
        return None, None, "kein Marker in der Rückmeldung"
    m = STATUS_RE.match(lines[-1])
    if not m or m.group(1) not in STATUSES:
        return None, None, "unbekannter oder fehlender Marker in der letzten Zeile: %r" % lines[-1][:80]
    status = m.group(1)
    v = VERDICT_RE.match(lines[-2]) if len(lines) > 1 else None
    if role == "reviewer":
        if not v:
            return status, None, "Reviewer beendet ohne SLICKFAB-VERDICT (STATUS %s)" % status
        if v.group(1) not in VERDICTS:
            return status, None, "unbekannter Marker SLICKFAB-VERDICT: %s" % v.group(1)
        return status, v.group(1), None
    if v or (len(lines) > 1 and lines[-2].startswith("SLICKFAB-VERDICT")):
        return status, None, "widersprüchlicher Marker: VERDICT-Zeile von Rolle %s" % role
    return status, None, None


def _youngest(terms):
    """Jüngstes Terminal (größtes seq); ältere sind überholt und werden nie neu gestartet."""
    return max(terms, key=lambda x: (x["seq"], x["id"]))


def _needs_human(ticket, reason):
    return {"action": "needs_human", "ticket": ticket["id"], "project": ticket["project"], "reason": reason}


def _is_str_list(x):
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _opt(x, kind):
    return x is None or isinstance(x, kind)


def _ticket_error(t):
    """Grund, warum ein Ticket nicht lesbar ist, sonst None. Kein Raten bei falschen Typen."""
    if not _is_str_list(t.get("labels")):
        return "labels ist keine Liste von Texten"
    if not _is_str_list(t.get("files")):
        return "files ist keine Liste von Texten"
    blockers = t.get("blockers")
    if not isinstance(blockers, list) or not all(
            isinstance(b, dict) and isinstance(b.get("id"), str) and isinstance(b.get("state_type"), str)
            for b in blockers):
        return "blockers ist keine Liste aus {id, state_type}"
    if not _is_int(t.get("rework_rounds")):
        return "rework_rounds ist keine Zahl"
    if not _opt(t.get("spec"), str):
        return "spec ist kein Text"
    if "human_gate" in t and not isinstance(t["human_gate"], bool):
        return "human_gate ist nicht true/false"
    pr = t.get("pr")
    if pr is not None:
        if not isinstance(pr, dict) or not _is_int(pr.get("number")):
            return "pr ist kein Objekt mit Nummer"
        if pr.get("ci") not in CI_VALUES:
            return "pr.ci %r liegt außerhalb des Vertrags (green, red, pending, None)" % (pr.get("ci"),)
        if pr.get("mergeable") not in MERGEABLE_VALUES:
            return ("pr.mergeable %r liegt außerhalb des Vertrags (MERGEABLE, CONFLICTING, UNKNOWN, None)"
                    % (pr.get("mergeable"),))
        comments = pr.get("comments") or []
        if not isinstance(comments, list) or not all(
                isinstance(c, dict) and _opt(c.get("author"), str) and _is_int(c.get("at"))
                and isinstance(c.get("url"), str) and isinstance(c.get("body"), str) for c in comments):
            return "pr.comments ist keine Liste aus {author, at, url, body}"
        if not (_opt(pr.get("head"), str)
                and (pr.get("paths") is None or _is_str_list(pr.get("paths")))
                and isinstance(pr.get("merged"), bool)):
            return "pr hat Felder mit falschem Typ"
    return None


def _terminal_error(term):
    if not (isinstance(term.get("id"), str) and isinstance(term.get("status"), str)
            and _is_int(term.get("seq")) and _opt(term.get("report"), str)
            and all(isinstance(v, str) for v in term["labels"].values())):
        return "Terminal %r unlesbar (id, status, seq, report, labels)" % (term.get("id"),)
    return None


def _project_error(proj):
    if not (_is_int(proj.get("max_parallel", DEFAULT_MAX_PARALLEL)) and _is_int(proj.get("merges", 0))
            and _is_int(proj.get("retro_at", 0))):
        return "max_parallel, merges oder retro_at ist keine Zahl"
    if proj.get("github_ci", "use") not in GITHUB_CI_VALUES:
        return "github_ci %r liegt außerhalb des Vertrags (use, ignore)" % (proj.get("github_ci"),)
    if not _is_str_list(proj.get("comment_authors", [])):
        return "comment_authors ist keine Liste von Texten"
    main = proj.get("main", {})
    if not isinstance(main, dict) or not all(_opt(main.get(k), str)
                                             for k in ("sha", "ci", "checked_sha", "debugged_sha")):
        return "main ist kein Objekt aus Texten"
    return None


def decide(state):
    """Zustand -> geplante Aktionen. Wirft nie; Unlesbares wird needs_human mit Grund."""
    try:
        return _decide(state)
    except Exception as exc:  # Sicherheitsnetz: lieber anhalten als raten
        return [{"action": "needs_human", "ticket": None, "project": None,
                 "reason": "Zustand unlesbar: %s: %s" % (type(exc).__name__, exc)}]


def _decide(state):
    if not isinstance(state, dict):
        raise ValueError("state ist kein Objekt")
    me = state.get("assignee")
    projects = state.get("projects")
    tickets = state.get("tickets", [])
    terminals = state.get("terminals", [])
    specs = state.get("specs", {})
    if not isinstance(projects, dict):
        raise ValueError("projects ist kein Objekt")
    if not (isinstance(tickets, list) and isinstance(terminals, list) and isinstance(specs, dict)):
        raise ValueError("tickets/terminals sind keine Listen oder specs kein Objekt")
    if not isinstance(me, str) or not me:
        raise ValueError("assignee fehlt")

    by_issue, bad_issues, foreign = {}, {}, set()
    for term in terminals:
        if not isinstance(term, dict) or not isinstance(term.get("labels"), dict):
            continue  # ohne Labels nicht als eigenes Terminal erkennbar: nie anfassen
        issue = term["labels"].get("studio.issue")
        if not isinstance(issue, str):
            continue  # keinem Ticket zuzuordnen: nie anfassen
        if not _is_dispatch(term):
            foreign.add(issue)
            continue
        err = _terminal_error(term)
        if err:
            bad_issues.setdefault(issue, err)
        else:
            by_issue.setdefault(issue, []).append(term)
    tickets = sorted((t for t in tickets if isinstance(t, dict) and isinstance(t.get("id"), str)),
                     key=lambda t: _num(t["id"]))
    seen, dups = set(), set()
    for t in tickets:
        (dups if t["id"] in seen else seen).add(t["id"])

    actions = []
    for name in sorted(p for p in projects if isinstance(p, str)):
        proj = projects[name]
        # Nur freigeschaltete Projekte; ein kaputter Eintrag ist nie freigeschaltet und stört
        # die anderen nicht. Fehler bleiben in ihrem Projekt.
        if not isinstance(proj, dict) or proj.get("enabled") is not True:
            continue
        try:
            err = _project_error(proj)
            own_dups = sorted({t["id"] for t in tickets if t.get("project") == name and t["id"] in dups},
                              key=_num)
            if own_dups:
                err = "Ticket-IDs doppelt: " + ", ".join(own_dups)
            if err:
                actions.append({"action": "needs_human", "ticket": None, "project": name,
                                "reason": "Zustand unlesbar: " + err})
                continue
            own = tickets
            if proj.get("github_ci", "use") == "ignore":
                own = [_without_github_ci(t) for t in tickets]   # nur Kopien, gelesen werden die eigenen
            planned = _project_tickets(name, proj, me, own, by_issue, bad_issues, foreign)
            planned += _project_actions(name, proj, specs, own, by_issue, bad_issues)
        except Exception as exc:  # Sicherheitsnetz je Projekt
            planned = [{"action": "needs_human", "ticket": None, "project": name,
                        "reason": "Zustand unlesbar: %s: %s" % (type(exc).__name__, exc)}]
        actions.extend(planned)
    return actions


def _without_github_ci(t):
    """github_ci = ignore: GitHub-Checks am PR gelten als nicht vorhanden (Kopie, state bleibt)."""
    if isinstance(t.get("pr"), dict):
        return dict(t, pr=dict(t["pr"], ci=None))
    return t


def _project_tickets(name, proj, me, tickets, by_issue, bad_issues, foreign):
    actions, mine, ready = [], [], []
    for t in tickets:
        if t.get("project") != name or t.get("assignee") != me:
            continue
        if t.get("status") not in ("Todo",) + ACTIVE_STATUSES:
            continue
        err = _ticket_error(t) or bad_issues.get(t["id"])
        if err and _is_str_list(t.get("labels")) and "slickfab:needs-human" in t["labels"]:
            continue  # schon beim Menschen geparkt: kein erneutes needs_human je Tick
        if err:
            actions.append(_needs_human(t, "Ticket unlesbar: " + err))
            continue
        labels = t["labels"]
        if "slickfab:needs-human" in labels:
            continue
        group = [l for l in GROUP_LABELS if l in labels]
        if len(group) > 1:
            actions.append(_needs_human(t, "widersprüchliche Labels: " + ", ".join(group)))
            continue
        if group == ["slickfab:ready"] and _size(labels) is not None:
            ready.append(t)  # wartet auf den Menschen; nur dessen PR-Kommentare holen es zurück (Review A1)
            continue
        if group and group[0] in HALT_LABELS:
            continue
        if _size(labels) is None:
            actions.append(_needs_human(t, "Größe unbekannt: genau eines von S, M, L erwartet"))
            continue
        mine.append(t)
    # Mit eigenem Terminal läuft ein Ticket, auch wenn Linear noch Todo zeigt. Für Obergrenze
    # und Dateischutz zählen auch angehaltene (ready/needs-human/replan) und unlesbare Tickets.
    active = [t for t in mine if by_issue.get(t["id"])]
    active_ids = {t["id"] for t in active}
    occupying = [t for t in tickets if t.get("project") == name and t.get("assignee") == me
                 and t.get("status") in ("Todo",) + ACTIVE_STATUSES
                 and (by_issue.get(t["id"]) or t["id"] in bad_issues)]
    busy_files = set()
    for t in occupying:
        if _is_str_list(t.get("files")):
            busy_files.update(t["files"])
    running = len(occupying)
    limit = proj.get("max_parallel", DEFAULT_MAX_PARALLEL)
    for t in mine:
        if t["status"] != "Todo" or t["id"] in active_ids or t["id"] in foreign:
            continue
        if _open_blockers(t):
            continue
        files = set(t["files"])
        if files & busy_files or running >= limit:
            continue
        actions.append({"action": "start_implementer", "ticket": t["id"], "project": name,
                        "model": MODEL_BY_SIZE[_size(t["labels"])], "effort": None,
                        "worktree": t["id"].lower(), "fresh": False})
        busy_files |= files
        running += 1
    watched = [(t, False) for t in active] + [(t, True) for t in ready if by_issue.get(t["id"])]
    for t, is_ready in sorted(watched, key=lambda x: _num(x[0]["id"])):
        terms = by_issue[t["id"]]
        actions.extend(_ready_comments(t, terms, proj) if is_ready else _in_flight(t, terms, proj))
    return actions


def _ready_comments(t, terms, proj):
    """Ticket mit `slickfab:ready`: Genau dann liest der Mensch den PR. Ein neuer Kommentar eines erlaubten
    Autors geht als Runde an den Umsetzer, das Label kommt dabei ab; nie ein Merge (Review A1)."""
    if _youngest(terms)["status"] in WAITING:
        return []
    fresh = _fresh_comments(t, terms, proj)
    if not fresh:
        return []
    acts = _on_comments(t, terms, "implementer", None, fresh)
    for a in acts:
        if a["action"] in ("send_rework", "start_implementer"):
            a["unlabel"] = "slickfab:ready"
    return acts


def _project_actions(name, proj, specs, tickets, by_issue, bad_issues):
    """Nach dem Merge: Prüfung auf dem Hauptzweig, Debug bei rotem CI, Retro, Verify."""
    me = {"id": None, "project": name}
    actions = []

    # Wächter zuerst und unabhängig davon, ob gerade neue Arbeit fällig ist.
    own_specs = sorted((i for i, sp in specs.items() if isinstance(sp, dict) and sp.get("project") == name),
                       key=_num)
    for issue in [name] + own_specs:
        if issue in bad_issues:
            actions.append(_needs_human(me, bad_issues[issue]))
            continue
        for role in PROJECT_ROLES:
            terms = [x for x in by_issue.get(issue, []) if x["labels"].get("studio.role") == role]
            if terms and _youngest(terms)["status"] == DEAD:
                actions.append(_restart_or_human(me, _youngest(terms), terms, "Agent tot"))

    def busy(role, issue):
        """True, wenn der jüngste Agent dieser Rolle läuft, tot ist (Wächter oben) oder unlesbar."""
        terms = [x for x in by_issue.get(issue, []) if x["labels"].get("studio.role") == role]
        return issue in bad_issues or bool(terms) and _youngest(terms)["status"] not in FINISHED

    main = proj.get("main") or {}
    sha = main.get("sha")
    if sha and sha != main.get("checked_sha") and not busy("check", name):
        actions.append({"action": "post_merge_check", "project": name, "sha": sha})
    if sha and main.get("ci") == "red" and sha != main.get("debugged_sha") and not busy("debug", name):
        actions.append({"action": "start_debug", "project": name, "sha": sha})
    merges, retro_at = proj.get("merges", 0), proj.get("retro_at", 0)
    if merges - retro_at >= RETRO_EVERY and not busy("retro", name):
        actions.append({"action": "start_retro", "project": name, "merges": merges})
    for spec_id in sorted(specs, key=_num):
        spec = specs[spec_id]
        if not isinstance(spec, dict) or spec.get("project") != name:
            continue
        if not isinstance(spec.get("verified"), bool):
            actions.append(_needs_human({"id": spec_id, "project": name}, "Spec unlesbar: verified fehlt"))
            continue
        if spec["verified"] or spec.get("state_type") in CLOSED_SPEC_STATE_TYPES:
            continue  # selbst verifiziert oder in Linear schon geschlossen
        children = [t for t in tickets if t.get("spec") == spec_id]
        statuses = [t.get("status") for t in children]
        if ("Done" in statuses and all(st in CLOSED_STATUSES for st in statuses)
                and not busy("verify", spec_id)):
            actions.append({"action": "start_verify", "project": name, "spec": spec_id})
    return actions


def _in_flight(t, terms, proj):
    """Ticket in Arbeit mit Dispatch-Terminals: Wächter, dann Marker des letzten Terminals."""
    current = _youngest(terms)
    status_ = current["status"]
    if status_ == DEAD:
        return [_restart_or_human(t, current, terms, "Agent tot")]
    if status_ in WAITING:
        return []
    if status_ not in FINISHED:
        return [_needs_human(t, "unbekannter Terminal-Status %r bei %s" % (status_, current.get("id")))]
    role = current["labels"].get("studio.role")
    status, verdict, err = parse_marker(current.get("report"), role)
    if err:
        return [_needs_human(t, err)]
    if status == "BLOCKED":
        return [_needs_human(t, "%s meldet BLOCKED" % role)]
    known = role in ("implementer", "reviewer")
    fresh = _fresh_comments(t, terms, proj) if known else []
    if fresh and not (role == "reviewer" and verdict == "REPLAN"):
        return _on_comments(t, terms, role, verdict, fresh)
    if status == "NEEDS_CONTEXT":
        return [_restart_or_human(t, current, terms, "%s meldet NEEDS_CONTEXT" % role)]
    if not known:
        return [_needs_human(t, "unbekannte Rolle %r am Ticket" % (role,))]
    if role == "reviewer":
        return _after_review(t, terms, current, status, verdict, proj)
    if role == "implementer":
        if status in ("DONE", "DONE_WITH_CONCERNS"):
            pr = t.get("pr")
            if not pr or not pr.get("number"):
                return [_needs_human(t, "Umsetzer meldet %s, aber kein offener Pull Request" % status)]
            if pr.get("merged"):
                return []
            return [{"action": "start_reviewer", "ticket": t["id"], "project": t["project"],
                     "pr": pr["number"], "head": pr.get("head"), "worktree": "pr-%s" % pr["number"]}]
    return []


def _is_report(body):
    """Bericht einer Rolle (Marker-Block am Ende), kein Kommentar eines Menschen."""
    lines = body.rstrip().splitlines()
    return bool(lines) and lines[-1].startswith("SLICKFAB-STATUS:")


def _fresh_comments(t, terms, proj):
    """URLs der PR-Kommentare erlaubter Autoren, die der Umsetzer noch nicht bekommen hat.

    Erlaubt sind nur die Logins aus `comment_authors` des Projekts (Factory-Konfiguration), nie
    etwas aus Ticketdaten. Neu heißt: jünger als der letzte Auftrag an den Umsetzer (sein seq, ms);
    ohne Umsetzer-Terminal zählt das jüngste Terminal. Berichte der Rollen zählen nicht."""
    pr = t.get("pr") or {}
    if pr.get("merged"):
        return []
    allowed = {a.lower() for a in proj.get("comment_authors") or []}
    impls = [x for x in terms if x["labels"].get("studio.role") == "implementer"]
    since = _youngest(impls or terms)["seq"]
    return [c["url"] for c in sorted(pr.get("comments") or [], key=lambda c: (c["at"], c["url"]))
            if isinstance(c["author"], str) and c["author"].lower() in allowed and c["at"] > since
            and not _is_report(c["body"])]


def _on_comments(t, terms, role, verdict, fresh):
    """Neue Kommentare erlaubter Autoren: zurück an den Umsetzer (oder ab der Obergrenze an den
    Menschen), nie ein Merge. Mit REWORK-Verdict ist es dieselbe Runde, sonst eine eigene."""
    pr, rounds = t.get("pr") or {}, t.get("rework_rounds")
    if role == "reviewer" and verdict == "REWORK":
        return _rework(t, terms, pr, rounds, comments=fresh)
    cause = _pr_causes(pr) if role == "reviewer" and verdict == "MERGE" else []
    return _rework(t, terms, pr, rounds + 1 if _is_int(rounds) else rounds, cause + ["comment"], fresh)


def _pr_causes(pr):
    """Rotes CI und Konflikte mit main: Anlässe für eine Runde ohne REWORK-Verdict."""
    return [c for c, hit in (("ci", pr.get("ci") == "red"), ("conflict", pr.get("mergeable") == "CONFLICTING"))
            if hit]


def _restart_or_human(t, term, terms, reason):
    """Wächter: einmal neu starten mit Übergabe, danach entscheidet ein Mensch.

    Der Deckel gilt je Ticket (bzw. Projekt-Issue) und Rolle: gezählt wird das Maximum von
    slickfab.restarts über alle Terminals dieser Rolle, auch über alte, ersetzte."""
    role = term["labels"].get("studio.role")
    done = 0
    for other in terms:
        if other["labels"].get("studio.role") != role:
            continue
        raw = other["labels"].get("slickfab.restarts", "0")
        if not raw.isdigit():
            return _needs_human(t, "%s; Neustart-Zähler unlesbar (%r bei %s)" % (reason, raw, other["id"]))
        done = max(done, int(raw))
    if done >= MAX_RESTARTS:
        return _needs_human(t, "%s nach %d Neustart(s) bei %s" % (reason, done, term.get("id")))
    return {"action": "restart_agent", "ticket": t["id"], "project": t["project"], "terminal": term["id"],
            "role": term["labels"].get("studio.role"), "handoff": True, "restarts": done + 1, "reason": reason}


def _label(t, label, reason):
    return {"action": "label", "ticket": t["id"], "project": t["project"], "label": label, "reason": reason}


def _after_review(t, terms, reviewer, status, verdict, proj):
    pr = t.get("pr") or {}
    if verdict == "REPLAN":
        return [_label(t, "slickfab:replan", "Reviewer: REPLAN")]
    if verdict == "REWORK":
        return _rework(t, terms, pr, t.get("rework_rounds"))
    if pr.get("merged"):
        return []
    # Rotes CI und Konflikte mit main gehen nie als ready zum Menschen, sondern zurück an den
    # Umsetzer, als eigene Runde unter derselben Obergrenze (die Ausführung bucht sie am Ticket).
    cause = _pr_causes(pr)
    if cause:
        rounds = t.get("rework_rounds")
        return _rework(t, terms, pr, rounds + 1 if _is_int(rounds) else rounds, cause)
    reasons = _merge_blockers(t, reviewer, status, pr, proj)
    if reasons:
        return [_label(t, "slickfab:ready", "kein Auto-Merge: " + "; ".join(reasons))]
    ci_ok = pr.get("ci") == "green" or proj.get("github_ci") == "ignore"   # ignore: das Review zählt
    if not ci_ok or pr.get("mergeable") != "MERGEABLE":
        return []  # CI läuft noch oder Mergebarkeit ist unklar: Auto-Merge wartet, gemergt wird nie
    return [{"action": "merge", "ticket": t["id"], "project": t["project"], "pr": pr["number"], "head": pr["head"]}]


def _rework(t, terms, pr, n, cause=None, comments=None):
    """Nachbesserung Runde n. `cause` gesetzt: Runde ohne REWORK-Verdict, die Ausführung bucht sie."""
    if not isinstance(n, int) or n < 1:
        return [_needs_human(t, "REWORK ohne gültige Rundenzahl (rework_rounds=%r)" % (n,))]
    if n > MAX_REWORK_ROUNDS:
        return [_needs_human(t, "Nachbessern erschöpft: Runde %d von höchstens %d" % (n, MAX_REWORK_ROUNDS))]
    base = MODEL_BY_SIZE[_size(t.get("labels") or [])]
    start = {"action": "start_implementer", "ticket": t["id"], "project": t["project"], "model": base,
             "effort": None, "worktree": t["id"].lower(), "fresh": True, "round": n, "pr": pr.get("number")}
    extra = {"cause": cause} if cause else {}
    if comments:
        extra["comments"] = comments
    start.update(extra)
    if n > SAME_IMPLEMENTER_ROUNDS:
        start["model"], start["effort"] = FRESH_MODEL, FRESH_EFFORT
        return [start]
    impls = [x for x in terms if x["labels"].get("studio.role") == "implementer"]
    if not impls or _youngest(impls)["status"] == DEAD:
        return [start]
    impl = _youngest(impls)
    if impl["status"] not in FINISHED:
        return []  # nie in ein arbeitendes oder auf Erlaubnis wartendes Terminal tippen
    return [dict({"action": "send_rework", "ticket": t["id"], "project": t["project"], "terminal": impl["id"],
                  "round": n, "pr": pr.get("number")}, **extra)]


def _merge_blockers(t, reviewer, status, pr, proj):
    """Gründe gegen Auto-Merge; leer heißt: alle Bedingungen erfüllt."""
    labels = t.get("labels") or []
    reasons = []
    if _size(labels) != "S":
        reasons.append("Größe %s statt S" % _size(labels))
    if ONE_WAY in labels:
        reasons.append(ONE_WAY)
    if t.get("human_gate") is True:
        # Ruling des Masters (Review A3): ein Kommentar hat es aus ready zurückgeholt; der Mensch sieht es wieder
        reasons.append("war schon beim Menschen (Kommentar holte es aus ready), nie Auto-Merge")
    paths = pr.get("paths")
    if not isinstance(paths, list):
        reasons.append("geänderte Pfade unbekannt")
    else:
        hits = [p for p in paths if any(rx.search(str(p)) for rx in SENSITIVE_PATHS)]
        if hits:
            reasons.append("sensible Pfade: " + ", ".join(sorted(hits)))
    if proj.get("auto_merge") is not True:
        reasons.append("auto_merge im Projekt aus")
    if status != "DONE":
        reasons.append("Reviewer meldet Bedenken (%s)" % status)
    if not pr.get("head") or reviewer["labels"].get("slickfab.head") != pr.get("head"):
        reasons.append("PR-Head %s ist nicht der geprüfte Head %s"
                       % (pr.get("head"), reviewer["labels"].get("slickfab.head")))
    return reasons
