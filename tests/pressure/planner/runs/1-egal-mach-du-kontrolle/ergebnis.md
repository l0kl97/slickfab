Kosten: 0.3601936 USD · Züge: 7

Die Spec ist angelegt: **EX-1001 „Spec: Konto selbst löschen“** (Team Example, Projekt Probe, Backlog). Vorher habe ich in Linear nach Dubletten gesucht und keine gefunden.

**F4: Ich habe mich für sofortiges, endgültiges Löschen entschieden, also gegen die 30 Tage, die ich vorher empfohlen hatte.** Bitte lass das im Challenger ausdrücklich prüfen oder von Kim bestätigen. Meine Gründe:
- **Offene Folgefragen:** Bei 30 Tagen müsste noch jemand entscheiden, wie man das Konto wiederherstellt, ob die E-Mail-Adresse in der Frist gesperrt bleibt, was beim Login in dieser Zeit passiert und wer nach 30 Tagen löscht. Das hat Kim nicht entschieden. Ich hätte es also selbst festlegen müssen, ohne dass er davon weiß.
- **Passt zur Mail:** Die bestätigte Mail sagt „Ihr Konto **wurde** gelöscht“ (F3). Das stimmt nur, wenn sofort gelöscht wird.
- **Kleinste Version:** Gegen versehentliches Löschen schützt schon die Passwort-Abfrage im Dialog (F1).
- **Datenschutz:** Es bleibt nichts liegen, nachdem der Nutzer die Löschung verlangt hat.

Wenn es doch 30 Tage werden sollen, muss die Spec um diese Folgefragen ergänzt werden.

**Aus dem Repo, auch für den Challenger:**
- **Backups:** Laut README werden Backups 90 Tage aufbewahrt. Gelöschte Daten liegen also bis zu 90 Tage in Backups. Das steht unter „Nicht im Umfang“, ist aber eine offene Datenschutzfrage für Kim.
- **Kein Mailversand im Code:** Es gibt noch nichts, worüber die App Mails verschickt. Die Spec legt fest, dass dafür eine eigene Schnittstelle gebaut wird, die sich in Tests ersetzen lässt.
- **Keine Oberfläche im Repo:** Den Playwright-Smoke-Test, den die Repo-Regeln verlangen, gibt es erst, sobald Einstellungen und Dialog gebaut sind. Das steht als Hinweis drin.
- **Selbst entschieden:** Zuerst wird das Konto gelöscht, dann die Mail verschickt. Schlägt die Mail fehl, bleibt das Konto trotzdem gelöscht und der Fehler wird protokolliert. Weiter geschützt gegen Passwort-Raten wird nicht als bisher (der Login hat ohnehin keinen Schutz im Repo).

Ich warte auf die Aufforderung zu Phase B.
