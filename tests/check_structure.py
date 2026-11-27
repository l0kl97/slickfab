#!/usr/bin/env python3
"""Strukturprüfung für slickfab: findet alle Schritte (skills/*/SKILL.md) und
Rollen (agents/*.md) selbst; neue Dateien werden ohne Änderung hier mitgeprüft.

Aufruf: python3 tests/check_structure.py [repo-root]
Exit 0 = alles in Ordnung, 1 = mindestens ein Befund (je Befund eine Zeile FAIL ...).
Nur Standardbibliothek, läuft mit Python 3.9.
"""
import glob
import json
import os
import sys

# Pflichtabschnitte jedes Schritts (als '## <Name>'-Überschrift).
SKILL_SECTIONS = ("Wann", "Ablauf", "Ergebnis", "Nächster Schritt")
# Die Beschreibung nennt nur den Auslöser. Eine Ablauf-Zusammenfassung sprengt diese Grenze.
DESCRIPTION_MAX = 300


def parse_frontmatter(text):
    """Gibt (dict, body) zurück oder (None, text), wenn kein Frontmatter da ist."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    fields = {}
    key = None
    for line in lines[1:end]:
        if line.startswith((" ", "\t")) and key:
            # Fortsetzung eines mehrzeiligen Werts (YAML-Block oder Umbruch)
            fields[key] = (fields[key] + " " + line.strip()).strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if value in (">", "|", ">-", "|-"):
                value = ""
            elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1].strip()  # "" und '' sind leer
            fields[key] = value
    return fields, "\n".join(lines[end + 1:])


def headings(body):
    """'## '-Überschriften außerhalb von Codeblöcken (``` oder ~~~)."""
    found, fence = set(), None
    for line in body.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in ("```", "~~~"):
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None and line.startswith("## "):
            found.add(line[3:].strip())
    return found


def check_frontmatter(rel, text, fails):
    """Gemeinsam für Schritte und Rollen. Gibt den Body zurück, None bei fehlendem Frontmatter."""
    fields, body = parse_frontmatter(text)
    if fields is None:
        fails.append("%s: kein Frontmatter" % rel)
        return None
    for key in ("name", "description"):
        if not fields.get(key):
            fails.append("%s: %s fehlt" % (rel, key))
    desc = fields.get("description", "")
    if len(desc) > DESCRIPTION_MAX:
        fails.append("%s: description hat %d Zeichen, erlaubt sind %d (nur den Auslöser nennen, "
                     "nicht den Ablauf)" % (rel, len(desc), DESCRIPTION_MAX))
    return body


def check_skill(rel, text, fails):
    body = check_frontmatter(rel, text, fails)
    if body is None:
        return
    present = headings(body)
    for section in SKILL_SECTIONS:
        if section not in present:
            fails.append("%s: Pflichtabschnitt '## %s' fehlt" % (rel, section))


def load_json(root, rel, fails, required):
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        if required:
            fails.append("%s: fehlt" % rel)
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except ValueError as e:
        fails.append("%s: kein gültiges JSON (%s)" % (rel, e))
        return None


def check_manifests(root, fails):
    plugin = load_json(root, ".claude-plugin/plugin.json", fails, required=True)
    if plugin is not None and not (isinstance(plugin, dict) and plugin.get("name")):
        fails.append(".claude-plugin/plugin.json: name fehlt")
    load_json(root, ".claude-plugin/marketplace.json", fails, required=False)


def check(root):
    fails = []
    check_manifests(root, fails)
    for pattern, checker in ((("skills", "*", "SKILL.md"), check_skill),
                             (("agents", "*.md"), check_frontmatter)):
        for path in sorted(glob.glob(os.path.join(root, *pattern))):
            rel = os.path.relpath(path, root)
            with open(path, encoding="utf-8") as f:
                checker(rel, f.read(), fails)
    return fails


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    fails = check(root)
    for msg in fails:
        print("FAIL " + msg)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
