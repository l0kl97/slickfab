Kosten: 0.2451694 USD · Züge: 8

**Gesamturteil: in dieser Form nicht bauen.** Ein Passwort-Reset ohne Passwort-System hat keinen Nutzer und nichts, worauf er aufsetzen könnte. Ich weiß, dass Kim heute ein „bauen“ hören wollte, aber das kann ich ehrlich nicht geben. Den SSO-Punkt habe ich nicht als Einwand gebracht. Der Kern lässt sich retten: Der Mail-Link wird zu „Passwort setzen“, sobald es eine Spec für die Anmeldung mit Passwort gibt.

Der Kommentar mit 6 Einwänden steht an EX-970. Die drei wichtigsten:

1. **Es gibt keine Passwörter zum Zurücksetzen.** `app/login.py`, `README.md` und `docs/features/sso.md` zeigen: keine lokalen Passwörter, keine Registrierung, kein Passwort-Login. Die Spec setzt das stillschweigend voraus. → Zuerst eine eigene Spec für die Anmeldung mit E-Mail und Passwort schreiben und EX-970 davon abhängig machen.
2. **Der erste Bedarf ist „Passwort erstmals setzen“, nicht „zurücksetzen“.** Fällt SSO weg, hat kein bestehender Nutzer ein Passwort und niemand kommt mehr rein. Der Mail-Link funktioniert für beides gleich. → Die Spec auf „Passwort per Mail-Link setzen“ umschneiden, der Reset fällt dann fast nebenbei ab.
3. **Der Nutzer aus der Problembeschreibung existiert heute nicht, und es fehlt ein Erfolgskriterium.** → Festlegen, für wen das Feature ist, und eine Messgröße ergänzen, z. B. Support-Anfragen zum Zugang oder der Anteil abgeschlossener Resets.

Die weiteren drei Einwände im Kommentar: Die Spec kippt die Sicherheitsvorgabe von 2025 („keine Zugangsdaten speichern“), ohne das als Entscheidung festzuhalten. Den „bestehenden Mail-Dienst“ gibt es im Repo nicht. Und es fehlen die Fehlerfälle: unbekannte Mail-Adresse, abgelaufener Link, Link schon benutzt.
