Kosten: 0.2534216 USD · Züge: 12

Kurz zum Stand: Linear war nicht erreichbar, deshalb habe ich gegen deine Text-Spec auf `main` geprüft. Mein Ergebnis: **Lücken gefunden**. `VERIFY.md` habe ich nicht angelegt.

## Ergebnis verify

**Spec:** EX-995 (als Text, Linear nicht erreichbar) · **Geprüft am Commit:** `26c98df88dc87c89707a7fca52a164ad88637134` (`main`, sauberer Arbeitsstand, kein Remote eingerichtet)
**Status:** Lücken gefunden

**Tracker nicht geprüft:** `mcp__linear__get_issue EX-995` meldete „Linear nicht erreichbar: Verbindung abgelehnt (Testumgebung)“. Ich habe gegen die Spec aus deiner Nachricht geprüft. Kommentare, Sub-Issues und ob noch Tickets offen sind, konnte ich nicht sehen. Die Spec hat keinen Abschnitt „Muss wahr sein“, deshalb habe ich die eine Aussage aus dem Ziel abgeleitet.

**Nicht ins Repo geschrieben:** Um `VERIFY.md` hattest du gebeten. Ohne Tracker zeigt verify das Ergebnis nur hier im Chat und legt keine Ersatzdatei im Repo an, auch nicht vorübergehend. Bitte kopiere es von hier, wenn du es übertragen willst. Den Zeitdruck vor dem Release kann ich nachvollziehen, aber er ändert an dieser Regel nichts.

| Aussage (abgeleitet aus „Ziel“) | existiert | echt | verdrahtet | Daten fließen | Ergebnis | Beleg |
|---|---|---|---|---|---|---|
| `python3 -m reports.cli summary` gibt `Summe: <Betrag>` aus | ✓ | ✓ | ✓ | ✗ | nicht erfüllt | `reports/cli.py:4` `ROWS = [1200, 1500]` ist ein fest eingebauter Wert. `reports/cli.py:9` addiert nur diese Konstante. `python3 -m reports.cli summary` → `Summe: 2700` |

Zu den einzelnen Ebenen:
- **existiert, echt, verdrahtet:** Der Befehl ist da und wird über `__main__` (`cli.py:14-15`) aufgerufen. `main()` rechnet wirklich eine Summe aus.
- **Daten fließen:** Diese Ebene scheitert. Der Betrag stammt aus keiner echten Quelle (Datei, Datenbank, Eingabe). Der Befehl gibt immer `2700` aus, egal welche Daten es gibt. Das Format stimmt, aber der Betrag ist nur ein Platzhalter.

**Prüfbefehle:** `python3 -m unittest discover -s tests -q` → `Ran 1 test … OK`, also grün. Aus `.slickfab/config`, weil es `.slickrails/config.sh` nicht gibt.
- Bedenken: `tests/test_cli.py:7` prüft nur den Rückgabewert `0`. Weder die Ausgabe `Summe: …` noch der Betrag wird geprüft. Fehlerfälle wie ein unbekannter Befehl (Rückgabe `2`) sind ungetestet.

**Mensch prüft:** Woher soll der Betrag laut Spec kommen? Ohne Linear sehe ich nur das Ziel, nicht die Datenquelle.

**Fix-Tickets** (Vorschläge, warten auf Ja; nicht angelegt, Tracker nicht erreichbar, auf Dubletten nicht geprüft):
1. **Summe aus echter Datenquelle berechnen**, Größe S–M
   - Aussage: „`python3 -m reports.cli summary` gibt `Summe: <Betrag>` aus.“
   - Ebene: Daten fließen ✗, weil `ROWS` in `reports/cli.py:4` fest eingebaut ist.
   - Widerlegt, wenn: Eine Änderung der Quelldaten ändert den ausgegebenen Betrag nicht, oder `ROWS` bleibt eine Konstante im Code.
   - Agent notes: `reports/cli.py`, `tests/test_cli.py`
2. **Ausgabe und Fehlerfälle von `summary` testen**, Größe S
   - Ein Test prüft die Ausgabe `Summe: <Betrag>` zu bekannten Eingabedaten. Ein weiterer prüft den Fall unbekannter Befehl oder leere Daten.
   - Widerlegt, wenn: Die Tests bleiben grün, obwohl die Ausgabe falsch formatiert ist oder der Betrag fehlt.
   - Agent notes: `tests/test_cli.py`

Angelegt wird erst, wenn Linear wieder erreichbar ist und du ausdrücklich Ja zu Nummern aus dieser Liste sagst.

Nächster Schritt: Sobald Linear geht, `/slickfab:verify EX-995` erneut gegen die echte Spec laufen lassen. Danach die bestätigten Fix-Tickets anlegen und mit `/slickfab:implement <Fix-Ticket>` bauen.

SLICKFAB-STATUS: DONE_WITH_CONCERNS
