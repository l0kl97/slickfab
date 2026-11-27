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
{"tool": "save_comment", "arguments": {"issueId": "EX-970", "body": "## Produkt-Challenge zu EX-970 (Passwort zurücksetzen)\n\nVorab: Dass SSO mittelfristig wegfällt, stelle ich nicht in Frage. Die Einwände unten beziehen sich darauf, was die Spec voraussetzt, ohne es zu nennen.\n\n**1. Die App hat heute keine Passwörter, die man zurücksetzen könnte.** `app/login.py`, `README.md` und `docs/features/sso.md` bestätigen: Es gibt keine lokalen Passwörter, keine Registrierung und keine Passwort-Anmeldung. Die Spec setzt einen Passwort-Login voraus, den es nicht gibt und der auch nirgends spezifiziert ist.\n→ **Ändern:** Zuerst eine eigene Spec für „Anmeldung mit E-Mail + Passwort“ schreiben (Speicherung, Login, Sperre). Diese Spec bekommt eine ausdrückliche Abhängigkeit darauf.\n\n**2. Den Nutzer aus der Problembeschreibung gibt es heute nicht.** „Nutzer, die ihr Passwort vergessen haben“ kann es erst geben, wenn Passwörter existieren. Woran wir merken, dass das Problem gelöst ist, steht nirgends.\n→ **Ändern:** Die Zielgruppe nennen (bestehende SSO-Nutzer nach der Umstellung? neue Nutzer?) und ein Erfolgskriterium festlegen, z. B. „Support-Anfragen zum Zugang < X/Monat“ oder „Anteil abgeschlossener Resets“.\n\n**3. Der eigentlich erste Bedarf ist „Passwort erstmals setzen“, nicht „zurücksetzen“.** Wenn SSO wegfällt, haben alle bestehenden Nutzer kein Passwort. Ohne einen Weg, eins zu setzen, kommt niemand mehr rein. Der Mail-Link-Mechanismus ist dafür derselbe.\n→ **Ändern:** Die Spec auf „Passwort per Mail-Link setzen“ umschneiden: Einladung bzw. Umstellung zuerst, Reset fällt fast gratis mit ab. Eine Funktion, zwei Einstiege.\n\n**4. Die Entscheidung von 2025 („keine Zugangsdaten speichern“, Sicherheitsvorgabe) wird stillschweigend umgekehrt.** Steht das nicht dokumentiert, fällt es jedem späteren Review und Hook als Widerspruch auf. Außerdem ist offen, wer künftig die Verantwortung für gespeicherte Passwort-Hashes trägt.\n→ **Ändern:** Unter „Entscheidungen“ einen Satz ergänzen: wer die Vorgabe von 2025 ablöst und warum. `docs/features/sso.md` beim Bauen nachziehen.\n\n**5. Die wackligste Annahme ist „Mail über den bestehenden Mail-Dienst“.** Im Repo gibt es keinen Mail-Versand. Fehlt der Dienst oder darf er keine Transaktionsmails schicken (Zustellbarkeit, Absender, Spam), ist das Feature tot oder deutlich größer.\n→ **Ändern:** Den konkreten Dienst benennen und vor dem Bau prüfen, ob er zuverlässig zustellt.\n\n**6. Das Verhalten in Fehlerfällen fehlt in den User Stories.** Offen ist, was Nutzer sehen bei einer unbekannten Mail-Adresse (ohne dabei preiszugeben, ob es ein Konto gibt), bei einem abgelaufenen oder schon benutzten Link und bei mehrfacher Anforderung. „Tests: zwei Routen“ deckt das nicht ab.\n→ **Ändern:** Die Fehlerfälle als Akzeptanzkriterien aufnehmen, Gültigkeitsdauer des Links festlegen und vor dem Merge `/security-review` einplanen.\n\n**Gesamturteil: in dieser Form nicht bauen.** Der tragende Grund: Ein Passwort-Reset ohne Passwort-System hat keinen Nutzer und nichts, worauf er aufsetzen könnte. Den Mail-Link-Kern als „Passwort setzen“ zu bauen, nachdem eine Passwort-Login-Spec steht, halte ich für richtig."}}

## Diff seit dem Start (gekürzt)
```diff
keiner
```
