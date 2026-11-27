Kosten: 0.3170134 USD · Züge: 10

Der Check ist eingebaut, und die Lehre steht in `.slickrails/review-learnings.md`. Beides liegt im Commit `fdfe310` auf dem Branch `chore/retro-http-timeout-guard`. Nicht auf main gepusht, kein PR. Mergen heißt Branch reinziehen.

**Retro #1–#6, Hauptbefund:** Derselbe Fehler kam zweimal. `urlopen()` lief ohne Timeout (Wetter #1 → Fix #2, Kurse #3 → Fix #4). Die Tests haben das nicht gemerkt, weil der Mock `lambda url, timeout=None` jeden Aufruf annimmt, egal mit welchen Argumenten. Beide Fixes kamen außerdem ohne Repro-Test.

**Der Check:** Nur die Zeile in den Learnings hätte den Fehler beim dritten Mal nicht verhindert. Deshalb gibt es einen echten Test, `tests/test_http_timeouts.py`. Er durchsucht `svc/` und schlägt fehl, sobald ein Netzwerk-Aufruf ohne `timeout=` auftaucht. Er hat eigene Tests für Fehlerfälle und für Fehlalarme wie `dict.get`.
- Auf dem alten Stand von #3 schlägt er an: `svc/rates.py:5 urlopen() ohne timeout=`.
- Auf main laufen alle 9 Tests grün (`python3 -m unittest discover -s tests -q`).

Eine Extra-Runde mit Kim war dafür nicht nötig.

**Zwei weitere Fehler, die ich nicht angefasst habe** (jeder braucht erst einen eigenen roten Test):
1. **`euro()` rechnet negative Beträge falsch:** `euro(-1999)` ergibt `"-20,01 €"` statt `"-19,99 €"`. Grund ist, dass `divmod` bei negativen Zahlen abrundet. Das betrifft #5, getestet ist nur der Normalfall.
2. **Die Tests ersetzen `urllib.request.urlopen` für den ganzen Prozess** und setzen es danach nicht zurück. Später laufende Tests bekommen dann den Mock statt der echten Funktion. Besser wäre `unittest.mock.patch` mit Prüfung, dass `timeout` übergeben wird.

Soll ich für beide Linear-Issues anlegen?
