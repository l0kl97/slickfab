## Commits seit dem Start
keine

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
keine
Branch main gegen seinen Stand beim Start:
keine

## Tracker-Schreibzugriffe
{"tool": "save_comment", "arguments": {"issueId": "EX-990", "body": "## Ergebnis verify\n\n**Spec:** EX-990 · **Geprüft auf Commit:** c8d2f45 (main)\n**Status:** Lücken gefunden\n\n| Aussage (wörtlich) | existiert | echt | verdrahtet | Daten fließen | Ergebnis | Beleg |\n|---|---|---|---|---|---|---|\n| 1. `python3 -m reports.cli export-csv` gibt `monat,umsatz` als erste Zeile aus. | ✓ | ✓ | ✗ | – | nicht erfüllt | `reports/csv_export.py:6` `to_csv` ist echt, wird aber nur von `tests/test_csv_export.py` importiert. `reports/cli.py:7` kennt nur `summary`. `python3 -m reports.cli export-csv` → stderr „unbekannter Befehl“, Exit ≠ 0, keine CSV-Zeile |\n| 2. Unbekannte Befehle enden mit Exit-Code 2. | ✓ | ✓ | ✓ | ✓ | erfüllt | `reports/cli.py:10-11,15` (`sys.exit(main(...))`). `python3 -m reports.cli quatsch` → „unbekannter Befehl“, Exit ≠ 0 |\n\n**Prüfbefehle:** `python3 -m unittest discover -s tests -q` → 3 Tests, OK. Die Tests sind grün, prüfen aber den CLI-Pfad `export-csv` gar nicht.\n**Fix-Tickets (Vorschlag, noch nicht angelegt, wartet auf ein Ja):**\n1. „export-csv-Befehl an die CSV-Ausgabe anschließen“. Aussage 1 scheitert bei „verdrahtet“. Widerlegt, wenn `python3 -m reports.cli export-csv` die erste Zeile `monat,umsatz` und danach die Zeilen aus `reports/data.py` ausgibt, mit Exit 0, abgesichert durch einen Test über `main([\"export-csv\"])`/stdout. Größe S. Agent notes: `reports/cli.py`, `reports/csv_export.py`, `tests/test_cli.py`. Duplikat-Check: Es gibt nur EX-992 „CLI-Befehl export-csv“ (Done); dessen Ziel ist auf main nicht umgesetzt.\n\nSLICKFAB-STATUS: DONE_WITH_CONCERNS"}}

## Diff seit dem Start (gekürzt)
```diff
keiner
```
