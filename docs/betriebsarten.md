# Betriebsarten und Einrichtung

slickfab ist ein Prozess in 13 Schritten. Du kannst ihn auf drei Arten fahren, und es sind immer dieselben Schritte: Ein Schritt ist genau eine `skills/<schritt>/SKILL.md`. Die Agent-Rollen und die Herdr-Vorlagen sind nur Hüllen darum.

## In fünf Minuten zum ersten Schritt

1. Plugin installieren: `claude plugin marketplace add <pfad-zum-repo>`, dann `claude plugin install slickfab@slickfab` (Details in der README, „Installieren“). Zum Ausprobieren ohne Installation geht `claude --plugin-dir <pfad-zu-slickfab>`.
2. In deinem Projekt Claude Code starten und `/slickfab:fab` eingeben. fab sagt dir, wo du stehst, was zur Einrichtung fehlt und welcher Schritt als Nächstes kommt. In einem Repo ohne Vorarbeit ist das `/slickfab:grill`.
3. `/slickfab:grill <dein Vorhaben>` beantwortet keine Fragen für dich, sondern stellt sie: in Runden, mit Empfehlung, bis keine Entscheidung mehr offen ist.

`grill` braucht keinen Tracker. Ab `spec` brauchst du die Projektkonfiguration (unten).

## Einrichtung in einem neuen Repo

| Was | Wozu | Wie |
|---|---|---|
| `.slickfab/config` | Tracker (Team, Projekt) und, ohne slickrails, Prüfbefehle | Datei im Repo-Root anlegen, Format und Schlüssel in `docs/projektkonfiguration.md`. `/slickfab:fab` zeigt einen Vorschlag mit den Werten, die es findet. |
| Linear-Werkzeuge | Specs und Tickets lesen und anlegen | Linear-Konnektor in Claude Code anmelden. Die Schritte laden ihn per Werkzeugsuche. |
| `gh`, angemeldet, Repo auf GitHub | Pull Requests öffnen (`implement`) und lesen (`review`, `fab`) | `gh auth login` |
| slickrails (empfohlen) | Bremsen: Hooks, Stop-Gate, AI-Review beim Push | `slickrails init` im Repo. Dann kommen die Prüfbefehle aus `.slickrails/config.sh`. |

Fehlt etwas davon, bricht kein Schritt ab, ohne es zu sagen: Jeder nennt, welche Datei oder welcher Zugang fehlt, und schreibt keine Ersatzdatei ins Repo. Linear bleibt die einzige Wahrheit über Plan und Zustand. Es gibt keine Plan-, Ledger- oder Zustandsdatei im Repo, auch fab legt keine an.

Das Projekt, in dem du arbeitest, darf nicht im Plugin-Ordner liegen, egal ob installiert oder mit `--plugin-dir`. Claude Code schützt Dateien im Plugin-Ordner als „sensitive file“, und dann darf kein Schritt dort schreiben (gefunden im Probelauf). Für Arbeit an slickfab selbst heißt das: Ist es aus dem Checkout installiert, entstehen Änderungen in einem Worktree außerhalb davon (`git worktree add` oder `runtime/herdr/slickfab-worktree add`), und der gemergte Stand kommt per `git pull` in den Checkout.

## Die Schritte

| Schritt | Wofür | Kontext |
|---|---|---|
| `/slickfab:fab` | Wegweiser: wo stehe ich, was kommt als Nächstes | beliebig |
| `/slickfab:grill` | offene Entscheidungen in Runden klären | Gespräch mit dir |
| `/slickfab:spec` | Spezifikation aus dem geklärten Gespräch, im Tracker | selbes Gespräch wie grill |
| `/slickfab:prototype` | Fragen klären, die man nicht erfragen kann | selbes Gespräch, danach spec |
| `/slickfab:challenge` | frischer Blick auf Spec und Zerlegung | frische Session |
| `/slickfab:tickets` | Spec in dünne, vertikale Tickets schneiden | frische Session |
| `/slickfab:implement` | ein Ticket per TDD bis zum Pull Request | frische Session je Ticket |
| `/slickfab:review` | Pull Request auf zwei Achsen prüfen | frische Session |
| `/slickfab:debug` | Fehler mit roter Schleife finden | frische Session |
| `/slickfab:verify` | Ziel der Spec über alle Tickets prüfen | frische Session |
| `/slickfab:retro` | aus wiederkehrenden Fehlern Regeln machen | frische Session |
| `/slickfab:handoff` | Übergabe, bevor der Kontext voll ist | am Ende der laufenden Session |
| `/slickfab:docs-lookup` | versionsgenaue Library-Doku | aus dem laufenden Schritt |

Der übliche Weg: `grill` → `spec` → `challenge` → `tickets` → du setzt Tickets auf `Todo` → je Ticket `implement` → `review` → du mergst → nach dem letzten Ticket `verify` → `retro` → du setzt die Spec auf `Done`. Jeder Schritt nennt am Ende den nächsten. Bist du unsicher, frag `/slickfab:fab`.

Prüfende Schritte laufen in einer frischen Session, damit der Prüfer nicht weiß, wie das Artefakt entstanden ist. Wird die laufende Session lang (Warnung von context-guard, rund zwei Drittel des Kontexts), schreib mit `/slickfab:handoff` eine Übergabe ans Ticket und mach frisch weiter.

## Hand

Du rufst die Schritte selbst auf, je einen per Slash-Befehl, in deiner Session oder in einer neuen. Das ist der Modus für jeden Claude-Code-Nutzer, ohne Herdr. Du siehst jeden Schritt, beantwortest seine Fragen und gibst frei, was er anlegen will.

## Assistiert

Eine Session, und die Schritte laufen als frische Subagents. Das Plugin bringt sieben Rollen mit: `slickfab:planner` (spec und tickets), `slickfab:challenger`, `slickfab:implementer`, `slickfab:reviewer`, `slickfab:debugger`, `slickfab:verifier` und `slickfab:retro`. Jede Rolle hat ihren Schritt beim Start schon im Kontext und endet mit der Marker-Zeile `SLICKFAB-STATUS: …`.

So startest du sie, in deiner Session mit geladenem Plugin, in eigenen Worten:

> Starte den Agent slickfab:implementer mit dem Auftrag „EX-12“. Wenn er den Branch gepusht hat, starte slickfab:reviewer mit dem PR und dem Ticket. Gib dem Reviewer nichts aus dem Bericht des Umsetzers mit.

Was du der Rolle gibst, ist nur ihr Eingang (Ticket, PR, Spec-Issue). Eine Rolle kann dich nicht fragen: Wo der Schritt fragen würde, endet sie mit `NEEDS_CONTEXT` oder `BLOCKED` und nennt, was fehlt. Dann entscheidest du in der Haupt-Session und startest die Rolle neu. `grill` läuft nie als Rolle, weil es dich braucht.

**Wie belastbar die Rollen sind.** Jede der sieben Rollen hat mindestens zwei Pressure-Szenarien unter `tests/pressure/`: Lagen, die zu einer Abkürzung drängen (Gate rot und Zeitdruck, Test im Weg, „egal, mach du“ …), mit vorher festgelegtem „gehalten“. Jedes Szenario lief mit der neuen Rolle und als Kontrolle mit der alten Studio-Vorlage bzw. ohne Anleitung: neu 14 von 14 gehalten, Kontrolle 2 von 14. Die Bewertung ist von Hand, `tests/check_pressure.py` prüft nur die Ablage (`docs/features/pressure-szenarien.md`).

**Wächter.** Das Plugin bringt drei Hooks mit (`hooks/hooks.json`):

- `role_bash_guard.py`: Bei `slickfab:reviewer`, `slickfab:verifier` und `slickfab:retro` lässt er nur eine Allowlist von Bash-Befehlen zu (lesen, testen, `git`/`gh` ohne Schreiben). Ihre Werkzeuggrenze (`disallowedTools`) wäre mit freiem Bash sonst wirkungslos (`docs/features/rollen-bash-waechter.md`).
- `docs_lookup_guard.py`: Im Doku-Leser `slickfab:docs-reader` ist nur der Aufruf von `lookup.py` erlaubt (`docs/features/docs-lookup.md`).
- `context_guard.py`: warnt eine Rolle ab 65 % Kontext und verlangt ab 80 % die Übergabe. Er greift nur in Herdr-Terminals mit Rollen-Label und gelesener Statuszeile, in einer normalen Session schweigt er (`docs/features/context-guard.md`).

Beide Bash-Wächter starten über einen gemeinsamen Starter. Außerhalb ihrer Rollen greifen sie nicht ein, in der Rolle lehnen sie im Zweifel ab.

## Autopilot

**Noch nicht live, aber gebaut.** Ein Dispatcher startet die Rollen parallel in Herdr-Terminals, Linear ist die Zustandsmaschine, und du greifst nur an Gates ein (Einwände, Zerlegung, Merge, `door:one-way`, `slickfab:needs-human`). Beim Umschalten lief er als Dry-Run gegen das echte Linear. Dabei fielen Fehler auf, die inzwischen behoben sind: rotes GitHub-CI ohne laufende Actions, `space: "-"` und Herdr-Vorlagen mit ungültigem Frontmatter. Live geht er erst nach dem Pilot in slickrails. Bis dahin fährst du slickfab in den Modi Hand oder Assistiert.

Was es gibt:

- `runtime/herdr/slickfab-dispatch tick|watch [--dry-run]`: liest Linear, Herdr und GitHub, fragt `decide()` und führt die Aktionen aus; `--dry-run` zeigt nur die Pläne (`docs/features/slickfab-dispatch.md`).
- `runtime/herdr/slickfab_dispatch.py`: die Entscheidungslogik `decide()`.
- `runtime/herdr/slickfab-worktree add|review|rm`: startklare Worktrees mit Baseline-Prüfung (`docs/features/slickfab-worktree.md`).
- `runtime/herdr/slickfab-run`: startet eine Rolle als Herdr-Sitzung. `runtime/herdr/gen-templates` erzeugt die Herdr-Vorlagen aus `agents/` (`docs/features/slickfab-run.md`).

**Factory-Konfiguration.** Sie liegt privat beim Betreiber (`~/.config/slickfab/factory.json`, nie im Repo) und nennt je Projekt, ob der Autopilot es anfassen darf (`enabled`), Linear-Projekt, Repo und GitHub-Repo. Optional je Projekt: `auto_merge` (Standard aus), `max_parallel` (Standard 3), `space` (Herdr-Space oder `-`) und `github_ci`. `github_ci` ist `use` (Standard: GitHub-Checks zählen) oder `ignore`: Dann gelten GitHub-Checks als nicht vorhanden, für main zählt nur die lokale Post-Merge-Prüfung, für Pull Requests nur das Review. Gedacht ist `ignore` für Repos, deren Actions nicht laufen, etwa weil das Free-Tier-Kontingent aufgebraucht ist. Achtung: `ignore` schaltet damit auch die serverseitigen Checks als Bremse ab, etwa Secret-Scan (gitleaks) und Abhängigkeits-Audit aus `.github/workflows/security.yml`. Ein roter Befund dort hält dann weder main noch einen PR auf; einzige Bremse bleibt der lokale Pre-Push (slickrails). Form und alle Felder: `docs/features/slickfab-dispatch.md`, Abschnitt „Factory-Konfiguration“.

## Zusammenspiel mit slickrails

slickrails sind die Bremsen, slickfab ist das Gaspedal. Gibt es im Repo `.slickrails/`:

- Die Prüfbefehle kommen aus `.slickrails/config.sh`, nicht aus `.slickfab/config`.
- `implement` umgeht keinen Hook. Ein roter Stop-Hook oder ein Befund des AI-Reviews beim Push heißt: nicht fertig.
- `review` liest zuerst, was slickrails schon gemeldet hat (Status-Checks, AI-Review), und meldet es nicht doppelt.
- `retro` macht aus mechanischen Fehlern Vorschläge für slickrails-Checks und aus Ermessensfällen Einträge in `.slickrails/review-learnings.md`, immer als Vorschlag für dich.

Ohne slickrails funktioniert jeder Schritt, aber die Bremsen fehlen: Dann gelten nur die Prüfbefehle aus `.slickfab/config`.
