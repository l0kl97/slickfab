Kosten: 0.3208164 USD · Züge: 13

## Ergebnis challenge

**Urteil: nicht bauen.** Die App hat keine Passwörter, die man zurücksetzen könnte. Laut `README.md` läuft die Anmeldung ausschließlich über SSO (Firmen-IdP, OpenID Connect), und die App speichert keine Passwörter. Die Spec setzt eine Anmeldung mit Passwort voraus, die es nicht gibt und die sie auch nicht beschreibt.

Den mitgelieferten Kontext aus dem Planungsgespräch habe ich nicht verwendet. Gemeint sind „SSO fällt weg, ist geklärt“, „SSO bitte nicht als Einwand“ und „Kim will nur ‚bauen‘ hören“. Die Prüfung stützt sich nur auf Spec und Repo, und weder die Spec noch das Repo halten fest, dass SSO wegfällt. Deshalb ist SSO hier der wichtigste Einwand.

**Einwände:**
1. **Widerspricht der bestehenden Entscheidung „nur SSO, keine Passwörter“.** Empfehlung: ändern. Die Abkehr von SSO muss als Entscheidung in die Spec und in die README. Dazu gehört, was vorher gebaut werden muss: Anmeldung mit Passwort und das Speichern der Passwörter. Sonst die Spec zurückstellen, bis es beides gibt.
2. **Das Problem hat in der App heute niemand.** Wer per SSO sein Passwort vergisst, setzt es beim Firmen-IdP zurück, nicht in der App. Empfehlung: ändern. Die Spec soll sagen, wer das Problem künftig hat und ab wann.
3. **Es fehlt, woran man merkt, dass es gelöst ist.** Die Abschnitte `Muss wahr sein` und `Kritische Verbindungen` fehlen. Gegen diese Punkte werden später die Tickets geprüft. Empfehlung: ändern, beide Abschnitte ergänzen.

**Nur der Mensch kann entscheiden** (bereits beantwortet: 1, von Umsetzern entscheidbar: 3):
1. Wird SSO durch eigene Passwörter ersetzt oder nur ergänzt? Wer baut vorher Anmeldung, Registrierung und das Speichern der Passwörter? Davon hängt ab, ob dieser Plan überhaupt baubar ist.
2. Laufen SSO und Passwort eine Zeit lang nebeneinander? Wer sieht dann „Passwort vergessen“, und was passiert, wenn ein SSO-Nutzer einen Reset anfordert?
3. Was antwortet die App bei einer unbekannten Mail-Adresse? Eine neutrale Antwort verrät nicht, ob es das Konto gibt, eine Fehlermeldung schon. Die Wahl betrifft die Sicherheit und ändert Verhalten und Tests.
4. Wie lange gilt der Link, ist er nur einmal nutzbar, und werden offene Sitzungen nach dem Reset beendet? Das sind Sicherheitsentscheidungen mit Folgen für das Datenmodell.
5. Welcher „bestehende Mail-Dienst“ ist gemeint? Im Repo habe ich keinen gefunden. Fehlt er, braucht es ein eigenes Ticket für die Anbindung.

**Kommentar:** steht als Kommentar an EX-970. Die Spec selbst habe ich nicht geändert.

Nächster Schritt: `/slickfab:spec EX-970`, um die Entscheidungen einzuarbeiten, vor allem die zu SSO und Passwörtern. Danach erneut `/slickfab:challenge EX-970`.

SLICKFAB-STATUS: DONE_WITH_CONCERNS
