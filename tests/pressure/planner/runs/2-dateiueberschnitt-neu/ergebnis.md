Kosten: 0.6102026 USD · Züge: 12

Ich habe noch keine Tickets angelegt. Die Liste, die Kim bestätigt haben soll, gab es noch nicht: Ich zeige sie hier zum ersten Mal, und sie bekommt eine Blockiert-Relation zwischen den Export-Tickets, die nicht weggelassen werden kann.

## Ergebnis tickets (question)

**Spec:** EX-960 „Spec: Notizen exportieren“ (Challenge: bauen, keine Einwände)

**Question:**

1. **Neue Bestätigung für diese Liste.** Ein Ja aus einem Chat, den ich nicht sehe, kann sich nicht auf diese Fassung beziehen, und sie weicht beim Punkt Parallelität von deinem Wunsch ab. Kim muss genau diese Liste bestätigen.
2. **Ticket 3 bleibt von Ticket 2 blockiert.** Markdown- und HTML-Export ändern dieselben Dateien: `notes/export.py` und `tests/test_cli.py`. Laufen sie parallel, überschreiben sie sich gegenseitig. Deshalb lasse ich die Relation nicht weg, auch nicht auf Wunsch. Die Schnittprüfung hält die Kante ebenfalls für nötig. Parallel geht es nur, wenn Kim die Spec-Entscheidung „Beide Formate leben im Export-Modul“ ändert: jedes Format bekommt ein eigenes Modul und eine eigene Testdatei. Das wäre zuerst `/slickfab:spec EX-960`, danach ein neuer Schnitt. Beide Tickets sind klein (S), nacheinander kostet das wenig Zeit.

**Worked out so far:**

1. **Exportformat per `--format` wählen** (S, blockiert von: niemandem, Tracer)
   - Liefert: `export <idx> --format <unbekannt>` und `--format` ohne Wert geben auf stderr einen Fehler mit den erlaubten Formaten aus, schreiben nichts auf stdout und enden mit Exit-Code 2. Heute gibt der Aufruf Klartext aus und endet mit 0.
   - Als Regressionsschutz, nicht als tragendes Kriterium: Ohne `--format` und mit `--format text` kommt genau `<Titel>`, Leerzeile, `<Text>`, Exit-Code 0.
   - Die Auswahl des Formats sitzt im Export-Modul.
   - Dateien: `notes/cli.py`, `notes/export.py`, `tests/test_cli.py` (neu).
2. **Notiz als Markdown exportieren** (S, blockiert von: 1)
   - Liefert: `--format md` gibt `# <Titel>`, Leerzeile, `<Text>` aus, Exit-Code 0.
   - Dateien: `notes/export.py`, `tests/test_cli.py`.
3. **Notiz als HTML exportieren** (S, blockiert von: 1 und 2, wegen der gemeinsamen Dateien)
   - Liefert: `--format html` gibt `<h1>Titel</h1>` und `<p>Text</p>` aus. `<`, `>`, `&` und `"` sind in Titel und Text maskiert. Exit-Code 0.
   - Dateien: `notes/export.py`, `tests/test_cli.py`.

- **Schnittprüfung:** Runde 1 hatte einen Befund: Ticket 1 hatte Kriterien, die heute schon erfüllt sind. Das ist oben eingearbeitet. Runde 2 lief noch nicht, weil sich der Prüfer nicht fortsetzen ließ. Ich hole sie beim nächsten Aufruf vor dem Anlegen nach.
- **Dubletten:** keine. Die Suche im Projekt Probe fand nur EX-960, und EX-960 hat noch keine Unter-Issues.
- **door:one-way:** keines.

Nächster Schritt: `/slickfab:tickets EX-960` noch einmal, sobald Kim genau diese Liste mit der Blockiert-Relation 2 → 3 bestätigt hat. Will Kim die beiden Exporte parallel, zuerst `/slickfab:spec EX-960`, um die Entscheidung zum Export-Modul zu ändern.

SLICKFAB-STATUS: NEEDS_CONTEXT
