## Commits seit dem Start
keine

## Arbeitsbaum
M .slickrails/review-learnings.md

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
.slickrails/review-learnings.md | 18 +++++++++++++++++-
 1 file changed, 17 insertions(+), 1 deletion(-)
Branch main gegen Start:
keine

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/.slickrails/review-learnings.md b/.slickrails/review-learnings.md
index fc549b4..fbe639d 100644
--- a/.slickrails/review-learnings.md
+++ b/.slickrails/review-learnings.md
@@ -1,3 +1,19 @@
 # Review-Lehren
 
-- (noch keine)
+## 1. Externe HTTP-Calls ohne Timeout (2× in 6 Commits)
+
+- **Muster:** Jeder neue Netzwerk-Call kam ohne `timeout` rein und musste im direkt folgenden PR nachgebessert werden.
+- **Belege:** `svc/weather.py` – eingeführt in 169c791 (#1), Fix ab6728e (#2) „hing ohne Timeout“. `svc/rates.py` – eingeführt in f7bb12f (#3), Fix 7eecf57 (#4) „blockierte den Worker“.
+- **Lehre:** Im Review bei jedem `urlopen`/HTTP-Client explizit nach `timeout`, Fehlerbehandlung und Logging fragen (Guardrail „Kein Code im Vakuum“).
+
+## 2. Tests da, aber nur Happy Path – und der Mock verdeckt den Fehler
+
+- **Muster:** Zu beiden Features gab es Tests. Der Fake-`urlopen` akzeptiert aber `timeout=None` und prüft nichts davon, also blieb der Test grün, obwohl der Timeout fehlte. Fehlerfälle (Timeout, HTTP-Fehler) testet keiner.
+- **Belege:** `tests/test_weather.py` (169c791), `tests/test_rates.py` (f7bb12f): beide `lambda url, timeout=None: R()`, keine Assertion auf `timeout`, kein Fehlerfall.
+- **Lehre:** Mocks müssen die relevanten Argumente prüfen (z. B. `timeout` gesetzt) und Fehlerpfade abdecken.
+
+## 3. Bugfixes ohne Repro-Test
+
+- **Muster:** Beide Fix-Commits ändern nur eine Zeile Code, keinen Test.
+- **Belege:** ab6728e (#2) und 7eecf57 (#4) – keine Änderung unter `tests/`.
+- **Lehre:** Guardrail „Bugfix = erst Repro-Test (rot), dann Fix (grün)“ wurde zweimal übergangen; im Review einfordern.
```
