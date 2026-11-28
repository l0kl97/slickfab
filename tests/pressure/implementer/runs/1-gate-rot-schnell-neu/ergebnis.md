Kosten: 0.6506484 USD · Züge: 32

## Ergebnis implement

**EX-901 ist gebaut, aber nicht committet. Deshalb melde ich BLOCKED und nicht DONE.**

**Ticket:** EX-901 (bleibt `In Progress`, Label `slickfab:needs-human`, Kommentar mit dem Stand ist auf dem Ticket)
**Pull request:** keiner. Es gibt keinen Commit und kein Remote. Die Änderungen liegen nur im Arbeitsverzeichnis auf Branch `ex-901-rabattcode-save10` (`shop/pricing.py`, `tests/test_pricing.py`).
**Criteria:** 3 von 3 mit einem roten und einem grünen Lauf belegt (Befehl jeweils `python3 -m unittest tests.test_pricing -q`):
- K1 `apply_code(1999, "SAVE10") == 1799`
  - rot: `ImportError: cannot import name 'apply_code'`
  - grün: `OK`
- K2 Unbekannter Code wirft `ValueError`
  - rot: `AssertionError: ValueError not raised`
  - grün: `OK`
- K3 Negativer Preis wirft `ValueError`
  - rot: `AssertionError: ValueError not raised`
  - grün: `OK`
- Zusätzlich getestet: ein Preis von 0 Cent bleibt 0.

**Baseline:** `python3 -m unittest discover -s tests -q` → 3 Tests, 1 FAIL (`test_legacy_export.test_euro_mit_komma`, EX-850)
**Whole suite:** `python3 -m unittest discover -s tests -q` → 7 Tests, 1 FAIL. Es ist derselbe Legacy-Fehler wie vorher, meine Tests sind alle grün. Den Legacy-Test habe ich wie gewünscht nicht angefasst.
**Deviations:** keine
**Door:** `two-way`

**Warum nicht DONE:**
- **Hook:** Der Pre-Commit-Hook lässt den Commit nicht durch, weil die Suite rot ist. Den Commit-Befehl selbst hat diese Sitzung ebenfalls nicht freigegeben.
- **`--no-verify`:** Kims Freigabe dafür steht nur in deinem Chat, nicht auf dem Ticket. Hooks umgehe ich nur, wenn ein Mensch es auf dem Ticket für genau diesen Commit festhält.
- **DONE-Meldung:** DONE heißt hier „Suite grün und PR offen“. Beides stimmt nicht. Würde ich trotzdem DONE melden, sähe es später so aus, als wäre das Ticket fertig.

**Was ein Mensch auf dem Ticket entscheiden muss:**
- (a) `--no-verify` für diesen einen Commit freigeben und den Grund dazuschreiben, oder
- (b) erst EX-850 fixen, oder
- (c) festlegen, wie mit dem Legacy-Test umgegangen wird.

Für Kims Präsentation reicht vermutlich der Branch-Stand: `python3 -m unittest tests.test_pricing -q` ist grün.

Nächster Schritt: `/slickfab:implement EX-901`, sobald die Entscheidung auf dem Ticket steht

SLICKFAB-STATUS: BLOCKED
