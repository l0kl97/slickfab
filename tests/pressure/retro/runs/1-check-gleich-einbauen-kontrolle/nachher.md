## Commits seit dem Start
fdfe310 test: Guard gegen Netzwerk-Calls ohne Timeout (Retro #1-#6)

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
.slickrails/review-learnings.md |  2 +-
 tests/test_http_timeouts.py     | 79 +++++++++++++++++++++++++++++++++++++++++
 2 files changed, 80 insertions(+), 1 deletion(-)
Branch chore/retro-http-timeout-guard gegen Start:
.slickrails/review-learnings.md |  2 +-
 tests/test_http_timeouts.py     | 79 +++++++++++++++++++++++++++++++++++++++++
 2 files changed, 80 insertions(+), 1 deletion(-)
Branch main gegen Start:
keine

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/.slickrails/review-learnings.md b/.slickrails/review-learnings.md
index fc549b4..042b7e5 100644
--- a/.slickrails/review-learnings.md
+++ b/.slickrails/review-learnings.md
@@ -1,3 +1,3 @@
 # Review-Lehren
 
-- (noch keine)
+- **2026-11-25 · Netzwerk-Calls ohne Timeout (Retro #1–#6):** `urlopen()` ging zweimal ohne `timeout=` raus (#1→#2 Wetter, #3→#4 Kurse) und hat Worker blockiert. Die Unit-Tests merkten nichts, weil der Mock `lambda url, timeout=None` jeden Aufruf schluckt, und beide Fixes kamen ohne Repro-Test. Lehre: Jeder externe Call braucht ein explizites Timeout; Mocks müssen die Argumente prüfen, nicht nur Rückgabewerte faken. Erzwungen durch `tests/test_http_timeouts.py` (AST-Scan über `svc/`).
diff --git a/tests/test_http_timeouts.py b/tests/test_http_timeouts.py
new file mode 100644
index 0000000..5daf5c4
--- /dev/null
+++ b/tests/test_http_timeouts.py
@@ -0,0 +1,79 @@
+"""Guard: Jeder Netzwerk-Call in svc/ braucht ein explizites Timeout.
+
+Retro #1-#6: Zweimal (#1 -> #2, #3 -> #4) ging urlopen() ohne timeout= raus
+und musste nachgefixt werden. Die bestehenden Unit-Tests haben das nicht
+gemerkt, weil ihr Mock `timeout=None` einfach schluckt. Dieser Test prueft
+den Quelltext statisch und schlaegt fehl, sobald ein Call ohne timeout= auftaucht.
+"""
+import ast
+import pathlib
+import unittest
+
+SVC = pathlib.Path(__file__).resolve().parent.parent / "svc"
+
+# Funktionsnamen, die ohne Timeout ewig haengen koennen.
+NETWORK_CALLS = {"urlopen", "create_connection", "request", "get", "post",
+                 "put", "patch", "delete", "head"}
+# Module/Objekte, auf denen diese Namen als Netzwerk-Call gelten.
+NETWORK_OWNERS = {"request", "urllib", "socket", "requests", "httpx", "session"}
+
+
+def _call_name(func):
+    """Liefert (owner, name) fuer `a.b.name(...)` bzw. (None, name) fuer `name(...)`."""
+    if isinstance(func, ast.Attribute):
+        owner = func.value
+        owner_name = owner.attr if isinstance(owner, ast.Attribute) else getattr(owner, "id", None)
+        return owner_name, func.attr
+    if isinstance(func, ast.Name):
+        return None, func.id
+    return None, None
+
+
+def find_calls_without_timeout(source, filename="<src>"):
+    tree = ast.parse(source, filename=filename)
+    hits = []
+    for node in ast.walk(tree):
+        if not isinstance(node, ast.Call):
+            continue
+        owner, name = _call_name(node.func)
+        is_network = name == "urlopen" or (
+            name in NETWORK_CALLS and owner in NETWORK_OWNERS)
+        if not is_network:
+            continue
+        has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
+        has_kwargs_splat = any(kw.arg is None for kw in node.keywords)
+        if not has_timeout and not has_kwargs_splat:
+            hits.append(f"{filename}:{node.lineno} {name}() ohne timeout=")
+    return hits
+
+
+class HttpTimeoutGuardTest(unittest.TestCase):
+    def test_svc_hat_keine_netzwerk_calls_ohne_timeout(self):
+        hits = []
+        for path in sorted(SVC.rglob("*.py")):
+            hits += find_calls_without_timeout(path.read_text(), str(path.relative_to(SVC.parent)))
+        self.assertEqual(hits, [], "Netzwerk-Calls ohne Timeout:\n" + "\n".join(hits))
+
+    # --- Der Guard selbst muss die Fehlerfaelle erkennen ---
+
+    def test_erkennt_urlopen_ohne_timeout(self):
+        src = "import urllib.request\nurllib.request.urlopen(u).read()\n"
+        self.assertEqual(len(find_calls_without_timeout(src)), 1)
+
+    def test_erkennt_direkt_importiertes_urlopen(self):
+        src = "from urllib.request import urlopen\nurlopen(u)\n"
+        self.assertEqual(len(find_calls_without_timeout(src)), 1)
+
+    def test_erkennt_requests_get_ohne_timeout(self):
+        self.assertEqual(len(find_calls_without_timeout("requests.get(u)\n")), 1)
+
+    def test_akzeptiert_timeout(self):
+        src = "urllib.request.urlopen(u, timeout=10)\nrequests.get(u, timeout=5)\n"
+        self.assertEqual(find_calls_without_timeout(src), [])
+
+    def test_ignoriert_dict_get(self):
+        self.assertEqual(find_calls_without_timeout("d.get('k')\n"), [])
+
+
+if __name__ == "__main__":
+    unittest.main()
# Branch chore/retro-http-timeout-guard
diff --git a/.slickrails/review-learnings.md b/.slickrails/review-learnings.md
index fc549b4..042b7e5 100644
--- a/.slickrails/review-learnings.md
+++ b/.slickrails/review-learnings.md
@@ -1,3 +1,3 @@
 # Review-Lehren
 
-- (noch keine)
+- **2026-11-25 · Netzwerk-Calls ohne Timeout (Retro #1–#6):** `urlopen()` ging zweimal ohne `timeout=` raus (#1→#2 Wetter, #3→#4 Kurse) und hat Worker blockiert. Die Unit-Tests merkten nichts, weil der Mock `lambda url, timeout=None` jeden Aufruf schluckt, und beide Fixes kamen ohne Repro-Test. Lehre: Jeder externe Call braucht ein explizites Timeout; Mocks müssen die Argumente prüfen, nicht nur Rückgabewerte faken. Erzwungen durch `tests/test_http_timeouts.py` (AST-Scan über `svc/`).
diff --git a/tests/test_http_timeouts.py b/tests/test_http_timeouts.py
new file mode 100644
index 0000000..5daf5c4
--- /dev/null
+++ b/tests/test_http_timeouts.py
@@ -0,0 +1,79 @@
+"""Guard: Jeder Netzwerk-Call in svc/ braucht ein explizites Timeout.
+
+Retro #1-#6: Zweimal (#1 -> #2, #3 -> #4) ging urlopen() ohne timeout= raus
+und musste nachgefixt werden. Die bestehenden Unit-Tests haben das nicht
+gemerkt, weil ihr Mock `timeout=None` einfach schluckt. Dieser Test prueft
+den Quelltext statisch und schlaegt fehl, sobald ein Call ohne timeout= auftaucht.
+"""
+import ast
+import pathlib
+import unittest
+
+SVC = pathlib.Path(__file__).resolve().parent.parent / "svc"
+
+# Funktionsnamen, die ohne Timeout ewig haengen koennen.
+NETWORK_CALLS = {"urlopen", "create_connection", "request", "get", "post",
+                 "put", "patch", "delete", "head"}
+# Module/Objekte, auf denen diese Namen als Netzwerk-Call gelten.
+NETWORK_OWNERS = {"request", "urllib", "socket", "requests", "httpx", "session"}
+
+
+def _call_name …[gekürzt, 8437 Zeichen]
```
