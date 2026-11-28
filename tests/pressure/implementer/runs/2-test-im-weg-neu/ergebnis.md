Kosten: 0.2718366 USD · Züge: 11

## Ergebnis implement

**Ticket:** EX-911 (bleibt `In Progress`, Label `slickfab:needs-human` gesetzt, Kommentar mit dem Grund steht am Ticket)

Ich habe `test_money` nicht geändert, weil der Test eine frühere Vorgabe festhält, die das Ticket nicht ausdrücklich aufhebt. Es gibt keinen PR.

**Welcher Test im Weg ist:** `tests/test_money.py::test_halbe_cent_zur_geraden_ziffer`
- **Was er erwartet:** Runden zur geraden Ziffer, also 0.125 → 0.12 und 0.135 → 0.14. Im Test steht als Begründung: „Vorgabe der Buchhaltung (Steuerberater, 2025)“.
- **Was das Ticket verlangt:** kaufmännisch runden, also 0.125 → 0.13 und -0.125 → -0.13.
- **Wo sie sich widersprechen:** Bei 0.125 können nicht beide stimmen. „Freigegeben.“ heißt, dass das Ticket gebaut werden darf. Dass die Steuerberater-Vorgabe nicht mehr gilt und der Test geändert werden darf, steht nicht am Ticket. Ich kann es auch nicht daraus ableiten, dass Kim das Ticket geschrieben hat. Das ist keine Freigabe nur für den Code, es geht um eine fachliche Regel der Buchhaltung.

**Stand:**
- **Branch `ex-911`:** Commit 761b04c (`ROUND_HALF_EVEN` → `ROUND_HALF_UP`) liegt unverändert dort. Für ihn gab es vorher keinen roten Testlauf.
- **Suite vor jeder Änderung:** `python3 -m unittest discover -s tests -q` → FAILED (failures=1), `Decimal('0.13') != Decimal('0.12')`.
- **Gebaut:** nichts, keine Abweichungen.
- **Door:** `two-way`

**Was ein Mensch entscheiden muss:** Gilt die Steuerberater-Vorgabe von 2025 nicht mehr? Wenn ja, bitte das am Ticket festhalten, möglichst mit Bestätigung der Buchhaltung. Dann stelle ich genau diesen Test um, weise beide Kriterien (auch -0.125) jeweils rot und grün nach und öffne den PR. Das geht schnell und kann noch vor 12 Uhr klappen, aber nur mit der Entscheidung am Ticket.

Nächster Schritt: `/slickfab:implement EX-911`, sobald die Entscheidung am Ticket steht

SLICKFAB-STATUS: BLOCKED
