#!/usr/bin/env python3
"""PreToolUse-Wächter für den Doku-Agent `slickfab:docs-reader`.

Der Agent liest fremde Doku; eingeschleuste Anweisungen darin sollen nichts
ausrichten können. Darum darf er nur das Hilfsskript lookup.py aufrufen:
keine freie Shell, kein Schreiben. Für alle anderen Agents und die
Hauptsession gibt der Wächter keine Entscheidung ab (normaler Ablauf).

Ein: Hook-JSON auf stdin. Aus: bei Verbot ein JSON mit permissionDecision deny.
Nur Standardbibliothek, läuft mit Python 3.9.
"""
import json
import os
import shlex
import sys

AGENT = "slickfab:docs-reader"
LOOKUP = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "skills", "docs-lookup", "lookup.py"))
INTERPRETERS = ("python3", "python")
# Alles, womit die Shell mehr als einen einfachen Aufruf macht: Verkettung,
# Umleitung, Ersetzung, Variablen, Escapes, Zeilenumbrüche.
SHELL_META = set(";&|<>$`\\\n\r")
RULE = ("Im Doku-Agent ist nur `python3 <plugin>/skills/docs-lookup/lookup.py <paket> <stichwort>... "
        "[--repo DIR] [--url https://…] [--timeout S]` erlaubt, ohne Verkettung, Umleitung oder Ersetzung; "
        "--url nur mit https://; kein Schreiben, keine andere Shell.")


def allowed_command(command):
    if not command or any(c in SHELL_META for c in command):
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:  # unbalancierte Anführungszeichen
        return False
    if len(tokens) < 3 or tokens[0] not in INTERPRETERS:
        return False
    if os.path.realpath(tokens[1]) != LOOKUP:
        return False
    return urls_are_https(tokens[2:])


def urls_are_https(args):
    """Jede --url (auch --url=…) beginnt mit https://; Abkürzungen wie --u gibt es nicht,
    und nirgends steht eine andere Adresse mit Schema (http://, file://)."""
    for i, arg in enumerate(args):
        if arg.startswith("--u") and not (arg == "--url" or arg.startswith("--url=")):
            return False
        if arg == "--url":
            value = args[i + 1] if i + 1 < len(args) else ""
        elif arg.startswith("--url="):
            value = arg[len("--url="):]
        else:
            if "://" in arg and not arg.startswith("https://"):
                return False
            continue
        if not value.startswith("https://"):
            return False
    return True


def is_docs_agent(event):
    """Kann selbst nicht werfen: nur Typprüfungen und ein Vergleich von Texten."""
    return isinstance(event, dict) and isinstance(event.get("agent_type"), str) \
        and event["agent_type"] == AGENT


def allowed(event):
    tool = event.get("tool_name")
    tool_input = event.get("tool_input")
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else None
    return tool == "Bash" and isinstance(command, str) and allowed_command(command)


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:  # unlesbar: kein Agent erkennbar, normale Arbeit nie blockieren
        return 0
    if not is_docs_agent(event):
        return 0
    # Ab hier fail-closed: Der Wächter ist die einzige Grenze zwischen dem Doku-Agent
    # und einer freien Shell. Jeder unerwartete Fehler (z. B. realpath bei NUL-Byte oder
    # einzelnem Surrogate ab Python 3.10) wird zu deny statt zu einem Absturz, den
    # Claude Code als nicht blockierend behandeln würde.
    try:
        ok = allowed(event)
    except Exception as e:
        print("slickfab docs-lookup guard: %s, abgelehnt" % type(e).__name__, file=sys.stderr)
        ok = False
    if ok:
        return 0
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": "deny",
                                      "permissionDecisionReason": RULE}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
