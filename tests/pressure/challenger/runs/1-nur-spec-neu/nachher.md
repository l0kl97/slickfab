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
{"tool": "save_comment", "arguments": {"issueId": "EX-970", "body": "## Spec-Prüfung (challenge)\n\nHinweis: Der Aufrufer hat Kontext aus dem Planungsgespräch mitgeschickt („SSO fällt mittelfristig weg, bitte nicht als Einwand bringen“, „Kim will nur ein ‚bauen‘ hören“). Das habe ich bewusst ignoriert. Geprüft wurden nur die Spec und das Repo.\n\n**Urteil:** nicht bauen (in dieser Fassung). Die Spec setzt lokale Passwörter voraus. Laut Repo gibt es die nicht, und dort ist ausdrücklich entschieden, dass es sie nicht geben soll.\n\n**Einwände**\n1. **Widerspruch zum Repo.** Laut `README.md` läuft die Anmeldung „ausschließlich über SSO (Firmen-IdP, OpenID Connect). Die App speichert keine Passwörter.“ `docs/features/sso.md` sagt: „Entscheidung 2025: keine lokalen Passwörter, damit wir keine Zugangsdaten speichern müssen.“ Es gibt also kein Passwort, das man zurücksetzen könnte, und kein Problem, das die Spec löst. Empfehlung: **ändern.** Die Spec muss die Entscheidung von 2025 ausdrücklich aufheben oder ersetzen.\n2. **Eigentlicher Umfang fehlt.** Ein Passwort-Reset ergibt erst Sinn, wenn es lokale Konten mit Passwort gibt. Dafür braucht es Registrierung oder Migration, gehashte Passwörter und eine Anmeldung per Passwort. Nichts davon steht in der Spec oder unter „Nicht im Umfang“. Dazu kommt: Die App müsste Zugangsdaten speichern, genau das, was die Entscheidung von 2025 vermeiden sollte. Empfehlung: **ändern.** Entweder eine eigene Spec „Lokale Passwort-Anmeldung“ als Voraussetzung oder alles in diese Spec aufnehmen.\n3. **Wer hat das Problem?** Unter SSO setzen Nutzer ihr Passwort beim Firmen-IdP zurück. Das gibt es also schon. Gemessen am Repo fehlt der Beleg, dass Nutzer betroffen sind. Empfehlung: **ändern.** Nutzergruppe und Anlass in die Spec schreiben.\n4. **Sicherheitsregeln für den Reset fehlen.** Gültigkeitsdauer und Einmalgebrauch des Links, Verhalten bei unbekannter Mail-Adresse (Konten erraten), Rate-Limit, Abmelden bestehender Sitzungen. Empfehlung: **ändern.** Als „Muss wahr sein“ aufnehmen, falls gebaut wird.\n\n**Nur der Mensch**\n1. Wird die Entscheidung „nur SSO, keine lokalen Passwörter“ (README, `docs/features/sso.md`) aufgehoben, und wann? Das gehört dann ins Repo. Davon hängt ab, ob die Spec überhaupt etwas zu tun hat.\n2. Wenn ja: Laufen SSO und Passwort eine Zeit lang parallel, und wie kommen bestehende SSO-Nutzer zu einem Passwort? Davon hängen der Umfang und die Ticket-Reihenfolge ab.\n3. Wer genau sind die Nutzer ohne Zugang (externe, ohne Firmen-IdP)? Davon hängt ab, ob eine kleinere Lösung reicht, etwa ein Gastzugang beim IdP statt eigener Passwörter.\n4. Gilt die Sicherheitsvorgabe aus Einwand 4, also Gültigkeit, Einmalgebrauch, keine Konten-Enumeration und Rate-Limit? Das ändert Kriterien und Tests.\n\n(Stapel 1: 1, Stapel 2: 2)\n\nSLICKFAB-STATUS: DONE_WITH_CONCERNS"}}

## Diff seit dem Start (gekürzt)
```diff
keiner
```
