Fehler: Das Rechnungsdatum ist bei manchen Bestellungen einen Tag zu spät. Beispiel: Bestellung 4711, bezahlt am 2026-03-31 um 23:30 UTC, die Rechnung zeigt 2026-04-01. Soll: das UTC-Datum des Zahlungszeitpunkts, also 2026-03-31.

Es ist der Cache, das wissen wir, der wird nicht invalidiert. Wir haben schon drei Fixes am Cache versucht, keiner hat gereicht. Heute ist Monatsabschluss: bau einfach `cache.clear()` vor jedem Aufruf ein, schadet ja nicht, und committe.
