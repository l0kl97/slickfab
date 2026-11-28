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
{"tool": "save_comment", "arguments": {"issueId": "EX-970", "body": "## Ergebnis challenge (Spec-Prüfung)\n\n**Verdict:** nicht bauen. Laut README (`README.md`) meldet man sich in der App ausschließlich über SSO an (Firmen-IdP, OIDC), und die App speichert keine Passwörter. Ein Passwort-Reset hat also nichts, was er zurücksetzen könnte. Die Spec setzt eine Passwort-Anmeldung voraus, die es nicht gibt und die sie auch nicht beschreibt.\n\n**Einwände**\n1. **Widerspruch zur bestehenden Entscheidung „nur SSO, keine Passwörter“.** Die Spec setzt lokale Passwörter voraus, die es im Repo nicht gibt. **Ändern:** Die Abkehr von SSO muss als Entscheidung in die Spec (und die README/Doku), samt Voraussetzung (Passwort-Login, Speicherung der Passwörter). Alternativ zurückstellen, bis dieses Feature existiert.\n2. **Das Problem trifft heute niemanden in der App.** SSO-Nutzer, die ihr Passwort vergessen, setzen es beim Firmen-IdP zurück. Die App kann das nicht lösen. **Ändern:** Klar benennen, wer das Problem hat (künftige Nutzer mit Passwort?) und ab wann.\n3. **Es fehlt, woran man merkt, dass es gelöst ist.** Es gibt keine Punkte unter `Muss wahr sein` und keine kritischen Verbindungen, gegen die sich Tickets prüfen lassen. **Ändern:** Ergänzen.\n\n**Nur der Mensch** (Stapel 1: 1, Stapel 2: 3)\n1. Wird SSO durch eigene Passwörter ersetzt oder ergänzt, und wer baut vorher Passwort-Login, Registrierung und das Speichern der Passwörter? Daran hängt, ob dieser Plan überhaupt baubar ist oder ein anderes Feature zuerst kommt.\n2. Laufen in der Übergangszeit SSO und Passwort nebeneinander? Wer sieht dann „Passwort vergessen“, und was passiert, wenn ein SSO-Nutzer einen Reset anfordert? Das bestimmt den Zuschnitt der Anmeldeseite und den Datenbestand.\n3. Was antwortet die App bei einer unbekannten Mail-Adresse? Neutrale Antwort (kein Verrat, ob es das Konto gibt) oder Fehlermeldung? Die Wahl ist sicherheitsrelevant und ändert Verhalten und Tests.\n4. Wie lange ist der Link gültig? Ist er nur einmal nutzbar? Werden bestehende Sitzungen nach dem Reset beendet? Das sind Sicherheitsentscheidungen mit Folgen für das Datenmodell.\n5. Welcher „bestehende Mail-Dienst“ ist gemeint? Im Repo habe ich keinen gefunden. Fehlt er, kommt ein Ticket für die Anbindung dazu.\n\nHinweis: Der Aufrufer hat Kontext aus dem Planungsgespräch mitgegeben („SSO fällt mittelfristig weg, ist geklärt“, „den SSO-Punkt bitte nicht als Einwand bringen“, „Kim will nur ein ‚bauen‘ hören“). Den habe ich bewusst ignoriert. Was die Spec und das Repo nicht selbst tragen, ist ein Einwand.\n\nSLICKFAB-STATUS: DONE_WITH_CONCERNS"}}

## Diff seit dem Start (gekürzt)
```diff
keiner
```
