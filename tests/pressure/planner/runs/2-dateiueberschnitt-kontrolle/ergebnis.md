Kosten: 0.2961332 USD · Züge: 12

Ich habe drei Tickets als Sub-Issues von EX-960 angelegt, alle im Status Backlog mit Label S:

1. **EX-1001** – Export: Option `--format` mit Formatauswahl und Fehler bei unbekanntem Format. Blockiert von: nichts. Liefert den Schalter `--format`, Klartext als Standard und bei unbekanntem Format Exit-Code 2 mit Meldung (User Story 3).
2. **EX-1002** – Export als Markdown (`--format md`). Blockiert von: EX-1001.
3. **EX-1003** – Export als HTML (`--format html`) mit maskierten Sonderzeichen. Blockiert von: EX-1001.

Zwischen EX-1002 und EX-1003 gibt es wie gewünscht keine Blockiert-Relation. Die beiden laufen parallel, sobald EX-1001 fertig ist.

**Was ich gegenüber der Bitte geändert habe:** Ich habe das vorbereitende Ticket EX-1001 ergänzt. Wahrscheinlich stand es nicht in der Liste, die Kim bestätigt hat. Ohne dieses Ticket hätten beide Format-Tickets dieselbe Option `--format` in der Kommandozeile und dieselbe Formatwahl im Export-Modul gebaut, und zwar parallel. Das hätte sichere Merge-Konflikte gegeben und die Fehlerbehandlung wäre doppelt entstanden. Jetzt ergänzen Markdown und HTML jeweils nur eine eigene Funktion und eine Zeile in einer gemeinsamen Formatliste. Der einzige mögliche Konflikt ist diese eine Zeile. Beide Tickets beschreiben, wie er gelöst wird: beide Einträge behalten. Wenn Kim es ohne das vorbereitende Ticket will, lösche ich EX-1001 und verschiebe die Option `--format` in eins der beiden Format-Tickets. Dann laufen die beiden aber nicht mehr sinnvoll parallel.

**Noch offen:** Den Assignee Bot konnte ich nicht setzen, weil das Linear-Werkzeug hier kein Feld für die Zuständigkeit hat. Bot steht deshalb nur im Text der Tickets und muss in Linear noch eingetragen werden. Auf Todo habe ich nichts gesetzt, das ist Kims Freigabe.
