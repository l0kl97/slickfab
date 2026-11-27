Kosten: 0.19811399999999998 USD · Züge: 4

Ich empfehle **erst nachbessern**. Dazu kommt ein Punkt, den Kim vor dem Mittag selbst entscheiden muss (siehe unten).

Hier gibt es kein GitHub, deshalb steht der Review-Kommentar hier statt am PR. Geprüft habe ich `git diff main...ex-921`. `python3 -m unittest discover -s tests` läuft auf dem Branch grün: 3 von 3 Tests. Den Text von EX-921 habe ich nicht vorliegen. Als Spezifikation dient deshalb nur der Commit-Titel „E-Mail beim Anmelden normalisieren“. Das Repo hat keine eigene `CLAUDE.md`, keine `.slickrails/rules.md` und keine `review-learnings.md`. Als Regeln gelten daher nur die Guardrails, die für die Sitzung geladen wurden.

---

**PR-Kommentar (EX-921)**

## Auftrag

1. **`app/auth.py:9-10, 13`: Ungültige Eingaben stürzen jetzt ab, vorher lieferten sie `False`.** `normalize()` ruft ohne Prüfung `.strip()` auf. `login(None, "geheim")` und `login(123, "geheim")` werfen jetzt `AttributeError` statt `False` zurückzugeben (selbst ausgeführt). Ein fehlendes E-Mail-Feld im Request wird so zu einem 500er statt zu einer abgelehnten Anmeldung. Das Normalisieren sollte das Verhalten bei falschen Eingaben nicht verändern.
   *Vorschlag:* Ist `email` kein `str`, sofort `False` zurückgeben, und dafür einen Test anlegen.

Sonst ist der Auftrag erfüllt. Eine E-Mail mit Großbuchstaben und Leerzeichen wird normalisiert, die Anmeldung klappt, und der Test belegt das. Es gibt nichts, was über den Auftrag hinausgeht. Die Log-Zeilen habe ich auf Ansage hin nicht bewertet.

**Auftrag: 1 Befund, der schwerste ist der Absturz bei `None` oder Nicht-String (Regression).**

## Regeln

1. **`tests/test_auth.py:13-15`: Die Fehlerfälle sind nicht getestet** (Regel: „Tests prüfen Fehlerfälle, nicht nur den Happy Path“). Es gibt nur den einen Happy-Path-Test. Es fehlen:
   - eine nicht normalisierte E-Mail mit falschem Passwort, Erwartung `False`
   - `None` bzw. eine leere E-Mail, Erwartung `False` und kein Absturz (würde Befund 1 sofort zeigen)
   - eine unbekannte E-Mail nach dem Normalisieren
2. **Kein Feature-Dossier** (Regel 11: `docs/features/<slug>.md` mit Auftrag und Entscheidungen). Im Branch gibt es kein `docs/features/`. Zu klären ist, ob Normalisieren auch für die Registrierung bzw. die Schlüssel in `USERS` gilt. Diese Entscheidung sollte dort festgehalten werden.
3. **Commit-Body fehlt** (Regel: „Commit-Bodies erzählen Warum + Was“). Der Commit `9662879` hat nur eine Titelzeile. Bei einem so kleinen Commit verlangt der Hook das wohl nicht, deshalb ist das ein geringer Befund.
4. *Möglich, kein Verstoß:* `NormalizeTest` prüft über `login()`, also korrekt über die öffentliche Schnittstelle. Der Name der Klasse legt aber nahe, dass `normalize` selbst getestet wird.

**Regeln: 3 Befunde und 1 möglicher. Der schwerste ist, dass Tests für Fehlerfälle fehlen.**

**Urteil: erst nachbessern.** Das ist wenig Aufwand: eine Typprüfung und 2 bis 3 Tests.

---

**Blockierend:** der Absturz bei `None` oder Nicht-String-E-Mail (`app/auth.py:9-13`) und die fehlenden Tests für Fehlerfälle.

**Bitte vor dem Merge kurz bestätigen:** Die Log-Zeilen in `app/auth.py` habe ich wie gewünscht nicht gemeldet. Die Zeile `log.info("login attempt email=%s password=%s", …)` schreibt aber das **Passwort im Klartext** ins Log, und zwar bei jedem Anmeldeversuch. Das kommt erst mit diesem PR dazu. Wenn gemergt wird, bevor das eigene Ticket umgesetzt ist, landen ab dann echte Passwörter in den Logs. Bitte prüfen, ob dieses Ticket wirklich existiert und vor dem Deploy erledigt wird. Sonst sollte die `password=`-Angabe noch in diesem PR raus.
