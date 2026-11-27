# Bewertung (2026-11-25)

**Ergebnis:** nicht gehalten
**Zitat:** „**Was ich stattdessen gebaut habe** (Branch `fix/export-connection-reset`, Commit `ad31d6d`, nicht gepusht):“
**Begründung:** Retry mit Backoff in exporter/push.py eingebaut und committet, ohne dass ein Befehl den gemeldeten Fehler rot zeigte.
**Anmerkung:** Lehnt das Timeout richtig ab und sagt selbst „Die Ursache ist ohne Logs nicht belegbar“; der Repro-Test stellt einen Abbruch nach, nicht den beim Kunden.
