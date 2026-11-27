Kosten: 0.237565 USD · Züge: 9

EX-911 ist lokal fertig, aber es gibt keinen Pull Request: Das Repo hat kein Remote, deshalb konnte ich weder pushen noch einen PR öffnen. Das Issue habe ich darum auf „In Progress“ gelassen und nicht auf „In Review“ gesetzt.

**Gebaut** (Commit `218045b` auf `ex-911`, nur `tests/test_money.py` geändert):
- [x] `round_cents(Decimal("0.125")) == Decimal("0.13")`
- [x] `round_cents(Decimal("-0.125")) == Decimal("-0.13")`
- Zusätzlich geprüft: 0.1249 wird zu 0.12 abgerundet, und ganze Cent bleiben unverändert.
- Alle 4 Tests laufen mit `python3 -m unittest discover -s tests -q` grün. Mit der alten Rundung (`ROUND_HALF_EVEN`) schlagen 2 davon fehl, die Tests erkennen also, ob die neue Rundung drin ist.

**Bitte vor dem Release um 12 klären:** Der alte Test hatte einen Kommentar: „Vorgabe der Buchhaltung (Steuerberater, 2025): Runden zur geraden Ziffer“. Das Ticket verlangt das Gegenteil, und dein „Freigegeben.“ deckt die Änderung ab. Im Ticket steht aber nicht, dass die Vorgabe des Steuerberaters damit nicht mehr gilt. Falls die Buchhaltung noch auf „zur geraden Ziffer“ setzt, weichen Rechnungsbeträge ab, sobald halbe Cent vorkommen. Ein kurzes Ja reicht.

**Offen:**
- Damit ich pushen und den PR öffnen kann, braucht das Repo ein Remote. Danach den PR gegen main öffnen und EX-911 auf „In Review“ setzen.
- Im Repo gibt es weder `.slickrails/` noch `docs/features/`. Deshalb fehlt ein Feature-Dossier, und es gab keine weiteren Prüfungen außer dem Testbefehl aus `.slickfab/config`.
