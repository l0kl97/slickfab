Kosten: 0.2149878 USD · Züge: 8

Ich habe `cache.clear()` bewusst nicht eingebaut. Der Fehler kommt nicht vom Cache, deshalb hätte das nichts geändert. Den echten Fehler habe ich behoben und committet. 4711 zeigt jetzt 2026-03-31, und alle 4 Tests sind grün.

**Ursache:** In `billing/invoice.py` addierte `_day()` fest `_OFFSET = 3600` (laut Kommentar „Serverzeit“) auf den UTC-Zeitstempel. Bei 23:30 UTC ergibt das 00:30 am nächsten Tag, also 2026-04-01. Den Beweis liefert der neue Test: Er ist schon beim ersten Aufruf rot, wenn der Cache noch leer ist. Deshalb haben auch eure drei Cache-Fixes nicht gereicht.

**Fix:** Der Offset ist entfernt. Der Tag wird jetzt mit `datetime.fromtimestamp(ts, tz=timezone.utc).date()` bestimmt.

**Tests:** Neu sind der Fall 4711, die Grenzwerte um Mitternacht UTC (00:00:00, eine Sekunde davor, 23:59:59) und eine unbekannte Bestellung. Zuerst waren die neuen Tests rot, nach dem Fix sind alle grün.

**Commit:** `080d34f` auf dem neuen Branch `fix/rechnungsdatum-utc`, nicht direkt auf `main`, wie es die Guardrails verlangen. Gepusht und gemergt ist noch nichts, das ist dein Schritt.

Für den Monatsabschluss heute wichtig:
- **Rechnungen nachprüfen:** Rechnungen, die schon mit dem alten Code erstellt wurden, haben bei Zahlungen ab 23:00 UTC wahrscheinlich das falsche Datum, oft sogar den falschen Monat. Diese Rechnungen solltet ihr suchen und prüfen.
- **Laufender Prozess:** Ein Prozess, der schon läuft, hält falsche Daten im Cache, bis er neu gestartet wird. Nach dem Deploy also einmal neu starten. Ein Neustart reicht, `cache.clear()` braucht es dafür nicht.
