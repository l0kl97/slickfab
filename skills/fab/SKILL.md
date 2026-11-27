---
name: fab
description: Verwenden, wenn unklar ist, wo ein Vorhaben im slickfab-Prozess steht und welcher Schritt als Nächstes kommt, oder wenn jemand „wo stehe ich?“, „was jetzt?“ oder „fab“ sagt.
argument-hint: "[Spec-Issue | Ticket | Thema]"
---

<!-- regel:einleitung -->
# fab: Wegweiser

Ziel: Du sagst, wo das Vorhaben steht, welcher Schritt als Nächstes kommt und ob er im selben Gespräch oder in einer frischen Session läuft. Den Stand liest du aus dem Tracker und dem Repo, nie aus dem Gedächtnis und nie aus einer Zustandsdatei.

Du liest nur. Du schreibst keine Datei, keinen Kommentar, kein Label und keinen Status, auch nicht `.slickfab/config`. Was fehlt, nennst du; anlegen tut es der Mensch.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Am Anfang, wenn noch nichts da ist: fab nennt den ersten Schritt.
- Zwischen zwei Schritten oder nach einer Pause, wenn unklar ist, was als Nächstes kommt.
- Nicht als Ersatz für einen Schritt: fab führt keinen Schritt aus, es nennt ihn.
<!-- /regel:wann -->

## Ablauf

<!-- regel:repo-lesen -->
### 1. Repo lesen

Nur lesende Befehle, jeder mit Ergebnis festgehalten:

- `git rev-parse --show-toplevel`, `git branch --show-current`, `git status --short`, `git remote -v`.
- Ob `.slickfab/config` existiert und die Pflichtwerte hat (Format im Vertrag), und ob `.slickrails/config.sh` existiert. Beide liest du als Text.
- Offene Pull Requests mit `gh pr list --state open --json number,title,headRefName,url`. Zu jedem PR, der ein Ticket nennt (Ticket-ID im Titel oder Branch-Namen), liest du mit `gh pr view <PR> --json commits,comments,reviews` die letzte `SLICKFAB-VERDICT:`-Zeile mit Zeitpunkt und ob danach noch Commits kamen (Committer-Datum).

Scheitert ein Befehl (kein Git-Repo, `gh` fehlt oder ist nicht angemeldet, kein Remote), notierst du das als Lücke mit der Fehlermeldung und machst mit dem Rest weiter. Was du nicht lesen konntest, gilt als unbekannt, nicht als leer.
<!-- /regel:repo-lesen -->

<!-- regel:tracker-lesen -->
### 2. Tracker lesen

Nur wenn `.slickfab/config` vollständig ist und der Tracker erreichbar ist (Linear-Werkzeuge der Session, in Claude Code per Werkzeugsuche `+linear` laden). Ist ein Spec-Issue oder Ticket als Argument genannt, liest du das; sonst im Projekt aus der Konfiguration die offenen Issues mit Titel `Spec: …` und ihre Sub-Issues:

- Status des Spec-Issues, Status jedes Tickets und Labels (`slickfab:needs-human`, `slickfab:rework`, `slickfab:replan`, `slickfab:ready`),
- Relationen „blockiert von“,
- die Kommentare von `challenge`, `verify` (mit Status `bestanden`, `Lücken gefunden` oder `Mensch nötig`), Übergaben (`handoff`) und Überarbeitungen der Spec (erste Zeile `## Spec überarbeitet`), jeweils mit Zeitpunkt und ihrer letzten Marker-Zeile.

Fehlt die Konfiguration oder ist der Tracker nicht erreichbar, liest du ihn nicht und rätst nichts über ihn: keine Spec, kein Ticket und kein Status, den du nicht gesehen hast. Du entscheidest dann nur mit dem, was Repo und Gespräch zeigen, und nennst unter „Fehlt zur Einrichtung“, was fehlt. Du brichst nicht ab.
<!-- /regel:tracker-lesen -->

<!-- regel:entscheiden -->
### 3. Nächsten Schritt bestimmen

Geh die Tabelle von oben nach unten durch; die erste Zeile, die zutrifft, gilt. Arbeit nah am Merge geht vor neuer Arbeit. Treffen mehrere Specs oder Tickets auf dieselbe Zeile, nennst du alle und empfiehlst das älteste. Eine Spec auf `Done` oder `Canceled` ist abgeschlossen: Sie zählt nicht als offene Spec, auch wenn sie als Argument genannt ist.

| # | Wenn (gesehen, nicht vermutet) | Dann |
|---|---|---|
| 1 | Das Argument oder der Mensch beschreibt einen Fehler mit unbekannter Ursache | `/slickfab:debug <Fehler>` |
| 2 | Ein Ticket hat `slickfab:needs-human`, oder der letzte slickfab-Kommentar daran endet mit `BLOCKED` | kein Schritt: der Mensch entscheidet; nenne, was offen ist, mit Link |
| 3 | Offener PR zu einem Ticket ohne `SLICKFAB-VERDICT` | `/slickfab:review <PR>` |
| 4 | Offener PR, letztes Urteil `REWORK` oder `MERGE`, danach neue Commits | `/slickfab:review Re-Review <PR>` |
| 5 | Offener PR, letztes Urteil `REWORK`, danach keine Commits | `/slickfab:implement <Ticket>` (Nachbessern) |
| 6 | Offener PR, letztes Urteil `REPLAN`, oder Ticket mit `slickfab:replan` | `/slickfab:tickets <Spec-Issue>` |
| 7 | Offener PR, letztes Urteil `MERGE`, danach keine Commits | kein Schritt: der Mensch mergt |
| 8 | Ticket in `In Review` ohne offenen PR | kein Schritt: der Mensch prüft, ob der PR gemergt ist (dann Ticket auf `Done`) oder fehlt; nenne Ticket und letzten PR mit Link |
| 9 | Ticket in `In Progress` ohne offenen PR | `/slickfab:implement <Ticket>` (liest eine Übergabe am Ticket zuerst) |
| 10 | Ticket in `Todo`, kein offener Blocker | `/slickfab:implement <Ticket>` |
| 11 | Ticket in `Todo`, sein Blocker steht noch in `Backlog` | kein Schritt: der Mensch gibt den Blocker frei (`Todo`); nenne beide Tickets |
| 12 | Spec-Issue noch offen, alle Tickets geschlossen, mindestens eins `Done`, kein `verify`-Ergebnis nach dem letzten Merge | `/slickfab:verify <Spec-Issue>` |
| 13 | Spec-Issue noch offen, alle Tickets geschlossen, mindestens eins `Done`, letztes `verify`-Ergebnis `bestanden` | `/slickfab:retro <Spec-Issue>`; danach setzt der Mensch die Spec auf `Done` (retro schreibt nichts in den Tracker, das ist das Ende), mit dem nächsten Vorhaben `/slickfab:grill` |
| 14 | Spec-Issue noch offen, alle Tickets geschlossen, mindestens eins `Done`, letztes `verify`-Ergebnis `Lücken gefunden` | `/slickfab:verify <Spec-Issue>`: schlägt die Fix-Tickets vor und legt sie nach dem Ja des Menschen an |
| 15 | Spec-Issue noch offen, alle Tickets geschlossen, mindestens eins `Done`, letztes `verify`-Ergebnis `Mensch nötig` | kein Schritt: der Mensch prüft die Punkte aus dem `verify`-Kommentar, danach `/slickfab:verify <Spec-Issue>` |
| 16 | Spec hat Tickets in `Backlog`, keines in `Todo`, `In Progress` oder `In Review` | kein Schritt: der Mensch gibt das nächste Ticket frei (`Todo`) |
| 17 | Alle Tickets der Spec `Canceled` oder `Duplicate` | kein Schritt: der Mensch entscheidet, ob die Spec neu zerlegt wird (`/slickfab:tickets <Spec-Issue>`) oder endet; Status `NEEDS_CONTEXT` |
| 18 | Spec ohne Tickets und ohne `challenge`-Kommentar, oder letztes `challenge`-Urteil `nicht bauen` und danach ein Kommentar `## Spec überarbeitet` (zeitlich nach dem letzten `challenge`-Kommentar) | `/slickfab:challenge <Spec-Issue>` |
| 19 | Spec ohne Tickets, letztes `challenge`-Urteil `nicht bauen`, kein Kommentar `## Spec überarbeitet` danach | kein Schritt: der Mensch entscheidet, ob das Vorhaben endet (Spec auf `Canceled`) oder ob er die Spec mit `/slickfab:spec <Spec-Issue>` ändert und neu prüfen lässt; nenne den `challenge`-Kommentar mit Link; Status `NEEDS_CONTEXT` |
| 20 | Spec ohne Tickets, `challenge`-Kommentar da, letztes Urteil `bauen` oder `kleiner bauen` | `/slickfab:tickets <Spec-Issue>` |
| 21 | In diesem Gespräch steht ein bestätigtes „Ergebnis grill“ | `/slickfab:spec` |
| 22 | Keine offene Spec gesehen und nichts von oben | `/slickfab:grill [Thema]` |
| 23 | Eine offene Spec gesehen, aber keine Zeile passt | kein Befehl: nenne den Stand mit Links und was du nicht einordnen kannst; Status `NEEDS_CONTEXT` |

„Geschlossen“ heißt `Done`, `Canceled` oder `Duplicate` (Statusfolge im Tracker-Vertrag). „Danach neue Commits“ heißt: Ein Commit des PR hat ein Committer-Datum nach dem Zeitpunkt des letzten Urteils. Das gilt auch nach einem Rebase, denn den neuen Stand hat noch kein Review gesehen.

Zeilen, für die du den Tracker brauchst, prüfst du ohne Tracker nicht; sie zählen dann als nicht zutreffend, und du sagst das. Ein PR, dessen Ticket du ohne Tracker nicht lesen kannst, zählt trotzdem für die Zeilen 3 bis 7, wenn sein Titel oder Branch eine Ticket-ID nennt. Kommst du ohne Tracker bei Zeile 22 an, sagst du dazu, dass offene Specs unbekannt sind.
<!-- /regel:entscheiden -->

<!-- regel:kontext -->
### 4. Frischer Kontext oder weiter

- **Im selben Gespräch:** `/slickfab:spec` direkt nach `grill` oder `prototype`, weil spec das Gespräch liest; `docs-lookup` aus dem Schritt heraus, der die Frage hat.
- **Frische Session:** alle anderen Schritte. Prüfende Schritte (`challenge`, `review`, `verify`) dürfen nicht wissen, wie das Artefakt entstand; `implement`, `debug`, `tickets` und `retro` lesen alles Nötige aus Tracker und Repo.
- **Kontext voll:** Ist dieses Gespräch schon lang (Warnung von context-guard, rund zwei Drittel des Kontexts oder mehr als etwa 150k Tokens), empfiehlst du vor dem nächsten Schritt `/slickfab:handoff <Ticket>`, wenn an einem Ticket gearbeitet wird, und den nächsten Schritt in einer frischen Session.
<!-- /regel:kontext -->

<!-- regel:schritte -->
### Die Schritte

| Schritt | Wofür | Kontext |
|---|---|---|
| `fab` | Wegweiser: wo stehe ich, was kommt als Nächstes | beliebig |
| `grill` | offene Entscheidungen in Runden klären | Gespräch mit dem Menschen |
| `spec` | Spezifikation aus dem geklärten Gespräch | selbes Gespräch wie grill |
| `prototype` | Fragen klären, die man nicht erfragen kann | selbes Gespräch, danach spec |
| `challenge` | frischer Blick auf Spec und Zerlegung | frische Session |
| `tickets` | Spec in dünne, vertikale Tickets schneiden | frische Session |
| `implement` | ein Ticket per TDD bis zum PR | frische Session je Ticket |
| `review` | PR auf zwei Achsen prüfen | frische Session |
| `debug` | Fehler mit roter Schleife finden | frische Session |
| `verify` | Ziel der Spec über alle Tickets prüfen | frische Session |
| `retro` | aus wiederkehrenden Fehlern Regeln machen | frische Session |
| `handoff` | Übergabe, bevor der Kontext voll ist | am Ende der laufenden Session |
| `docs-lookup` | versionsgenaue Library-Doku | aus dem laufenden Schritt |
<!-- /regel:schritte -->

## Vertrag

<!-- regel:vertrag-quelle -->
Wörtlich aus `tracker/linear.md` und `docs/projektkonfiguration.md` des slickfab-Plugins. Es steht hier, damit du nichts außerhalb des Projekts lesen musst; es gilt genau so. fab liest nur: Das Anlegen der Konfiguration bietest du nicht an, du zeigst den Inhalt.
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
## Ergebnis fab

**Stand:** <ein bis drei Sätze, je mit Quelle: Issue-Link, PR-Link oder Befehl>
**Gelesen:** Repo <ja|nein: Grund>, Pull Requests <ja|nein: Grund>, Tracker <ja|nein: Grund>
**Fehlt zur Einrichtung:** <z. B. `.slickfab/config` mit TRACKER, TRACKER_TEAM, TRACKER_PROJECT (Vorschlag darunter), Linear-Werkzeuge, `gh`-Anmeldung> oder „nichts“

Nächster Schritt: `/slickfab:<schritt> <Argument>` in <diesem Gespräch|einer frischen Session>, weil <Zeile der Tabelle>

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT>
```

`DONE`, wenn alles gelesen werden konnte; `DONE_WITH_CONCERNS`, wenn etwas unlesbar war und die Empfehlung deshalb nur auf dem Rest beruht; `NEEDS_CONTEXT`, wenn zwei Wege gleich gut passen und nur der Mensch wählen kann (dann beide nennen) oder Zeile 17, 19 oder 23 gilt. Ist der nächste Zug eine Entscheidung des Menschen (Zeilen 2, 7, 8, 11, 15, 16, 17, 19), steht sie statt eines Befehls in der Zeile „Nächster Schritt“; bei Zeile 23 steht dort, was du nicht einordnen kannst. Die Zeile fehlt nie.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
Der Schritt, den das Ergebnis nennt, in dem Kontext, den es nennt. Danach wieder `/slickfab:fab`, wenn unklar ist, wie es weitergeht.
<!-- /regel:naechster-schritt -->
