---
name: tickets
description: Verwenden, wenn eine geprüfte Spec in Tickets für den Tracker zerlegt werden soll, oder wenn jemand „schneid das in Tickets“ oder „leg die Tickets an“ sagt.
argument-hint: "<Spec-Issue>"
---

<!-- regel:einleitung -->
# tickets: Spec in dünne, durchgehende Tickets schneiden

Ziel: Tickets, die ein Agent ohne Rückfrage bauen kann, möglichst parallel, und die zusammen genau die Spec liefern, nicht weniger. Angelegt wird erst, wenn der Mensch die Liste bestätigt hat.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Nach `/slickfab:challenge`, wenn der Mensch über Einwände entschieden hat und die Spec stimmt.
- Nicht ohne Spec im Tracker; nicht, wenn das Urteil `nicht bauen` lautet und der Mensch zugestimmt hat.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Voraussetzung prüfen

- Lies `.slickfab/config`. Fehlt sie oder ist der Tracker nicht erreichbar, hör hier auf und melde genau das. Tickets gibt es nur im Tracker; du schreibst keine Ticket-, Plan- oder State-Datei ins Repo als Ersatz.
- Du brauchst das Spec-Issue (Argument oder „Ergebnis spec“ in diesem Gespräch). Fehlt es, empfiehl `/slickfab:spec`.
- Lies das Spec-Issue mit allen Kommentaren. Suche den Kommentar aus `challenge` (Urteil, Einwände). Fehlt er, sag das und empfiehl zuerst `/slickfab:challenge <Spec-Issue>`; weiter nur, wenn der Mensch ausdrücklich ohne Prüfung zerlegen will. Hat der Mensch über Einwände entschieden, die noch nicht in der Spec stehen, zuerst `/slickfab:spec <Spec-Issue>`. Lautet das letzte Urteil `nicht bauen`, hör hier auf und leg die Frage dem Menschen vor (Vorlage „Rückfrage“ unten), außer er hat ausdrücklich gesagt, dass trotzdem zerlegt wird.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:repo-lesen -->
### 2. Repo lesen

Finde, wo die Spec das Repo berührt: Module, Schnittstellen, Tests, `GLOSSARY.md`, `docs/adr/`, `CLAUDE.md`. Für mehr als ein paar Dateien einen Sub-Agent. Achte auf vorbereitende Umbauten, die die eigentliche Änderung leicht machen.
<!-- /regel:repo-lesen -->

<!-- regel:schneiden -->
### 3. Schneiden

- **Tracer zuerst:** Das erste Ticket ist der dünnste Pfad durch alle Schichten, der die kritischen Verbindungen der Spec einmal echt verdrahtet und von außen prüfbar macht. Es blockiert alle übrigen Tickets.
- **Durchgehende Scheiben:** Jedes weitere Ticket liefert ein von außen prüfbares Verhalten quer durch die Schichten, ist für sich vorführbar und passt in eine frische Session. Frontend und Backend trennst du nur, wenn das Ticket die Schnittstelle zwischen beiden wörtlich festlegt.
- **Vorbereitender Umbau**, den mehrere Tickets brauchen, ist ein eigenes Ticket direkt nach dem Tracer.
- **Breite mechanische Umbauten** (Spalte umbenennen, geteilten Typ ändern) schneidest du als Expand–Migrate–Contract: erst das Neue neben das Alte (Expand), dann die Aufrufer paketweise umziehen, je Paket ein Ticket, blockiert vom Expand, die Prüfungen bleiben dazwischen grün (Migrate), zuletzt das Alte entfernen, blockiert von allen Paketen (Contract).
- Ein „und“ im Titel heißt meist zwei Tickets; mehr als etwa 5 Kriterien heißt meist zu groß.

Jedes Ticket in dieser Form:

```markdown
## Was gebaut wird

<Verhalten aus Nutzersicht, nicht Schichten>

## Akzeptanzkriterien

- [ ] <beobachtbares Verhalten, auch Fehlerfälle>. **Widerlegt, wenn** <die Beobachtung, die es widerlegt>.

## Schnittstellen

- Verbraucht: <Namen, Datenformen, Routen, die dieses Ticket von anderen nutzt, mit Ticket-Nr.>
- Liefert: <Namen, Datenformen, Routen, die andere Tickets von diesem nutzen>

## Nicht im Umfang

- <was ausdrücklich ein anderes Ticket macht>

+++ Agent notes

**Betroffene Dateien (voraussichtlich)**
- <Pfad>

**Fundstellen** <wo im Repo Vorbilder liegen>

+++
```

Zum Text: Was gebaut wird und Kriterien in der Sprache der Spec, ohne Pfade; Pfade stehen nur in den Agent notes. Jedes Kriterium wäre am heutigen Stand falsch; ist es schon wahr, ist es kein Kriterium. Die Global Constraints der Spec gelten für jedes Ticket, weil es ein Sub-Issue der Spec ist.

Labels je Ticket: genau eine Größe `S`, `M` oder `L`, und `door:one-way`, wenn das Ticket schwer umkehrbar ist (Migration, Auth, Zahlung, Löschen von Daten, Deploy, öffentliche Schnittstelle).
<!-- /regel:schneiden -->

<!-- regel:abhaengigkeiten-setzen -->
### 4. Abhängigkeiten setzen

- Der Tracer blockiert alle übrigen Tickets.
- Echte Abhängigkeiten (ein Ticket verbraucht, was ein anderes liefert) werden Blockiert-Relationen.
- **Dateiüberschnitt:** Mach eine Tabelle Datei → Tickets aus den Agent notes. Nennen zwei Tickets dieselbe Datei, bekommt das spätere eine Blockiert-Relation auf das frühere, auch wenn sie inhaltlich nichts voneinander brauchen; parallel gebaut würden sie sich gegenseitig überschreiben.
- Keine Zyklen. Was danach keine Blocker außer dem Tracer hat, kann parallel laufen.
<!-- /regel:abhaengigkeiten-setzen -->

<!-- regel:auf-stille-kuerzung-pruefen -->
### 5. Auf stille Kürzung prüfen

Lies jeden Titel, jede Beschreibung und jedes Kriterium auf Formulierungen, die Arbeit vertagen: „v1“, „vereinfacht“, „Platzhalter“, „wird später verdrahtet“, und alles Gleichbedeutende (Stub, erstmal hart kodiert, TODO, folgt später, placeholder, simplified). Ein Ticket mit so einer Formulierung legst du nicht an. Statt das Wort zu ersetzen, korrigierst du den Schnitt: Entweder das Ticket liefert es ganz, oder der vertagte Teil wird ein eigenes Ticket mit eigenen Kriterien und Blockiert-Relation und steht im ersten unter „Nicht im Umfang“.

| Ausrede | Realität |
|---|---|
| „Für den Anfang reicht eine vereinfachte Version.“ | Dann ist die kleinere Version die Spec, und das entscheidet der Mensch in `grill` oder `challenge`, nicht der Ticket-Text. |
| „Die Verdrahtung macht das nächste Ticket.“ | Dann ist sie ein eigenes Ticket mit Kriterien. Sonst baut niemand sie. |
<!-- /regel:auf-stille-kuerzung-pruefen -->

<!-- regel:zerlegung-pruefen-und-bestaetigen-lassen -->
### 6. Zerlegung prüfen und bestätigen lassen

1. Ruf die Zerlegungsprüfung von `/slickfab:challenge` mit Spec und Liste auf (frischer Sub-Agent, Runde 1). Bei Befunden: Liste überarbeiten, Runde 2 mit der Befundzahl aus Runde 1. Es gibt höchstens diese 2 Runden; was danach offen ist, legst du dem Menschen vor.
2. Prüf auf Dubletten: Suche im Projekt aus `.slickfab/config` nach offenen und erledigten Issues mit ähnlichem Titel, auch unter den Sub-Issues der Spec. Treffer zeigst du in der Liste an. Antwortet der Tracker bei der Suche mit einem Fehler, hör auf (Vorlage „Abbruch“ unten, `BLOCKED`).
3. Zeig die nummerierte Liste:

```
1. <Titel> — <Größe>, <door:one-way falls zutreffend> — blockiert von: — (Tracer)
   liefert: <ein Satz> · Dateien: <kurz>
2. <Titel> — <Größe> — blockiert von: 1
   liefert: … · Dateien: …
…
Zerlegungsprüfung: bestanden in Runde <n> | offen: <Befunde>
Dubletten: keine | <Treffer>
```

Frag: Stimmt die Größe der Scheiben? Stimmen die Abhängigkeiten? Etwas zusammenlegen oder teilen? Dann wartest du. Änderungswünsche arbeitest du ein und zeigst die Liste erneut. Angelegt wird erst nach einem ausdrücklichen Ja zur Liste; „passt schon“ zu einer einzelnen Zeile ist kein Ja zur ganzen Liste.
<!-- /regel:zerlegung-pruefen-und-bestaetigen-lassen -->

<!-- regel:anlegen -->
### 7. Anlegen

Erst nach dem Ja, und in Abhängigkeitsreihenfolge (Tracer zuerst), damit jede Relation auf eine echte Issue-ID zeigt:

- je Ticket ein Sub-Issue der Spec, Status `Backlog`, Labels wie in Schritt 3, Relationen wie in Schritt 4,
- danach ein Kommentar am Spec-Issue mit der Liste der Tickets und der Marker-Zeile nach Tracker-Vertrag.

Kein Ticket setzt du auf `Todo`; das ist die Freigabe des Menschen. Die Spec selbst änderst du nicht. Bricht der Tracker mitten im Anlegen ab, hör auf und melde, welche Tickets angelegt sind und welche nicht, mit der Fehlermeldung (Vorlage „Abbruch“ unten, `BLOCKED`). Du legst keine Datei als Ersatz an.
<!-- /regel:anlegen -->

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

### Tracker: Issues

<!-- vertrag:issues -->
| Kind | Title | Location | Initial status |
|---|---|---|---|
| Spec | `Spec: <Feature>` | project from the configuration | `Backlog` |
| Ticket | verb + outcome, without “and” | sub-issue of the spec | `Backlog` |

- Before creating anything, check for duplicates: search open and completed issues in the project with a similar title. If there is a match, name it and ask instead of creating a duplicate.
- Dependencies are Linear relations “blocked by”, not text in the description.
- Details for agents (affected files, locations) go in a collapsible section “Agent notes” at the end of the description.

Answer in the user's language.
<!-- /vertrag:issues -->

### Tracker: Statusfolge

<!-- vertrag:status -->
`Backlog` → `Todo` → `In Progress` → `In Review` → `Done` (abort: `Canceled`, duplicate: `Duplicate`)

| Transition | Who |
|---|---|
| create in `Backlog` | `spec`, `tickets` |
| `Backlog` → `Todo` | only the human (this is the approval to build) |
| `Todo` → `In Progress` | the implementer at the start |
| `In Progress` → `In Review` | the implementer, once the pull request is open |
| `In Review` → `Done` | after the merge |

No step sets a ticket to `Todo` by itself.

Answer in the user's language.
<!-- /vertrag:status -->

### Tracker: Labels

<!-- vertrag:labels -->
The labels exist in the team; a step does not create new ones. If one is missing, it reports that.

| Label | Meaning |
|---|---|
| `slickfab:rework` | reviewer demands rework |
| `slickfab:ready` | review passed, waiting for a human to merge |
| `slickfab:needs-human` | loop exhausted or agent blocked: a human decides |
| `slickfab:replan` | ticket or spec is cut wrong: back to planning |
| `door:one-way` | hard to reverse (migration, auth, payment, deletion, deploy): always a human gate, never auto-merge |
| `S`, `M`, `L` | size (effort small, medium, large); exactly one per ticket. `L` is a hint that the ticket should rather be split |

In Linear, `rework`, `ready`, `needs-human` and `replan` are children of the label group `slickfab`; in texts, comments and this contract they are written as `slickfab:<name>`. When searching and setting via the Linear tools, the label is called `rework`, `ready`, `needs-human` or `replan` in the group `slickfab`; a search for `slickfab:rework` finds nothing, and that does not mean the label is missing. The group allows only one at a time.

Answer in the user's language.
<!-- /vertrag:labels -->

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
Wo tickets endet, und mit welcher Vorlage. Jede Stelle im Ablauf, an der du aufhörst, empfiehlst, wartest oder dem Menschen etwas vorlegst, steht hier:

| Stelle | Fall | Vorlage | STATUS |
|---|---|---|---|
| Schritt 1 | `.slickfab/config` fehlt oder Tracker nicht erreichbar | Ergebnis tickets (Abbruch) | `BLOCKED` |
| Schritt 1 | Spec-Issue fehlt | Ergebnis tickets (Rückfrage) | `NEEDS_CONTEXT` |
| Schritt 1 | `challenge`-Kommentar fehlt | Ergebnis tickets (Rückfrage) | `NEEDS_CONTEXT` |
| Schritt 1 | Entscheidung steht noch nicht in der Spec | Ergebnis tickets (Rückfrage) | `NEEDS_CONTEXT` |
| Schritt 1 | letztes `challenge`-Urteil `nicht bauen` | Ergebnis tickets (Rückfrage) | `NEEDS_CONTEXT` |
| Schritt 6 | Tracker antwortet bei der Dublettensuche mit einem Fehler | Ergebnis tickets (Abbruch) | `BLOCKED` |
| Schritt 6 | Dublette, Liste wartet auf das Ja oder Befunde offen nach Runde 2 | Ergebnis tickets (Rückfrage) | `NEEDS_CONTEXT` |
| Schritt 7 | Tracker bricht beim Anlegen ab | Ergebnis tickets (Abbruch) | `BLOCKED` |
| Schritt 7 | alle Tickets angelegt | Ergebnis tickets | `DONE` oder `DONE_WITH_CONCERNS` |

```
## Ergebnis tickets

**Spec:** <Issue-ID>
**Tickets:** <ID> Tracer, <ID>, … (alle in Backlog)
**Parallel möglich nach dem Tracer:** <IDs>
**door:one-way:** <IDs oder „keine“>
**Offen aus der Zerlegungsprüfung:** <Befunde oder „keine“>

Nächster Schritt: `/slickfab:implement <Tracer-ID>`, sobald du die Tickets auf Todo gesetzt hast

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS>
```

Endet der Schritt, ohne Tickets anzulegen, weil du den Menschen etwas fragst (Dublette, fehlender `challenge`-Kommentar, Urteil `nicht bauen`, Liste wartet auf das Ja) oder weil etwas fehlt (Spec, Entscheidung in der Spec), gilt diese Vorlage. Den nächsten Schritt wählst du nach dem Grund, wie in Schritt 1:

```
## Ergebnis tickets (Rückfrage)

**Spec:** <Issue-ID>
**Frage:** <was der Mensch entscheiden oder liefern muss, mit Links zu Treffern>
**Bisher erarbeitet:** <Liste oder Stand, damit nichts verloren geht>

Nächster Schritt: `/slickfab:<Schritt>` nach dem Grund: fehlt die Spec oder steht eine Entscheidung noch nicht darin: `/slickfab:spec [Spec-Issue]`; fehlt die Prüfung: `/slickfab:challenge <Spec-Issue>`; lautet das Urteil `nicht bauen`: `/slickfab:spec <Spec-Issue>`, wenn du die Spec änderst (danach `/slickfab:challenge <Spec-Issue>`); stimmst du dem Urteil zu, endet das Vorhaben und du setzt die Spec auf `Canceled`; Frage zum Schnitt (Dublette, Liste wartet auf das Ja, Befunde offen nach Runde 2): `/slickfab:tickets <Spec-Issue>` erneut, sobald die Antwort da ist

SLICKFAB-STATUS: NEEDS_CONTEXT
```

Fehlt in Schritt 1 die Konfiguration oder ist der Tracker nicht erreichbar, antwortet er bei der Dublettensuche mit einem Fehler (Schritt 6) oder bricht er mitten im Anlegen ab (Schritt 7), gilt diese Vorlage:

```
## Ergebnis tickets (Abbruch)

**Spec:** <Issue-ID>
**Wo:** Schritt 1 (Konfiguration oder Tracker) | Schritt 6 (Dublettensuche) | Schritt 7 (beim Anlegen)
**Schon angelegt:** <IDs mit Titel und gesetzten Relationen> (in Schritt 1 und 6: keine)
**Nicht angelegt:** <Titel aus der bestätigten Liste> (in Schritt 1: alle, Liste gibt es noch nicht; in Schritt 6: alle Titel der noch nicht bestätigten Liste)
**Fehlermeldung:** <wörtlich: fehlende Datei oder fehlender Schlüssel, oder die Fehlerantwort des Trackers>

Nächster Schritt: `/slickfab:tickets <Spec-Issue>` erneut, nachdem du <`.slickfab/config` angelegt | den Tracker geprüft (Werkzeuge geladen, angemeldet, Team und Projekt vorhanden)> hast; nach einem Abbruch in Schritt 7 findet die Dublettenprüfung die schon angelegten Tickets, angelegt wird nur der Rest

SLICKFAB-STATUS: BLOCKED
```

Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei einer Rückfrage (`NEEDS_CONTEXT`). Die Marker-Zeile ist die letzte Zeile deiner Antwort und steht außerhalb jedes Codeblocks. Die Vorlagen stehen hier nur zur Darstellung in Codeblöcken; deine Antwort schreibst du als normalen Text, ohne Codeblock um Ergebnis oder Marker.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
Der Mensch prüft die Tickets und setzt sie auf `Todo`. Dann `/slickfab:implement <Tracer-ID>` für das erste Ticket; die übrigen werden frei, sobald der Tracer gemergt ist.
<!-- /regel:naechster-schritt -->
