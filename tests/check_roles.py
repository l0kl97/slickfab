#!/usr/bin/env python3
"""Prüfung der Agent-Rollen: dünne Hüllen um einen Schritt.

Eine Rolle liegt in agents/<name>.md. Sie verweist auf ihren Schritt, statt ihn
zu kopieren: Frontmatter `schritt` nennt ihn (beim Planer zwei, durch Komma
getrennt), `skills` lädt ihn beim Start vor (`slickfab:<schritt>`), und der
Text nennt `/slickfab:<schritt>`. Dazu Pflichtabschnitte, eine Längengrenze und
kein abgeschriebener Ablauf.

Frontmatter-Schnittstelle (liest auch gen-templates): name, description, model,
schritt, skills, disallowedTools.

Aufruf: python3 tests/check_roles.py [repo-root]
Exit 0 = in Ordnung, 1 = Befunde (je Befund eine Zeile FAIL ...).
Nur Standardbibliothek, läuft mit Python 3.9.
"""
import os
import re
import sys

ROLES = ("planner", "challenger", "implementer", "reviewer", "debugger", "verifier", "retro")
SECTIONS = ("Input", "Output", "Marker", "Model", "Excuse → Reality")
HEADINGS = {"## " + s for s in SECTIONS}
MODELS = ("sonnet", "opus", "haiku", "inherit")
# Zeichen der Hülle ohne eingebettete Vertragsblöcke (die kommen wörtlich aus
# tracker/linear.md und zählen nicht als eigener Text).
LENGTH_MAX = 4000
# Zeilen des Schritts ab dieser Länge dürfen nicht wörtlich in der Hülle stehen.
COPY_MIN = 60
TABLE_ROWS = (5, 8)
# Rollen, die fremde Inhalte lesen (Issues, PRs, Kommentare), schützt das Werkzeug,
# nicht der Prompt (review-learnings). Eine `tools`-Allowlist sperrte auch
# die Linear-Werkzeuge, daher `disallowedTools`. Der Reviewer braucht Edit für die
# Mutationsprobe seines Schritts.
# planner und challenger brauchen auch keine Shell (Review PR #10, R1); reviewer,
# verifier und retro führen Prüfbefehle aus, ihr Bash-Wächter steht in hooks/role_bash_guard.py.
NO_WRITE = {"planner": ("Bash", "Edit", "NotebookEdit", "Write"),
            "challenger": ("Bash", "Edit", "NotebookEdit", "Write"),
            "verifier": ("Edit", "NotebookEdit", "Write"),
            "retro": ("Edit", "NotebookEdit", "Write"),
            "reviewer": ("NotebookEdit", "Write")}
# Der Challenger prüft selbst (Hülle: „startest keinen weiteren Sub-Agent“). In C1 der Pressure-
# Szenarien startete er trotzdem einen Explore-Subagent; das Werkzeug sperrt es (Punkt 3).
NO_AGENT = {"challenger": ("Agent", "Task")}
# Beim Start mit `claude --agent` und aus der Herdr-Vorlage lädt Claude Code `skills:` nicht vor
# (Doku sub-agents: „Preload skills into subagents“ gilt für Subagents). Jede Hülle lädt ihren
# Schritt deshalb als Erstes per Skill-Werkzeug und behauptet nicht, er sei schon da (Punkt 2).
LOAD_FIRST = "first, before any other tool, with the Skill tool"
PRELOAD_CLAIM = re.compile(r"\b(is|are) (already )?(preloaded|in your context) (at|on) start")
CONTRACT = re.compile(r"<!-- vertrag:([a-z-]+) -->\n.*?<!-- /vertrag:\1 -->\n?", re.S)
COMMENT = re.compile(r"<!--.*?-->")
RULE = re.compile(r"<!-- regel:([a-z0-9-]+) -->\n.*?<!-- /regel:\1 -->\n?", re.S)


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    fields = {}
    for line in lines[1:end]:
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip("\"'")
    return fields, "\n".join(lines[end + 1:]) + "\n"


def sections(body):
    """{überschrift: text} der '## '-Abschnitte außerhalb von Codeblöcken."""
    out, current, fence = {}, None, None
    for line in body.splitlines():
        mark = line.lstrip()[:3]
        if mark in ("```", "~~~"):
            fence = mark if fence is None else (None if mark == fence else fence)
        if fence is None and line.startswith("## "):
            current = line[3:].strip()
            out[current] = ""
            continue
        if current is not None:
            out[current] += line + "\n"
    return out


def split_list(value):
    return [v.strip() for v in value.strip("[]").split(",") if v.strip()]


def step_lines(root, step):
    """Lange Zeilen des Schritts ohne Vertragsblöcke und Markerzeilen (die
    sind Vertragsformat und dürfen gleich sein)."""
    with open(os.path.join(root, "skills", step, "SKILL.md"), encoding="utf-8") as f:
        text = CONTRACT.sub("", f.read())
    return {l.strip() for l in text.splitlines()
            if len(l.strip()) >= COPY_MIN and not l.startswith("SLICKFAB-")}


def check_role(root, name, text, fails):
    rel = "agents/%s.md" % name
    fields, body = parse_frontmatter(text)
    if fields is None:
        fails.append("%s: kein Frontmatter" % rel)
        return
    if fields.get("name") != name:
        fails.append("%s: name muss '%s' sein" % (rel, name))
    if not fields.get("description"):
        fails.append("%s: description fehlt" % rel)
    model = fields.get("model", "")
    if model not in MODELS and not model.startswith("claude-"):
        fails.append("%s: model '%s' ist kein gültiges Modell (%s oder claude-…)" % (rel, model, ", ".join(MODELS)))
    steps = split_list(fields.get("schritt", ""))
    if not steps:
        fails.append("%s: Verweis auf den Schritt fehlt (Frontmatter 'schritt')" % rel)
    preloaded = split_list(fields.get("skills", ""))
    blocked = set(split_list(fields.get("disallowedTools", "")))
    if name in NO_WRITE and not set(NO_WRITE[name]) <= blocked:
        fails.append("%s: disallowedTools muss %s sperren" % (rel, ", ".join(NO_WRITE[name])))
    if name in NO_AGENT and not set(NO_AGENT[name]) <= blocked:
        fails.append("%s: startet keine Subagents, disallowedTools muss %s sperren" % (rel, ", ".join(NO_AGENT[name])))
    for skill in preloaded:
        if skill.startswith("slickfab:") and skill[len("slickfab:"):] not in steps:
            fails.append("%s: 'skills' lädt %s vor, aber 'schritt' nennt %s nicht"
                         % (rel, skill, skill[len("slickfab:"):]))
    for step in steps:
        if not os.path.isfile(os.path.join(root, "skills", step, "SKILL.md")):
            fails.append("%s: verweist auf Schritt '%s', den es nicht gibt (skills/%s/SKILL.md fehlt)" % (rel, step, step))
            continue
        if "slickfab:%s" % step not in preloaded:
            fails.append("%s: 'skills' lädt slickfab:%s nicht vor" % (rel, step))
        if "/slickfab:%s" % step not in body:
            fails.append("%s: Text nennt /slickfab:%s nicht" % (rel, step))
        known = step_lines(root, step)
        copied = [l for l in body.splitlines() if l.strip() in known]
        for line in copied[:3]:
            fails.append("%s: wiederholt den Schritt %s wörtlich: „%s…“" % (rel, step, line.strip()[:50]))
    intro = RULE.search(body)
    intro = intro.group(0) if intro and intro.group(1) == "einleitung" else ""
    if LOAD_FIRST not in intro or not all("`slickfab:%s`" % st in intro for st in steps):
        fails.append("%s: Einleitung sagt nicht, dass der Schritt als Erstes per Skill-Werkzeug geladen wird" % rel)
    if PRELOAD_CLAIM.search(intro):
        fails.append("%s: Einleitung behauptet, der Schritt sei beim Start vorgeladen" % rel)
    found = sections(body)
    for section in SECTIONS:
        if section not in found:
            fails.append("%s: Pflichtabschnitt '## %s' fehlt" % (rel, section))
    if "Ablauf" in found:
        fails.append("%s: '## Ablauf' gehört in den Schritt, nicht in die Hülle" % rel)
    if "NEEDS_CONTEXT" not in found.get("Input", ""):
        fails.append("%s: Eingang sagt nicht, dass ein fehlender Pflicht-Eingang mit NEEDS_CONTEXT endet" % rel)
    if "<!-- vertrag:marker -->" not in found.get("Marker", ""):
        fails.append("%s: Abschnitt Marker bettet den Vertrag 'marker' nicht ein" % rel)
    rows = [l for l in found.get("Excuse → Reality", "").splitlines()
            if l.startswith("|") and not re.fullmatch(r"\|[\s|:-]*\|", l.strip())][1:]
    if not TABLE_ROWS[0] <= len(rows) <= TABLE_ROWS[1]:
        fails.append("%s: Ausrede-Tabelle hat %d Zeilen, erlaubt %d–%d" % (rel, len(rows), *TABLE_ROWS))
    # Außerhalb der eingefrorenen Regel- und Vertragsblöcke stehen nur Überschriften
    # und Leerzeilen; sonst ginge dort eine Erlaubnis gegen den Schritt durch
    # (Review PR #10, A1).
    for line in RULE.sub("", CONTRACT.sub("", body)).splitlines():
        # Nur die festen Pflichtüberschriften; jede andere Zeile, auch eine
        # erfundene '## '-Überschrift, ist freier Text (Re-Review PR #10, A1).
        if line.strip() and line.rstrip() not in HEADINGS:
            fails.append("%s: freier Text außerhalb der Regel- und Vertragsblöcke: „%s…“" % (rel, line.strip()[:50]))
            break
    own = len(COMMENT.sub("", CONTRACT.sub("", body)))
    if own > LENGTH_MAX:
        fails.append("%s: %d Zeichen ohne Vertragsblöcke, erlaubt sind %d (Ablauf gehört in den Schritt)" % (rel, own, LENGTH_MAX))


def check(root):
    fails = []
    for name in ROLES:
        path = os.path.join(root, "agents", "%s.md" % name)
        if not os.path.isfile(path):
            fails.append("agents/%s.md: fehlt" % name)
            continue
        with open(path, encoding="utf-8") as f:
            check_role(root, name, f.read(), fails)
    return fails


def main(argv):
    fails = check(argv[1] if len(argv) > 1 else ".")
    for msg in fails:
        print("FAIL " + msg)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
