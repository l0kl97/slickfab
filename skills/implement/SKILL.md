---
name: implement
description: Verwenden, wenn ein freigegebenes Ticket gebaut werden soll, oder wenn jemand „bau das Ticket“ oder „setz EX-123 um“ sagt.
argument-hint: "<Ticket>"
---

<!-- regel:einleitung -->
# implement: ein Ticket per TDD bis zum Pull Request

Ziel: Ein Pull Request, der genau das Ticket erfüllt und für jedes Kriterium belegt, dass der Test erst rot und dann grün war. Nicht mehr, nicht weniger.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Wenn ein Ticket auf `Todo` steht (der Mensch hat es freigegeben) und gebaut werden soll.
- Nicht ohne Ticket; nicht für die Fehlersuche ohne bekannte Ursache (dafür `/slickfab:debug`).
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Voraussetzung prüfen

- Du brauchst das Ticket (Argument). Lies es mit allen Kommentaren und die Spec, deren Sub-Issue es ist. Gibt es schon einen Pull Request zum Ticket, liest du auch dessen Review-Kommentare; mit denen am Ticket zeigen sie, welche Lücken ein Review schon gefunden hat.
- Lies `.slickfab/config` und, falls vorhanden, `.slickrails/config.sh`, beide nur als Text (Regeln im Vertrag). Fehlt die Konfiguration oder ist der Tracker nicht erreichbar, hör hier auf und melde genau das.
- Prüfbefehle nimmst du nur aus `.slickrails/config.sh` oder `.slickfab/config`; du rätst keine aus `package.json`, `Makefile` oder der Gewohnheit. Fehlt ein Prüfbefehl, sagst du, welcher, und dass du ihn nicht ausführen kannst. Ohne `CHECK_TEST` kannst du nicht belegen, dass die ganze Suite grün ist; dann endet der Schritt höchstens mit `DONE_WITH_CONCERNS`.
- Steht das Ticket nicht auf `Todo` oder `In Progress`, ist es nicht zum Bauen freigegeben: hör auf und sag das.
- Sind im Arbeitsbaum fremde Änderungen offen, hör auf und sag es. Du verschiebst oder versteckst keine fremde Arbeit.
- **Ausgangslage:** Lass `CHECK_TEST` einmal vor der ersten Änderung laufen und halte Befehl und Ergebnis fest. Ist es schon rot, meldest du das, bevor du baust; fremde rote Tests reparierst du nicht nebenbei.
- Prüf vor dem ersten Test, ob das Ticket die Stopp-Liste (Schritt 5) berührt.
- Setz das Ticket auf `In Progress`.
<!-- /regel:voraussetzung -->

<!-- regel:kriterien-in-tests-uebersetzen -->
### 2. Kriterien in Tests übersetzen

Geh die Akzeptanzkriterien des Tickets der Reihe nach durch, eines nach dem anderen. Für jedes überlegst du:

- **Teststelle:** Über welche öffentliche Schnittstelle zeigt sich das Verhalten (die Teststellen der Spec)? Tests prüfen Verhalten von außen, keine privaten Methoden, keine Aufrufzähler, kein direkter Blick in die Datenbank, wenn es eine Schnittstelle dafür gibt. Ein Test, der bei einem Umbau ohne Verhaltensänderung bricht, ist falsch geschnitten.
- **Erwarteter Wert:** aus der Spec, dem Ticket oder einem von Hand durchgerechneten Beispiel, nie aus derselben Logik wie der Code.
- **Gegenprobe:** Nenne die Änderung am Produktionscode, die diesen Test rot machen würde. Fällt dir keine ein, prüft der Test nichts.
- **Fehlerfälle** (ungültige Eingaben, Fehlerantworten, Grenzwerte) gehören dazu. Gemockt wird nur an Systemgrenzen (fremde APIs, Mail, Zeit, Zufall), nie eigener Code.

Das Review (`/slickfab:review`) prüft mit einer Mutationsprobe jedes Verhalten im Diff, nicht nur die Kriterien. Deshalb gilt für dich dieselbe Regel: Jedes Verhalten, das dein Diff einführt oder ändert, braucht einen Test, auch wenn das Ticket es nicht nennt. Eine bekannte Lücke aus einem früheren Review-Kommentar am Ticket oder am Pull Request schließt du mit rotem und grünem Lauf, oder du begründest im Pull Request unter „Nicht angefasst“ ausdrücklich, warum sie offen bleibt.

Schreib nicht alle Tests vorab und bau nichts auf Vorrat.
<!-- /regel:kriterien-in-tests-uebersetzen -->

<!-- regel:rot-gruen -->
### 3. Je Kriterium: rot, dann grün

1. **Rot:** Schreib genau den Test für dieses Kriterium und lass ihn laufen. Halte Befehl und Ausgabe fest. Er muss aus dem erwarteten Grund rot sein (die Assertion schlägt fehl, weil das Verhalten fehlt), nicht wegen eines Tippfehlers oder Imports. Ist er sofort grün, ist das Kriterium schon erfüllt oder der Test prüft nichts: klär das, bevor du weitermachst.
2. **Grün:** Schreib genau so viel Produktionscode, dass dieser Test besteht, und lass ihn wieder laufen. Halte Befehl und Ausgabe fest.
3. Zwischendurch Typprüfung (`CHECK_TYPECHECK`, falls vorhanden) und die betroffene Testdatei.

Ohne roten Lauf kein Produktionscode für dieses Kriterium. Aufräumen und Umbauen gehören nicht in diese Schleife; was dir auffällt, nennst du im Pull Request unter „Bedenken“.

Ein Fix-Versuch ist eine Änderung am Produktionscode, nach der derselbe Test wieder rot ist. Zähl sie sichtbar mit („Versuch 1/3“). Nach 3 gescheiterten Fix-Versuchen an derselben Stelle hörst du auf. Einen vierten Versuch startest du nicht. Du meldest `BLOCKED` mit den drei Versuchen und ihren Ausgaben und empfiehlst `/slickfab:debug` in einer frischen Session; drei gescheiterte Versuche heißen meist, dass die Annahme über die Ursache falsch ist, nicht, dass ein vierter Einfall fehlt.

Bestehende Tests schwächst du nicht ab, um grün zu werden: kein Überspringen (`skip`, `only`, `xfail`, auskommentiert), keine gelöschten oder gelockerten Assertions, keine gesenkten Schwellen (Abdeckung, Zeitlimits, Toleranzen), keine neuen Unterdrückungen (`@ts-ignore`, `eslint-disable`, `noqa`). Steht ein bestehender Test im Weg, änderst du ihn nicht, sondern hörst auf und meldest ihn: welcher Test, was er erwartet, was das Ticket verlangt, worin sie sich widersprechen. Status `BLOCKED`; ob der Test oder das Ticket falsch ist, entscheidet der Mensch. Das gilt auch, wenn das Ticket das Verhalten, das der Test festhält, ausdrücklich ändern will: Ob ein bestehender Test fallen darf, steht erst fest, wenn der Mensch es am Ticket festgehalten hat. Mit dieser Freigabe änderst du genau diesen Test und nennst ihn unter „Änderungen“.

| Ausrede | Realität |
|---|---|
| „Das Ticket verlangt doch genau dieses neue Verhalten.“ | Der Test hält eine Entscheidung fest, die jemand früher getroffen hat. Ob sie nicht mehr gilt, entscheidet der Mensch, nicht der Ticket-Text und nicht du. |
| „Der alte Test ist sowieso falsch.“ | Dann ist das ein Befund für den Menschen. Ein Test, den der Umsetzer passend macht, prüft nur noch den Umsetzer. |
| „Der Test ist flaky, ich setze ihn kurz auf skip.“ | Ein übersprungener Test ist ein gelöschter Test, den niemand bemerkt. Melden. |
| „Die Schwelle war eh zu streng.“ | Wer die Schwelle senkt, entscheidet über Qualität; das ist nicht Teil des Tickets. |
<!-- /regel:rot-gruen -->

<!-- regel:abweichungen -->
### 4. Abweichungen

Beim Bauen findest du Arbeit, die nicht im Ticket steht. So gehst du damit um:

- **Regel 1, Fehler:** Bestehender Code tut nicht, was er soll, und hindert dein Kriterium (falsche Abfrage, Logikfehler, kaputte Prüfung). Du behebst ihn mit eigenem rotem und grünem Lauf.
- **Regel 2, fehlende kritische Funktion:** Ohne sie wäre dein Kriterium nicht korrekt oder nicht sicher (fehlende Fehlerbehandlung, fehlende Eingabeprüfung, fehlendes Timeout an einem externen Aufruf). Du ergänzt sie mit Test.
- **Regel 3, Blocker:** Etwas hält dich mechanisch auf (falscher Typ, kaputter Import, fehlende Testkonfiguration). Du räumst es weg.
- **Regel 4, Architekturfrage:** Hier hörst du auf und meldest `BLOCKED` mit Begründung. Architekturfrage heißt: neue Tabelle oder Schnittstelle, die das Ticket nicht nennt, ein anderes Muster als das bestehende, eine neue Abhängigkeit, eine Änderung, die andere Tickets mitändern müssten. Du nennst die Frage, die Optionen und deine Empfehlung.

Was du nach Regel 1–3 tust, nennst du im Pull Request unter „Änderungen“ als `[Regel N] was, warum`, und schreibst je Entscheidung, die ein Mensch anders hätte treffen können, ein Ruling am Ticket. Die Stopp-Liste geht den Regeln 1–3 vor.
<!-- /regel:abweichungen -->

<!-- regel:stopp-liste -->
### 5. Stopp-Liste

Prüf vor jeder Änderung, ob sie einen dieser Punkte berührt:

- Auth und Berechtigungen (Anmeldung, Rollen, Zugriffsprüfungen),
- destruktive Migrationen (Spalte oder Tabelle löschen, Typ verengen, Daten umschreiben),
- Zahlungen,
- Löschungen von Daten,
- Deploys und alles, was live ausrollt,
- Secrets (anlegen, ändern, ausgeben, in Dateien schreiben),
- alles, was ein Revert nicht zurückholt (verschickte Mails, Aufrufe fremder Systeme mit Wirkung, veröffentlichte Pakete).

Berührt das Ticket oder dein Weg dorthin einen dieser Punkte, hörst du auf, bevor du ihn baust, und meldest `BLOCKED` mit Begründung: welcher Punkt, wo, was du bauen würdest, was ein Fehler kosten würde. Das gilt auch, wenn das Ticket es ausdrücklich verlangt; die Freigabe dafür gibt ein Mensch für genau diesen Punkt, und sie steht danach am Ticket. Mit dieser Freigabe baust du weiter und setzt `door:one-way`.

Beim Anhalten (Regel 4, Stopp-Liste, Test im Weg) schreibst du einen Kommentar am Ticket mit Grund und bisherigem Stand und setzt `slickfab:needs-human`. Was schon gebaut ist, bleibt auf dem Branch.
<!-- /regel:stopp-liste -->

<!-- regel:pruefungen -->
### 6. Ganze Suite und Prüfungen

Wenn alle Kriterien grün sind, lässt du die ganze Suite laufen (`CHECK_TEST`), dazu `CHECK_TYPECHECK` und `CHECK_LINT`, soweit vorhanden. Halte Befehl und Ergebnis fest. Rot heißt nicht fertig. Hooks umgehst du nie (`--no-verify` und Ähnliches), außer der Mensch hat es für genau diesen Push am Ticket festgehalten; dann steht der Grund im Commit. Eine Zusage im Gespräch reicht nicht. Blockiert ein Hook mit Befunden, behebst du die Befunde.

Verlangt das Repo (etwa `CLAUDE.md`) vor dem Pull Request ein Review, machst du es jetzt. Ein Pflicht-Review vor dem Pull Request (etwa `/security-review`) ist ein Zwischenschritt: Danach machst du mit Commit, Push und Pull Request weiter. Echte Befunde behebst du mit rotem und grünem Lauf, den Rest nennst du unter „Bedenken“.
<!-- /regel:pruefungen -->

<!-- regel:pull-request -->
### 7. Pull Request

Committe mit einer Nachricht, die sagt, warum und was. Push den Branch und öffne einen Pull Request gegen den Hauptzweig. Nicht mergen. Der Text hat diese Form:

```markdown
<Ticket-ID>: <Titel>

## Änderungen

- <was sich für Nutzer oder Aufrufer ändert, je Punkt ein Satz>
- [x] <Akzeptanzkriterium aus dem Ticket, abgehakt, wenn belegt>
- Abweichungen: <[Regel 1–3] was, warum> oder „keine“

## Nicht angefasst

- <was nah dran war, aber bewusst nicht geändert wurde, und warum> oder „keine“

## Bedenken

- <was dir aufgefallen ist und nicht zum Ticket gehört, offene Risiken> oder „keine“

## Door

`one-way` | `two-way`: <ein Satz, warum; `one-way`, wenn ein Revert nicht alles zurückholt>

## Blast Radius

<ein Wort oder kurzer Satz: wer oder was betroffen ist, wenn es schiefgeht>

## Nachweise

Ausgangslage: `<CHECK_TEST>` → <Ergebnis vor der ersten Änderung>

- K1 <Kriterium in Kurzform>
  - rot: `<Befehl>` → <Ausgabe, gekürzt auf die entscheidende Zeile>
  - grün: `<Befehl>` → <Ausgabe>
- K2 …

Ganze Suite: `<CHECK_TEST>` → <Ergebnis>
```

Fehlt für ein Kriterium der rote Lauf, ist der Pull Request nicht fertig. Jeder Abschnitt steht im Text, auch wenn er leer ist; dann steht darunter „keine“. Ein leerer Abschnitt sagt dem Prüfer, dass du daran gedacht hast; ein fehlender sagt ihm nichts.
<!-- /regel:pull-request -->

<!-- regel:abschluss -->
### 8. Abschluss

Setz das Ticket auf `In Review`, sobald der Pull Request offen ist, und schreib einen Kommentar am Ticket mit dem Link. Der Schritt endet erst mit dem „Ergebnis implement“ (unten); ein Review-Bericht, eine Testausgabe oder ein offener Pull Request ohne dieses Ergebnis ist kein Ende.
<!-- /regel:abschluss -->

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

### Tracker: Rulings

<!-- vertrag:rulings -->
If an agent decides something itself that a human could have decided differently, it immediately writes a comment on the affected issue in exactly this form:

`Ruling: what — why — cost if wrong`

Example: `Ruling: date stored as ISO string — that is how the existing API reads it — a migration of the column if time zones become necessary`

Rulings are collected and presented to the human at the end; they do not replace asking back on product questions or hard-to-reverse decisions.

Answer in the user's language.
<!-- /vertrag:rulings -->

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
## Ergebnis implement

**Ticket:** <ID> (jetzt `In Review`)
**Pull Request:** <Link>
**Kriterien:** <n> von <n> mit rotem und grünem Lauf belegt
**Ganze Suite:** `<CHECK_TEST>` → <Ergebnis>
**Abweichungen:** <[Regel N] …> oder „keine“
**Door:** `one-way` | `two-way`

Nächster Schritt: `/slickfab:review <Pull Request>` in einer frischen Session

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT>
```

Bei `BLOCKED` oder `NEEDS_CONTEXT` steht statt Pull Request und Kriterien der Grund: welcher Punkt der Stopp-Liste, welche Architekturfrage, welcher Test im Weg oder welche drei Fix-Versuche, und was der Mensch entscheiden muss. Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei `BLOCKED` oder `NEEDS_CONTEXT`. Dann lautet sie `Nächster Schritt: /slickfab:implement <Ticket>, sobald die Entscheidung am Ticket steht` (bei drei gescheiterten Versuchen: `/slickfab:debug`).
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:review <Pull Request>` in einer frischen Session, damit der Prüfer deinen Bericht nicht kennt. Bei `BLOCKED`: der Mensch entscheidet, danach erneut `/slickfab:implement <Ticket>`.
<!-- /regel:naechster-schritt -->
