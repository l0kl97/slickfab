---
name: spec
description: Verwenden, wenn aus einem geklärten Gespräch (nach grill) eine Spezifikation im Tracker entstehen soll, oder wenn jemand „schreib die Spec“ sagt.
argument-hint: "[Feature-Name oder Spec-Issue zum Überarbeiten]"
---

<!-- regel:einleitung -->
# spec: Spezifikation aus dem Gespräch

Ziel: Eine Spec, aus der Umsetzer und Prüfer dasselbe Ziel lesen, ohne das Gespräch gesehen zu haben. Du schreibst auf, was entschieden ist. Du befragst nicht neu: Inhaltliche Entscheidungen fallen in `grill`, nicht hier.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Nach `/slickfab:grill`, wenn die Zusammenfassung „Ergebnis grill“ bestätigt ist.
- Zum Überarbeiten einer bestehenden Spec, wenn der Mensch über Einwände aus `challenge` entschieden hat (Argument: das Spec-Issue).
- Nicht, solange Produktfragen offen sind; dann zuerst `grill`.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Voraussetzung prüfen

Du brauchst eine geklärte Grundlage. Suche in dieser Reihenfolge:

1. eine bestätigte Zusammenfassung „Ergebnis grill“ in diesem Gespräch,
2. ein als Argument genanntes Spec-Issue (dann liest du es samt Kommentaren und arbeitest die dort genannten Entscheidungen ein),
3. ein Gespräch, in dem der Mensch Problem, Nutzer, Umfang und Erfolgskriterium ausdrücklich entschieden hat.

Findest du nichts davon, hörst du hier auf: Sag, dass die Grundlage fehlt, und empfiehl `/slickfab:grill <Thema>`. Schreib keine Spec auf Verdacht.

Lies dann `.slickfab/config` (Format und Regeln: Projektkonfiguration). Fehlt sie oder ist der Tracker nicht erreichbar, sag das gleich jetzt: Du kannst die Spec im Chat zeigen, aber nicht anlegen.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:lage-im-repo-lesen -->
### 2. Lage im Repo lesen

Lies, was die Spec binden muss: `CLAUDE.md`/`AGENTS.md`, `.slickrails/` (falls vorhanden), `GLOSSARY.md`, `docs/adr/`, bestehende Feature-Doku zum Thema. Benutze die Begriffe aus `GLOSSARY.md` und widersprich keinem ADR, ohne es zu nennen. Bei mehr als ein paar Dateien schickst du einen Sub-Agent und lässt dir das Ergebnis kurz geben.
<!-- /regel:lage-im-repo-lesen -->

<!-- regel:jede-aussage-auf-ihre-herkunft-pruefen -->
### 3. Jede Aussage auf ihre Herkunft prüfen

Geh Abschnitt für Abschnitt durch die Vorlage (Schritt 4). Jede Aussage, die du schreiben willst, stammt aus einer dieser Quellen:

- vom Menschen entschieden (im Gespräch oder in „Ergebnis grill“),
- „Autonom entschieden“ aus `grill`,
- eine Tatsache aus dem Repo.

Passt eine Aussage zu keiner Quelle, ist sie eine **offene Entscheidung**. Ordne sie ein wie in `grill`:

- **Umkehrbar, technisch** (austauschbar hinter stabiler Schnittstelle): entscheide selbst und trag sie unter „Autonom entschieden“ ein, mit Grund.
- **Produktfrage oder schwer umkehrbar:** Hier hörst du auf. Liste die offenen Entscheidungen auf, je ein Satz, warum die Spec sie braucht, und empfiehl `/slickfab:grill` mit genau diesen Punkten. Du schreibst die Spec erst weiter, wenn sie entschieden sind.

Diese Regel hat keine Ausnahme:

| Ausrede | Realität |
|---|---|
| „Die Antwort ist doch offensichtlich.“ | Dann kostet die Rückfrage in `grill` eine Minute. Eine stille Annahme kostet ein falsch gebautes Feature. |
| „Ich markiere es als Annahme in der Spec.“ | Eine markierte Annahme ist trotzdem eine Entscheidung, die der Mensch nicht getroffen hat. |
| „Ich frage hier kurz selbst nach.“ | `spec` stellt keine Inhaltsfragen; die Befragung mit Empfehlung und Einordnung gehört zu `grill`. |
<!-- /regel:jede-aussage-auf-ihre-herkunft-pruefen -->

<!-- regel:spec-schreiben -->
### 4. Spec schreiben

Füll diese Vorlage. Schreib in Verhalten und Begriffen der Domäne: Module und Schnittstellen beim Namen, aber ohne Dateipfade und ohne Code, weil beides schnell veraltet. Wo ein Pfad naheläge, nenne das Modul oder das Verhalten.

```markdown
## Bitte (wörtlich)

> „<die ursprüngliche Bitte des Menschen, wörtlich zitiert, auch mit Tippfehlern>“

## Problem

<aus Sicht der Nutzer: wer hat welches Problem, woran merkt man es heute>

## Lösung

<aus Sicht der Nutzer: was ist danach anders. Bei Änderungen an einem bestehenden Feature als Delta: vorher → nachher>

## User Stories

1. Als <Rolle> möchte ich <Fähigkeit>, damit <Nutzen>.
(lieber zu viele als zu wenige; Fehlerfälle und Randfälle eigene Stories)

## Entscheidungen

- <Entscheidung> (vom Menschen)
- Autonom entschieden: <Entscheidung> — <warum> — umkehrbar, weil <…> (oder „keine“)

## Muss wahr sein

- <beobachtbare Wahrheit aus Nutzersicht, die nach dem Bauen gilt; 3–7 Punkte>

## Kritische Verbindungen

- <Teil A> ↔ <Teil B>: <was zwischen beiden fließen muss; woran man merkt, dass es verdrahtet ist>
(die Stellen, an denen es am ehesten bricht)

## Grenzen

- **Immer:** <was jeder Umsetzer immer tut>
- **Erst fragen:** <was nur mit Ja des Menschen passiert>
- **Nie:** <was ausgeschlossen ist>

## Global Constraints

- <Regel, die jedes Ticket einhalten muss, wörtlich aus CLAUDE.md, slickrails-Regeln, Versionen, Konventionen>

## Review-Fokus

- <Eingabeklasse oder Risiko, das kein Test prüft und auf das der Prüfer schauen soll>

## Teststellen

- <öffentliche Schnittstelle, an der das Verhalten geprüft wird> — fängt: <…> — verpasst: <…>
(möglichst weit oben, möglichst wenige, bestehende bevorzugt; ideal genau eine)

## Nicht im Umfang

- <was ausdrücklich nicht gebaut wird>
```

Waren die Teststellen in `grill` nicht entschieden, schlägst du sie vor und trägst sie unter „Autonom entschieden“ ein; der Mensch sieht sie in Schritt 5.
<!-- /regel:spec-schreiben -->

<!-- regel:selbstpruefung-dann-zeigen -->
### 5. Selbstprüfung, dann zeigen

Prüf den Entwurf, bevor der Mensch ihn sieht:

- alle Abschnitte der Vorlage da, keiner leer (leer = „keine“ mit einem Satz warum),
- die Bitte steht wörtlich da, nicht umformuliert,
- kein Dateipfad, kein Dateiname, kein Code im Text,
- jede Aussage hat eine Quelle aus Schritt 3.

Zeig die Spec im Chat und frag, ob du sie so anlegen sollst. Das ist eine Freigabe, keine Inhaltsfrage: Will der Mensch etwas anders, übernimm es; öffnet seine Antwort eine neue Produktfrage, zurück zu Schritt 3.
<!-- /regel:selbstpruefung-dann-zeigen -->

<!-- regel:im-tracker-anlegen -->
### 6. Im Tracker anlegen

Erst nach dem Ja. Wie im Tracker-Vertrag: Dubletten prüfen, dann Issue `Spec: <Feature>` im Projekt aus `.slickfab/config`, Status `Backlog`. Beim Überarbeiten aktualisierst du das bestehende Spec-Issue statt ein neues anzulegen und schreibst einen Kommentar, dessen erste Zeile genau `## Spec überarbeitet` lautet; darunter steht, was sich geändert hat, am Ende die Marker-Zeile. An dieser ersten Zeile erkennt `fab`, dass die Spec nach einem `challenge`-Urteil geändert wurde.

Ist der Tracker nicht erreichbar oder fehlt die Konfiguration, meldest du das mit der Fehlermeldung und lässt die Spec im Chat stehen. Du legst keine Spec-, Plan- oder Ticket-Datei im Repo an.
<!-- /regel:im-tracker-anlegen -->

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
Ein Spec-Issue im Tracker (oder, ohne Tracker, die Spec im Chat und die klare Meldung, warum sie nicht angelegt ist). Im Chat zum Schluss:

```
## Ergebnis spec

**Spec:** <Issue-ID und Link> (oder: nicht angelegt, weil <Grund>)
**Autonom entschieden:** <Liste oder „keine“>
**Offene Entscheidungen:** <Liste, dann zurück zu grill, oder „keine“>

Nächster Schritt: `/slickfab:challenge <Issue-ID>`
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:challenge <Issue-ID>` — frischer Blick auf Produkt, Baubarkeit und später die Zerlegung; am besten in einer neuen Session, damit der Prüfer das Gespräch nicht kennt. Gibt es Fragen, die man nicht erfragen kann (Aussehen, Bedienung, ob eine Logik sich richtig anfühlt), vorher `/slickfab:prototype`. Fehlen Entscheidungen, zurück zu `/slickfab:grill`.
<!-- /regel:naechster-schritt -->
