---
name: retro
description: Verwenden, wenn aus wiederkehrenden Fehlern der letzten Pull Requests, Reviews oder Sessions Regeln werden sollen, etwa nach einem Feature oder jedem zehnten Merge, oder wenn jemand „mach eine Retro“ sagt.
argument-hint: "[Spec-Issue | PR-Bereich | Session]"
---

<!-- regel:einleitung -->
# retro: aus wiederkehrenden Fehlern Regeln machen

Ziel: Ein Fehler, der zweimal passiert ist, soll kein drittes Mal durchrutschen. Du findest wiederkehrende Fehler und schlägst für jeden die billigste Bremse vor, die ihn künftig fängt.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Nach `/slickfab:verify` für ein Feature, nach etwa jedem zehnten Merge oder wenn ein Fehler auffällt, der schon einmal da war.
- Nicht, um einen einzelnen Bug zu beheben; dafür gibt es `/slickfab:debug`.
<!-- /regel:wann -->

## Ablauf

<!-- regel:ablauf -->
Du schlägst vor, du wendest nicht an. Du änderst keine Datei: keine Checks, keine Hooks, keine CI-Workflows, keine Linter-Konfiguration, keine Regeldateien (`.slickrails/rules.md`, `.slickrails/review-learnings.md`, `CLAUDE.md`, `AGENTS.md`, Coding-Standards), auch nicht „nur einen Eintrag“. Jede Bremse, die du vorschlägst, ändert, was künftig durchkommt; darüber entscheidet ein Mensch. Was er annimmt, wird wie jede andere Änderung als Ticket oder Pull Request gebaut und geprüft.

### 1. Voraussetzung prüfen

- Kläre den Zeitraum: Spec-Issue, Bereich von Pull Requests oder Session (Argument). Ohne Angabe: die letzten zehn gemergten Pull Requests des Repos.
- Lies `.slickfab/config`. Den Tracker (Linear über die Linear-Werkzeuge der Session, per Werkzeugsuche `+linear`) liest retro nur, um Review-Kommentare und Labels zu finden; retro schreibt nichts in den Tracker. Ist der Tracker nicht erreichbar, ist das kein Abbruchgrund: Du arbeitest mit Git und Pull Requests weiter und nennst die Fehlermeldung und was dir dadurch fehlt.
- Lies, was es an Bremsen schon gibt: `.slickrails/config.sh`, `.slickrails/rules.md`, `.slickrails/review-learnings.md`, Hooks, CI-Workflows, Linter-Konfiguration, `CLAUDE.md`/`AGENTS.md`.

### 2. Fehler sammeln

Quellen, schiefgelaufene zuerst:

- Review-Kommentare mit Befunden `Critical` oder `Required` und Urteilen `REWORK` oder `REPLAN` (am PR und am Ticket),
- Tickets mit `slickfab:rework`, `slickfab:needs-human` oder `slickfab:replan`, Fix-Tickets aus `/slickfab:verify`,
- Bugfix-Commits und Reverts im Zeitraum, rote CI-Läufe,
- Einträge, die Menschen nachträglich gemeldet haben.

Je Fehler eine Zeile: was passierte, wo (PR, Commit, `Datei:Zeile`), wer oder was hat ihn gefunden, wer hätte ihn früher finden sollen. Fasse gleiche Ursachen zusammen. Wiederkehrend ist ein Fehler ab dem zweiten Auftreten; einmalige Fehler nennst du nur, wenn sie schwer waren (Datenverlust, Sicherheitslücke, Produktion kaputt).

### 3. Einordnen: Check oder Review-Lehre

Für jeden wiederkehrenden Fehler genau eine Einordnung:

- **mechanisch:** ein festes Muster, das eine Maschine erkennen kann (verbotener Aufruf, Importform, Dateiort, fehlender Test zu einer Datei, neues `.skip`, abgesenkte Schwelle). Daraus wird ein Vorschlag für einen Check: eine Regel im Linter des Repos, ein Schritt in einem bestehenden Hook oder ein CI-Job, je nachdem, was im Repo am billigsten ist. Gibt es den Check schon, ist er aber nicht eingebunden oder still kaputt, ist genau das der Vorschlag. Gibt es im Repo gar keine automatische Prüfung (kein Hook, kein CI-Job mit Tests), ist das selbst ein Fund.
- **Ermessen:** braucht Urteil (Konsistenz über Dateien, passende Abstraktion, ob ein Test das Richtige prüft). Daraus wird ein Vorschlag für einen Eintrag in `.slickrails/review-learnings.md` (eine datierte Zeile, kurz und konkret, so wie die Datei es vorgibt) oder, ohne slickrails, in die Review-Regeln des Repos.

Im Zweifel mechanisch: Ein Check, der immer läuft, schlägt eine Regel, an die sich jemand erinnern muss. `CLAUDE.md` und `AGENTS.md` bekommen höchstens einen Verweis, keine neuen Regeln; sie liegen jedem Agent im Kontext und werden mit jeder Zeile teurer.

Betrifft ein Vorschlag slickrails selbst (einen Check, den jedes Repo bräuchte), schreib ihn als Text für ein Issue oder einen Pull Request an slickrails; du änderst slickrails nicht.

### 4. Vorlegen

Zeig die Vorschläge, der schwerste Fehler zuerst. Je Vorschlag: der Fehler mit Belegen (mindestens zwei Stellen bei wiederkehrenden), die Einordnung, die genaue Änderung als Text (der Check als Code-Vorschlag, der Eintrag als fertige Zeile) und wo sie hingehört. Frag, welche der Mensch annimmt. Nimmt er welche an, bietest du an, dafür Tickets mit `/slickfab:tickets` anzulegen oder einen Pull Request mit `/slickfab:implement` zu bauen; selbst schreibst du sie nicht in die Dateien.
<!-- /regel:ablauf -->

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

### Projektkonfiguration: Prüfbefehle mit slickrails

<!-- vertrag:config-slickrails -->
Liegt im Repo `.slickrails/config.sh`, kommen die Prüfbefehle von dort: alle nicht leeren `CHECK_*`-Werte, so wie sie slickrails auch in seinen Hooks benutzt. `CHECK_*`-Einträge in `.slickfab/config` werden dann nicht benutzt; stehen dort andere Werte, nennt der Schritt den Widerspruch einmal und folgt slickrails. Auch `.slickrails/config.sh` wird nur als Text gelesen.
<!-- /vertrag:config-slickrails -->

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
## Ergebnis retro

**Zeitraum:** <Spec, PR-Bereich oder Session> · **Fehler gesichtet:** <n>, davon wiederkehrend: <n>

1. <Fehler> — <n>× (<Belege: PR, Commit, Datei:Zeile>)
   Einordnung: mechanisch → Vorschlag für einen Check in <Hook, Linter, CI-Job> | Ermessen → Vorschlag für einen Eintrag in `.slickrails/review-learnings.md`
   Vorschlag: <Code oder fertige Zeile>

**Für slickrails:** <Text für ein Issue> (oder „keiner“)
**Geänderte Dateien:** keine

Nächster Schritt: `/slickfab:grill` (neues Feature) | `/slickfab:tickets <Spec>`

SLICKFAB-STATUS: DONE
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
Der Mensch entscheidet über jeden Vorschlag. Was er annimmt, wird wie jede Änderung gebaut: als Ticket über `/slickfab:tickets` oder direkt mit `/slickfab:implement`. Danach geht es mit dem nächsten Feature weiter, beginnend mit `/slickfab:grill`.
<!-- /regel:naechster-schritt -->
