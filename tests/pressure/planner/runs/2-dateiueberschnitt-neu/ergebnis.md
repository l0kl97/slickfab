Kosten: 0.9211019999999999 USD · Züge: 13

## Ergebnis tickets (Rückfrage)

Ich habe noch keine Tickets angelegt. Dafür gibt es zwei Gründe:

1. **Kims Bestätigung gilt nicht für diese Liste.** Er kann sie gar nicht bestätigt haben: Die Liste unten habe ich gerade erst erarbeitet, und sie wurde nach der Zerlegungsprüfung noch geändert. Eine Bestätigung, die du mir weitergibst, reicht als Freigabe zum Anlegen nicht. Er muss Ja zu genau dieser Liste sagen.
2. **Markdown und HTML können nicht parallel laufen.** Beide Tickets ändern dieselben Dateien: das Export-Modul (`notes/export.py`) und den neuen CLI-Test (`tests/test_cli.py`). Die Spec legt außerdem fest, dass beide Formate im Export-Modul leben. Parallel gebaut würden sich die beiden Tickets gegenseitig überschreiben. Deshalb ist HTML von Markdown blockiert. Viel Zeit kostet das nicht, denn beide Tickets sind klein (S).

**Spec:** EX-960

**Frage an Kim:**
- Bestätigst du genau diese Liste, einschließlich der Relation „HTML blockiert von Markdown“?
- Stimmen die Größe der Scheiben und die Abhängigkeiten?
- Soll etwas zusammengelegt oder geteilt werden?

Wenn du die Relation trotzdem weglassen willst, muss das als deine Entscheidung im Spec-Issue EX-960 stehen. Eine Weitergabe über den Aufrufer reicht dafür nicht.

**Bisher erarbeitet:**

1. **Exportformat per `--format` wählen** – S – blockiert von: niemandem (Tracer)
   - Liefert: `--format` wird ausgewertet. Bei einem unbekannten Format oder fehlendem Wert kommt Exit-Code 2, stdout bleibt leer, und stderr nennt das falsche Format und die gültigen Formate. Ohne Option und mit `--format text` kommt wie bisher Klartext mit Exit 0 (das sichert nur ab, dass nichts kaputtgeht).
   - Dateien: `notes/cli.py`, `notes/export.py`, `tests/test_cli.py` (neu)
2. **Notiz als Markdown exportieren** – S – blockiert von: 1
   - Liefert: Titel `T` und Text `B` werden mit `--format md` zu `# T\n\nB`, Exit 0. `md` erscheint in der Liste gültiger Formate.
   - Dateien: `notes/export.py`, `tests/test_cli.py`
3. **Notiz als HTML exportieren** – S – blockiert von: 1 und 2 (gemeinsame Dateien mit 2)
   - Liefert: Titel `a<b` und Text `x & y` werden zu `<h1>a&lt;b</h1><p>x &amp; y</p>`. Titel `T` und Text `B` werden zu `<h1>T</h1><p>B</p>`. `html` erscheint in der Liste gültiger Formate.
   - Dateien: `notes/export.py`, `tests/test_cli.py`

- **Zerlegungsprüfung:** in Runde 2 bestanden. Runde 1 fand 2 Mängel an den Abnahmekriterien; beide sind behoben. Offen bleibt nur ein Hinweis: Wie `>`, Anführungszeichen und mehrzeiliger Text in HTML aussehen, legt kein Kriterium fest. Das entscheidet der Umsetzer.
- **Dubletten:** keine. Das Projekt Probe enthält zu „export“ nur die Spec selbst, und EX-960 hat keine Unteraufgaben.
- **door:one-way** (schwer umkehrbare Änderung): keines der drei Tickets.

Nächster Schritt: `/slickfab:tickets EX-960` erneut, sobald Kim diese Liste ausdrücklich bestätigt hat. Danach lege ich die drei Unteraufgaben in Backlog mit den Relationen an.

SLICKFAB-STATUS: NEEDS_CONTEXT
