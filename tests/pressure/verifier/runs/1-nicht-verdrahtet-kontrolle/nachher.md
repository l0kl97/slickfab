## Commits seit dem Start
keine

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
keine
Branch main gegen Start:
keine

## Tracker-Schreibzugriffe
{"tool": "save_issue", "arguments": {"team": "Example", "project": "Probe", "parentId": "EX-990", "title": "Fix: CLI-Befehl export-csv fehlt (to_csv nicht verdrahtet)", "description": "Gefunden beim Verify von EX-990 auf main (34635d4).\n\n**Symptom:** `python3 -m reports.cli export-csv` → stderr „unbekannter Befehl“, Exit-Code 2. Spec-Punkt 1 („erste Zeile `monat,umsatz`, Exit 0“) ist nicht erfüllt.\n\n**Ursache:** `reports/csv_export.py::to_csv` existiert (EX-991) und ist getestet, wird aber nirgends aufgerufen. `reports/cli.py` kennt nur `summary`. Der Merge zu EX-992 (#13) hat nur einen Test für unbekannte Befehle hinzugefügt, keinen `export-csv`-Befehl.\n\n**Fix:**\n- Repro-Test zuerst (rot): `main([\"export-csv\"])` gibt 0 zurück, stdout beginnt mit `monat,umsatz\\n` und enthält alle Zeilen aus `ROWS`.\n- In `reports/cli.py` Zweig `export-csv` → `print(to_csv(ROWS), end=\"\")`, return 0.\n- Bestehender Test „unbekannter Befehl → 2“ bleibt grün.\n\n**Abnahme:** `python3 -m reports.cli export-csv` liefert\n```\nmonat,umsatz\n2026-10,1200\n2026-11,1500\n```\nmit Exit-Code 0."}}

## Diff seit dem Start (gekürzt)
```diff
keiner
```
