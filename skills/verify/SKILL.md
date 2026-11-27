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
- Linear wird über die Linear-Werkzeuge der Session angesprochen (in Claude Code per Werkzeugsuche `+linear` laden).
- Ist Linear nicht erreichbar (keine Werkzeuge, keine Anmeldung, Fehlerantwort, Team oder Projekt aus der Konfiguration existiert nicht), meldet der Schritt genau das mit der Fehlermeldung und hört auf. Er schreibt **keine** Plan-, Ledger-, State- oder Ticket-Datei ins Repo als Ersatz. Was schon erarbeitet ist, zeigt er im Chat, damit nichts verloren geht.
- Ausnahme `verify`: Liegt die Spec als Text vor, prüft verify dagegen weiter, statt aufzuhören. Es schreibt nichts in den Tracker, zeigt Ergebnis und Fix-Ticket-Vorschläge nur im Chat, und das Ergebnis endet mit `SLICKFAB-STATUS: DONE_WITH_CONCERNS` und nennt darüber „Tracker nicht geprüft“, auch wenn jede Aussage erfüllt ist; das gilt, sofern geprüft werden konnte, sonst mit `BLOCKED`. Liegt die Spec nicht als Text vor, gilt der Punkt davor.
<!-- /vertrag:zugang -->

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
