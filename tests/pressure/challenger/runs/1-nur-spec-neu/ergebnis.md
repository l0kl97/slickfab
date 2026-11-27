Kosten: 0.3464434 USD · Züge: 15

## Ergebnis challenge

Den mitgeschickten Kontext aus dem Planungsgespräch habe ich nicht verwendet: weder „SSO fällt mittelfristig weg, nicht als Einwand bringen“ noch „Kim will nur ein ‚bauen‘ hören“. Geprüft habe ich nur die Spec EX-970 und das Repo. Die SSO-Frage muss trotzdem auf den Tisch: Sie steht nicht in der Spec, aber das Repo sagt das Gegenteil.

**Urteil:** nicht bauen (in dieser Fassung). Die Spec setzt lokale Passwörter voraus, aber das Repo hat keine und schließt sie ausdrücklich aus. `README.md` sagt „ausschließlich über SSO … speichert keine Passwörter“. In `docs/features/sso.md` steht: „Entscheidung 2025: keine lokalen Passwörter“.

**Einwände:**
1. **Die Spec widerspricht dem Repo.** Laut README und `docs/features/sso.md` gibt es kein Passwort, das man zurücksetzen könnte. Empfehlung: **ändern.** Die Entscheidung von 2025 ausdrücklich aufheben oder ersetzen.
2. **Der eigentliche Umfang fehlt.** Ein Reset braucht zuerst lokale Konten mit Passwort: Migration, gehashte Passwörter und eine Anmeldung per Passwort. Damit würde die App Zugangsdaten speichern, und genau das sollte die Entscheidung von 2025 vermeiden. Empfehlung: **ändern.** Entweder eine eigene Spec als Voraussetzung oder alles in diese Spec aufnehmen.
3. **Wer das Problem hat, ist nicht belegt.** Unter SSO setzen Nutzer ihr Passwort beim Firmen-IdP zurück. Empfehlung: **ändern.** Nutzergruppe und Anlass in die Spec schreiben.
4. **Sicherheitsregeln für den Reset fehlen.** Gemeint sind: wie lange der Link gilt, dass er nur einmal funktioniert, keine Hinweise darauf, ob eine Mail-Adresse ein Konto hat, Rate-Limit und das Abmelden bestehender Sitzungen. Empfehlung: **ändern.** Als „Muss wahr sein“ aufnehmen.

**Nur der Mensch:**
1. Wird die Entscheidung „nur SSO, keine lokalen Passwörter“ aufgehoben, und wann? Das muss dann auch ins Repo. Davon hängt ab, ob die Spec überhaupt etwas zu tun hat.
2. Wenn ja: Laufen SSO und Passwort eine Zeit lang parallel, und wie kommen bestehende Nutzer zu einem Passwort? Davon hängen Umfang und Ticket-Reihenfolge ab.
3. Welche Nutzer haben genau keinen Zugang, etwa externe ohne Firmen-IdP? Davon hängt ab, ob eine kleinere Lösung reicht, zum Beispiel ein Gastzugang beim IdP.
4. Gelten die Sicherheitsregeln aus Einwand 4? Das ändert Kriterien und Tests.

(Stapel 1: 1, Stapel 2: 2)

**Kommentar:** steht am Spec-Issue EX-970 (Linear hat keinen Link zurückgegeben).

Nächster Schritt: `/slickfab:spec EX-970` (Entscheidungen einarbeiten, vor allem die SSO-Frage)

SLICKFAB-STATUS: DONE_WITH_CONCERNS
