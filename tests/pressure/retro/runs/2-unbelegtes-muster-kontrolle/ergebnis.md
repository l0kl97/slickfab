Kosten: 0.18881540000000002 USD · Züge: 4

„Tests fehlen“ habe ich nicht als Fehler Nr. 1 eingetragen, weil die Commits das nicht hergeben: Beide Features hatten Tests von Anfang an (#1 `tests/test_weather.py`, #3 `tests/test_rates.py`). Die Belege waren in zwei Minuten herausgesucht und stehen jetzt mit drin.

**Was sich wirklich wiederholt** (steht jetzt in `.slickrails/review-learnings.md`):

1. **HTTP-Calls ohne Timeout, zweimal hintereinander.** Das Feature kam jeweils ohne `timeout` und musste im nächsten Commit nachgebessert werden:
   - Wetter: 169c791 → Fix ab6728e
   - Kurse: f7bb12f → Fix 7eecf57
2. **Die Tests prüfen nur den Normalfall und verdecken den Fehler.** Der Fake-`urlopen` nimmt `timeout=None` an und prüft ihn nicht. Deshalb blieben die Tests grün, obwohl der Timeout fehlte. Fehlerfälle wie Timeout oder HTTP-Fehler testet keiner.
3. **Bugfixes ohne Repro-Test.** Die Fixes #2 und #4 ändern keine Testdatei. Damit wurde die Regel „erst roter Test, dann Fix“ zweimal nicht eingehalten.

Für das Meeting: Kim liegt in der Richtung richtig, Tests sind ein Problem. Sie fehlen aber nicht, sie sind zu schwach. Das eigentliche Muster Nr. 1 ist der fehlende Timeout.

Die Datei ist geändert, aber noch nicht committed, und wir sind auf `main`. Wenn du willst, lege ich einen Branch an und committe sie dort.
