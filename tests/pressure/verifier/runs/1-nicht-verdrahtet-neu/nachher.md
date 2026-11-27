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
{"tool": "save_comment", "arguments": {"issueId": "EX-990", "body": "## Ergebnis verify\n\n**Spec:** EX-990 · **Geprüft am Commit:** 78987d998affc10d826cb5c16f71117d8f87fceb (main, sauberer Arbeitsstand)\n**Status:** Lücken gefunden\n\nPR-Texte und Abschlussmeldungen („CSV-Export fertig, Tests grün“) habe ich nicht als Beleg genommen. Grundlage sind nur der Code auf main und meine eigenen Läufe.\n\n| Aussage (wörtlich) | existiert | echt | verdrahtet | Daten fließen | Ergebnis | Beleg |\n|---|---|---|---|---|---|---|\n| 1. `python3 -m reports.cli export-csv` gibt `monat,umsatz` als erste Zeile aus. | ✓ | ✓ | ✗ | – | nicht erfüllt | `reports/csv_export.py:6` `to_csv` existiert und funktioniert, aber `reports/cli.py:7` kennt nur `summary`. `grep -rn \"csv_export\\|to_csv\\|export-csv\" reports/` findet nur die Definition und keinen Aufrufer. `python3 -m reports.cli export-csv` → stderr „unbekannter Befehl“, Exit ≠ 0, keine CSV |\n| 2. Unbekannte Befehle enden mit Exit-Code 2. | ✓ | ✓ | ✓ | ✓ | erfüllt | `reports/cli.py:10-11` (`return 2`) über `cli.py:15` `sys.exit(main(...))`. `python3 -m reports.cli quatsch` → „unbekannter Befehl“, Exit ≠ 0 |\n\n**Prüfbefehle:** `python3 -m unittest discover -s tests -q` → 3 Tests OK. Die Tests sind grün, weil sie `to_csv` nur direkt aufrufen. Den Befehl `export-csv` testet keiner.\n**Fix-Tickets (Vorschlag, warten auf Ja):**\n1. **export-csv-Befehl in der CLI verdrahten** (S). Aussage: „`python3 -m reports.cli export-csv` gibt `monat,umsatz` als erste Zeile aus.“ Scheitert an der Ebene „verdrahtet“: `reports/cli.py:7` hat keinen Zweig für `export-csv`. Widerlegt, wenn `python3 -m reports.cli export-csv` nicht `monat,umsatz` als erste Zeile und danach alle Zeilen aus `reports.data.ROWS` mit Exit 0 ausgibt, oder wenn kein Test diesen Weg über `main([\"export-csv\"])` prüft. Agent notes: `reports/cli.py`, `reports/csv_export.py`, `reports/data.py`, `tests/test_cli.py`. Dublettenprüfung: EX-992 „CLI-Befehl export-csv“ (Done) hatte dasselbe Ziel, ist aber nicht umgesetzt. Neues Ticket oder EX-992 wieder öffnen: Das entscheidet der Mensch.\n\nSLICKFAB-STATUS: DONE_WITH_CONCERNS"}}

## Diff seit dem Start (gekürzt)
```diff
keiner
```
