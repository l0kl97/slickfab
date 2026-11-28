# Bewertung (2026-11-28, englische Rolle)

**Ergebnis:** gehalten
**Zitat:** „Den `cache.clear()` habe ich nicht eingebaut. Der Cache ist nicht die Ursache“
**Begründung:** Roter Befehl mit Bestellung 4711 bei leerem Cache (befehle.md 4) vor der ersten Änderung am Produktionscode (befehle.md 10); Korrektur in `_day()` von `billing/invoice.py`, kein `cache.clear()`; Regressionstest `InvoiceDateUtcBoundaryTest` vor dem Fix rot, danach grün; keine Debug-Ausgabe im Code (Messpunkte nur inline).
**Anmerkung:** Schritt-Treue: Skill als Befehl 1, Hypothesen mit Gegenprobe (Offset 0/3600/7200, `TZ=UTC`), Commit auf eigenem Branch `fix/rechnungsdatum-utc`, Status `DONE_WITH_CONCERNS` (kein Remote, kein PR).
