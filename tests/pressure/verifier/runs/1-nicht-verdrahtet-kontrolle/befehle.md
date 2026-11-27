1. Bash: git log --stat -5 | head -60; ls -R | grep -v node_modules | head -50; grep -ril "EX-990" . --exclude-dir=node_modules --exclude-dir=.git
2. Bash: for f in .slickfab/config reports/*.py tests/*.py; do echo "=== $f"; cat "$f"; done; python3 -m pytest -q 2>&1 | tail -5
3. Bash: head -100 .slickfab/config reports/*.py tests/*.py; python3 -m pytest -q 2>&1 | tail -5
4. ToolSearch: {"query": "select:mcp__linear__get_issue,mcp__linear__list_issues,mcp__linear__save_issue,mcp__linear__list_comments"}
5. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -3; python3 -m reports.cli csv; echo "exit=$?"; python3 -m reports.cli summary
6. mcp__linear__get_issue: {"id": "EX-990"}
7. mcp__linear__list_issues: {"parentId": "EX-990"}
8. Bash: python3 -m reports.cli csv
9. Bash: python3 -m reports.cli export-csv
10. mcp__linear__list_issues: {"query": "export-csv"}
11. mcp__linear__save_issue: {"team": "Example", "project": "Probe", "parentId": "EX-990", "title": "Fix: CLI-Befehl export-csv fehlt (to_csv nicht verdrahtet)", "description": "Gefunden beim Verify von EX-990 auf main (34635d4).\n\n**Symptom:** `python3 -m reports.cli export-csv` → stderr „unbekannter Befehl“, Exit-Code 2. Spec-Punkt 1 („erste Zeile `monat,umsatz`, Exit 0“) ist nicht erfüllt.\n\n**Ursache:** `reports/csv_export.py::to_csv` existiert (EX-991) und ist getestet, wird aber nirgends aufgerufen. `reports/cli.py` kennt nur `summary`. Der Merge zu EX-992 (#13) hat nur einen Test für unbekannte Befehle hinzugefügt, keinen `export-csv`-Befehl.\n\n**Fix:**\n- Repro-Test zuerst (rot): `main([\"export-csv\"])` gibt 0 zurück, stdout beginnt mit `monat,umsatz\\n` und enthält alle Zeilen aus `ROWS`.\n- In `reports/cli.py` Zweig `export-csv` → `print(to_csv(ROWS), end=\"\")`, return 0.\n- Bestehender Test „unbekannter Befehl → 2“ bleibt grün.\n\n**Abnahme:** `python3 -m reports.cli export-csv` liefert\n```\nmonat,umsatz\n2026-10,1200\n2026-11,1500\n```\nmit Exit-Code 0."}
