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
`.slickfab/config` in the repo root: one line per value, `KEY="value"`. Blank lines and lines starting with `#` do not count.

```sh
# slickfab: project configuration
TRACKER="linear"
TRACKER_TEAM="Example"
TRACKER_PROJECT="Example"
# Check commands, only without slickrails (otherwise the ones from .slickrails/config.sh apply)
CHECK_TYPECHECK="npm run typecheck"
CHECK_TEST="npm test"
CHECK_LINT=""
```

| Key | Required | Meaning |
|---|---|---|
| `TRACKER=` | yes | Which tracker contract applies. Currently only `linear`. |
| `TRACKER_TEAM=` | yes | Name or key of the Linear team. |
| `TRACKER_PROJECT=` | yes | Name of the Linear project that holds specs and tickets. |
| `CHECK_TYPECHECK=` | no | Type check; empty = does not exist. |
| `CHECK_TEST=` | yes, without slickrails | All tests; empty = does not exist (then every step that is supposed to check says that it cannot). |
| `CHECK_LINT=` | no | Lint; empty = does not exist. |

The file is read as text, not executed as a shell script (no `source`), so that a configuration cannot inject code.

Answer in the user's language.
<!-- /vertrag:config-format -->

### Projektkonfiguration: Prüfbefehle mit slickrails

<!-- vertrag:config-slickrails -->
If the repo has `.slickrails/config.sh`, the check commands come from there: all non-empty `CHECK_*` values, the same way slickrails uses them in its hooks. `CHECK_*` entries in `.slickfab/config` are then not used; if they hold different values, the step names the contradiction once and follows slickrails. `.slickrails/config.sh` is also read only as text.

Answer in the user's language.
<!-- /vertrag:config-slickrails -->

### Projektkonfiguration: wenn sie fehlt

<!-- vertrag:config-fehlt -->
If `.slickfab/config` is missing, a required value is missing, or `TRACKER=` names an unknown tracker, the step reports exactly that (which file, which key) and stops at the point where it would need the tracker. It writes no plan, ledger or state file and no ticket list into the repo as a substitute; whatever it has already worked out, it shows in the chat.

It offers to create `.slickfab/config` and shows the content with the values it found in the repo or in the tracker. The file is created only once the human has confirmed team and project.

Answer in the user's language.
<!-- /vertrag:config-fehlt -->

### Tracker: Zugang

<!-- vertrag:zugang -->
- Linear is accessed through the session's Linear tools (in Claude Code, load them via tool search `+linear`).
- If Linear is unreachable (no tools, not logged in, error response, team or project from the configuration does not exist), the step reports exactly that, with the error message, and stops. It writes **no** plan, ledger, state or ticket file into the repo as a substitute. Whatever has already been worked out, it shows in the chat, so that nothing is lost.
- Exception `verify`: If the spec is available as text, verify keeps checking against it instead of stopping. It writes nothing to the tracker, shows the result and fix-ticket proposals only in the chat, and the result ends with `SLICKFAB-STATUS: DONE_WITH_CONCERNS` and states “Tracker not checked” above it, even if every statement is met; this applies provided checking was possible, otherwise with `BLOCKED`. If the spec is not available as text, the previous point applies.

Answer in the user's language.
<!-- /vertrag:zugang -->

### Tracker: Marker

<!-- vertrag:marker -->
Every comment that a slickfab step or role writes, and every report to a caller, ends with the marker block, with no text after it:

- Last line, always: `SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`
- Second-to-last line, only for the reviewer: `SLICKFAB-VERDICT: MERGE|REWORK|REPLAN`

All other steps and roles write only the STATUS line. Each line holds exactly one value.

| Value | Meaning |
|---|---|
| `DONE` | task fulfilled, nothing open |
| `DONE_WITH_CONCERNS` | fulfilled, but with stated concerns |
| `BLOCKED` | cannot continue; the reason is stated above |
| `NEEDS_CONTEXT` | information or context is missing; what is missing is stated above |

Example (every step):

```
SLICKFAB-STATUS: BLOCKED
```

Example (reviewer):

```
SLICKFAB-VERDICT: REWORK
SLICKFAB-STATUS: DONE
```

Answer in the user's language.
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
