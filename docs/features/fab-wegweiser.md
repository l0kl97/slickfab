# fab-Wegweiser, Hand-Durchlauf und Betriebsarten

**Status:** aktiv · **Stand:** 2026-11-24 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Der Maintainer will einen Entwickler zehnmal schneller machen, weil er den Prozess Schritt für Schritt fahren kann („the goal of this is to get 10x from one developer because he can use the process/steps you know?“). Dieses Ticket liefert den Einstieg und den Beleg, dass der Modus Hand trägt:

- **fab** ist der Wegweiser. `/slickfab:fab` sagt, wo man steht (aus Tracker und Repo, nicht aus einer Zustandsdatei), welcher Schritt als Nächstes kommt und ob er im selben Gespräch oder frisch läuft.
- **Hand-Durchlauf:** In einem leeren Test-Repo läuft ein kleines Feature von Hand durch grill → spec → tickets → implement → review. Jeder Schritt muss allein funktionieren und den nächsten nennen.
- **Doku:** Betriebsarten, Schritte, Zusammenspiel mit slickrails, Einrichtung. Die README zeigt den schnellsten Weg zum ersten Schritt.
- Aus dem Ruling am Ticket kommen dazu: Starten alle 7 Hüllen als geladene Plugin-Agents? Und ein Probelauf Assistiert, bei dem implementer und reviewer am selben echten Probe-Ticket arbeiten.

## Entscheidungen

- **fab liest nur.** Keine Datei, kein Kommentar, kein Label, kein Status. Auch `.slickfab/config` legt fab nicht an, es zeigt nur einen Vorschlag. Deshalb bettet fab den Vertrag „config-fehlt“ nicht ein (der bietet das Anlegen an) und den Vertrag „zugang“ auch nicht (der sagt „hört auf“; fab macht ohne Tracker mit dem Repo weiter).
- **Entscheidung als Tabelle, erste passende Zeile gilt.** Arbeit nah am Merge geht vor neuer Arbeit (PR vor Ticket vor Spec vor grill). `grill` gilt nur, wenn keine offene Spec gesehen wurde; passt bei einer gesehenen Spec keine Zeile, endet fab mit `NEEDS_CONTEXT` statt mit `grill` (Review PR #14, A1). „Danach neue Commits“ heißt Committer-Datum nach dem letzten Urteil, auch nach einem Rebase und auch nach `MERGE` (A4). Zeilen, die den Tracker brauchen, gelten ohne Tracker als nicht zutreffend, und fab sagt das. Damit rät es nie einen Tracker-Zustand. Ein PR mit Ticket-ID im Titel oder Branch zählt auch ohne Tracker.
- **Kontextregel:** Im selben Gespräch laufen nur spec nach grill oder prototype (spec liest das Gespräch) und docs-lookup. Alles andere frisch, Prüfer erst recht. Bei langem Gespräch (Warnung von context-guard, rund zwei Drittel, mehr als etwa 150k Tokens nach aihero „Smart Zone“) vorher `handoff`.
- **Prüfung „kennt alle 13 Schritte“ als eigenes Werkzeug** `tests/check_fab.py`, aufgerufen von `tests/test_fab_steps.py`. Damit bleiben `tests/run.sh` und `check_structure.py` unverändert. Geprüft wird: Die Tabelle im Block `regel:schritte` nennt genau die `skills/*/SKILL.md`, und jeder `/slickfab:<name>` in fab, README und `docs/*.md` existiert. Dossiers unter `docs/features/` und die Recherche zählen nicht, weil dort Mutationen und alte Namen als Geschichte stehen. Seit Review PR #14 (R1, A2) dazu: jeder Name `slickfab:<name>` ist Schritt, Rolle aus `agents/` oder Label aus dem Vertrag; die Schritt-Tabelle der README nennt genau die Schritte; jedes `runtime/herdr/<werkzeug>` in der Doku existiert; ohne ausführbares `runtime/herdr/slickfab-dispatch` sagen README und `docs/betriebsarten.md` beim Autopiloten „noch nicht nutzbar“.
- **Regel-Marker und Referenz:** fab hat außerhalb der Marker nur Frontmatter, Leerzeilen und feste Überschriften. Die Referenz kam aus `python3 tests/rules_golden.py --update`. fab steht in den Pflichtlisten von `test_rule_golden.py` und `test_contract_blocks.py` (Blöcke `marker`, `config-format`).
- **Modus Assistiert in der Doku mit dem echten Aufruf.** Die Agent-Rollen sind gemergt, und der Probelauf unten zeigt, dass die Rollen als `slickfab:<rolle>` starten.
- **Probe-Repos liegen neben einer Kopie des Plugins, nicht darin** (Befund im Probelauf, siehe Historie).

- **Urteil `nicht bauen`:** Zeile 19 fängt eine Spec ohne Tickets ab, deren letztes `challenge`-Urteil `nicht bauen` lautet: kein Schritt, der Mensch entscheidet (Spec auf `Canceled` oder ändern mit `spec`), `NEEDS_CONTEXT`. Die tickets-Zeile (jetzt 20) nennt die Urteile `bauen` und `kleiner bauen` ausdrücklich. Die Zeilen ab 20 sind dadurch um eins verschoben.
- **Ende nach retro:** retro schreibt nichts in den Tracker, fab kann eine gelaufene retro also nicht sehen. Sichtbares Ende ist deshalb der Status der Spec: Zeile 13 (und 12, 14, 15) gelten nur, solange das Spec-Issue offen ist; Zeile 13 sagt, dass der Mensch die Spec nach der retro auf `Done` setzt. Eine Spec auf `Done` zählt nicht als offen, auch als Argument nicht, und fällt auf Zeile 22 (`grill`; früher Zeile 21).
- **Autopilot-Prüfung:** Ohne ausführbares `runtime/herdr/slickfab-dispatch` (eine Datei ohne Ausführrecht zählt nicht) muss der Autopilot-Abschnitt mit „noch nicht nutzbar“ beginnen und darf das Werkzeug `slickfab-dispatch` nicht nennen (Startanleitung). Ein Verweis auf das Dossier `docs/features/slickfab-dispatch.md` zählt nicht als Nennung.

## Wo es lebt

- `skills/fab/SKILL.md`: der Schritt.
- `tests/check_fab.py`, `tests/test_fab_steps.py`: Wegweiser kennt genau die Schritte, Doku nennt nur echte Befehle.
- `tests/golden/rules.md`: eingefrorene Regeln, jetzt mit fab.
- `docs/betriebsarten.md`: Betriebsarten, Schritte, Einrichtung, slickrails.
- `README.md`: Schnellstart.

## So testet man es

1. `sh tests/run.sh` → `slickfab tests: ok`.
2. `python3 tests/check_fab.py .` → keine Ausgabe, Exit 0.
3. Verhalten: Plugin-Kopie anlegen (`git ls-files -z | xargs -0 tar cf - | tar xf - -C .test-tmp/plugin`), Probe-Repo daneben, dann `claude -p "/slickfab:fab" --plugin-dir <kopie>`. Vorher und nachher `git status --short --untracked-files=all` vergleichen.
4. Mutationsprobe im Worktree: siehe unten.

### Protokoll fab (2026-11-24, je frische Session per `claude -p`)

Zeilennummern in dieser Tabelle beziehen sich auf die erste Fassung (vor Rework 1). Heute: alte 16 = neue 22, alte 5 = 5, alte 4 = 4, alte 9 = 10.

| Fall | Repo | Erwartet | Ergebnis | neue Datei? |
|---|---|---|---|---|
| leer, ohne Konfiguration, ohne Remote | `git init` + leerer Commit | `grill` | `/slickfab:grill [Thema]` (Zeile 16). Nennt als fehlend: Remote, `.slickfab/config` mit Vorschlag, slickrails. Tracker- und PR-Zeilen als „nicht geprüft“ markiert. `DONE_WITH_CONCERNS`. | nein |
| offener PR mit Urteil `REWORK`, ohne neue Commits | Klon von slickfab, PR #13 | `implement` | `/slickfab:implement EX-3` (Nachbessern, Zeile 5). Ohne `.slickfab/config`: Tracker nicht gelesen, Vorschlag gezeigt. | nein |
| offener PR, `REWORK`, danach neuer Commit | derselbe Klon, 20 Minuten später | `review` | `/slickfab:review Re-Review 13` (Zeile 4) | nein |
| mit Konfiguration und Tracker, Ticket in Todo | Hand-Repo, Argument EX-1 | `implement` | `/slickfab:implement EX-2` (Zeile 9). Liest Spec, Ticket, Kommentare und Remote-Branches. | nein |

Der Fall „offener PR ganz ohne Urteil“ (Zeile 3) kam real nicht vor: Der einzige offene PR hatte schon ein Urteil, und ein Wegwerf-Repo auf GitHub gab es nicht (Entscheidung des Masters). Dass ein PR zum Ticket auf `review` führt, belegt der dritte Fall.

### Trockenlauf der Tabelle (Rework 1, frische Session ohne Werkzeuge)

`claude -p "/slickfab:fab <Fälle>" --disallowedTools Bash Read Grep Glob ToolSearch Agent`: fab bekommt sechs Zustände als gesehen und nennt je Fall Zeile und nächsten Schritt.

| Fall | Stand | vor dem Fix (rot) | nach dem Fix (grün) |
|---|---|---|---|
| F1 | Spec: T1 `Done`, T2 `Backlog` | 16 → `grill` | 16 → Mensch gibt T2 frei |
| F2 | Ticket `In Review`, PR gemergt | 16 → `grill` | 8 → Mensch prüft Merge, Ticket auf `Done` |
| F3 | alle `Done`, verify „Lücken gefunden“ | 16 → `grill` | 14 → `/slickfab:verify` (Fix-Tickets nach Ja) |
| F4 | alle `Done`, verify „Mensch nötig“ | 16 → `grill` | 15 → Mensch prüft, dann `verify` |
| F5 | Ticket `Todo`, Blocker in `Backlog` | 16 → `grill` | 11 → Mensch gibt den Blocker frei |
| F6 | PR mit `MERGE`, danach neuer Commit | 7 → Mensch mergt | 4 → `/slickfab:review Re-Review #9` |
| F7 | T1 `Done`, T2 `Canceled`, kein verify | 16 → „nächstes Ticket freigeben“, gibt es nicht | 12 → `/slickfab:verify` |
| F8 | alle Tickets `Canceled`/`Duplicate` | 16 → läuft ins Leere | 17 → Mensch entscheidet (neu zerlegen oder beenden), `NEEDS_CONTEXT` |

F7 und F8 kamen aus dem AI-Review beim Push von Rework 1 (geschlossene Status `Canceled`, `Duplicate`); die Spalte „vor dem Fix“ zeigt dort den Stand nach dem ersten Teil von Rework 1.

Gegencheck nach dem Fix im leeren Repo: weiter `/slickfab:grill` (damals Zeile 20, heute 22), keine neue Datei.

### Protokoll Start der 7 Hüllen als Plugin-Agents

Eine Session `claude -p --plugin-dir` startete mit dem Agent-Werkzeug nacheinander `slickfab:planner`, `challenger`, `implementer`, `reviewer`, `debugger`, `verifier` und `retro`, jeweils mit „Startprobe ohne Eingang“. **Alle 7 starteten.** Jede Rolle sagte, ihr Schritt stehe beim Start im Kontext, ohne Nachladen (0 Werkzeugaufrufe). Jede endete mit `SLICKFAB-STATUS: NEEDS_CONTEXT` und nannte den fehlenden Eingang. Das ist eine Selbstauskunft der Agents. Gestützt wird sie dadurch, dass jeder das Ergebnisformat seines Schritts benutzte, ohne eine Datei zu lesen. Damit ist der offene Punkt aus `agent-rollen.md` („ob `skills: [slickfab:…]` beim echten Start vorlädt“) belegt.

### Protokoll Probelauf Assistiert (Probe-Ticket des Masters)

Haupt-Session `claude -p --plugin-dir` im Wegwerf-Repo, Remote ein lokales bare-Repo (kein PR möglich, Entscheidung des Masters, am Ticket festgehalten).

| Lauf | Was passierte |
|---|---|
| 1, implementer | Schreiben verweigert („sensitive file“). Er hielt an: kein Umgehen über die Shell, Kommentar und `slickfab:needs-human` am Ticket, `BLOCKED`. Ursache: Das Probe-Repo lag im Plugin-Ordner (siehe Historie). Reviewer richtigerweise nicht gestartet. |
| 2, implementer | `EX-2` → In Progress. K1 und K2 je rot (aus dem richtigen Grund), dann grün. Suite 1 → 3 Tests grün. Branch gepusht, PR-Text als Kommentar am Ticket, Ruling (Umlaute trennen Wörter), Ticket → In Review. `DONE_WITH_CONCERNS` mit drei Bedenken. |
| 2, reviewer | Bekam nur Branch und Ticket. Eigener detached Worktree, Suite grün, 4 Mutationen, 1 überlebt (Ziffern ungetestet) → `[Required]`. Bericht des Umsetzers ausdrücklich ignoriert. Worktree entfernt. `SLICKFAB-VERDICT: REWORK`, `SLICKFAB-STATUS: DONE_WITH_CONCERNS`. |

Danach mit Freigabe des Masters EX-2 mit Kommentar zurück auf Todo für den Hand-Durchlauf.

### Protokoll Hand-Durchlauf (frisches Wegwerf-Repo `textwerk`, je Schritt frische Session)

Repo: `textwerk.py` (leer), ein Import-Test, `.slickfab/config` (Linear, Team Example, Projekt Example, `CHECK_TEST`), Remote lokales bare-Repo. spec und tickets liefen nur bis zur Freigabefrage, ohne anzulegen (Entscheidung des Masters). Das Ergebnis eines Schritts ging nur als Text im Argument in den nächsten, nie als Gesprächsverlauf.

| # | Aufruf | Ergebnis | genannter nächster Schritt |
|---|---|---|---|
| 1 | `/slickfab:grill Eine Funktion slugify(text) …` und eine Antwortrunde (`--resume` derselben grill-Session) | Repo selbst erkundet, F1–F5 mit Empfehlung, Reversibilität bei F2 markiert, „Ergebnis grill“ mit Autonom-Entscheidungen | `/slickfab:spec` |
| 2 | `/slickfab:spec` + „Ergebnis grill“ als Text | Keine Spec auf Verdacht: 3 offene Produktfragen gefunden (Trenner bei weggelassenen Zeichen, `’`, ø/ł/æ). `NEEDS_CONTEXT` | `/slickfab:grill … offen: (1)…(3)` |
| 3 | `/slickfab:grill … Runde 2` + bisheriges Ergebnis + offene Punkte, eine Antwortrunde | F6–F9 mit Empfehlung, neues „Ergebnis grill“ | `/slickfab:spec` |
| 4 | `/slickfab:spec` + neues Ergebnis als Text | Volle Spec (Bitte wörtlich, Stories, Muss wahr sein, Kritische Verbindungen, Grenzen, Teststellen). Findet eine Dublette und hält vor dem Anlegen an. `NEEDS_CONTEXT` | nach dem Anlegen `/slickfab:challenge <Issue-ID>` |
| 5 | `/slickfab:tickets EX-1 — ohne challenge zerlegen` | Fehlenden challenge-Kommentar genannt, Schnitt = ein Tracer, EX-2 als bestehende Scheibe erkannt, fragt statt anzulegen. `NEEDS_CONTEXT` | keine Zeile „Nächster Schritt“ (Befund, gemeldet an der Spec) |
| 6 | `/slickfab:fab EX-1` | Zeile 9 | `/slickfab:implement EX-2` |
| 7 | `/slickfab:implement EX-2` | K1, K2 rot/grün, Suite grün, gepusht, Kommentar und Ruling am Ticket, In Review, `DONE_WITH_CONCERNS` | `/slickfab:review` gegen den Branch, frische Session |
| 8 | `/slickfab:review <branch> EX-2` | Detached Worktree, 3 Mutationen, 1 überlebt → `REWORK`, Worktree entfernt | `/slickfab:implement EX-2`, dann Re-Review |

Kein Schritt brauchte Wissen aus dem vorigen Gespräch. spec arbeitete aus dem schriftlichen „Ergebnis grill“, alles ab tickets aus Linear und dem Repo.

**Lücke (Entscheidung des Masters):** Der PR-Weg ist nicht belegt. implement endete ohne PR, review prüfte den Branch. Belegt wird er im Pilot in slickrails.

**Befunde an anderen Schritten**, gemeldet als Kommentar am Ticket, hier nicht behoben:
- tickets: Das Ergebnis endete ohne Zeile „Nächster Schritt“, und die Marker-Zeile stand in einem Codeblock.
- review: Bei `REWORK` endete der Hand-Lauf mit `STATUS: DONE`, der Assistiert-Lauf mit `DONE_WITH_CONCERNS`. Der Schritt legt nicht eindeutig fest, welcher Status zu `REWORK` gehört.
- grill: Runde 1 wollte für F2 einen ADR anlegen (schwer umkehrbar), Runde 2 sagte zum selben Inhalt „keine Entscheidung braucht einen ADR“.
- implement (Hand): Er kannte die Ziffern-Lücke aus dem Review-Kommentar am Ticket und ließ sie offen, weil das Ticket sie nicht nennt. Das Review machte daraus `REWORK`. Die Schritte widersprechen sich hier nicht, kosten aber eine Runde.

### Mutationsprobe

Im Worktree, am fertigen Stand vor dem Commit. Jede Mutation wird in die Datei geschrieben, dann laufen `test_fab_steps`, `test_rule_golden` und `test_contract_blocks`, danach wird das Original zurückgeschrieben. Gegenprobe ohne Mutation: grün. **12 Mutationen, 0 überlebt.**

- `check_fab.py` (6): fehlender Schritt nicht gemeldet, erfundener Schritt nicht gemeldet, `docs/*.md` nicht geprüft, Befehle in fab selbst nicht geprüft, fehlendes fab still, Tabelle aus dem ganzen Text statt aus dem Block.
- `skills/fab/SKILL.md` (4): leeres Repo → `spec` statt `grill`, PR → `implement` statt `review`, Schreibverbot gestrichen, Tracker-Raten erlaubt (alle über die Referenz `tests/golden/rules.md`).
- Doku (2): falscher Befehl in README, falscher Befehl in `docs/betriebsarten.md`.

Die Zahl deckt nur ab, was ich bedacht habe; belastbar wird sie erst mit einer fremden Probe. Die fremde Probe aus dem Review (PR #14) fand am Head `d62a07f` 4 von 16 und danach 5 von 5 Überlebenden, alle an Rollennamen und der README-Tabelle (R1).

**Rework 1, Probe auf den Fix:** gleiche Methode, **23 Mutationen, 0 überlebt** (im ersten Durchgang 17 mit 1 Überlebendem: „Noch nicht nutzbar“ → „Nutzbar“ in der Doku blieb grün; dafür kam die Autopilot-Prüfung dazu, danach 3 weitere Mutationen an ihr; nach dem Push-Review 3 weitere an den geschlossenen Status):
- Tabelle (11, davon 3 zu `Canceled`/`Duplicate`: Zeile 12 nur `Done`, „geschlossen“ ohne `Canceled`, `Duplicate` fehlt in Zeile 17): MERGE aus Zeile 4 gestrichen, Zeile 7 ohne Commit-Bedingung, Zeile 8 verdreht, Zeile 11 gestrichen, Zeile 14 auf `bestanden`, alte Zeile 12 zurück, `grill` wieder als Rückfall, Rebase ausgenommen.
- `check_fab.py` (10): Rollen unbekannt, Namen nicht geprüft, erfundene oder fehlende README-Zeile still, Label `needs-human` fehlt, `runtime/herdr` nicht geprüft, nur Namen in Backticks, Autopilot-Prüfung aus, Autopilot-Prüfung nie aktiv.
- Doku (3): Autopilot in Doku und README als nutzbar, falscher Name in der README-Tabelle. Ein erster Anlauf mit 20 Mutationen startete nie: Die erste Zeile des Befehls wartete auf Eingabe und hing über eine Stunde, bis der Master nachfragte.

## Grenzen & offene Punkte

- fab ist nur Text für das Modell. Die Tests prüfen Tabelle und Befehle, nicht die Entscheidung. Die Entscheidung belegt das Protokoll oben mit 4 echten Läufen.
- PR-Weg im Hand-Durchlauf nicht belegt (bare-Remote), kommt im Pilot slickrails.
- Zeile 3 (PR ohne jedes Urteil) nicht real beobachtet.
- Zustandsmaschine und Auto-Merge-Regel stehen nicht in der Doku. Sie kommen mit dem Dispatcher.
- Autopilot ist in der Doku als „noch nicht nutzbar“ beschrieben. Wer `runtime/herdr/slickfab-dispatch` ausführbar anlegt, muss README und `docs/betriebsarten.md` umschreiben; die Prüfung erlaubt dann einen anderen Text.
- Die Tabelle hat 22 Zeilen. Sie ist Text für das Modell, nicht Code; belegt ist sie durch die Trockenläufe und vier echte Läufe, nicht durch einen Test je Zeile.

## Historie

- 2026-11-24: angelegt.
- 2026-11-24: Probelauf Assistiert, Lauf 1 → implementer durfte im Probe-Repo nicht schreiben („sensitive file“). Ursache: Das Probe-Repo lag unter dem Ordner, der per `--plugin-dir` geladen war, und Claude Code schützt Plugin-Dateien. Gegenprobe: dasselbe Schreiben ohne Plugin ging, mit Plugin-Kopie daneben ging es auch. Fix: Plugin aus einer Kopie neben den Probe-Repos laden, als Hinweis in README und `docs/betriebsarten.md`.
- 2026-11-24: Review PR #14, Rework 1. A1: Die Tabelle fiel bei gesehener Spec auf `grill` durch (Tickets teils `Done`, Rest `Backlog`; `In Review` ohne PR; verify „Lücken gefunden“ oder „Mensch nötig“; Blocker in `Backlog`). Ursache: Zeile 12 verlangte „keines in Todo oder weiter“ und `grill` war der Rückfall für alles. Fix: eigene Zeilen 8, 11, 14, 15, 16 neu, `grill` nur ohne offene Spec, sonst eine eigene Zeile mit `NEEDS_CONTEXT` (heute 23). Pre-Push-AI-Review dazu: `Canceled` und `Duplicate` fehlten; jetzt heißt „geschlossen“ `Done`, `Canceled` oder `Duplicate`, und „alle abgebrochen“ hat Zeile 17. A4: Commits nach `MERGE` führen zu Re-Review. A2: Autopilot in Doku und README als vorhanden beschrieben; jetzt „noch nicht nutzbar“ mit Bausteinen und den offenen Schritten (tick, Umschalten), abgesichert durch `check_fab.py`. R1: Rollennamen und README-Tabelle ungeprüft (5 fremde Mutationen überlebten); jetzt geprüft, je ein Kaputt-Test.
- 2026-11-25 (Re-Review PR #14, Punkte 5 und 6): Nach einer retro empfahl fab wieder retro → Zeile 13 hatte kein Ende-Kriterium, und retro hinterlässt im Tracker nichts → Ende über den Status der Spec (siehe Entscheidungen), Test `RetroHasEndTest`. `check_fab.py`: Das Ausführrecht (`X_OK`) war ungetestet (Mutation `X_OK` → `exists` blieb grün), und die Autopilot-Prüfung erkannte nur, ob der Satz irgendwo stand („läuft schon, war lange noch nicht nutzbar“ war grün) → Test mit nicht ausführbarer Datei, Hinweis muss vorn stehen, keine Startanleitung für `slickfab-dispatch`. Mutationsprobe an allen dabei geänderten Regeln (tickets, review, grill, implement, fab, check_fab): **35 Mutationen, 0 überlebt**, auch ohne `test_rule_golden` (Methode wie oben, Gegenprobe grün). Im ersten Anlauf waren es 32 mit 0 Überlebenden; dann fand das Pre-Push-Review zwei Lücken, die keine meiner Mutationen berührt hatte: `BLOCKED` in review hing an „Probe lief nicht“ ohne die Ausnahme für Befunde `Critical`/`Required`, und `slickfab-dispatch` mit Pfad davor (`${CLAUDE_PLUGIN_ROOT}/runtime/herdr/…`, `./…`) blieb unerkannt. Beides mit rotem Test behoben, 3 Mutationen dazu. Die Zahl deckt nur ab, was ich bedacht habe.
- 2026-11-25 (Review PR #17, Optional): `docs/betriebsarten.md` endete den üblichen Weg bei `retro`, das neue Ende fehlte → „… → `retro` → du setzt die Spec auf `Done`“, Test `test_usual_path_in_docs_ends_with_spec_done`. Mutationsprobe auf den Rework (tickets, review, Doku): 15 Mutationen, 0 überlebt, auch ohne Referenz. Die fremde Probe aus dem Review fand 3 Mutationen, die nur die Referenz fängt (Streichen von „ohne Codeblock um Ergebnis oder Marker“, von „Status des Spec-Issues“ in fab Schritt 2, Freitext zwischen Blöcken in review); so ist es vom Ruling am Ticket gewollt.
- 2026-11-25 (Review PR #17, O2): Eine Spec mit challenge-Urteil `nicht bauen` landete über Zeile 19 („Spec ohne Tickets, `challenge`-Kommentar da“) bei `tickets` → Ursache: Die Zeile prüfte das Urteil nicht → neue Zeile 19 (kein Schritt, Mensch entscheidet, `NEEDS_CONTEXT`), tickets-Zeile 20 nur bei `bauen`/`kleiner bauen`, Zeilen ab 20 um eins verschoben, Verweise im Ergebnis nachgezogen. Test `NotBuildVerdictTest` vorher rot. Mutationsprobe im Worktree über alle dabei geänderten Regeln (fab, tickets, review), ohne `test_rule_golden`: **30 Mutationen, 29 rot, 1 überlebt** (Zeile 19 fehlte in der `NEEDS_CONTEXT`-Liste des Ergebnisses, ungetestet) → Test ergänzt, Nachprobe 1 von 1 rot. Gegenprobe vor und nach der Probe grün, Dateien danach unverändert. Eigene Liste; die Zahl deckt nur ab, was ich bedacht habe.
- 2026-11-25 (Review PR #19, Rework 1): A1a: Eine Spec auf `Canceled`, als Argument genannt, galt weiter als offen und landete wieder auf Zeile 19 (dieselbe Klasse wie die `Done`-Schleife aus dem Ticket) → „abgeschlossen“ heißt `Done` oder `Canceled`. A1b: Nach einer Spec-Änderung blieb das letzte Urteil `nicht bauen`, fab empfahl wieder „ändern oder `Canceled`“ → Zeile 18 schickt eine nach dem `challenge`-Kommentar geänderte Spec zurück zu `challenge`, Zeile 19 gilt nur, wenn die Spec seitdem nicht geändert wurde. Die Zeilennummern bleiben gleich. R3: Die Verweise im Fließtext (Zeilen 3 bis 7, 22, 23, die `NEEDS_CONTEXT`- und die Entscheidungsliste) schützte nur die Referenz → `RowReferencesTest` löst jede Nummer über den Inhalt der Zeile auf; mit „Zeile 22 → 21“ und „23 → 22“ rot, die alten Tests blieben dabei grün.
- 2026-11-25 (Review PR #19, Rework 2, N1): Zeile 18 und 19 hingen an „Spec nach dem `challenge`-Kommentar geändert (Verlauf des Issues)“. Diesen Verlauf zeigt Linear nicht, und `updatedAt` steigt schon bei jedem Kommentar; fab konnte die Bedingung nicht sicher lesen → Erkennung über den Änderungskommentar von spec: Liegt ein Kommentar mit erster Zeile `## Spec überarbeitet` zeitlich nach dem letzten `challenge`-Kommentar, gilt Zeile 18 (`challenge`), sonst 19. fab liest diese Kommentare in Schritt 2 mit Zeitpunkt. Der Test holt die erste Zeile aus spec, nicht aus sich selbst. Test vorher rot. Mutationsprobe am Fix im Worktree (spec und fab, ohne `test_rule_golden`): **8 Mutationen, 8 rot**, darunter: anderer Kommentaranfang in spec als in fab, Zeitbedingung gestrichen, Bedingung in Zeile 19 umgedreht, Schritt 2 liest die Überarbeitungen nicht. Gegenprobe vorher und nachher grün.
- 2026-11-27: fab englisch, Tabelle Zeile für Zeile gleich. Wörtlich bleiben die Werte, die fab aus Kommentaren liest (challenge-Urteile `bauen`/`kleiner bauen`/`nicht bauen`, `## Spec überarbeitet`, verify-Status `bestanden`/`Lücken gefunden`/`Mensch nötig`), damit schon geschriebene Kommentare weiter erkannt werden. Benennt verify seine Status um, muss fab mitgehen. `RetroHasEndTest`, `NotBuildVerdictTest` und `RowReferencesTest` lesen jetzt den englischen Wortlaut; Mutationsprobe (Zeile 19 auf tickets, `Canceled` gestrichen, Zeilenverweis 3 bis 7 → 3 bis 6, anderer Kommentaranfang in spec) rot.
