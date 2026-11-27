Kosten: 0.447796 USD · Züge: 18

## Ergebnis debug

Den `cache.clear()`-Fix habe ich nicht eingebaut. Der Cache ist nicht die Ursache: Das falsche Datum kommt auch mit leerem Cache. Die eigentliche Ursache ist ein fest eingebauter Versatz von einer Stunde („Serverzeit“). Den habe ich entfernt, die Tests laufen jetzt grün. Committen konnte ich nicht, weil `git commit` in dieser Sitzung eine Freigabe braucht, die ich nicht holen kann.

**Fehler:** Bestellung 4711 (bezahlt 2026-03-31 23:30 UTC) bekommt das Rechnungsdatum 2026-04-01 statt 2026-03-31.

**Roter Befehl:** `python3 -c 'from billing.invoice import invoice_date, cache; cache.clear(); r=invoice_date(4711); print("4711 mit leerem Cache:", r); assert r=="2026-03-31", r'`
- vorher rot: `4711 mit leerem Cache: 2026-04-01` und `AssertionError: 2026-04-01`
- nachher grün: `4711 mit leerem Cache: 2026-03-31`

**Ursache:** `billing/invoice.py` → `_day()` rechnet `(ts + _OFFSET) // 86400` mit `_OFFSET = 3600`. Jede Zahlung zwischen 23:00 und 24:00 UTC landet so auf dem Folgetag. Gemessen ohne Codeänderung, nur durch Setzen von `_OFFSET` beim Aufruf:
- Versatz 0: 4711 ergibt 2026-03-31, 4712 ergibt 2026-03-31 (Fehler weg).
- Versatz 3600: 4711 ergibt 2026-04-01 (das gemeldete Symptom).
- Versatz 13 h: auch 4712 (12:00 UTC) ergibt 2026-04-01 (wie vorhergesagt schlimmer).

**Ausgeschlossen:**
- **Cache wird nicht invalidiert:** Mit `cache.clear()` direkt vor dem Aufruf kommt trotzdem 2026-04-01. Deshalb haben die drei Cache-Fixes nichts gebracht, und `cache.clear()` vor jedem Aufruf würde nur den Cache abschalten, ohne das Datum zu korrigieren.
- **`paid_at` in `orders.py` falsch:** Der Wert ist `1774999800`, also 2026-03-31 23:30:00+00:00, und damit richtig.

**Regressionstest:** `tests/test_invoice.py::test_kurz_vor_mitternacht_utc` prüft 4711 auf 2026-03-31.
- Vor der Korrektur rot: `AssertionError: '2026-04-01' != '2026-03-31'`.
- Nach der Korrektur ist `python3 -m unittest discover -s tests -q` mit beiden Tests grün: `Ran 2 tests … OK`.

**Korrektur:** `_OFFSET` entfernt, `_day()` rechnet jetzt `ts // 86400`, also den UTC-Tag.

**Debug-Tag entfernt:** Ich habe keine Messpunkte in den Code gesetzt, alle Messungen liefen in der REPL. `grep -rn -e "_OFFSET" -e "DEBUG-" billing tests` findet nichts.

**Liegen geblieben:**
- Die Änderung liegt **nicht committet** auf dem Branch `fix/rechnungsdatum-utc`; `billing/invoice.py` und `tests/test_invoice.py` sind gestaged. Grund: `git commit` wurde mit „This command requires approval“ abgelehnt.
- Ein Pull Request fehlt, das Repo hat keinen Remote.
- Es gibt kein Ticket, deshalb auch keinen Ticket-Kommentar.
- Bitte selbst committen, die Nachricht nennt die bestätigte Hypothese:
  ```
  git commit -m "Rechnungsdatum: UTC-Tag statt Serverzeit (+1 h) verwenden" -m "Bestätigt: _day() addierte _OFFSET=3600 vor dem Abrunden auf Tage. Widerlegt: Cache (Fehler auch bei leerem Cache). Warum nicht gefangen: einziger Test lag auf 12:00 UTC."
  ```
- Zu klären: Bereits ausgestellte Rechnungen mit Zahlung zwischen 23:00 und 24:00 UTC tragen wahrscheinlich das falsche Datum. Wichtig zum Monatsabschluss, weil sie in den falschen Monat fallen können. Eine Korrektur alter Rechnungen habe ich nicht angefasst.

**Warum nicht gefangen:** Der einzige Test lag auf 12:00 UTC. Dort ändert ein Versatz von einer Stunde den Tag nicht, die Grenze kurz vor Mitternacht war nicht getestet.

**Wiederholungs-Sperre (Vorschlag für `/slickfab:retro`):** Datums-Ableitungen aus Zeitstempeln bekommen Pflicht-Grenzfälle (00:00, 23:59 UTC, Monatsletzter). Außerdem wäre ein Lint- oder Review-Check auf fest eingebaute Zeitzonen-Versätze sinnvoll (`+ 3600`, `_OFFSET`) statt `datetime.timezone.utc`.

Nächster Schritt: Änderung committen und einen Pull Request gegen main öffnen, danach `/slickfab:review <Pull Request>` in einer frischen Session

SLICKFAB-STATUS: DONE_WITH_CONCERNS
