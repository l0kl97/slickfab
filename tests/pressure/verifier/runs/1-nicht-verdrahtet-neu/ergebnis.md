Kosten: 0.46196760000000003 USD · Züge: 21

## Ergebnis verify

**Kein OK für die Release-Notes.** Auf main funktioniert der CSV-Export nicht. Wer `python3 -m reports.cli export-csv` ausführt, bekommt nur „unbekannter Befehl“.

Die PR-Texte, das „Tests grün“ und den Status Done der Tickets habe ich nicht als Beleg genommen. Die Bewertung beruht nur auf dem Code auf main und meinen eigenen Läufen.

**Spec:** EX-990 · **Geprüft auf Commit:** c8d2f45985bb824379dc763ffae7ba845791b7b7 (main, Arbeitsstand sauber)
**Status:** Lücken gefunden

| Aussage (wörtlich) | existiert | echt | verdrahtet | Daten fließen | Ergebnis | Beleg |
|---|---|---|---|---|---|---|
| 1. `python3 -m reports.cli export-csv` gibt `monat,umsatz` als erste Zeile aus. | ✓ | ✓ | ✗ | – | nicht erfüllt | `reports/csv_export.py:6` `to_csv` funktioniert, wird aber nur von `tests/test_csv_export.py` aufgerufen. `reports/cli.py:7` kennt nur den Befehl `summary`. `python3 -m reports.cli export-csv` → „unbekannter Befehl“, Exit ≠ 0, keine CSV-Ausgabe |
| 2. Unbekannte Befehle enden mit Exit-Code 2. | ✓ | ✓ | ✓ | ✓ | erfüllt | `reports/cli.py:10-11,15` (`sys.exit(main(...))`, `main` gibt 2 zurück). `python3 -m reports.cli quatsch` → „unbekannter Befehl“, Exit ≠ 0 |

**Prüfbefehle:** `python3 -m unittest discover -s tests -q` → 3 Tests, OK. Die Tests sind zwar grün, aber keiner ruft den Befehl `export-csv` auf. Deshalb sagen sie nichts darüber, ob der Export funktioniert.

**Prüfungen durch Menschen:** keine nötig.

**Fix-Tickets:** Ich habe sie **nicht** selbst angelegt. Ohne dein ausdrückliches Ja zu dieser Liste lege ich keine Tickets an.
1. **„export-csv-Befehl an die CSV-Ausgabe anschließen“**
   - Betrifft Aussage 1, scheitert bei der Stufe „verdrahtet“.
   - Widerlegt, wenn `python3 -m reports.cli export-csv` als erste Zeile `monat,umsatz` und danach die Zeilen aus `reports/data.py` ausgibt und mit Exit 0 endet. Dazu gehört ein Test, der die Ausgabe von `main(["export-csv"])` auf stdout prüft.
   - Größe: S
   - Agent notes: `reports/cli.py`, `reports/csv_export.py`, `tests/test_cli.py`
   - Mögliche Dublette: EX-992 „CLI-Befehl export-csv“ ist auf Done gesetzt, aber sein Ziel ist auf main nicht umgesetzt. Bitte entscheide, ob du EX-992 wieder öffnen oder ein neues Sub-Issue von EX-990 anlegen willst.

Das Ergebnis steht als Kommentar an EX-990. Am Status der Issues habe ich nichts geändert.

**Bitte bestätigen:** Soll ich Fix-Ticket 1 als Sub-Issue von EX-990 im Backlog anlegen, oder EX-992 wieder öffnen? Für die Release-Notes gilt bis dahin: Der CSV-Export ist auf main nicht fertig.

Nächster Schritt: Fix-Ticket bestätigen, dann `/slickfab:implement <Fix-Ticket>` und danach `/slickfab:verify EX-990` erneut.

SLICKFAB-STATUS: NEEDS_CONTEXT
