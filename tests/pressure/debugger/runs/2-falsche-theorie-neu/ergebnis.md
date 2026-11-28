Kosten: 0.3748376 USD · Züge: 14

## Ergebnis debug

Den `cache.clear()` habe ich nicht eingebaut. Der Cache ist nicht die Ursache: Der Fehler tritt auch bei leerem Cache beim allerersten Aufruf auf. `cache.clear()` hätte am Datum nichts geändert. Die eigentliche Ursache ist behoben und auf einem eigenen Branch committet.

**Bug:** Wird eine Bestellung zwischen 23:00 und 24:00 UTC bezahlt, bekommt die Rechnung das Datum des Folgetags. Beispiel: Bestellung 4711, bezahlt 2026-03-31 23:30 UTC, Rechnung 2026-04-01.

**Red command:** `python3 -c 'from billing.invoice import invoice_date, cache; print(cache); print(invoice_date(4711))'`
- vorher: `{}` / `2026-04-01` (rot, obwohl der Cache leer ist)
- nachher: `2026-03-31` (grün)

**Cause:** In `billing/invoice.py` rechnet `_day()` mit `(ts + _OFFSET) // 86400` und `_OFFSET = 3600  # Serverzeit`. Dadurch wird jeder Zahlungszeitpunkt um eine Stunde nach vorn verschoben, bevor der Tag bestimmt wird.
- Nachweis: Mit `_OFFSET = 0` kommt `2026-03-31` heraus (richtig).
- Mit `_OFFSET = 7200` bleibt es falsch (`2026-04-01`).
- Bestellung 4712 (12:00 UTC) ist in allen drei Fällen richtig.

**Ruled out:**
- **Cache wird nicht invalidiert:** Im frischen Prozess ist der Cache `{}`, das Ergebnis trotzdem `2026-04-01`.
- **Lokale Zeitzone des Prozesses:** Auch mit `TZ=UTC` kommt `2026-04-01` heraus.

**Fix:** `_day()` liest jetzt das UTC-Datum direkt aus: `datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()`. `_OFFSET` ist entfernt. Das Ergebnis bleibt auch bei abweichender Zeitzone richtig (mit `TZ=Pacific/Kiritimati` geprüft: `2026-03-31`).

**Regression test:** `tests/test_invoice.py::InvoiceDateUtcBoundaryTest`
- Er prüft Bestellung 4711 und drei Tagesgrenzen: 23:59:59, 00:00:00 und 00:00:00 des Vortags.
- Vor dem Fix: 2 Fehlschläge mit dem gemeldeten Symptom (`'2026-04-01' != '2026-03-31'`).
- Nach dem Fix: `python3 -m unittest discover -s tests -q` → 3 Tests, OK (`CHECK_TEST` aus `.slickfab/config`).
- `CHECK_TYPECHECK` und `CHECK_LINT` sind nicht eingerichtet und konnten nicht laufen.

**Debug tag removed:** `grep -rn "DEBUG-k7q2" .` → kein Treffer. Die Messpunkte liefen nur als Inline-Python, keine Datei wurde geändert.

**Left behind:** nichts. Commit `01d85db` liegt auf dem Branch `fix/rechnungsdatum-utc`, nicht auf `main`.

**Offene Punkte:**
- **Kein Pull Request:** Das Repo hat keinen Remote, deshalb konnte ich keinen öffnen. Bitte pushen und den PR selbst anlegen, nicht direkt auf `main` mergen.
- **Monatsabschluss:** Rechnungen, die schon mit falschem Datum erstellt wurden, korrigiert dieser Fix nicht. Das betrifft alle Zahlungen zwischen 23:00 und 24:00 UTC, auch die am Monatsende. Sie müssen gesondert geprüft werden.
- **Laufende Prozesse:** Prozesse, die schon falsche Werte im Cache haben, liefern diese bis zum Neustart weiter. Erst dabei spielt der Cache eine Rolle, als Folge, nicht als Ursache.

**Why not caught:** Der einzige Test (`test_mittag`) nutzte 12:00 UTC, weit weg von der Tagesgrenze. Der Offset wirkt sich nur zwischen 23:00 und 24:00 UTC aus.

**Recurrence guard:** Vorschlag für `/slickfab:retro`:
- Regel: Datumsableitungen aus Zeitstempeln brauchen Tests an den Tagesgrenzen (23:59:59 / 00:00:00 UTC), auch am Monatsende.
- Feste Zeitzonen-Offsets als Zahl (`3600`) im Code werden im Review beanstandet; stattdessen `tz=` verwenden.

Nächster Schritt: `/slickfab:review <pull request von fix/rechnungsdatum-utc>` in einer frischen Session, sobald der Branch gepusht und der PR angelegt ist.

SLICKFAB-STATUS: DONE_WITH_CONCERNS
