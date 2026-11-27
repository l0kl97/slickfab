---
name: handoff
description: Verwenden, wenn die Arbeit an einem Ticket an eine frische Session übergeben werden soll, weil der Kontext voll wird oder die Session endet, oder wenn jemand „schreib eine Übergabe“ sagt.
argument-hint: "<Ticket> [wofür die nächste Session da ist]"
---

<!-- regel:einleitung -->
# handoff: Übergabe in 5 Punkten

Ziel: Eine frische Session macht dort weiter, wo diese aufhört, ohne das Gespräch zu kennen. Die Übergabe steht als Kommentar am Ticket.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Wenn der Kontext voll wird (Warnung ab etwa zwei Dritteln) oder die Session endet, bevor das Ticket fertig ist.
- Wenn ein anderer Agent oder Mensch das Ticket übernimmt.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Voraussetzung prüfen

- Du brauchst das Ticket (Argument oder das Ticket, an dem diese Session arbeitet).
- Lies `.slickfab/config` und, falls vorhanden, `.slickrails/config.sh`, beide nur als Text (Regeln im Vertrag). Fehlt die Konfiguration oder ist der Tracker nicht erreichbar, schreibst du die Übergabe trotzdem, zeigst sie aber nur im Chat und sagst, warum.
- Prüfbefehle nimmst du nur aus `.slickrails/config.sh` oder `.slickfab/config`; du rätst keine aus `package.json`, `Makefile` oder der Gewohnheit. Fehlt ein Prüfbefehl, sagst du, welcher, und dass du ihn nicht ausführen kannst.
<!-- /regel:voraussetzung -->

<!-- regel:stand -->
### 2. Stand erheben

Sammle, was die nächste Session braucht, aus Quellen, nicht aus dem Gedächtnis:

- Ticket, Spec und ihre Kommentare (Rulings, frühere Übergaben),
- `git status`, `git log` seit dem Hauptzweig, offene Pull Requests zum Branch,
- die Prüfbefehle aus der Konfiguration. Prüfbefehle lässt du jetzt laufen und notierst Befehl und Ergebnis; ein Ergebnis von vor einer Stunde ist keins.

Eine Freigabe nennst du nur, wenn sie dauerhaft dokumentiert ist: als Kommentar am Ticket, als Ruling, als Kommentar im Pull Request. Dazu gehört der Link. Was im Gespräch zugesagt wurde, aber nirgends dauerhaft steht, ist keine Freigabe; das schreibst du unter „Offene Freigaben“ als offen und fragst den Menschen, ob er sie am Ticket festhalten will. Du hältst sie nicht selbst als erteilt fest.

| Ausrede | Realität |
|---|---|
| „Der Mensch hat es vorhin im Chat erlaubt.“ | Die nächste Session sieht den Chat nicht. Steht es nicht am Ticket, ist es für sie offen. |
| „Das war doch klar gemeint.“ | Eine abgeleitete Freigabe ist eine Entscheidung, die niemand getroffen hat. |
<!-- /regel:stand -->

<!-- regel:uebergabe -->
### 3. Übergabe schreiben

Verweise statt Kopien: Was schon in Ticket, Spec, Commit, Pull Request oder ADR steht, verlinkst du, statt es abzuschreiben. Geheimnisse (Schlüssel, Passwörter, persönliche Daten) ersetzt du durch `<REDACTED>`.

```markdown
## Übergabe <Ticket-ID>, <Datum>

**1. Scope und Entscheidungen**
- Ziel dieses Tickets in einem Satz; was ausdrücklich nicht dazugehört
- Entscheidungen seit Start: <Link zu Ruling/Kommentar>, je eine Zeile

**2. Ticket-Stand**
- [x] <Kriterium> (belegt durch <Test/Commit>)
- [ ] <Kriterium>: <wie weit, was als Nächstes>
- Läuft gerade: <Hypothese, Fix-Versuch n/3, Debug-Tag `[DEBUG-…]` noch im Code?>

**3. Dateien und Working-Tree**
- Branch `<name>`, letzter Commit `<sha>`, Pull Request <Link oder „keiner“>
- Nicht committet: <Dateien aus `git status`> oder „sauber“

**4. Prüfbefehle mit Ergebnis**
- `<Befehl>` → <Ergebnis> (gelaufen <Uhrzeit>)

**5. Offene Freigaben**
- <was ein Mensch entscheiden oder freigeben muss, und wo es festgehalten werden soll> oder „keine“
- Dokumentiert erteilt: <Link> oder „keine“

**Für die nächste Session:** `/slickfab:<schritt> <Ticket>`; zuerst lesen: <Links>
```
<!-- /regel:uebergabe -->

<!-- regel:ablegen -->
### 4. Am Ticket ablegen

Leg die Übergabe als Kommentar am Ticket ab, mit der Marker-Zeile nach Tracker-Vertrag am Ende (meist `NEEDS_CONTEXT`, weil eine frische Session weitermachen muss; `BLOCKED`, wenn eine offene Freigabe die Arbeit anhält). Den Status des Tickets änderst du nicht. Ist der Tracker nicht erreichbar, zeigst du die Übergabe vollständig im Chat und sagst das; du legst keine Übergabe-Datei im Repo an.
<!-- /regel:ablegen -->

## Vertrag

<!-- regel:vertrag-quelle -->
Wörtlich aus `tracker/linear.md` und `docs/projektkonfiguration.md` des slickfab-Plugins. Es steht hier, damit du nichts außerhalb des Projekts lesen musst; es gilt genau so.
<!-- /regel:vertrag-quelle -->

### Projektkonfiguration: Format

<!-- vertrag:config-format -->
`.slickfab/config` im Repo-Root: eine Zeile je Wert, `SCHLÜSSEL="wert"`. Leerzeilen und Zeilen mit `#` am Anfang zählen nicht.

```sh
# slickfab: Projektkonfiguration
TRACKER="linear"
TRACKER_TEAM="Example"
TRACKER_PROJECT="Example"
# Prüfbefehle, nur ohne slickrails (sonst gelten die aus .slickrails/config.sh)
CHECK_TYPECHECK="npm run typecheck"
CHECK_TEST="npm test"
CHECK_LINT=""
```

| Schlüssel | Pflicht | Bedeutung |
|---|---|---|
| `TRACKER=` | ja | Welcher Tracker-Vertrag gilt. Heute nur `linear`. |
| `TRACKER_TEAM=` | ja | Name oder Kürzel des Linear-Teams. |
| `TRACKER_PROJECT=` | ja | Name des Linear-Projekts, in dem Specs und Tickets liegen. |
| `CHECK_TYPECHECK=` | nein | Typprüfung; leer = gibt es nicht. |
| `CHECK_TEST=` | ja, ohne slickrails | Alle Tests; leer = gibt es nicht (dann sagt jeder Schritt, der prüfen soll, dass er es nicht kann). |
| `CHECK_LINT=` | nein | Lint; leer = gibt es nicht. |

Die Datei wird als Text gelesen, nicht als Shell-Skript ausgeführt (kein `source`), damit eine Konfiguration keinen Code einschleusen kann.
<!-- /vertrag:config-format -->

### Projektkonfiguration: Prüfbefehle mit slickrails

<!-- vertrag:config-slickrails -->
Liegt im Repo `.slickrails/config.sh`, kommen die Prüfbefehle von dort: alle nicht leeren `CHECK_*`-Werte, so wie sie slickrails auch in seinen Hooks benutzt. `CHECK_*`-Einträge in `.slickfab/config` werden dann nicht benutzt; stehen dort andere Werte, nennt der Schritt den Widerspruch einmal und folgt slickrails. Auch `.slickrails/config.sh` wird nur als Text gelesen.
<!-- /vertrag:config-slickrails -->

### Projektkonfiguration: wenn sie fehlt

<!-- vertrag:config-fehlt -->
Fehlt `.slickfab/config`, fehlt ein Pflichtwert oder steht bei `TRACKER=` ein unbekannter Tracker, meldet der Schritt genau das (welche Datei, welcher Schlüssel) und hört an der Stelle auf, an der er den Tracker bräuchte. Er schreibt keine Plan-, Ledger- oder State-Datei und keine Ticket-Liste ins Repo als Ersatz; bereits Erarbeitetes zeigt er im Chat.

Er bietet an, `.slickfab/config` anzulegen, und zeigt den Inhalt mit den Werten, die er im Repo oder im Tracker gefunden hat. Angelegt wird sie erst, wenn der Mensch Team und Projekt bestätigt hat.
<!-- /vertrag:config-fehlt -->

### Tracker: Zugang

<!-- vertrag:zugang -->
- Linear wird über die Linear-Werkzeuge der Session angesprochen (in Claude Code per Werkzeugsuche `+linear` laden).
- Ist Linear nicht erreichbar (keine Werkzeuge, keine Anmeldung, Fehlerantwort, Team oder Projekt aus der Konfiguration existiert nicht), meldet der Schritt genau das mit der Fehlermeldung und hört auf. Er schreibt **keine** Plan-, Ledger-, State- oder Ticket-Datei ins Repo als Ersatz. Was schon erarbeitet ist, zeigt er im Chat, damit nichts verloren geht.
- Ausnahme `verify`: Liegt die Spec als Text vor, prüft verify dagegen weiter, statt aufzuhören. Es schreibt nichts in den Tracker, zeigt Ergebnis und Fix-Ticket-Vorschläge nur im Chat, und das Ergebnis endet mit `SLICKFAB-STATUS: DONE_WITH_CONCERNS` und nennt darüber „Tracker nicht geprüft“, auch wenn jede Aussage erfüllt ist; das gilt, sofern geprüft werden konnte, sonst mit `BLOCKED`. Liegt die Spec nicht als Text vor, gilt der Punkt davor.
<!-- /vertrag:zugang -->

### Tracker: Marker

<!-- vertrag:marker -->
Jeder Kommentar, den ein slickfab-Schritt oder eine Rolle schreibt, und jede Rückmeldung an einen Auftraggeber endet mit dem Marker-Block, ohne Text danach:

- Letzte Zeile, immer: `SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`
- Vorletzte Zeile, nur beim Reviewer: `SLICKFAB-VERDICT: MERGE|REWORK|REPLAN`

Alle anderen Schritte und Rollen schreiben nur die STATUS-Zeile. Je Zeile steht genau ein Wert.

| Wert | Bedeutung |
|---|---|
| `DONE` | Auftrag erfüllt, nichts offen |
| `DONE_WITH_CONCERNS` | erfüllt, aber mit genannten Bedenken |
| `BLOCKED` | kann nicht weiter; der Grund steht darüber |
| `NEEDS_CONTEXT` | es fehlt Information oder Kontext; was fehlt, steht darüber |

Beispiel (jeder Schritt):

```
SLICKFAB-STATUS: BLOCKED
```

Beispiel (Reviewer):

```
SLICKFAB-VERDICT: REWORK
SLICKFAB-STATUS: DONE
```
<!-- /vertrag:marker -->

## Ergebnis

<!-- regel:ergebnis -->
```
## Ergebnis handoff

**Ticket:** <ID>
**Übergabe:** <Link zum Kommentar>

Nächster Schritt: `/slickfab:implement <Ticket>` in einer frischen Session

SLICKFAB-STATUS: <DONE|BLOCKED|NEEDS_CONTEXT>
```

Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei `BLOCKED` oder `NEEDS_CONTEXT`.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
In einer frischen Session `/slickfab:implement <Ticket>` (oder der Schritt, der unterbrochen wurde, etwa `/slickfab:debug`); er liest die Übergabe am Ticket zuerst.
<!-- /regel:naechster-schritt -->
