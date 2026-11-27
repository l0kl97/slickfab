"""Nachgestellte Systemgrenzen für die Tests von `runtime/herdr/slickfab-dispatch`.

- `hc` (Herdr) und `gh` (GitHub) sind kleine Python-Skripte im PATH. Sie halten ihren Zustand in
  einer JSON-Datei und hängen jeden Aufruf als Zeile an `<zustand>.calls` an.
- Linear ist ein HTTP-Server auf 127.0.0.1 in diesem Testprozess; er merkt sich jede Anfrage.
- `Repo` legt ein Wegwerf-Repo an (nacktes origin + Haupt-Checkout), damit `slickfab-worktree`
  echt laufen kann. Alles liegt unter `<repo>/.test-tmp/`, nichts spricht mit echten Diensten.
"""
import datetime
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO_ROOT, "runtime", "herdr", "slickfab-dispatch")
ME = "bot@example.com"
# Platzhalter für den Linear-Schlüssel; kein echter Wert (zusammengesetzt, damit kein Secret-Scanner anschlägt)
KEY = "-".join(["platzhalter", "schluessel", "nie", "im", "log"])

FAKE_HC = r'''#!%(py)s
import json, os, sys, time
path = os.environ["FAKE_HC_STATE"]
args = sys.argv[1:]
with open(path + ".calls", "a", encoding="utf-8") as f:
    f.write(json.dumps(args) + "\n")
with open(path, encoding="utf-8") as f:
    st = json.load(f)
cmd = args[0] if args else ""
mode = st.get("mode", {}).get(cmd, "ok")
calls = st.setdefault("count", {})
calls[cmd] = calls.get(cmd, 0) + 1
with open(path, "w", encoding="utf-8") as f:
    json.dump(st, f)
if mode.startswith("fail_after_"):   # die ersten n Aufrufe klappen, danach Fehler
    mode = "fail" if calls[cmd] > int(mode.rsplit("_", 1)[1]) else "ok"
if mode == "fail":
    print("core nicht erreichbar", file=sys.stderr); sys.exit(3)
if mode == "garbage":
    print("<html>kaputt"); sys.exit(0)
if mode == "hang":
    time.sleep(60)
if mode == "zombie":
    # Enkel verlässt die Prozessgruppe und hält stdout offen; hc selbst endet sofort. Übrig bleibt
    # eine Gruppe nur aus einem Zombie: killpg meldet darauf unter macOS EPERM statt ESRCH.
    if os.fork() == 0:
        os.setsid()
        time.sleep(8)
        os._exit(0)
    sys.exit(0)
def save():
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f)
def find(t):
    return next((x for x in st["terminals"] if t in (x["address"], x.get("name"))), None)
def positional(rest):
    out = []
    while rest:
        a = rest.pop(0)
        if a in ("--json", "--bg", "--force", "--wait", "--all"):
            continue
        if a.startswith("--"):
            rest.pop(0); continue
        out.append(a)
    return out
if cmd == "ls":
    shown = [t for t in st["terminals"] if "--all" in args or t["state"] == "live"]
    print(json.dumps({"terminals": shown, "hidden_finished": len(st["terminals"]) - len(shown), "machines": []}))
elif cmd == "get":
    t = find(positional(args[1:])[0])
    if not t:
        print("not_found", file=sys.stderr); sys.exit(1)
    t = dict(t, **st.get("get_override", {}).get(t["address"], {}))  # Zustand hat sich seit `ls` geändert
    print(json.dumps(t))
elif cmd == "run":
    rest, labels, name, cwd = args[1:], {}, None, None
    while rest and rest[0].startswith("--"):
        o = rest.pop(0)
        if o == "--bg":
            continue
        v = rest.pop(0)
        if o == "--label":
            k, _, val = v.partition("="); labels[k] = val
        elif o == "--name":
            name = v
        elif o == "--cwd":
            cwd = v
    addr = "t%%d" %% st["next"]
    st["next"] += 1
    st["terminals"].append({"address": addr, "name": name, "cwd": cwd, "labels": labels, "argv": rest,
                            "state": "live", "status": {"state": "working"},
                            "created_ms": int(time.time() * 1000)})
    save()
    if mode.startswith("hang_after_create"):   # Terminal ist angelegt, hc antwortet aber nicht mehr
        if mode.endswith("_other_cwd"):          # Herdr meldet einen anderen Ordner (z. B. Symlink aufgelöst)
            st["terminals"][-1]["cwd"] = "/anderswo"
        if mode.endswith("_no_name"):            # Herdr hat den Namen nicht übernommen
            st["terminals"][-1]["name"] = None
        save()
        time.sleep(60)
    print("the terminal %%s runs" %% addr)   # hc run druckt Text, auch wenn die Ausgabe umgeleitet ist
elif cmd == "label":
    pos = positional(args[1:])
    t = find(pos[0])
    for kv in pos[1:]:
        k, _, v = kv.partition("=")
        t["labels"][k] = v
    save()
elif cmd == "send":
    pos = positional(args[1:])
    t = find(pos[0])
    if t is None:
        print("not_found", file=sys.stderr); sys.exit(1)
    if (t.get("status") or {}).get("state") == "blocked" and "--force" not in args:
        print("blocked", file=sys.stderr); sys.exit(1)
    t["status"] = {"state": "working"}
    save()
    print(json.dumps({"turn": 1}))
elif cmd == "events":
    for _ in range(int(st.get("events", 1))):
        print(json.dumps({"event": {"kind": "status"}}), flush=True)
    time.sleep(float(st.get("events_sleep", 30)))
else:
    print("unbekannt", file=sys.stderr); sys.exit(2)
'''

FAKE_GH = r'''#!%(py)s
import json, os, sys, time
path = os.environ["FAKE_GH_STATE"]
args = sys.argv[1:]
with open(path + ".calls", "a", encoding="utf-8") as f:
    f.write(json.dumps(args) + "\n")
with open(path, encoding="utf-8") as f:
    st = json.load(f)
cmd = " ".join(args[:2])
mode = st.get("mode", {}).get(cmd, "ok")
if mode == "fail":
    print("HTTP 502", file=sys.stderr); sys.exit(1)
if mode == "garbage":
    print("nicht json"); sys.exit(0)
if mode == "hang":
    time.sleep(60)
if mode == "slow":   # antwortet, aber spät: was nach dem Lesen am PR passiert, kennt der tick nicht
    time.sleep(1.2)
if cmd == "api graphql":
    vals = dict(a.split("=", 1) for a in args if "=" in a and not a.startswith("query="))
    repo = st["repos"].get(vals.get("owner", "") + "/" + vals.get("name", ""))
    if repo is None:
        print("Could not resolve to a Repository", file=sys.stderr); sys.exit(1)
    import re
    query = next((a[6:] for a in args if a.startswith("query=")), "")
    for node in (repo.get("pullRequests") or {}).get("nodes") or []:
        for key in ("comments", "reviews"):   # Fenster wie GitHub: first = älteste, last = neueste
            m = re.search(key + r"\((first|last): (\d+)\)", query)
            if m and isinstance(node.get(key), dict):
                n, items = int(m.group(2)), node[key]["nodes"]
                node[key] = {"nodes": items[:n] if m.group(1) == "first" else items[-n:]}
    print(json.dumps({"data": {"repository": repo}}))
elif args[0] == "api" and args[1] in st.get("rest", {}):
    print(json.dumps(st["rest"][args[1]]))
elif cmd == "pr view":
    print(json.dumps({"headRefOid": st["heads"][args[2]]}))
elif cmd == "pr merge":
    pass
else:
    print("unbekannt", file=sys.stderr); sys.exit(2)
'''


def iso(ms):
    return datetime.datetime.utcfromtimestamp(ms / 1000.0).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


def issue(ident, status="Todo", stype="unstarted", assignee=ME, labels=("S",), parent="EX-100",
          blockers=(), files=(), comments=()):
    """Ein Issue so, wie die Linear-Abfrage des Dispatchers es zurückbekommt."""
    desc = "Text.\n\n>>> Agent notes\n\n**Betroffene Dateien**\n\n" + "".join(
        "* `%s` (Hinweis)\n" % f for f in files) + "\n**Fundstellen**\n\n* `docs/x.md`\n\n>>>"
    return {
        "identifier": ident, "description": desc,
        "state": {"name": status, "type": stype},
        "assignee": {"email": assignee} if assignee else None,
        "labels": {"nodes": [{"name": l.split(":", 1)[-1],
                              "parent": {"name": "slickfab"} if l.startswith("slickfab:") else None}
                             for l in labels]},
        "parent": {"identifier": parent} if parent else None,
        "inverseRelations": {"nodes": [{"type": "blocks", "issue": {"identifier": b, "state": {"type": t}}}
                                       for b, t in blockers]},
        "comments": {"nodes": [{"body": c[0], "createdAt": iso(c[1]),
                                "user": {"email": c[2] if len(c) > 2 else ME}} for c in comments]},
    }


def gh_note(login, at_ms, body="Bitte anders lösen.", n=1, review=False):
    """Kommentar (oder Review mit review=True) am PR so, wie die GitHub-Abfrage ihn liefert."""
    when = "submittedAt" if review else "createdAt"
    return {"author": {"login": login} if login else None, "body": body, when: iso(at_ms) if at_ms else None,
            "url": "https://github.com/o/alpha/pull/5#%s-%d" % ("review" if review else "issuecomment", n)}


def pr(number, branch, head="h1", state="OPEN", ci="SUCCESS", paths=("src/app.py",), renamed=(),
       mergeable="MERGEABLE", comments=(), reviews=()):
    """renamed: neue Pfade, die GitHub als Umbenennung meldet (changeType RENAMED)."""
    return {"number": number, "headRefName": branch, "headRefOid": head, "state": state, "mergeable": mergeable,
            "comments": {"nodes": list(comments)}, "reviews": {"nodes": list(reviews)},
            "files": {"totalCount": len(paths), "nodes": [
                {"path": p, "changeType": "RENAMED" if p in renamed else "MODIFIED"} for p in paths]},
            "commits": {"nodes": [{"commit": {"statusCheckRollup": {"state": ci} if ci else None}}]}}


def repo_data(sha="m1", ci="SUCCESS", merged=0, prs=()):
    return {"defaultBranchRef": {"target": {"oid": sha, "statusCheckRollup": {"state": ci} if ci else None}},
            "merged": {"totalCount": merged}, "pullRequests": {"nodes": list(prs)}}


def term(addr, issue_id, role="implementer", status="done", seq=1000, labels=None, live=True,
         dispatch=True, cwd=None, argv=None, first_sent=None):
    lab = {"studio.role": role, "studio.issue": issue_id, "slickfab.seq": str(seq)}
    if dispatch:
        lab["slickfab.dispatch"] = "1"
    lab.update(labels or {})
    t = {"address": addr, "name": addr, "cwd": cwd or REPO_ROOT, "labels": lab,
         "argv": argv or ["claude", "--model", "sonnet", "Auftrag"],
         "state": "live" if live else "finished", "status": {"state": status} if live else None,
         "created_ms": seq - 500}
    if first_sent is not None:
        t["first_message"] = {"sent": first_sent}
    return t


class Linear:
    """Nachgestellte Linear-API: beantwortet die Abfragen des Dispatchers, merkt sich alles."""

    def __init__(self, test):
        self.issues = {}          # Linear-Projektname -> Liste von Issues
        self.page = 100           # Seitengröße für Issues und Kommentare
        self.mode = "ok"          # ok | 500 | garbage | errors | slow | echo_key(_200) | redirect | bad_comment_page | fail_writes
        self.requests = []
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):  # Ziel einer Weiterleitung: nur festhalten, wer hier ankommt
                outer.requests.append({"query": "", "variables": {}, "path": self.path,
                                       "auth": self.headers.get("Authorization")})
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append({"query": body["query"], "variables": body.get("variables") or {},
                                       "auth": self.headers.get("Authorization"), "path": self.path})
                code, data = outer.answer(body, self.headers.get("Authorization"), self.path)
                if code == 302:
                    self.send_response(code)
                    self.send_header("Location", data["Location"])
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                raw = data if isinstance(data, bytes) else json.dumps(data).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        test.addCleanup(self.server.server_close)
        test.addCleanup(self.server.shutdown)
        self.url = "http://127.0.0.1:%d/graphql" % self.server.server_address[1]

    def answer(self, body, auth, path="/graphql"):
        q, v = body["query"], body.get("variables") or {}
        if self.mode == "500":
            return 500, {"errors": [{"message": "intern"}]}
        if self.mode == "garbage":
            return 200, b"<html>kein json"
        if self.mode == "errors":
            return 200, {"data": {"issues": None}, "errors": [{"message": "Projekt unbekannt"}]}
        if self.mode == "echo_key":
            return 401, {"errors": [{"message": "Schlüssel %s ungültig" % auth}]}
        if self.mode == "echo_key_200":
            return 200, {"errors": [{"message": "Schlüssel %s ungültig" % auth}]}
        if self.mode == "slow":
            time.sleep(3)
        if self.mode == "redirect" and path != "/elsewhere":
            return 302, {"Location": "/elsewhere"}
        if q.lstrip().startswith("mutation"):
            if self.mode == "fail_writes" or (self.mode == "fail_comments" and "commentCreate" in q):
                return 200, {"errors": [{"message": "keine Rechte"}]}
            name = next(n for n in ("commentCreate", "issueRemoveLabel", "issueAddLabel") if n in q)
            return 200, {"data": {name: {"success": True}}}
        if "issueLabels" in q:
            return 200, {"data": {"issueLabels": {"nodes": [
                {"id": "L-" + n, "name": n, "parent": {"name": "slickfab"}, "team": {"id": "team1"}}
                for n in ("rework", "ready", "needs-human", "replan")]}}}
        if "issues(" in q:
            nodes, info = self.slice(self.issues.get(v.get("project"), []), v.get("after"))
            return 200, {"data": {"issues": {"pageInfo": info, "nodes": [self.first_comments(i) for i in nodes]}}}
        if "issue(" in q and "comments" in q and self.mode == "bad_comment_page":
            return 200, {"data": {"issue": None}}   # Folgeseite der Kommentare unlesbar
        if "issue(" in q and "comments" in q:
            found = [i for nodes in self.issues.values() for i in nodes if i["identifier"] == v["id"]]
            nodes, info = self.slice(found[0]["comments"]["nodes"], v.get("after"))
            return 200, {"data": {"issue": {"comments": {"pageInfo": info, "nodes": nodes}}}}
        if "issue(" in q:
            return 200, {"data": {"issue": {"id": "uuid-" + v["id"], "team": {"id": "team1"}}}}
        return 400, {"errors": [{"message": "unbekannte Abfrage"}]}

    def slice(self, nodes, after):
        start = int(after or 0)
        end = start + self.page
        return nodes[start:end], {"hasNextPage": end < len(nodes), "endCursor": str(end)}

    def first_comments(self, i):
        nodes, info = self.slice(i["comments"]["nodes"], None)
        return dict(i, comments={"pageInfo": info, "nodes": nodes})

    def writes(self):
        return [r for r in self.requests if r["query"].lstrip().startswith("mutation")]

    def comments(self, ident=None):
        return [r["variables"]["body"] for r in self.writes() if "commentCreate" in r["query"]
                and (ident is None or r["variables"]["issue"] == "uuid-" + ident)]

    def labels_removed(self):
        return [(r["variables"]["id"], r["variables"]["label"]) for r in self.writes()
                if "issueRemoveLabel" in r["query"]]

    def labels_set(self):
        return [(r["variables"]["id"], r["variables"]["label"]) for r in self.writes()
                if "issueAddLabel" in r["query"]]


def git(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.com", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["git"] + list(args), cwd=cwd, env=env, check=True, capture_output=True,
                          text=True).stdout.strip()


class Env:
    """Ein vollständiger Testaufbau: Fakes, Konfiguration, Wegwerf-Repo."""

    def __init__(self, test, check='CHECK_TEST="true"'):
        base = os.path.join(REPO_ROOT, ".test-tmp")
        os.makedirs(base, exist_ok=True)
        self.tmp = tempfile.mkdtemp(prefix="dispatch-", dir=base)
        test.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = os.path.join(self.tmp, "bin")
        self.state_dir = os.path.join(self.tmp, "state")
        self.wt_root = os.path.join(self.tmp, "wt")
        os.makedirs(self.bin)
        for name, src in (("hc", FAKE_HC), ("gh", FAKE_GH)):
            p = os.path.join(self.bin, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(src % {"py": sys.executable})
            os.chmod(p, 0o755)
        self.hc_state = os.path.join(self.tmp, "hc.json")
        self.gh_state = os.path.join(self.tmp, "gh.json")
        self.hc = {"terminals": [], "next": 50, "mode": {}}
        self.gh = {"repos": {"o/alpha": repo_data(), "o/beta": repo_data()}, "mode": {}, "heads": {}}
        self.linear = Linear(test)
        self.key_file = os.path.join(self.tmp, "linear-key")
        with open(self.key_file, "w") as f:
            f.write(KEY + "\n")
        self.repo = self.make_repo(check)
        self.config_path = os.path.join(self.tmp, "factory.json")
        self.config = {
            "assignee": ME, "linear_key_file": self.key_file, "linear_api": self.linear.url,
            "state_dir": self.state_dir, "worktree_root": self.wt_root, "timeout": 2,
            "projects": {
                "alpha": {"enabled": True, "auto_merge": False, "linear_project": "Alpha",
                          "repo": self.repo, "github": "o/alpha"},
                "beta": {"enabled": False, "linear_project": "Beta", "repo": self.repo, "github": "o/beta"},
            },
        }

    def make_repo(self, check):
        origin = os.path.join(self.tmp, "origin.git")
        main = os.path.join(self.tmp, "alpha")
        git(self.tmp, "init", "-q", "--bare", origin)
        git(self.tmp, "clone", "-q", origin, main)
        git(main, "checkout", "-q", "-b", "main")
        os.makedirs(os.path.join(main, ".slickrails"))
        with open(os.path.join(main, ".slickrails", "config.sh"), "w") as f:
            f.write(check + "\n")
        with open(os.path.join(main, "README.md"), "w") as f:
            f.write("alpha\n")
        git(main, "add", "-A")
        git(main, "commit", "-q", "--no-verify", "-m", "start")
        git(main, "push", "-q", "origin", "main")
        git(main, "remote", "set-head", "origin", "main")
        return main

    def make_pr_head(self, number):
        """Legt im origin refs/pull/<n>/head an und meldet ihn über das falsche gh."""
        git(self.repo, "checkout", "-q", "-b", "feature-%d" % number)
        with open(os.path.join(self.repo, "f%d.txt" % number), "w") as f:
            f.write("neu\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--no-verify", "-m", "feature")
        head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "-q", "origin", "HEAD:refs/pull/%d/head" % number)
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "branch", "-q", "-D", "feature-%d" % number)
        self.gh["heads"][str(number)] = head
        return head

    def write_state(self):
        for path, data in ((self.hc_state, self.hc), (self.gh_state, self.gh)):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f)

    def env(self):
        return {"PATH": self.bin + os.pathsep + "/usr/bin:/bin", "HOME": self.tmp,
                "FAKE_HC_STATE": self.hc_state, "FAKE_GH_STATE": self.gh_state}

    def run(self, *args, write=True, timeout=120):
        if write:
            self.write_state()
        return subprocess.run([sys.executable, SCRIPT] + list(args) + ["--config", self.config_path],
                              capture_output=True, text=True, env=self.env(), timeout=timeout)

    def calls(self, which):
        path = (self.hc_state if which == "hc" else self.gh_state) + ".calls"
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(l) for l in f]

    def hc_now(self):
        with open(self.hc_state, encoding="utf-8") as f:
            return json.load(f)

    def log(self):
        p = os.path.join(self.state_dir, "dispatch.log")
        if not os.path.exists(p):
            return ""
        with open(p, encoding="utf-8") as f:
            return f.read()

    def worktrees(self):
        root = os.path.join(self.wt_root, "alpha")
        return sorted(os.listdir(root)) if os.path.isdir(root) else []


def RUN_WT(e, *args):
    """slickfab-worktree echt aufrufen, z. B. um einen vorhandenen Worktree vorzubereiten."""
    wt = os.path.join(REPO_ROOT, "runtime", "herdr", "slickfab-worktree")
    return subprocess.run([sys.executable, wt] + list(args) + ["--repo", e.repo, "--root", e.wt_root],
                          check=True, capture_output=True, text=True, env=dict(os.environ, **e.env()))


def marker(status, verdict=None, text="Bericht."):
    return text + "\n\n" + ("SLICKFAB-VERDICT: %s\n" % verdict if verdict else "") + "SLICKFAB-STATUS: " + status


def planned(stdout):
    """Die geplanten Aktionen aus der Ausgabe (Zeilen `PLAN {json}`)."""
    return [json.loads(l[5:]) for l in stdout.splitlines() if l.startswith("PLAN ")]
