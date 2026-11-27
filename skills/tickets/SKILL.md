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

### Tracker: Issues

<!-- vertrag:issues -->
| Art | Titel | Ort | Anfangsstatus |
|---|---|---|---|
| Spec | `Spec: <Feature>` | Projekt aus der Konfiguration | `Backlog` |
| Ticket | Verb + Ergebnis, ohne „und“ | Sub-Issue der Spec | `Backlog` |

- Vor jedem Anlegen auf Dubletten prüfen: offene und erledigte Issues im Projekt mit ähnlichem Titel suchen. Gibt es einen Treffer, nennen und fragen, statt doppelt anzulegen.
- Abhängigkeiten sind Linear-Relationen „blockiert von“, nicht Text in der Beschreibung.
- Details für Agents (betroffene Dateien, Fundstellen) stehen in einem einklappbaren Abschnitt „Agent notes“ am Ende der Beschreibung.
<!-- /vertrag:issues -->

### Tracker: Statusfolge

<!-- vertrag:status -->
`Backlog` → `Todo` → `In Progress` → `In Review` → `Done` (Abbruch: `Canceled`, Dublette: `Duplicate`)

| Übergang | Wer |
|---|---|
| anlegen in `Backlog` | `spec`, `tickets` |
| `Backlog` → `Todo` | nur der Mensch (das ist die Freigabe zum Bauen) |
| `Todo` → `In Progress` | der Umsetzer beim Start |
| `In Progress` → `In Review` | der Umsetzer, wenn der Pull Request offen ist |
| `In Review` → `Done` | nach dem Merge |

Kein Schritt setzt ein Ticket selbst auf `Todo`.
<!-- /vertrag:status -->

### Tracker: Labels

<!-- vertrag:labels -->
Die Labels existieren im Team; ein Schritt legt keine neuen an. Fehlt eines, meldet er das.

| Label | Bedeutung |
|---|---|
| `slickfab:rework` | Reviewer verlangt Nachbesserung |
| `slickfab:ready` | Review bestanden, wartet auf den Merge durch einen Menschen |
| `slickfab:needs-human` | Schleife erschöpft oder Agent blockiert: ein Mensch entscheidet |
| `slickfab:replan` | Ticket oder Spec ist falsch geschnitten: zurück zur Planung |
| `door:one-way` | schwer umkehrbar (Migration, Auth, Zahlung, Löschen, Deploy): immer menschliches Gate, nie Auto-Merge |
| `S`, `M`, `L` | Größe (Aufwand klein, mittel, groß); genau eines je Ticket. `L` ist ein Hinweis, das Ticket eher zu teilen |

In Linear sind `rework`, `ready`, `needs-human` und `replan` Kinder der Label-Gruppe `slickfab`; in Texten, Kommentaren und diesem Vertrag wird `slickfab:<name>` geschrieben. Beim Suchen und Setzen über die Linear-Werkzeuge heißt das Label `rework`, `ready`, `needs-human` bzw. `replan` in der Gruppe `slickfab`; eine Suche nach `slickfab:rework` findet nichts, das Label fehlt dann nicht. Die Gruppe erlaubt nur eines zur Zeit.
<!-- /vertrag:labels -->

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
