"""Tests für den nachgestellten Linear-Server der Pressure-Szenarien.

`tests/pressure/fake_linear_mcp.py` spricht MCP über stdio (eine JSON-RPC-Nachricht je Zeile)
und liest Issues aus einer Zustandsdatei. Jeder schreibende Aufruf landet als Zeile in
`<zustand>.calls`, damit die Auswertung sieht, ob eine Rolle etwas angelegt hat.
Geprüft wird über die öffentliche Schnittstelle: Nachrichten rein, Antworten und Protokoll raus.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "pressure", "fake_linear_mcp.py")
TMP_ROOT = os.path.join(os.path.dirname(HERE), ".test-tmp")

STATE = {
    "issues": {
        "EX-900": {
            "title": "Rabattcode einlösen",
            "status": "Todo",
            "description": "Kriterium 1",
            "comments": [{"author": "Kim", "body": "freigegeben"}],
        }
    }
}


class FakeLinear:
    def __init__(self, state):
        os.makedirs(TMP_ROOT, exist_ok=True)
        self.dir = tempfile.mkdtemp(dir=TMP_ROOT)
        self.state = os.path.join(self.dir, "linear.json")
        with open(self.state, "w", encoding="utf-8") as f:
            json.dump(state, f)
        self.proc = subprocess.Popen(
            [sys.executable, SERVER, self.state],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8",
        )
        self.next_id = 1

    def raw(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def request(self, method, params=None):
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params is not None:
            msg["params"] = params
        self.next_id += 1
        return self.raw(json.dumps(msg))

    def notify(self, method):
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def call(self, name, arguments):
        return self.request("tools/call", {"name": name, "arguments": arguments})["result"]

    def calls(self):
        path = self.state + ".calls"
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)
        self.proc.stdout.close()
        self.proc.stderr.close()
        shutil.rmtree(self.dir, ignore_errors=True)


def text_of(result):
    return result["content"][0]["text"]


class FakeLinearTest(unittest.TestCase):
    def start(self, state=STATE):
        srv = FakeLinear(state)
        self.addCleanup(srv.close)
        srv.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                   "clientInfo": {"name": "test", "version": "0"}})
        srv.notify("notifications/initialized")
        return srv

    def test_initialize_nennt_werkzeuge(self):
        srv = FakeLinear(STATE)
        self.addCleanup(srv.close)
        init = srv.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")
        self.assertIn("tools", init["result"]["capabilities"])
        srv.notify("notifications/initialized")
        names = {t["name"] for t in srv.request("tools/list")["result"]["tools"]}
        for name in ("get_issue", "list_comments", "list_issues", "save_issue", "save_comment"):
            self.assertIn(name, names)

    def test_get_issue_liefert_bekanntes_issue(self):
        srv = self.start()
        res = srv.call("get_issue", {"id": "EX-900"})
        self.assertFalse(res.get("isError", False))
        issue = json.loads(text_of(res))
        self.assertEqual(issue["title"], "Rabattcode einlösen")
        self.assertEqual(issue["status"], "Todo")

    def test_get_issue_unbekannt_ist_fehler(self):
        srv = self.start()
        res = srv.call("get_issue", {"id": "EX-1"})
        self.assertTrue(res["isError"])
        self.assertIn("EX-1", text_of(res))

    def test_save_comment_wird_protokolliert_und_ist_lesbar(self):
        srv = self.start()
        res = srv.call("save_comment", {"issueId": "EX-900", "body": "Ergebnis"})
        self.assertFalse(res.get("isError", False))
        bodies = [c["body"] for c in json.loads(text_of(srv.call("list_comments", {"issueId": "EX-900"})))["comments"]]
        self.assertEqual(bodies, ["freigegeben", "Ergebnis"])
        self.assertEqual([c["tool"] for c in srv.calls()], ["save_comment"])

    def test_save_issue_ohne_id_legt_an_und_protokolliert(self):
        srv = self.start()
        created = json.loads(text_of(srv.call("save_issue", {"title": "Neu", "team": "Example"})))
        self.assertTrue(created["id"].startswith("EX-"))
        self.assertEqual(json.loads(text_of(srv.call("get_issue", {"id": created["id"]})))["title"], "Neu")
        self.assertEqual(srv.calls()[0]["arguments"]["title"], "Neu")

    def test_lesen_wird_nicht_protokolliert(self):
        srv = self.start()
        srv.call("get_issue", {"id": "EX-900"})
        srv.call("list_issues", {})
        self.assertEqual(srv.calls(), [])

    def test_unerreichbar_jedes_werkzeug_ist_fehler(self):
        srv = self.start(dict(STATE, unreachable=True))
        for name, args in (("get_issue", {"id": "EX-900"}), ("list_issues", {}),
                           ("save_issue", {"title": "x"})):
            res = srv.call(name, args)
            self.assertTrue(res["isError"], name)
            self.assertIn("nicht erreichbar", text_of(res))
        self.assertEqual(srv.calls(), [])

    def test_unbekanntes_werkzeug_und_methode(self):
        srv = self.start()
        self.assertTrue(srv.call("delete_issue", {"id": "EX-900"})["isError"])
        self.assertEqual(srv.request("foo/bar")["error"]["code"], -32601)

    def test_unerwartete_eingaben_brechen_den_server_nicht(self):
        srv = self.start(dict(STATE, issues=dict(STATE["issues"], **{"ABC-X-5": {"title": "krumm"}})))
        self.assertTrue(srv.call("list_issues", {"query": 5})["isError"])
        created = srv.call("save_issue", {"title": "neu"})  # krumme ID darf das Anlegen nicht abschießen
        self.assertFalse(created.get("isError", False), text_of(created))
        self.assertEqual(json.loads(text_of(created))["id"], "EX-1001")
        self.assertEqual(srv.raw("[1, 2]")["error"]["code"], -32600)
        self.assertFalse(srv.call("get_issue", {"id": "EX-900"}).get("isError", False))

    def test_list_issues_filtert_nach_eltern_und_status(self):
        state = {"issues": {
            "EX-1": {"title": "Spec", "status": "Backlog"},
            "EX-2": {"title": "Kind offen", "status": "Todo", "parentId": "EX-1"},
            "EX-3": {"title": "Kind fertig", "status": "Done", "parentId": "EX-1"},
            "EX-4": {"title": "Fremd", "status": "Todo", "parentId": "EX-9"},
        }}
        srv = self.start(state)
        ids = lambda args: sorted(i["id"] for i in json.loads(text_of(srv.call("list_issues", args)))["issues"])
        self.assertEqual(ids({"parentId": "EX-1"}), ["EX-2", "EX-3"])
        self.assertEqual(ids({"state": "Todo"}), ["EX-2", "EX-4"])
        self.assertEqual(ids({"parentId": "EX-1", "state": "Done"}), ["EX-3"])
        self.assertEqual(ids({"query": "kind"}), ["EX-2", "EX-3"])

    def test_anlegen_vergibt_neue_ids(self):
        srv = self.start()
        a = json.loads(text_of(srv.call("save_issue", {"title": "A"})))["id"]
        b = json.loads(text_of(srv.call("save_issue", {"title": "B"})))["id"]
        self.assertNotEqual(a, b)
        self.assertEqual(json.loads(text_of(srv.call("get_issue", {"id": a})))["title"], "A")
        self.assertEqual(json.loads(text_of(srv.call("get_issue", {"id": b})))["title"], "B")
        self.assertEqual(json.loads(text_of(srv.call("get_issue", {"id": "EX-900"})))["title"], "Rabattcode einlösen")

    def test_get_issue_ohne_kommentare(self):
        srv = self.start()
        self.assertNotIn("comments", json.loads(text_of(srv.call("get_issue", {"id": "EX-900"}))))

    def test_kaputte_zeile_bricht_den_server_nicht(self):
        srv = self.start()
        self.assertEqual(srv.raw("{kein json")["error"]["code"], -32700)
        self.assertFalse(srv.call("get_issue", {"id": "EX-900"}).get("isError", False))


if __name__ == "__main__":
    unittest.main()
