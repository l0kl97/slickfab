---
name: challenge
description: Verwenden, wenn eine Spec vor dem Zerlegen einen frischen Blick von außen braucht (Produkt, Baubarkeit) oder eine Ticket-Zerlegung vor dem Anlegen geprüft werden soll, oder wenn jemand „challenge das“ sagt.
argument-hint: "<Spec-Issue> | Zerlegung <Spec-Issue> Runde <1|2>"
---

<!-- regel:einleitung -->
# challenge: frischer Blick auf Spec und Zerlegung

Ziel: Fehler fallen auf, bevor gebaut wird. Der Prüfer kennt nur das Ergebnis der Planung, nicht das Gespräch, aus dem es entstand; so sieht er, was im Text fehlt, statt es aus dem Gedächtnis zu ergänzen.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- **Spec-Prüfung:** nach `/slickfab:spec`, bevor zerlegt wird. Prüft Produkt und Baubarkeit.
- **Zerlegungsprüfung:** aus `/slickfab:tickets` heraus, bevor der Mensch die Ticket-Liste sieht. Prüft, ob die Tickets die Spec vollständig und sauber abdecken.
- Nicht für Code-Review; dafür gibt es den Review-Schritt.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Voraussetzung prüfen

- **Spec-Prüfung** braucht eine Spec: als Spec-Issue (Argument) oder, ohne Tracker, als Text im Argument. Gibt es keine, hör auf und empfiehl `/slickfab:spec`.
- **Zerlegungsprüfung** braucht die Spec, die nummerierte Ticket-Liste und die Runde (1 oder 2, ohne Angabe 1). In Runde 2 auch die Zahl der Befunde aus Runde 1. Fehlt die Liste, empfiehl `/slickfab:tickets`.
- Lies `.slickfab/config` und das Spec-Issue samt Kommentaren. Fehlt die Konfiguration oder ist der Tracker nicht erreichbar, sag das; du kannst trotzdem prüfen, wenn die Spec als Text vorliegt, aber das Ergebnis nur im Chat zeigen.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:frischen-blick-herstellen -->
### 2. Frischen Blick herstellen

Der Prüfer bekommt nur die Spec (bei der Zerlegungsprüfung: Spec und Ticket-Liste) und darf das Repo lesen, aber nicht das Planungsgespräch.

- Läuft in dieser Session schon Planung (`grill`, `spec`, `tickets` oder ein Gespräch über das Feature), starte einen frischen Sub-Agent. Gib ihm wörtlich nur die Spec bzw. Spec und Liste, den passenden Prüfauftrag aus Schritt 3 oder 4 und das Ausgabeformat. Keine Zusammenfassung des Gesprächs, keine Begründungen, keine eigene Einschätzung.
- Ist die Session frisch (nur dieser Aufruf), prüfst du selbst.
- Kannst du keinen Sub-Agent starten, sag das und empfiehl, `/slickfab:challenge <Spec-Issue>` in einer neuen Session aufzurufen. Prüf nicht selbst in einer Session, die das Gespräch kennt.
<!-- /regel:frischen-blick-herstellen -->

<!-- regel:spec-pruefung -->
### 3. Spec-Prüfung (Auftrag an den Prüfer)

Lies die Spec und dann im Repo, was es schon gibt (README, Feature-Doku, ADRs, betroffene Stellen).

**A. Produkt.** Prüf aus Nutzersicht, nicht die Technik:

- Wer hat das Problem wirklich, und woran merkt man, dass es gelöst ist?
- Was ist die kleinste Version mit demselben Nutzen? Was kann raus?
- Was gibt es schon, das dasselbe leistet oder dem widerspricht?
- Welche Annahme ist am wackligsten, und was passiert, wenn sie falsch ist?
- Passt es zu früheren Entscheidungen im Repo?

Schreib höchstens 7 Einwände, die wichtigsten zuerst, je mit einem Satz Begründung und einer Empfehlung: streichen, ändern oder behalten. Hast du keinen echten Einwand, sag das; erfinde keinen. Dann ein Urteil, genau eines: `bauen`, `kleiner bauen` oder `nicht bauen`, mit dem einen Grund, der es trägt.

**B. Baubarkeit.** Stell dir vor, du sollst danach Tickets schneiden und bauen, ohne den Autor fragen zu können. Sammle jede Stelle, an der du raten müsstest, und sortiere sie in drei Stapel:

1. **schon beantwortet** (steht in der Spec oder im Repo; streichen),
2. **Kleinkram** (ein Umsetzer kann es selbst entscheiden, ein falscher Griff ist billig),
3. **nur der Mensch** (ein falscher Griff ändert den Plan).

Berichte Stapel 3 vollständig, je Frage mit einem Satz, warum die Antwort den Plan ändert, die wichtigste zuerst. Für Stapel 1 und 2 genügt die Anzahl.
<!-- /regel:spec-pruefung -->

<!-- regel:zerlegungspruefung -->
### 4. Zerlegungsprüfung (Auftrag an den Prüfer)

Die Zerlegung wird in höchstens 2 Runden geprüft. Prüf die Ticket-Liste gegen die Spec:

- **Abdeckung:** Jeder Punkt aus „Muss wahr sein“ und jede User Story hat ein Ticket, das ihn liefert.
- **Kritische Verbindungen:** Jede ist in einem Ticket verdrahtet und geprüft, nicht nur auf beiden Seiten gebaut.
- **Reihenfolge:** Das erste Ticket ist ein Tracer und blockiert alle übrigen; keine Zyklen; Tickets, die dieselbe Datei nennen, haben eine Blockiert-Relation.
- **Schnitt:** Jedes Ticket ist eine durchgehende Scheibe, für sich vorführbar und in einer frischen Session baubar; ein „und“ im Titel heißt meist zwei Tickets.
- **Kriterien:** Jedes Kriterium nennt, was es widerlegt, und wäre am heutigen Stand falsch.
- **Stille Kürzung:** Nichts aus der Spec ist verkleinert oder vertagt, ohne dass es dasteht; keine Formulierungen wie „v1“, „vereinfacht“, „Platzhalter“, „wird später verdrahtet“.

Jeder Befund nennt die **Eigenschaft, die gelten muss** (bindend), den **Beleg**, wo sie verletzt ist, und **einen möglichen Weg** dorthin (nur Beispiel, nicht bindend). Zähl die Befunde.

Auswertung durch den Aufrufer:

- **Runde 1:** keine Befunde → bestanden. Sonst überarbeitet `tickets` die Liste und ruft Runde 2 mit der Befundzahl aus Runde 1.
- **Runde 2:** keine Befunde → bestanden. Wenn die Zahl der Befunde gegenüber Runde 1 nicht sinkt, wird abgebrochen: Die Überarbeitung dreht sich im Kreis. Ist sie gesunken, aber nicht null, ist die Prüfung ebenfalls zu Ende. In beiden Fällen gehen die offenen Befunde an den Menschen, der entscheidet.
- Es gibt keine dritte Runde. Wirst du mit Runde 3 aufgerufen, prüfst du nicht, sondern gibst die letzten Befunde an den Menschen weiter. Die holst du wörtlich aus dem Ergebnis von Runde 2 am Spec-Issue (Kommentare) und nennst sie im Ergebnis; ein Verweis darauf reicht nicht. Steht dort keins, sagst du das. Das Ergebnis endet mit `SLICKFAB-STATUS: NEEDS_CONTEXT`: Ohne Entscheidung des Menschen geht es nicht weiter.
<!-- /regel:zerlegungspruefung -->

<!-- regel:festhalten -->
### 5. Festhalten

- **Spec-Prüfung:** Kommentar am Spec-Issue mit Einwänden, Urteil und Stapel 3, letzte Zeile die Marker-Zeile nach Tracker-Vertrag (`DONE`, oder `DONE_WITH_CONCERNS`, wenn das Urteil nicht `bauen` ist oder Stapel 3 nicht leer). Du änderst die Spec nicht selbst; über Einwände entscheidet der Mensch.
- **Zerlegungsprüfung:** Ergebnis zurück an `tickets` bzw. in den Chat; im Tracker entsteht dabei nichts.
- Ohne Tracker: alles im Chat, mit dem Hinweis, dass nichts gespeichert ist. Keine Datei im Repo als Ersatz.
<!-- /regel:festhalten -->

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
Spec-Prüfung:

```
## Ergebnis challenge

**Urteil:** bauen | kleiner bauen | nicht bauen — <tragender Grund>
**Einwände:** <1–7, je Empfehlung> (oder „keine echten Einwände“)
**Nur der Mensch:** <Fragen> (Stapel 1: <n>, Stapel 2: <n>)
**Kommentar:** <Link> oder „nur im Chat“

Nächster Schritt: `/slickfab:spec <Spec-Issue>` (Entscheidungen einarbeiten) oder `/slickfab:tickets <Spec-Issue>`
```

Zerlegungsprüfung: Runde, Zahl der Befunde, die Befunde, und „bestanden“, „Runde 2 nötig“ oder „an den Menschen“; Nächster Schritt: `/slickfab:tickets` (weiter mit der Bestätigung der Liste).
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
Nach der Spec-Prüfung entscheidet der Mensch über die Einwände und Stapel 3. Ändert sich etwas, `/slickfab:spec <Spec-Issue>` zum Einarbeiten; sonst `/slickfab:tickets <Spec-Issue>`. Lautet das Urteil `nicht bauen` und der Mensch stimmt zu, endet die Planung hier: Der Mensch setzt die Spec auf `Canceled`. Nach der Zerlegungsprüfung geht es in `/slickfab:tickets` weiter.
<!-- /regel:naechster-schritt -->
