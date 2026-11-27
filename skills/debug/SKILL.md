---
name: debug
description: Verwenden, wenn etwas kaputt ist, einen Fehler wirft, falsch rechnet oder langsam ist und die Ursache unbekannt ist, oder wenn jemand „debug das“ sagt.
argument-hint: "<Fehlerbeschreibung oder Ticket>"
---

<!-- regel:einleitung -->
# debug: Fehler mit roter Schleife finden

Ziel: Die Ursache eines Fehlers belegt finden, beheben und mit einem Regressionstest festnageln. Raten ist nicht erlaubt; jede Aussage stützt sich auf einen Lauf.

Antworte in der Sprache des Menschen. Projektkonfiguration und Marker stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Wenn ein Verhalten falsch ist und die Ursache nicht offensichtlich ist.
- Wenn `/slickfab:implement` nach drei Fix-Versuchen an derselben Stelle gestoppt hat.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Voraussetzung prüfen

- Du brauchst die Beschreibung des Fehlers: was passiert, was stattdessen passieren soll.
- Ein Ticket ist nicht nötig. Gibt es eins, liest du es mit allen Kommentaren. Gibt es ein Ticket und ist der Tracker nicht erreichbar, gilt der Vertrag „Zugang“: melden und aufhören, keine Datei als Ersatz.
- Lies `.slickfab/config` und, falls vorhanden, `.slickrails/config.sh`, beide nur als Text (Regeln im Vertrag). Prüfbefehle nimmst du nur aus `.slickrails/config.sh` oder `.slickfab/config`; du rätst keine aus `package.json`, `Makefile` oder der Gewohnheit. Fehlt ein Prüfbefehl, sagst du, welcher, und dass du ihn nicht ausführen kannst. Der rote Befehl aus Schritt 2 ist kein Prüfbefehl: Den baust du selbst, für genau diesen Fehler.
<!-- /regel:voraussetzung -->

<!-- regel:rote-schleife -->
### 2. Rote Schleife bauen

Das ist der Kern des Schritts. Bau einen Befehl, der auf genau diesen Fehler rot wird und grün, sobald er behoben ist. Mögliche Formen, ungefähr in dieser Reihenfolge: ein fehlschlagender Test an der Stelle, die den Fehler erreicht; ein `curl` gegen einen laufenden Dienst; ein CLI-Aufruf mit fester Eingabe, verglichen mit der erwarteten Ausgabe; ein Browser-Skript; ein abgespielter mitgeschnittener Aufruf; ein kleines Wegwerf-Gerüst um den betroffenen Pfad; bei „manchmal falsch“ eine Schleife über viele Eingaben; bei „ging früher“ ein `git bisect run` mit diesem Befehl.

Fertig ist die Schleife, wenn du **einen** Befehl nennen kannst, den du schon einmal ausgeführt hast (Befehl und Ausgabe zeigen, Geheimnisse durch `<REDACTED>` ersetzt), und der

- genau das Symptom prüft, das gemeldet wurde, nicht „läuft ohne Fehler“,
- bei jedem Lauf dasselbe Urteil liefert (bei sporadischen Fehlern: eine hohe, feste Trefferquote),
- in Sekunden läuft und ohne Menschen auskommt.

Ohne einen Befehl, der auf genau diesen Fehler rot wird, keine Ursachensuche und keine Korrektur. Ertappst du dich dabei, Code zu lesen, um eine Theorie zu bauen, bevor dieser Befehl existiert: zurück an den Anfang dieses Abschnitts.

Gelingt dir kein roter Befehl, hörst du auf: Du nennst, was du versucht hast, und fragst nach dem, was fehlt. Du schlägst keine Korrektur vor. Was fehlen kann: Zugang zu der Umgebung, in der es passiert; ein mitgeschnittenes Beispiel (Log, Anfrage, Datei); die Erlaubnis für vorübergehende Messpunkte. Status `NEEDS_CONTEXT`. Vor dem Aufhören gilt Schritt 7.

| Ausrede | Realität |
|---|---|
| „Die Ursache ist offensichtlich, ich sehe es im Code.“ | Dann ist der rote Befehl in zwei Minuten gebaut und beweist es. Ohne ihn weißt du nach dem Fix nicht, ob er wirkt. |
| „Ich kann es nicht nachstellen, aber diese Änderung schadet nicht.“ | Eine Korrektur ohne roten Befehl ist geraten. Melden, nicht raten. |
<!-- /regel:rote-schleife -->

<!-- regel:nachstellen-und-minimieren -->
### 3. Nachstellen und minimieren

Lass den Befehl laufen und vergleich die Ausgabe mit der Meldung: Ist es derselbe Fehler, nicht ein benachbarter? Dann verkleinere den Fall Stück für Stück (Eingaben, Aufrufer, Konfiguration, Daten), nach jedem Schnitt neu laufen lassen, bis jedes übrige Teil nötig ist, damit es rot bleibt.
<!-- /regel:nachstellen-und-minimieren -->

<!-- regel:hypothesen -->
### 4. Hypothesen

Schreib 3 bis 5 Hypothesen auf, nach Wahrscheinlichkeit geordnet, bevor du eine prüfst. Jede muss widerlegbar sein, in der Form: „Wenn <X> die Ursache ist, dann macht <Änderung Y> den Fehler weg und <Änderung Z> schlimmer.“ Kannst du die Vorhersage nicht nennen, ist es keine Hypothese. Zeig die Liste dem Menschen, falls er da ist; er weiß oft, was schon ausgeschlossen ist. Warte nicht auf ihn.

Führ zwei Listen und hänge nur an: **Ausgeschlossen** (Hypothese, Beleg) und **Belege** (Befund, Befehl). So prüfst du keine Hypothese zweimal.
<!-- /regel:hypothesen -->

<!-- regel:messen -->
### 5. Messen

Prüf die Hypothesen der Reihe nach. Jede Messung gehört zu einer Vorhersage aus Schritt 4; du änderst eine Sache zur Zeit. Am liebsten mit Debugger oder REPL; sonst gezielte Ausgaben an den Stellen, die zwei Hypothesen unterscheiden, nie „alles loggen und suchen“.

Wähl am Anfang einen kurzen Tag aus vier Zeichen, etwa `[DEBUG-a4f2]`, im Folgenden `[DEBUG-<tag>]`. Jeder Messpunkt trägt den Tag, ohne Ausnahme. Nur so findest du am Ende alle wieder.

Bei Performance-Fehlern misst du zuerst eine Ausgangszahl (Zeitmessung, Profiler, Abfrageplan) und vergleichst danach; Logs helfen da selten.
<!-- /regel:messen -->

<!-- regel:regressionstest -->
### 6. Regressionstest und Korrektur

Mach aus dem verkleinerten Fall einen Test an einer Teststelle, die den Fehler so trifft, wie er beim Aufrufer entsteht. Lass ihn laufen: Er muss rot sein, mit dem gemeldeten Symptom (Befehl und Ausgabe). Dann die Korrektur, und zwar die kleinste, die die belegte Ursache behebt. Lass den Test und den Befehl aus Schritt 2 laufen: beide grün (Befehl und Ausgabe). Prüfbefehle aus der Konfiguration laufen danach vollständig.

Fehlt eine Teststelle, die den Fehler so trifft, wie er entsteht, ist das ein eigener Befund: Du schreibst keinen flachen Test, der nur so tut, sondern nennst, welche Teststelle fehlt und warum. Der rote Befehl aus Schritt 2 bleibt dann der Nachweis.

Scheitert die Korrektur dreimal, ist meist die Ursache falsch verstanden: zurück zu Schritt 4 mit den neuen Belegen, nicht ein vierter Versuch an derselben Stelle. Zu Schritt 4 zurück gehst du höchstens einmal. Scheitern danach wieder drei Korrekturen, hörst du auf und meldest `BLOCKED` mit den Hypothesen, Belegen und Versuchen; dann entscheidet der Mensch.

Für die Korrektur gelten dieselben Grenzen wie in `/slickfab:implement`:

- **Stopp-Liste:** Berührt die Ursache oder die Korrektur einen dieser Punkte: Auth und Berechtigungen, destruktive Migrationen, Zahlungen, Löschungen von Daten, Deploys, Secrets, alles, was ein Revert nicht zurückholt, dann hörst du vor der Korrektur auf und meldest `BLOCKED` mit Ursache, Beleg und der Korrektur, die du vorschlägst. Gebaut wird erst mit einer Freigabe am Ticket.
- **Bestehende Tests:** kein Überspringen, keine gelöschten oder gelockerten Assertions, keine gesenkten Schwellen. Steht ein bestehender Test im Weg, änderst du ihn nicht, sondern hörst auf und meldest ihn (Status `BLOCKED`), auch wenn du sicher bist, dass er falsch ist.
<!-- /regel:regressionstest -->

<!-- regel:aufraeumen -->
### 7. Aufräumen

- Entferne jeden Messpunkt und prüf es mit `grep -rn "DEBUG-<tag>" .` (mit deinem Tag). Solange der Tag irgendwo steht, bist du nicht fertig.
- Lösch Wegwerf-Gerüste und Hilfsdateien, die nicht zum Regressionstest gehören.
- Lass den Befehl aus Schritt 2 gegen den ursprünglichen, nicht verkleinerten Fall laufen: grün.

Hörst du vor Schritt 7 auf (`NEEDS_CONTEXT`, `BLOCKED`), räumst du trotzdem auf: Messpunkte und Wegwerf-Gerüste, auch außerhalb des Repos, löschst du, oder du nennst im Ergebnis jeden Pfad, der bleibt, und warum.
<!-- /regel:aufraeumen -->

<!-- regel:warum-nicht-gefangen -->
### 8. Warum nicht gefangen

Beantworte zwei Fragen und schreib sie ins Ergebnis, in den Commit und, falls es ein Ticket gibt, als Kommentar dorthin:

- **Warum nicht gefangen:** Welche Prüfung hätte den Fehler finden müssen und warum hat sie es nicht? (kein Test an der Stelle, Test prüfte etwas anderes, Fall nicht bedacht, Mock verdeckte ihn)
- **Wiederholungs-Sperre:** Was verhindert, dass ein Fehler dieser Art wiederkommt? Der Regressionstest gilt nur für diesen Fall; nenne eine Prüfung oder Regel für die ganze Art und schlag sie als Vorschlag vor (für `/slickfab:retro`), statt sie ungefragt einzubauen.

Dann committest du (die Nachricht nennt die bestätigte Hypothese, damit der Nächste daraus lernt). Gehört der Fehler zu einem Ticket, das gerade gebaut wird, geht es dort weiter; sonst öffnest du einen Pull Request gegen den Hauptzweig, nicht mergen.
<!-- /regel:warum-nicht-gefangen -->

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
## Ergebnis debug

**Fehler:** <ein Satz>
**Roter Befehl:** `<Befehl>` → vorher <rot>, nachher <grün>
**Ursache:** <die bestätigte Hypothese, mit Beleg>
**Ausgeschlossen:** <Hypothesen mit Beleg>
**Regressionstest:** <Test> | fehlt, Befund: <welche Teststelle fehlt>
**Debug-Tag entfernt:** `grep -rn "DEBUG-<tag>" .` → kein Treffer
**Liegen geblieben:** <Pfad und Grund> oder „nichts“
**Warum nicht gefangen:** <…>
**Wiederholungs-Sperre:** <Vorschlag>

Nächster Schritt: `/slickfab:review <Pull Request>` in einer frischen Session

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT>
```

Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei `BLOCKED` oder `NEEDS_CONTEXT`. Ohne roten Befehl lautet sie `Nächster Schritt: /slickfab:debug <Fehler>, sobald <was fehlt> da ist`.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:review <Pull Request>` in einer frischen Session. Ist der Fix Teil eines Tickets, das noch nicht fertig ist: zurück zu `/slickfab:implement <Ticket>`.
<!-- /regel:naechster-schritt -->
