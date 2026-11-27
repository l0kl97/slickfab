#!/usr/bin/env python3
"""Prüft die Ablage der Pressure-Szenarien.

Aufruf: python3 tests/check_pressure.py [tests/pressure]

- Jede der sieben Rollen hat mindestens zwei Szenarien: tests/pressure/<rolle>/<szenario>/ mit
  szenario.md, auftrag.md und setup.sh.
- szenario.md hat `## Drucksorten` mit mindestens drei Punkten, `## Erwartet` und
  `## Nicht gehalten, wenn` mit je mindestens einem Punkt.
- Alle Pflichtfälle aus dem Ticket (Beschreibung und Kommentare) stehen in einer Zeile
  `**Pflichtfall:** <schlüssel>[, <schlüssel>]` irgendeines Szenarios.
- Die Anleitung tests/pressure/README.md existiert, ebenso die alten Vorlagen der Kontrolle
  (tests/pressure/kontrolle/<rolle>.md für planner, challenger, implementer, reviewer).
- Zu jedem Szenario sind beide Läufe abgelegt: <rolle>/runs/<szenario>-neu und -kontrolle mit
  ergebnis.md, befehle.md, nachher.md, transkript.md, lauf.md und bewertung.md. Die Bewertung
  nennt `**Ergebnis:** gehalten` oder `nicht gehalten` und mindestens ein `**Zitat:** „…“`, das
  wörtlich (bis auf Leerraum) in den Dateien des Laufs steht. Kein Home-Pfad, kein Schlüssel.
Inhalt in ```-Blöcken zählt nicht. Prüft die Form, nicht das Verhalten; das Verhalten zeigen die Läufe.
"""
import os
import re
import sys

ROLLEN = ("planner", "challenger", "implementer", "reviewer", "debugger", "verifier", "retro")
PFLICHTFAELLE = (
    "stop-gate-rot", "test-im-weg",                 # Umsetzer
    "nicht-melden", "pr-text-gruen",                # Reviewer
    "egal-mach-du",                                 # Planer (spec)
    "nicht-verdrahtet",                             # Verifier
    "nicht-reproduzierbar",                         # Debugger
    "ausnahme-ausserhalb-marker",                   # Kommentar Re-Review PR #7
    "challenge-keine-dritte-runde", "challenge-nur-spec",
    "tickets-dateiueberschnitt", "tracker-unerreichbar",  # Kommentar Re-Review PR #2
)
DATEIEN = ("szenario.md", "auftrag.md", "setup.sh")
VORLAGEN = ("planner", "challenger", "implementer", "reviewer")
ARME = ("neu", "kontrolle")
LAUF_DATEIEN = ("ergebnis.md", "befehle.md", "nachher.md", "transkript.md", "lauf.md", "bewertung.md")
MIN_ZITAT = 15
ERGEBNIS = re.compile(r"^\*\*Ergebnis:\*\*\s*(gehalten|nicht gehalten)\s*(?:[.(]|$)", re.M)
ZITAT = re.compile(r"^\*\*Zitat:\*\*\s*„(.+?)“", re.M)
HOME_PFAD = re.compile(r"/(?:Users|home)/[^/\s]+")
SCHLUESSEL = re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                        r"|lin_(?:api|oauth)_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")


def ohne_codebloecke(text):
    """Text ohne Inhalt von ```- und ~~~-Blöcken; ein Block endet nur mit seiner eigenen Zaunart."""
    out, zaun = [], None
    for line in text.split("\n"):
        kopf = line.lstrip()[:3]
        if kopf in ("```", "~~~"):
            if zaun is None:
                zaun = kopf
                continue
            if kopf == zaun:
                zaun = None
                continue
        if zaun is None:
            out.append(line)
    return "\n".join(out)


def norm(text):
    return " ".join(text.split())


def scenarios(base):
    out = []
    for rolle in ROLLEN:
        d = os.path.join(base, rolle)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name != "runs" and os.path.isdir(os.path.join(d, name)):
                out.append((rolle, name))
    return out


def section_items(text, heading):
    lines = ohne_codebloecke(text).split("\n")
    if heading not in lines:
        return None
    items = []
    for line in lines[lines.index(heading) + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("- ") and line[2:].strip():
            items.append(line)
    return items


def check(base):
    errors = []
    if not os.path.isfile(os.path.join(base, "README.md")):
        errors.append("README.md (Anleitung) fehlt")
    found = scenarios(base)
    for rolle in ROLLEN:
        n = sum(1 for r, _ in found if r == rolle)
        if n < 2:
            errors.append("%s: %d Szenario(s), verlangt sind mindestens 2" % (rolle, n))
    pflicht = set()
    for rolle, name in found:
        where = "%s/%s" % (rolle, name)
        missing = [f for f in DATEIEN if not os.path.isfile(os.path.join(base, rolle, name, f))]
        if missing:
            errors.append("%s: fehlt %s" % (where, ", ".join(missing)))
        p = os.path.join(base, rolle, name, "szenario.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        drucks = section_items(text, "## Drucksorten")
        if drucks is None or len(drucks) < 3:
            errors.append("%s: ## Drucksorten braucht mindestens 3 Punkte" % where)
        for heading in ("## Erwartet", "## Nicht gehalten, wenn"):
            items = section_items(text, heading)
            if not items:
                errors.append("%s: %s fehlt oder ist leer" % (where, heading[3:]))
        for m in re.finditer(r"^\*\*Pflichtfall:\*\*\s*(.+)$", ohne_codebloecke(text), re.M):
            pflicht.update(k.strip() for k in m.group(1).split(","))
        for arm in ARME:
            errors.extend(check_lauf(base, rolle, name, arm))
    for rolle in VORLAGEN:
        if not os.path.isfile(os.path.join(base, "kontrolle", rolle + ".md")):
            errors.append("Vorlage der Kontrolle fehlt: kontrolle/%s.md" % rolle)
    for key in PFLICHTFAELLE:
        if key not in pflicht:
            errors.append("Pflichtfall %s hat kein Szenario" % key)
    return errors


def check_lauf(base, rolle, name, arm):
    where = "%s/runs/%s-%s" % (rolle, name, arm)
    d = os.path.join(base, rolle, "runs", "%s-%s" % (name, arm))
    if not os.path.isdir(d):
        return ["%s: Lauf (%s) nicht abgelegt" % (where, arm)]
    errors = []
    texte = {}
    for f in LAUF_DATEIEN:
        p = os.path.join(d, f)
        if not os.path.isfile(p):
            errors.append("%s: fehlt %s" % (where, f))
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                texte[f] = fh.read()
        except (UnicodeDecodeError, ValueError):
            errors.append("%s/%s: nicht UTF-8" % (where, f))
    for f, text in texte.items():
        if HOME_PFAD.search(text):
            errors.append("%s/%s: enthält einen Home-Pfad" % (where, f))
        if SCHLUESSEL.search(text):
            errors.append("%s/%s: enthält einen Schlüssel" % (where, f))
    bew = texte.get("bewertung.md")
    if bew is None:
        return errors
    if not ERGEBNIS.search(bew):
        errors.append("%s/bewertung.md: **Ergebnis:** gehalten | nicht gehalten fehlt" % where)
    zitate = ZITAT.findall(bew)
    if not zitate:
        errors.append("%s/bewertung.md: **Zitat:** „…“ fehlt" % where)
    belege = norm(" ".join(t for f, t in texte.items() if f != "bewertung.md"))
    for z in zitate:
        if len(norm(z)) < MIN_ZITAT:
            errors.append("%s/bewertung.md: Zitat leer oder kürzer als %d Zeichen" % (where, MIN_ZITAT))
        elif norm(z) not in belege:
            errors.append("%s/bewertung.md: Zitat steht nicht im Lauf: „%s“" % (where, z[:80]))
    return errors


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "pressure")
    errors = check(base)
    for e in errors:
        print("FAIL pressure: %s" % e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
