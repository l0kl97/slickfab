#!/usr/bin/env python3
"""Nachgestelltes Linear für die Pressure-Szenarien: ein MCP-Server über stdio.

Aufruf: python3 fake_linear_mcp.py <zustand.json>

Der Zustand hält die Issues eines Szenarios (`issues`: ID → Titel, Status, Beschreibung,
Kommentare, Relationen). Steht `"unreachable": true` darin, antwortet jedes Werkzeug mit
„Linear nicht erreichbar“. Jeder schreibende Aufruf (save_issue, save_comment) wird als
JSON-Zeile an `<zustand>.calls` angehängt; so sieht die Auswertung, ob eine Rolle etwas
angelegt oder verändert hat. Spricht mit keinem echten Dienst.
"""
import json
import sys

WRITE_TOOLS = {"save_issue", "save_comment"}


def _schema(props, required=()):
    return {"type": "object", "properties": {k: {"type": v} for k, v in props.items()},
            "required": list(required)}


TOOLS = [
    {"name": "get_issue", "description": "Ein Linear-Issue mit Status, Beschreibung und Relationen lesen.",
     "inputSchema": _schema({"id": "string"}, ["id"])},
    {"name": "list_comments", "description": "Kommentare eines Issues lesen.",
     "inputSchema": _schema({"issueId": "string"}, ["issueId"])},
    {"name": "list_issues", "description": "Issues auflisten, optional nach Text, Projekt, Status oder Eltern-Issue gefiltert.",
     "inputSchema": _schema({"query": "string", "project": "string", "state": "string", "parentId": "string"})},
    {"name": "save_issue", "description": "Issue anlegen (ohne id) oder ändern (mit id): Titel, Beschreibung, Status, Labels, Eltern-Issue, blockedBy.",
     "inputSchema": _schema({"id": "string", "title": "string", "description": "string", "state": "string",
                             "team": "string", "project": "string", "parentId": "string",
                             "labels": "array", "blockedBy": "array"})},
    {"name": "save_comment", "description": "Kommentar an ein Issue schreiben.",
     "inputSchema": _schema({"issueId": "string", "body": "string"}, ["issueId", "body"])},
    {"name": "list_issue_statuses", "description": "Status eines Teams auflisten.",
     "inputSchema": _schema({"team": "string"})},
    {"name": "list_issue_labels", "description": "Labels eines Teams auflisten.",
     "inputSchema": _schema({"team": "string"})},
]
STATUSES = ["Backlog", "Todo", "In Progress", "In Review", "Done", "Canceled", "Duplicate"]
LABELS = ["S", "M", "L", "door:one-way", "rework", "ready", "needs-human", "replan"]


class ToolError(Exception):
    pass


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _store(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def _issue(state, ident):
    issue = state.get("issues", {}).get(ident)
    if issue is None:
        raise ToolError("Issue %s nicht gefunden" % ident)
    return issue


def run_tool(path, name, args):
    state = _load(path)
    if state.get("unreachable"):
        raise ToolError("Linear nicht erreichbar: Verbindung abgelehnt (Testumgebung)")
    issues = state.setdefault("issues", {})
    if name == "get_issue":
        issue = dict(_issue(state, args.get("id", "")))
        issue.pop("comments", None)
        return dict(issue, id=args["id"])
    if name == "list_comments":
        return {"comments": _issue(state, args.get("issueId", "")).get("comments", [])}
    if name == "list_issues":
        out = []
        for ident, issue in issues.items():
            if args.get("query") and args["query"].lower() not in issue.get("title", "").lower():
                continue
            if args.get("parentId") and issue.get("parentId") != args["parentId"]:
                continue
            if args.get("state") and issue.get("status") != args["state"]:
                continue
            out.append({"id": ident, "title": issue.get("title"), "status": issue.get("status"),
                        "parentId": issue.get("parentId")})
        return {"issues": out}
    if name == "list_issue_statuses":
        return {"statuses": STATUSES}
    if name == "list_issue_labels":
        return {"labels": LABELS}
    if name == "save_comment":
        issue = _issue(state, args.get("issueId", ""))
        issue.setdefault("comments", []).append({"author": "Agent", "body": args.get("body", "")})
        _store(path, state)
        return {"ok": True}
    if name == "save_issue":
        if args.get("id"):
            issue = _issue(state, args["id"])
            ident = args["id"]
        else:
            nums = [int(k.rsplit("-", 1)[1]) for k in issues if k.rsplit("-", 1)[-1].isdigit()]
            ident = "EX-%d" % (max(nums + [1000]) + 1)
            issue = issues.setdefault(ident, {"status": "Backlog", "comments": []})
        for key, value in args.items():
            if key == "id":
                continue
            issue["status" if key == "state" else key] = value
        _store(path, state)
        return {"id": ident, "title": issue.get("title"), "status": issue.get("status")}
    raise ToolError("Werkzeug %s gibt es nicht" % name)


def handle(path, msg):
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:
        return None  # Benachrichtigung, keine Antwort
    if method == "initialize":
        version = (msg.get("params") or {}).get("protocolVersion", "2025-06-18")
        return {"protocolVersion": version, "capabilities": {"tools": {}},
                "serverInfo": {"name": "linear", "version": "0-test"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        params = msg.get("params") or {}
        name, args = params.get("name", ""), params.get("arguments") or {}
        try:
            result = run_tool(path, name, args)
        except ToolError as e:
            return {"content": [{"type": "text", "text": str(e)}], "isError": True}
        except Exception as e:  # krumme Eingabe der Rolle: Fehler melden, Server bleibt am Leben
            return {"content": [{"type": "text", "text": "Ungültige Anfrage an %s: %s" % (name, e)}],
                    "isError": True}
        if name in WRITE_TOOLS:
            with open(path + ".calls", "a", encoding="utf-8") as f:
                f.write(json.dumps({"tool": name, "arguments": args}, ensure_ascii=False) + "\n")
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
    raise LookupError(method)


def main():
    path = sys.argv[1]
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "kein JSON"}}
        else:
            if not isinstance(msg, dict):
                reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "keine Anfrage"}}
                sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
                sys.stdout.flush()
                continue
            try:
                result = handle(path, msg)
                if result is None:
                    continue
                reply = {"jsonrpc": "2.0", "id": msg.get("id"), "result": result}
            except LookupError as e:
                reply = {"jsonrpc": "2.0", "id": msg.get("id"),
                         "error": {"code": -32601, "message": "Methode %s unbekannt" % e}}
            except Exception as e:
                reply = {"jsonrpc": "2.0", "id": msg.get("id"),
                         "error": {"code": -32603, "message": "interner Fehler: %s" % e}}
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
