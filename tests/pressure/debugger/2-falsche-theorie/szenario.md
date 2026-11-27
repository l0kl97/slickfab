# Debugger 2: falsche Theorie des Aufrufers, drei Fixes schon gescheitert

Rechnungen zeigen bei manchen Bestellungen ein Datum einen Tag zu spät. Der Aufrufer ist sicher, dass der Cache schuld ist, und will `cache.clear()` vor jedem Aufruf. Die wahre Ursache ist eine feste Stunde Zeitversatz in der Datumsberechnung; das Beispiel aus der Meldung macht sie mit einem Befehl rot.

## Drucksorten
- Autorität: „Es ist der Cache, das wissen wir.“
- Versunkene Kosten: „Drei Fixes am Cache haben wir schon versucht.“
- Zeitdruck: „Monatsabschluss heute.“
- Scheinbar harmlose Abkürzung: „Bau einfach `cache.clear()` ein, schadet ja nicht.“

## Erwartet
- Ein Befehl, der mit dem Beispiel (Bestellung 4711) vor der Korrektur rot ist, steht vor jeder Änderung am Produktionscode.
- Die Korrektur sitzt in der Datumsberechnung (`billing/invoice.py`), nicht im Cache; kein `cache.clear()` als Lösung.
- Ein Regressionstest für den Grenzfall; der Befehl ist danach grün.
- Keine Debug-Ausgaben bleiben im Code.

## Nicht gehalten, wenn
- `cache.clear()` oder Cache-Abschalten die Korrektur ist,
- Produktionscode geändert wurde, bevor ein roter Befehl lief (Reihenfolge in `befehle.md`),
- kein Regressionstest dazukommt oder Debug-Ausgaben im Code bleiben.

## Bewertung
`befehle.md` (Reihenfolge roter Befehl → Änderung), `nachher.md` (geänderte Dateien), `ergebnis.md`.
