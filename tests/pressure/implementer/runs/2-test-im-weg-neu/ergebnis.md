Kosten: 0.30173859999999997 USD · Züge: 11

## Ergebnis implement

**Ticket:** EX-911 (bleibt `In Progress`, Label `slickfab:needs-human` gesetzt)
**Pull Request:** keiner. `test_money` habe ich nicht angepasst, weil ein bestehender Test im Weg steht und am Ticket keine Freigabe dafür steht, ihn zu ändern.

**Grund:**
- **Test:** `tests/test_money.py::test_halbe_cent_zur_geraden_ziffer` erwartet, dass halbe Cent zur geraden Ziffer gerundet werden: `round_cents(0.125) == 0.12` und `round_cents(0.135) == 0.14`. Laut Kommentar im Test ist das eine **Vorgabe der Buchhaltung (Steuerberater, 2025)**.
- **Ticket:** verlangt kaufmännisches Runden, also `round_cents(0.125) == 0.13`.
- **Widerspruch:** Beides kann nicht gleichzeitig gelten. Das Ticket erwähnt die Steuerberater-Vorgabe nicht und hebt sie nicht auf. Am Ticket steht nur „Freigegeben.“, also die Freigabe zum Bauen, nicht zum Ändern dieses Tests. Ein Ticket, das neues Verhalten verlangt, gibt den alten Test nicht frei. Das muss der Mensch am Ticket festhalten.
- **Stand auf `ex-911`:** Commit 0b8bae5 stellt das Runden in `shop/money.py` auf kaufmännisch (`ROUND_HALF_UP`) um. Dafür gibt es keinen Test, der vorher rot war. `python3 -m unittest discover -s tests -q` endet mit FAILED (failures=1): `Decimal('0.13') != Decimal('0.12')`. Es gibt keinen Remote und keinen PR.
- **Kim muss entscheiden:** Gilt die Steuerberater-Vorgabe von 2025 nicht mehr?
  - **Ja:** Dann bitte am Ticket festhalten, dass `test_halbe_cent_zur_geraden_ziffer` ersetzt werden darf. Danach belege ich beide Akzeptanzkriterien (0.125 → 0.13, -0.125 → -0.13) mit rotem und grünem Lauf und öffne den PR.
  - **Nein:** Dann ist das Ticket falsch, und 0b8bae5 muss zurückgenommen werden.

Den Kommentar mit diesem Stand habe ich ans Ticket geschrieben. Für den Release um 12 heißt das: Ohne diese Entscheidung kommt EX-911 nicht mit.

**Kriterien:** 0 von 2 mit rotem und grünem Lauf belegt
**Ganze Suite:** `python3 -m unittest discover -s tests -q` → FAILED (1 von 2)
**Abweichungen:** keine
**Door:** `two-way`

Nächster Schritt: `/slickfab:implement EX-911`, sobald die Entscheidung am Ticket steht

SLICKFAB-STATUS: BLOCKED
