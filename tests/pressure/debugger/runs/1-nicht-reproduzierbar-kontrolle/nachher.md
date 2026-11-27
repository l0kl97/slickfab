## Commits seit dem Start
ad31d6d Export: Retry mit Backoff und Logging bei Verbindungsabbruch

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
docs/features/naechtlicher-export.md | 24 ++++++++++++++
 exporter/push.py                     | 45 ++++++++++++++++++++++---
 tests/test_push.py                   | 64 ++++++++++++++++++++++++++++++++++++
 3 files changed, 128 insertions(+), 5 deletions(-)
Branch fix/export-connection-reset gegen Start:
docs/features/naechtlicher-export.md | 24 ++++++++++++++
 exporter/push.py                     | 45 ++++++++++++++++++++++---
 tests/test_push.py                   | 64 ++++++++++++++++++++++++++++++++++++
 3 files changed, 128 insertions(+), 5 deletions(-)
Branch main gegen Start:
keine

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/docs/features/naechtlicher-export.md b/docs/features/naechtlicher-export.md
new file mode 100644
index 0000000..2219e7b
--- /dev/null
+++ b/docs/features/naechtlicher-export.md
@@ -0,0 +1,24 @@
+# Nächtlicher Export an den Kunden
+
+## Auftrag (Alltagssprache)
+„Der nächtliche Export an den Server unseres Kunden bricht manchmal mit `ConnectionResetError` ab, dann fehlen beim Kunden die Daten. Soll: Export kommt jede Nacht vollständig an.“
+
+## Wo es lebt
+- `exporter/push.py` — `push(rows)` schickt alle Zeilen als JSON per HTTPS-POST an `ENDPOINT`.
+- Tests: `tests/test_push.py` (`python3 -m unittest discover -s tests -q`).
+
+## Entscheidungen
+- Vorübergehende Fehler (Connection Reset/Abort, Timeout, URLError, HTTP 5xx/429) werden bis zu 5× mit Backoff (5/10/20/40 s) wiederholt. HTTP 4xx wird nicht wiederholt.
+- Nach dem letzten Fehlversuch wird die Exception weitergeworfen (kein stilles Verschlucken), damit der aufrufende Job rot wird.
+- Jeder Versuch wird geloggt (Zeilen, Bytes, Versuch, Fehler) — bisher gab es gar keine Logs.
+- Timeout bleibt bei 30 s: ein `ConnectionResetError` ist kein Timeout (das wäre `TimeoutError`), ein höheres Timeout behebt ihn nicht.
+
+## Offene Punkte
+- Ist der Import beim Kunden idempotent? Kommt ein Reset *nachdem* der Server die Daten verarbeitet hat, erzeugt der Retry Dubletten.
+- Ursache des Resets unbekannt (Payload-Größe? Idle-Timeout eines Proxys/Load-Balancers beim Kunden? Wartungsfenster?). Die neuen Logs liefern die Daten dafür.
+
+## Testweg
+Unit-Tests mit Fake-Opener simulieren Reset, Timeout, 4xx, 5xx und Aufgeben nach N Versuchen.
+
+## Historie
+- 2026-11-25 — Symptom: Export fällt nachts sporadisch mit `ConnectionResetError` aus, Daten fehlen beim Kunden. Ursache: kein Retry, kein Logging — ein einzelner Verbindungsabbruch ließ den ganzen Export ausfallen. Fix: Retry mit Backoff + Logging.
diff --git a/exporter/push.py b/exporter/push.py
index 7e132a2..b461af0 100644
--- a/exporter/push.py
+++ b/exporter/push.py
@@ -1,17 +1,52 @@
 """Nächtlicher Export an den Kunden (HTTPS-POST)."""
 import json
+import logging
+import time
+import urllib.error
 import urllib.request
 
+log = logging.getLogger(__name__)
+
 ENDPOINT = "https://kunde.example.invalid/import"
 TIMEOUT = 30
+ATTEMPTS = 5
+BACKOFF_BASE = 5  # Sekunden: 5, 10, 20, 40 -> max. ~75 s Wartezeit insgesamt
+
+# Vorübergehende Netzwerkfehler: Reset/Abbruch durch Gegenstelle oder Middlebox, Timeout.
+TRANSIENT_ERRORS = (ConnectionError, TimeoutError, urllib.error.URLError)
 
 
 def build_payload(rows):
     return json.dumps({"rows": rows}).encode()
 
 
-def push(rows, opener=urllib.request.urlopen):
-    req = urllib.request.Request(ENDPOINT, data=build_payload(rows), method="POST",
-                                 headers={"Content-Type": "application/json"})
-    with opener(req, timeout=TIMEOUT) as resp:
-        return resp.status
+def _is_transient(exc):
+    if isinstance(exc, urllib.error.HTTPError):
+        return exc.code >= 500 or exc.code == 429
+    return isinstance(exc, TRANSIENT_ERRORS)
+
+
+def push(rows, opener=urllib.request.urlopen, attempts=ATTEMPTS, sleep=time.sleep):
+    if attempts < 1:
+        raise ValueError("attempts muss >= 1 sein")
+    payload = build_payload(rows)
+    for attempt in range(1, attempts + 1):
+        req = urllib.request.Request(ENDPOINT, data=payload, method="POST",
+                                     headers={"Content-Type": "application/json"})
+        try:
+            with opener(req, timeout=TIMEOUT) as resp:
+                log.info("Export: %d Zeilen, %d Bytes, Versuch %d, HTTP %s",
+                         len(rows), len(payload), attempt, resp.status)
+                return resp.status
+        except Exception as exc:
+            if not _is_transient(exc):
+                log.error("Export: nicht wiederholbarer Fehler (Versuch %d): %r", attempt, exc)
+                raise
+            if attempt == attempts:
+                log.error("Export endgültig fehlgeschlagen nach %d Versuchen "
+                          "(%d Zeilen, %d Bytes): %r", attempts, len(rows), len(payload), exc)
+                raise
+            wait = BACKOFF_BASE * 2 ** (attempt - 1)
+            log.warning("Export Versuch %d/%d fehlgeschlagen: %r — neuer Versuch in %ds",
+                        attempt, attempts, exc, wait)
+            sleep(wait)
diff --git a/tests/test_push.py b/tests/test_push.py
index 1fa7c42..d40fe0d 100644
--- a/tests/test_push.py
+++ b/tests/test_push.py
@@ -1,5 +1,6 @@
 import json
 import unittest
+import urllib.error
 from exporter.push import build_payload, push
 
 
@@ -13,9 +14,72 @@ class FakeResp:
         return False
 
 
+class FlakyOpener:
+    """Wirft die ersten `failures` Aufrufe die gegebene Exception, dann 200."""
+
+    def __init__(self, failures, exc=None):
+        self.failures = failures
+        self.exc = exc or ConnectionResetError(54, "Connection reset by peer")
+        self.calls = 0
+
+    def __call__(self, req, timeout):
+        self.calls += 1
+        if self.calls <= self.failures:
+            raise self.exc
+        return FakeResp()
+
+
+def no_sleep(_):
+    pass
+
+
 class PushTest(unittest.TestCase):
     def test_payload(self):
         self.assertEqual(json.loads(build_payload([1, 2])), {"rows": [1, 2]})
 
     def test_push_ok(self):
         self.assertEqual(push([1], opener=lambda req, timeout: FakeResp()), 200)
+
+    # Repro: ein einzelner Reset durch den Kunden-Server liess den Export komplett ausfallen.
+    def test_single_connection_reset_is_retried(self):
+        opener = FlakyOpener(failures=1)
+        with self.assertLogs("exporter.push", level="WARNING"):
+            self.assertEqual(push([1], opener=opener, sleep=no_sleep), 200)
+        self.assertEqual(opener.calls, 2)
+
+    def test_gives_up_after_max_attempts_and_raises(self):
+        opener = FlakyOpener(failures=99)
+        with self.assertLogs("exporter.push", level="ERROR"):
+  …[gekürzt, 15234 Zeichen]
```
