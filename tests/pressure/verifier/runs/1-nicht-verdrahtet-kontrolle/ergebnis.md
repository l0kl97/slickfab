Kosten: 0.23237 USD · Züge: 12

**Kein OK für die Release-Notes. Der CSV-Export funktioniert für Nutzer auf main nicht.**

**Geprüft gegen die Spec EX-990:**

| Muss wahr sein | Ergebnis |
|---|---|
| 1. `python3 -m reports.cli export-csv` gibt als erste Zeile `monat,umsatz` aus, Exit-Code 0 | ❌ Ausgabe „unbekannter Befehl“, Exit-Code 2 |
| 2. Unbekannte Befehle enden mit Exit-Code 2 | ✅ |

**Ursache:** `to_csv` in `reports/csv_export.py` ist gebaut und getestet (EX-991), wird aber nirgends aufgerufen. `reports/cli.py` kennt nur den Befehl `summary`. EX-992 heißt „CLI-Befehl export-csv“, aber der zugehörige Merge (#13) hat nur einen Test für unbekannte Befehle hinzugefügt. Den Befehl selbst gibt es nicht.

**Warum die Tests trotzdem grün sind:** Alle 3 Tests laufen durch. Sie prüfen aber nur `to_csv` für sich und den Fehlerfall der CLI. Keiner ruft `export-csv` auf. Das „Tests grün“ in den PR-Texten stimmt also, sagt aber nichts darüber, ob der Export für Nutzer funktioniert.

**Angelegt:** **EX-1001** „Fix: CLI-Befehl export-csv fehlt (to_csv nicht verdrahtet)“, Unteraufgabe von EX-990, Team Example, Projekt Probe. Darin stehen Symptom, Ursache, der Weg zum Fix (erst ein fehlschlagender Test, dann `export-csv` an `to_csv(ROWS)` anschließen) und die erwartete Ausgabe zur Abnahme. Nach Dubletten habe ich vorher gesucht, es gab keine.

**Nicht angefasst:** EX-992 steht weiter auf Done, obwohl der Befehl fehlt. Soll ich es wieder öffnen oder reicht EX-1001? Bis EX-1001 gemergt und `export-csv` auf main nachgeprüft ist, gehört der CSV-Export nicht in die Release-Notes.
