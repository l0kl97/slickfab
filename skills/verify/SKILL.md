---
name: verify
description: Verwenden, wenn alle Tickets einer Spec gemergt sind und geprüft werden soll, ob das Ziel der Spec wirklich erreicht ist, oder wenn jemand „ist das Feature fertig?“ fragt.
argument-hint: "<Spec-Issue>"
---

<!-- regel:grenzen -->
# verify: Ist das Ziel der Spec erreicht?

Ziel: Nach dem letzten Ticket festzustellen, ob das, was die Spec unter „Muss wahr sein“ verspricht, im Code auf dem Hauptzweig wirklich gilt, nicht nur, ob alle Tickets erledigt sind. Erledigte Tickets beweisen nichts; jedes einzelne kann bestanden haben, während die Teile nicht miteinander verbunden sind.

Du änderst keinen Code. Dein Ergebnis ist ein Bericht und, nach Bestätigung, Fix-Tickets.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:grenzen -->

## Wann

<!-- regel:wann -->
- Wenn alle Tickets einer Spec `Done` sind (gemergt).
- Wieder, nachdem Fix-Tickets aus einem früheren Lauf gemergt sind.
- Nicht für einen einzelnen Pull Request; dafür gibt es `/slickfab:review`.
<!-- /regel:wann -->

## Ablauf

<!-- regel:ablauf -->
### 1. Voraussetzung prüfen

- Du brauchst das Spec-Issue (Argument). Fehlt es, frag danach und hör auf.
- Lies `.slickfab/config` und das Spec-Issue mit allen Kommentaren und Sub-Issues, mit den Linear-Werkzeugen der Session (in Claude Code per Werkzeugsuche `+linear` laden). Fehlt die Konfiguration, gilt der Vertrag unten (Abschnitt „wenn sie fehlt“). Ist der Tracker nicht erreichbar, sag das mit der Fehlermeldung. Liegt die Spec als Text im Argument vor, prüfst du dagegen und zeigst das Ergebnis im Chat; Fix-Tickets bleiben dann eine Liste im Chat (Schritt 5). Das Ergebnis endet dann mit `DONE_WITH_CONCERNS` und nennt darüber „Tracker nicht geprüft“, auch bei `bestanden`, sofern geprüft werden konnte, sonst mit `BLOCKED` (Vertrag, Abschnitt Zugang). Liegt sie nicht vor, hörst du auf und meldest das mit `SLICKFAB-STATUS: NEEDS_CONTEXT`. Du schreibst keine Plan-, Ticket- oder Ergebnisdatei ins Repo als Ersatz.
- Sind noch Tickets offen, nenne sie. Weiter nur, wenn der Mensch ausdrücklich trotzdem prüfen will; offene Tickets erklären dann Lücken nicht weg.
- Prüf auf dem aktuellen Hauptzweig mit sauberem Arbeitsstand (`git status --short` leer). Nenne den Commit, den du prüfst. Steht deine Session nicht schon sauber auf dem Hauptzweig, bewegst du keinen fremden Checkout (kein `git checkout`), sondern legst nach `git fetch` wie bei review einen Worktree im detached-Zustand im Arbeitsverzeichnis an (`git worktree add --detach .slickfab-verify-<Spec> origin/<Hauptzweig>`), lässt die Prüfbefehle dort laufen und entfernst ihn danach in jedem Fall (`git worktree remove --force`).

### 2. Aussagen sammeln

Nimm aus der Spec jede Zeile unter „Muss wahr sein“ und jede unter „Kritische Verbindungen“ als eigene Aussage, wörtlich. Erledigte Tickets, PR-Texte und Berichte der Umsetzer sind keine Belege; du gehst davon aus, dass das Ziel nicht erreicht ist, bis der Code das Gegenteil zeigt. Hat die Spec keinen Abschnitt „Muss wahr sein“, sag das und leite die Aussagen aus Problem und User Stories ab, gekennzeichnet als abgeleitet.

### 3. Je „Muss wahr sein“ vier Ebenen prüfen

Für jede Aussage: Welche Dateien, Funktionen, Routen oder Befehle müssen es tragen? Dann der Reihe nach, und eine Ebene zählt erst, wenn die davor erfüllt ist:

1. **existiert:** Die tragenden Teile sind auf dem Hauptzweig da (Datei, Funktion, Route, Befehl).
2. **echt:** Sie tun etwas, statt nur da zu sein. Kein Stub: keine leere Funktion, kein `return null`/fester Rückgabewert ohne Logik, kein `TODO`/`Platzhalter`/„not implemented“, kein Handler, der nur loggt, keine Oberfläche, die festen Beispieltext zeigt.
3. **verdrahtet:** Der Produktivcode ruft sie auf, auf dem Weg, den die Aussage beschreibt (Import und Aufruf, registrierte Route, Eintrag im Menü, Hook in der Konfiguration). Such die Aufrufer; Tests zählen hier nicht als Aufrufer.
4. **Daten fließen:** Echte Eingaben kommen durch: Verfolge einen Wert von der Quelle (Nutzereingabe, Datenbank, API) bis zur Ausgabe. Endet die Kette in einem festen Wert, einem Mock oder einer leeren Liste, ist die Ebene nicht erfüllt. Wo es geht, führ den Weg aus (Befehl, Test über die öffentliche Schnittstelle, Aufruf der Route) und notiere Befehl und Ausgabe.

Existiert eine Datei oder Funktion, aber nichts im Produktivcode ruft sie auf, ist die Aussage nicht erfüllt, auch wenn ihre eigenen Tests grün sind. Vorhandensein ist kein Verhalten.

Lass zum Schluss die Prüfbefehle des Repos laufen (aus `.slickrails/config.sh`, sonst `.slickfab/config`). Rot ist eine Lücke, auch wenn sie keine Aussage direkt betrifft.

Je Aussage ein Ergebnis: `erfüllt` (alle vier Ebenen mit Beleg), `nicht erfüllt` (Ebene nennen, an der es scheitert, mit `Datei:Zeile` oder Befehl und Ausgabe) oder `unklar` (lässt sich nicht maschinell prüfen, etwa Aussehen, Gefühl, Verhalten gegen ein fremdes System, das du nicht erreichst; sag, was ein Mensch prüfen müsste). Wähle `unklar` nicht, wenn das Fehlen beobachtbar ist; dann ist es `nicht erfüllt`.

### 4. Status

Genau ein Status für die Spec:

| Status | Wann |
|---|---|
| `bestanden` | jede Aussage `erfüllt`, Prüfbefehle grün |
| `Lücken gefunden` | mindestens eine Aussage `nicht erfüllt` oder ein Prüfbefehl rot |
| `Mensch nötig` | keine Aussage `nicht erfüllt`, aber mindestens eine `unklar` |

`bestanden` nur, wenn jede Aussage alle vier Ebenen erfüllt. Ein hoher Anteil erfüllter Aussagen macht die übrigen nicht leichter; prüf die letzte so genau wie die erste.

### 5. Fix-Tickets vorschlagen

Nur bei `Lücken gefunden`. Je Lücke ein Ticket-Vorschlag: Titel (Verb + Ergebnis), die Aussage aus der Spec wörtlich, die Ebene, an der es scheitert, mit Beleg, ein Kriterium mit „Widerlegt, wenn“, Größe `S`, `M` oder `L`, und unter „Agent notes“ die betroffenen Dateien. Lücken, die dieselbe Ursache haben, fasst du zu einem Ticket zusammen.

1. Zeig dem Menschen die Vorschläge als nummerierte Liste.
2. Prüf auf Dubletten: offene und erledigte Issues im Projekt mit ähnlichem Titel. Treffer nennst du an der Stelle in der Liste.
3. Angelegt wird erst nach einem ausdrücklichen Ja zur Liste (ganz oder zu einzelnen Nummern). Ohne Ja legst du kein Issue an; Schweigen, „klingt gut“ zu etwas anderem oder ein Ja aus einem früheren Gespräch zählen nicht.
4. Erst nach dem Ja: Lege die bestätigten Tickets als Sub-Issues der Spec in `Backlog` an, nach dem Vertrag unten (Abschnitt Issues). Kein Fix-Ticket setzt du auf `Todo`; die Freigabe zum Bauen gibt der Mensch. Den Status anderer Issues änderst du nicht.

Ist der Tracker nicht erreichbar, bleibt die Liste im Chat; du legst keine Datei als Ersatz an.

### 6. Festhalten

Schreib das Ergebnis als Kommentar an das Spec-Issue (wenn der Tracker erreichbar ist), letzte Zeile die STATUS-Zeile nach Vertrag: `DONE` bei `bestanden`, `DONE_WITH_CONCERNS` bei `Lücken gefunden` oder `Mensch nötig`, `BLOCKED`, wenn du nicht prüfen konntest. Ohne Tracker, gegen die Spec als Text, kein Kommentar: Das Ergebnis steht im Chat, nennt „Tracker nicht geprüft“ und endet mit `DONE_WITH_CONCERNS`, sofern geprüft werden konnte, sonst mit `BLOCKED`. Den Status des Spec-Issues änderst du nicht.
<!-- /regel:ablauf -->

## Vertrag

<!-- regel:vertrag-quelle -->
Wörtlich aus `tracker/linear.md` und `docs/projektkonfiguration.md` des slickfab-Plugins. Es steht hier, damit du nichts außerhalb des Projekts lesen musst; es gilt genau so.
<!-- /regel:vertrag-quelle -->

### Tracker: Zugang

<!-- vertrag:zugang -->
- Linear is accessed through the session's Linear tools (in Claude Code, load them via tool search `+linear`).
- If Linear is unreachable (no tools, not logged in, error response, team or project from the configuration does not exist), the step reports exactly that, with the error message, and stops. It writes **no** plan, ledger, state or ticket file into the repo as a substitute. Whatever has already been worked out, it shows in the chat, so that nothing is lost.
- Exception `verify`: If the spec is available as text, verify keeps checking against it instead of stopping. It writes nothing to the tracker, shows the result and fix-ticket proposals only in the chat, and the result ends with `SLICKFAB-STATUS: DONE_WITH_CONCERNS` and states “Tracker not checked” above it, even if every statement is met; this applies provided checking was possible, otherwise with `BLOCKED`. If the spec is not available as text, the previous point applies.

Answer in the user's language.
<!-- /vertrag:zugang -->

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
## Ergebnis verify

**Spec:** <Issue> · **Geprüft am Commit:** <SHA auf dem Hauptzweig>
**Status:** bestanden | Lücken gefunden | Mensch nötig

| Aussage (wörtlich) | existiert | echt | verdrahtet | Daten fließen | Ergebnis | Beleg |
|---|---|---|---|---|---|---|
| <Zeile aus „Muss wahr sein“> | ✓ | ✓ | ✗ | – | nicht erfüllt | `<Datei:Zeile>` / `<Befehl>` → <Ausgabe> |

**Prüfbefehle:** `<Befehl>` → <Ergebnis>
**Mensch prüft:** <was, wie> (bei `unklar`)
**Fix-Tickets:** <Vorschläge, nummeriert> · angelegt: <Links> oder „warten auf Ja“

Nächster Schritt: `/slickfab:implement <Fix-Ticket>` | `/slickfab:retro`

SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
- `bestanden`: `/slickfab:retro`, um aus den Fehlern dieses Features Regeln zu machen.
- `Lücken gefunden`: die Fix-Tickets freigeben (`Todo`) und mit `/slickfab:implement <Fix-Ticket>` bauen, danach wieder `/slickfab:verify <Spec-Issue>`.
- `Mensch nötig`: der Mensch prüft die genannten Punkte; danach `/slickfab:verify <Spec-Issue>` erneut.
<!-- /regel:naechster-schritt -->
