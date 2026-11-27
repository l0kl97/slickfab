# slickfab-dispatch: Entscheidungslogik des Autopiloten

**Status:** aktiv (`decide` und `tick`/`watch`; Dauerbetrieb noch aus) · **Stand:** 2026-11-25 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Der Maintainer will einen Autopiloten, der Tickets parallel bauen, reviewen, nachbessern und mergen lässt und nur an Entscheidungspunkten einen Menschen holt („Ein Lauf wartet nie auf einen Menschen“, drei Bremsen, jede Schleife hat eine Obergrenze). Das Herz davon ist eine reine Funktion `decide(state) → actions`: Sie bekommt einen Schnappschuss (Tickets, laufende Terminals, PRs, Projekt-Schalter) und plant Aktionen. Sie liest und schreibt selbst nichts, deshalb ist jede Kante der Zustandsmaschine mit einem Test belegt.

Am 25.11. fragte der Maintainer, ob slickfab etwas vom neuen `/ship` aus Claude Code übernehmen soll. Nicht als Ganzes (dort reviewt der Bauende selbst, es gäbe eine zweite Steuerung, und `/ship` reagiert auf beliebige Kommentare), aber drei Beobachtungen am PR: Rotes CI und Konflikte mit main gehen nicht mehr als `ready` zum Menschen, sondern zurück an den Umsetzer, und ein Kommentar des Menschen am PR geht nicht mehr unter. Kein Kommentar führt je zu einem Merge.

Der Ausbau mit `tick` macht den Autopiloten lauffähig: Ein `tick` liest den echten Zustand (Linear, Herdr, GitHub, Factory-Konfiguration), fragt `decide` und führt die Aktionen aus, mit `--dry-run`, Lockdatei und Log (Abschnitt „Ausführung“ unten). Er verbraucht genau die Schnittstelle unten; `decide` ist unverändert.

## Schnittstelle (Vertrag für `tick`)

```python
from slickfab_dispatch import decide   # runtime/herdr/slickfab_dispatch.py
actions = decide(state)                # list[dict], wirft nie, verändert state nicht
```

### `state`

Nur JSON-Typen. Fehlende optionale Felder haben den genannten Standard; falsche Typen ergeben `needs_human` mit Grund.

```python
{
  "assignee": "bot@example.com",              # E-Mail des Dispatch-Users; nur seine Tickets werden angefasst
  "projects": {
    "<name>": {
      "enabled": True,                # nur genau True zählt; sonst keine einzige Aktion für das Projekt
      "auto_merge": False,            # nur genau True erlaubt Auto-Merge
      "max_parallel": 3,              # Standard 3; Tickets In Progress/In Review mit Dispatch-Terminal
      "main": {                       # Hauptzweig; alle Felder Text oder None
        "sha": "…", "ci": "green|red|pending",
        "checked_sha": "…",           # Buchführung: SHA, für die post_merge_check schon lief
        "debugged_sha": "…"           # Buchführung: SHA, für die start_debug schon lief
      },
      "merges": 0,                    # Merges im Projekt insgesamt
      "retro_at": 0,                  # Buchführung: Stand von merges bei der letzten Retro
      "comment_authors": ["login"],   # Standard []; GitHub-Logins, deren PR-Kommentare zählen
      "github_ci": "use"              # Standard "use"; "ignore" = pr.ci gilt als None, Auto-Merge wartet
                                      # nicht auf grünes CI (es zählt das Review); anderer Wert → needs_human
    }
  },
  "specs": {"EX-10": {"project": "<name>", "verified": False,
                      "state_type": "started"}},  # Linear-Statustyp der Spec; completed/canceled → kein Verify
  "tickets": [{
    "id": "EX-12", "project": "<name>", "spec": "EX-10",   # spec = Eltern-Issue
    "status": "Backlog|Todo|In Progress|In Review|Done|Canceled|Duplicate",   # Linear-Statusname
    "assignee": "…" ,                 # E-Mail oder None
    "labels": ["S", "door:one-way", "slickfab:ready"],   # Gruppen-Labels als slickfab:<name>
    "blockers": [{"id": "EX-11", "state_type": "started"}],  # Linear „blockiert von“ + state.type
    "files": ["runtime/herdr/x.py"],  # voraussichtlich betroffene Dateien (Agent notes)
    "rework_rounds": 0,               # Anzahl SLICKFAB-VERDICT: REWORK am Ticket bisher (inkl. aktuellem)
                                      # plus gebuchte Runden ohne Verdict (SLICKFAB-ROUND);
                                      # zählt am Ticket über alle Umsetzer hinweg, nie je Terminal zurücksetzen
    "human_gate": False,              # Standard False; True = ein Kommentar holte es aus ready (SLICKFAB-GATE),
                                      # danach nie Auto-Merge (Ruling des Masters, Review A3); kein bool → needs_human
    "pr": None | {"number": 7, "ci": "green|red|pending" | None,   # anderer Wert → needs_human
                  "paths": ["…"] | None,
                  "head": "<sha>", "merged": False,
                  "mergeable": "MERGEABLE|CONFLICTING|UNKNOWN" | None,   # fehlt = None; anderer Wert → needs_human
                  "comments": [{"author": "login" | None, "at": 1700000000000,   # ms, dieselbe Uhr wie seq
                                "url": "https://…", "body": "…"}]}   # Standard []
  }],
  "terminals": [{                     # alle Herdr-Terminals, auch fremde
    "id": "t9z",
    "labels": {"slickfab.dispatch": "1", "studio.role": "implementer|reviewer|check|debug|retro|verify",
               "studio.issue": "EX-12 | <projektname> | <spec-id>",
               "slickfab.restarts": "0",   # Neustarts dieses Laufs (fehlend = 0)
               "slickfab.head": "<sha>"},  # nur Reviewer: geprüfter PR-Head
    "status": "working|blocked|done|idle|dead",
    "report": "… letzte Rückmeldung (hc send / letzter Kommentar) … | None",
    "seq": 17                          # Reihenfolge der letzten Aktivität, größer = jünger
  }]
}
```

Hinweise für das Lesen:
- `status` `done` und `idle` gelten gleich als „fertig“ (Herdr meldet nach einem Turn `done`, Kommentar am Ticket). `blocked` heißt Berechtigungsabfrage: `decide` wartet und beantwortet sie nie. `dead` setzt der Leser, wenn der Agent-Prozess weg ist oder `first_message.sent` nicht kam.
- `seq` wächst mit jeder Aktivität eines Terminals (Start, gesendete Nachricht, Turn beendet), **nicht** mit dem Wechsel auf `dead`. Das jüngste Terminal eines Tickets ist der aktuelle Schritt und bestimmt, wessen Marker gilt (nach `send_rework` ist der Umsetzer wieder das jüngste). Ältere Terminals sind überholt: `decide` startet sie nie neu, und ihr Status hält nichts auf. Für Projekt-Rollen gilt dasselbe je Issue und Rolle.
- Ist der Umsetzer bei `REWORK` in Runde 1–2 tot oder weg, plant `decide` einen frischen Umsetzer (`start_implementer`, `fresh`, gleiche Runde). Das ist kein Neustart nach Absturz und zählt nicht gegen den Neustart-Deckel; die Rundenzahl bleibt am Ticket.
- Der Neustart-Deckel gilt je Ticket (bzw. Projekt-Issue) und Rolle: das Maximum von `slickfab.restarts` über alle Terminals dieser Rolle, auch über ersetzte. Die Ausführung muss den Zähler deshalb am neuen Terminal setzen, alte Terminals darf sie schließen, muss aber nicht.
- `report` ist der rohe Text; `decide` liest den Marker-Block selbst (exakte Zeilen aus `tracker/linear.md`).
- Projekt-Rollen (`check`, `debug`, `retro`) tragen als `studio.issue` den Projektnamen, `verify` die Spec-ID.
- Ein Ticket mit eigenem Dispatch-Terminal gilt als laufend, auch wenn Linear noch `Todo` zeigt (zählt für `max_parallel`, Dateischutz und Wächter). Für Obergrenze und Dateischutz zählen auch Tickets mit Halt-Label (`ready`, `needs-human`, `replan`) und solche mit unlesbaren Daten; Aktionen plant `decide` für sie keine. Ein Ticket mit unlesbaren Daten bekommt `needs_human`, außer es trägt schon `slickfab:needs-human` (lesbare Labels vorausgesetzt): dann bleibt `decide` still, damit nicht jeder Tick einen neuen Kommentar erzeugt. `ready` und `replan` stellen unlesbare Tickets nicht still.
- `projects`-Einträge, die kein Objekt sind, gelten als nicht freigeschaltet und werden übersprungen. Doppelte Ticket-IDs oder ein unerwarteter Fehler halten nur das betroffene Projekt an (`needs_human` mit `project`, ohne `ticket`), die anderen laufen weiter.
- Terminals, deren `studio.issue` kein Text ist, ignoriert `decide` vollständig.
- PR-Kommentare: Es zählt ein Kommentar, dessen `author` (Groß/klein egal) in `comment_authors` des Projekts steht, der kein Bericht einer Rolle ist (letzte Zeile beginnt mit `SLICKFAB-STATUS:`) und dessen `at` größer ist als `seq` des jüngsten Umsetzer-Terminals (ohne Umsetzer: des jüngsten Terminals). `at` und `seq` sind deshalb beide Millisekunden derselben Uhr.

### `actions`

Jede Aktion ist ein Dict mit `action`; Reihenfolge: je Projekt (alphabetisch) erst Starts, dann laufende Tickets, dann Projekt-Aktionen; Tickets nach Nummer.

| `action` | Felder | Bedeutung für die Ausführung |
|---|---|---|
| `start_implementer` | `ticket, project, model, effort, worktree, fresh` (+ `round, pr` bei Nachbessern) | `slickfab-worktree add <worktree>` (bei `fresh` mit `round` den vorhandenen Branch/PR weiterführen), `slickfab-run --model <model>` (Alias: `sonnet` = Sonnet 5.5, `opus` = Opus 5.5), bei `effort` ungleich None mit dieser Reasoning-Effort, Labels `slickfab.dispatch=1`, `studio.role=implementer`, `studio.issue` |
| `start_reviewer` | `ticket, project, pr, head, worktree` | `slickfab-worktree review <pr>`; Label `slickfab.head=<head>` setzen |
| `send_rework` | `ticket, project, terminal, round, pr` (+ `cause`, `comments`) | Nachbesserung an dasselbe Terminal; Status vorher prüfen, ohne `--if idle` senden, nie bei `blocked` |
| `restart_agent` | `ticket` (oder None), `project, terminal, role, handoff, restarts, reason` | Agent für `terminal` neu starten (neues Terminal mit höherem `seq` oder dasselbe), Übergabe mitgeben, `slickfab.restarts=<restarts>` am laufenden Terminal setzen |
| `merge` | `ticket, project, pr, head` | nur mergen, wenn der PR-Head noch `head` ist (`gh pr merge --match-head-commit`) |
| `label` | `ticket, project, label, reason` | `slickfab:ready` oder `slickfab:replan` setzen, Grund als Kommentar |
| `needs_human` | `ticket` (oder None), `project` (oder None), `reason` | Label `slickfab:needs-human` + Kommentar mit Grund; ohne Ticket an den Master melden |
| `post_merge_check` | `project, sha` | Prüfung auf main; danach `checked_sha` merken |
| `start_debug` | `project, sha` | Debug-Rolle; danach `debugged_sha` merken |
| `start_retro` | `project, merges` | Retro; danach `retro_at = merges` merken |
| `start_verify` | `project, spec` | Verify der Spec; Ergebnis setzt `verified` |

Optionale Felder bei `send_rework` und beim nachbessernden `start_implementer`: `cause` ist eine Liste aus `ci` (PR-CI rot), `conflict` (Konflikt mit main), `comment` (neuer PR-Kommentar eines erlaubten Autors) und steht nur, wenn die Runde **kein** REWORK-Verdict hat; die Ausführung bucht sie dann am Ticket. `comments` sind die URLs der neuen Kommentare, die der Umsetzer bearbeiten soll (auch zusammen mit einem REWORK-Verdict, dann ohne `cause` und ohne eigene Runde). `unlabel: "slickfab:ready"` steht, wenn ein Kommentar ein `ready`-Ticket zurückholt; die Ausführung nimmt das Label nach Auftrag und Buchung ab.

## Ausführung: `slickfab-dispatch`

```
runtime/herdr/slickfab-dispatch tick  [--dry-run] [--config <factory.json>]
runtime/herdr/slickfab-dispatch watch [--dry-run] [--interval <sek>] [--config <factory.json>]
```

- **tick:** Lockdatei nehmen → alles lesen (`hc ls --all --json`, je freigeschaltetem Projekt Linear-Issues per GraphQL und `gh api graphql`) → `decide(state)` → jede Aktion ausführen. Jede geplante Aktion steht als `PLAN {json}` auf stdout und im Log. `--dry-run` hört nach den Plänen auf: kein Aufruf, der Linear, Herdr, Git oder GitHub ändert, keine Buchführung.
- **watch:** tick beim Start, nach jedem Ereignis aus `hc events --json --label slickfab.dispatch=1` (Herzschläge zählen nicht, Ereignisse innerhalb von 2 s fallen zusammen) und spätestens alle `--interval` Sekunden (Standard 300). Endet `hc events`, läuft der Ersatz-tick weiter und `hc events` startet beim nächsten Warten neu. Als Dienst einrichten gehört zum Umschalten.
- **Exit:** 0 ok · 1 Lesefehler, nichts ausgeführt · 2 Aufruf oder Konfiguration falsch, nichts getan · 3 einzelne Aktionen gescheitert (ihr Ticket hat `needs-human`) · 75 ein anderer tick hält die Lockdatei.
- **Ablage** (`state_dir`, nie im Repo): `dispatch.lock`, `dispatch.log`, `bookkeeping.json` (Buchführung je Projekt: `checked_sha`, `debugged_sha`, `retro_at`, `verified`).

### Factory-Konfiguration (Beispiel ohne echte Werte)

Liegt privat in `~/.config/slickfab/factory.json` (anderer Pfad: `--config` oder `SLICKFAB_FACTORY`). Der Linear-Schlüssel steht nie darin, nur der Pfad zur Schlüsseldatei.

```json
{
  "assignee": "dispatch-user@example.com",
  "linear_key_file": "~/.config/studio-board/linear-key",
  "state_dir": "~/.local/state/slickfab",
  "worktree_root": "~/.herdr/worktrees",
  "timeout": 30,
  "pr_comment_authors": ["github-login"],
  "projects": {
    "beispiel": {
      "enabled": false,
      "auto_merge": false,
      "max_parallel": 3,
      "linear_project": "Beispiel",
      "repo": "~/code/beispiel",
      "github": "owner/beispiel",
      "github_ci": "use",
      "space": "-"
    }
  }
}
```

Pflicht: `assignee`, `linear_key_file`, `state_dir`, `projects`, je Projekt `enabled` (`true` oder `false`, kein Standardwert). Für freigeschaltete Projekte zusätzlich `linear_project`, `repo` (vorhandener Ordner, Haupt-Checkout) und `github` (`owner/name`). Optional: `auto_merge` (Standard `false`), `max_parallel` (Standard 3), `space` (Herdr-Space-ID oder `-` für keinen Space, Standard `-`), `github_ci` (`use` oder `ignore`, Standard `use`; bei `ignore` gelten GitHub-Checks als nicht vorhanden: für main zählt nur die lokale Post-Merge-Prüfung, für PRs nur das Review. Für Repos, deren Actions nicht laufen, etwa wegen aufgebrauchtem Free-Tier-Kontingent.  Achtung: `ignore` schaltet damit auch die serverseitigen Checks als Bremse ab, etwa Secret-Scan (gitleaks) und Abhängigkeits-Audit aus `.github/workflows/security.yml`. Ein roter Befund dort hält dann weder main noch einen PR auf; einzige Bremse bleibt der lokale Pre-Push (slickrails).), `worktree_root` (Standard `~/.herdr/worktrees`; geht immer als `--root` an `slickfab-worktree`, Worktrees liegen unter `<worktree_root>/<Ordnername des Repos>/<name>`), `timeout` (Sekunden je Aufruf, Standard 30), `pr_comment_authors` (GitHub-Logins, deren Kommentare am PR der Dispatcher beachtet, Standard `[]` = keine), `linear_api` (nur `https://`, für Tests `http://127.0.0.1`). Fehlt etwas oder ist es falsch, tut der tick nichts, nennt jedes falsche Feld und endet mit 2.

### Vom echten Zustand zu `state`

| Feld | Quelle |
|---|---|
| Tickets | Linear-Issues des Projekts (`linear_project`), seitenweise je 100, bis 2000; Kommentare je Issue seitenweise je 100 |
| `status`, `assignee`, `spec` | Statusname, E-Mail des Assignees, Eltern-Issue |
| `labels` | Labelnamen; Kinder der Gruppe `slickfab` als `slickfab:<name>` |
| `blockers` | Relationen „blocks“ auf das Ticket mit `state.type` des Blockers |
| `files` | Pfade in Backticks aus der Liste nach „Betroffene Dateien“ (Agent notes) |
| `human_gate` | ein Kommentar des Dispatch-Users mit der Zeile `SLICKFAB-GATE: human` (geschrieben in der Buchung, wenn ein Kommentar das Ticket aus `ready` holt); fremde Autoren zählen nicht |
| `rework_rounds` | Kommentare des Dispatch-Users (`assignee`), deren Marker-Block `SLICKFAB-VERDICT: REWORK` trägt oder die eine Zeile `SLICKFAB-ROUND: <n>` enthalten (gebuchte Runde ohne Verdict); alle Seiten, je 100 |
| `pr` | PR mit Branch = Ticket-ID klein (Worktree-Name aus `decide`), offener vor gemergtem; `ci` aus dem Check-Rollup des letzten Commits (SUCCESS → green, FAILURE/ERROR → red, PENDING/EXPECTED → pending, keiner → None, anderer Wert unverändert → `decide` meldet ihn); `paths` None, wenn der PR mehr als 100 Dateien hat; `mergeable` unverändert aus GitHub (fehlt → None); `comments` aus den letzten 30 Kommentaren und den letzten 30 abgeschickten Reviews (`createdAt` bzw. `submittedAt` als ms, Entwürfe ohne Zeit fehlen) |
| `github_ci` | `github_ci` des Projekts aus der Factory-Konfiguration; bei `ignore` geht der Check-Rollup von main nicht in `main.ci` ein (nur die lokale Prüfung zählt), `pr.ci` blendet `decide` aus |
| `comment_authors` | `pr_comment_authors` aus der Factory-Konfiguration, für jedes Projekt gleich; nie aus Ticketdaten |
| `main` | Hauptzweig: SHA; `ci` aus Check-Rollup **und** lokaler Post-Merge-Prüfung derselben SHA (rot gewinnt, fehlendes CI ist weder grün noch rot, ein Wert außerhalb des Vertrags geht unverändert weiter); `checked_sha`, `debugged_sha` aus der Buchführung |
| `merges`, `retro_at` | gemergte PRs auf GitHub; `retro_at` aus der Buchführung, bei der ersten Sicht = `merges` |
| `specs` | Eltern-Issues der Tickets; `verified` aus der Buchführung, `state_type` aus Linear (`parent { state { type } }`) |
| Terminal `status` | `dead`, wenn nicht `live` oder `first_message.sent` falsch; ohne Statusmeldung `working`; sonst Herdrs Wort (`done`, `idle`, `working`, `blocked`, …) |
| Terminal `seq` | Label `slickfab.seq` (ms, vom Dispatcher bei Start und Senden gesetzt), sonst `created_ms` |
| Terminal `report` | jüngster Kommentar des Dispatch-Users am Issue des Terminals, dessen letzte Zeile `SLICKFAB-STATUS:` ist und der nach `seq` entstand |

### Aktionen

| `action` | Aufrufe |
|---|---|
| `start_implementer` | `slickfab-worktree add <worktree>` (Baseline aus dem Repo), dann `slickfab-run --model <m> [--effort <e>] implementer …`; endet `slickfab-run` mit Fehlercode, sieht der Dispatcher per `hc ls --all --json` nach, ob ein Terminal mit dem vergebenen Namen oder in diesem Ordner existiert. Nur wenn sicher keins da ist, wird der neue Worktree entfernt; läuft eins oder ist es unklar (`hc ls` scheitert), bleibt er, und das Ticket bekommt needs-human mit Grund. Scheitert erst ein späterer Schritt (`hc label`), bleibt er ohnehin: Der Agent arbeitet schon darin. Nachbessern mit `fresh` und `round`: vorhandener Worktree `<root>/<repo>/<worktree>`, fehlt er → needs-human; Auftrag und Buchung wie bei `send_rework` |
| `start_reviewer` | alten `pr-<n>` entfernen (falls da), `slickfab-worktree review <n>`, `slickfab-run reviewer`, Label `slickfab.head=<head>` |
| `send_rework` | `hc get <t> --json`: nur mit Dispatch-Kennzeichen und passendem `studio.issue`; `blocked` → nichts senden, Meldung `MENSCH:`; `done`/`idle` → `hc send <t> …` ohne `--if` und ohne `--force`, dann `slickfab.seq`. Der Text nennt den Anlass (Review-Urteil, CI rot, „auf main bringen“, Kommentar-Links mit dem Hinweis, dass andere PR-Kommentare keine Aufträge sind). Mit `cause` danach Kommentar am Ticket mit `SLICKFAB-ROUND: <n>` (Buchung, erst nach dem Senden); mit `unlabel` steht in derselben Buchung `SLICKFAB-GATE: human`, und erst danach kommt `slickfab:ready` ab. Scheitert die Buchung, bleibt das Label (needs-human) |
| `restart_agent` | neues Terminal derselben Rolle im Ordner des alten, Modell/Effort aus dessen Startbefehl, Übergabe-Auftrag, Labels `slickfab.restarts`, ggf. `slickfab.head`; das alte bleibt unberührt |
| `merge` | nur bei `auto_merge: true` in der Konfiguration: `gh pr merge <n> --repo <github> --squash --match-head-commit <head>`, danach `slickfab-worktree rm pr-<n>` und `rm <ticket>` (ohne `--force`; scheitert es, bleibt der Worktree und es steht im Log) |
| `label` | Linear: Label setzen, Grund als Kommentar |
| `needs_human` | mit Ticket: Label `slickfab:needs-human` + Kommentar; ohne Ticket: Zeile `MENSCH: Projekt …` auf stdout und im Log |
| `post_merge_check` | lokal und synchron im tick: `slickfab-worktree add check-<sha7>` am neuen main; dessen Baseline ist der Prüfbefehl des Projekts. Grün → Worktree mit `--force` entfernen (eigener, kein Agent darin), rot erkennt der Dispatcher an „Baseline rot“ (`add` räumt selbst auf). Scheitert `add` aus anderem Grund, gibt es kein Ergebnis (`MENSCH:`). Gebucht werden `checked_sha` und `check = {sha, result}` (Ruling unten) |
| `start_debug` | `slickfab-worktree add debug-<sha7> --check true`, Rolle `debugger` mit `studio.role=debug`, `debugged_sha` merken; Rollback des Worktrees wie bei `start_implementer` |
| `start_retro` | Rolle `retro` im Haupt-Checkout, `retro_at = merges` merken |
| `start_verify` | Rolle `verifier` mit `studio.role=verify`, `studio.issue=<spec>`, Spec als `verified` merken |

Jeder Start läuft über `slickfab-run` mit einem Namen, den der Dispatcher vergibt (`<rolle>-<issue>-<hex>`); danach setzt `hc label <name>` `studio.role` auf den Namen aus `decide` und `slickfab.seq`. Adressiert wird über diesen Namen, nie über eine aus der Textausgabe von `hc run` geratene Adresse. Der Auftrag nennt Ticket, Repo, Worktree und verlangt die Rückmeldung als Linear-Kommentar mit Marker-Block, beim Reviewer ausdrücklich mit VERDICT-Zeile. `--model` und `--effort` kommen nur aus `decide` bzw. dem eigenen Startbefehl, nie aus Titel, Labels oder Kommentaren eines Tickets.

Scheitert eine Aktion (auch mit unerwartetem Fehler), bekommt ihr Ticket `slickfab:needs-human` mit dem Grund; eine Aktion ohne Ticket meldet sich mit `MENSCH: Projekt …`. Die übrigen laufen weiter. In `watch` beendet auch ein unerwarteter Fehler eines ticks nie die Schleife. Wartet ein eigenes Terminal auf eine Berechtigung, steht in jedem tick `MENSCH: <t> (<issue>) wartet auf eine Berechtigung` im Log; der Dispatcher tippt nie hinein.

## Regeln und Tests (Regel → Testname in `tests/test_dispatch.py`)

| Regel | positiv | negativ |
|---|---|---|
| **Starten:** Todo, Assignee = `assignee`, keine offenen Blocker, kein Dateiüberschnitt mit laufendem oder im selben Tick gestartetem Ticket, unter `max_parallel` → Umsetzer, Modell nach Größe (S → sonnet, M und L → opus) | `StartRule.test_free_todo_ticket_of_bot_starts_with_model_by_size`, `test_blocker_done_or_canceled_frees_ticket`, `test_disjoint_files_both_start` | `test_blocked_ticket_never_starts`, `test_ticket_of_kim_or_without_assignee_never_starts`, `test_not_todo_never_starts`, `test_two_free_tickets_sharing_a_file_only_one_starts`, `test_file_overlap_with_running_ticket_blocks_start`, `test_parallel_limit_reached_blocks_start`, `test_running_implementer_means_no_second_start`, `test_started_ticket_still_on_todo_counts_as_running`, `test_halted_ticket_with_terminal_counts_for_files_and_limit`, `test_done_ticket_with_leftover_terminal_frees_slot_and_files` |
| **Review:** jüngstes Terminal = fertiger Umsetzer mit `DONE`/`DONE_WITH_CONCERNS` und offenem PR → Reviewer am PR-Head | `ReviewRule.test_done_with_open_pr_starts_reviewer_at_pr_head`, `test_idle_counts_like_done` | `test_still_working_means_wait`, `test_permission_prompt_is_never_answered`, `test_done_without_pr_needs_human`, `test_merged_or_closed_pr_is_not_reviewed`, `test_running_reviewer_means_no_second_reviewer` |
| **Nachbessern:** `REWORK` Runde 1–2 → `send_rework` an denselben Umsetzer, Runde 3 → frischer auf Opus mit Effort `high`, ab Runde 4 `needs_human` | `ReworkRule.test_rework_sequence_1_2_3_4`, `test_round_3_is_opus_with_higher_effort_for_every_size`, `test_finished_implementer_in_state_done_gets_rework_like_idle`, `test_implementer_gone_starts_fresh_one_on_same_model`, `test_dead_old_implementer_gets_fresh_one_for_rework`, `test_fresh_implementer_takes_over_round_count` | `test_rework_sequence_1_2_3_4` (Runde 4), `test_rework_never_typed_into_blocked_terminal`, `test_rework_without_round_count_needs_human` |
| **Zurück zum Planer:** `REPLAN` → Label `slickfab:replan`, sonst nichts | `ReplanRule.test_replan_sets_label_and_nothing_else` | `test_ticket_with_replan_label_gets_no_action` |
| **Merge:** `MERGE` → `merge` nur wenn alles zutrifft, sonst `slickfab:ready` mit Gründen | `MergeRule.test_all_conditions_met_auto_merges_at_reviewed_head`, `test_harmless_paths_are_not_sensitive` | `test_each_single_violation_leads_to_ready`, `test_ci_pending_or_unknown_waits_instead_of_ready`, `test_ci_value_outside_contract_needs_human`, `test_sensitive_paths_lead_to_ready`, `test_unknown_paths_lead_to_ready`, `test_head_moved_since_review_is_not_merged`, `test_reviewer_blocked_with_verdict_needs_human`, `test_ticket_already_ready_or_merged_gets_no_action` |
| **PR-Beobachtung:** `MERGE` mit rotem CI oder `CONFLICTING` → Nachbessern (Anlass `ci`/`conflict`, Runde = `rework_rounds` + 1, gleiche Obergrenze), auch wenn Auto-Merge sonst ausgeschlossen wäre; `UNKNOWN`/fehlend → nie Merge. Neuer Kommentar eines erlaubten Autors → Nachbessern (Anlass `comment`) bzw. ab der Obergrenze `needs_human`, bei REWORK in derselben Runde, bei REPLAN bleibt es beim Label. An einem Ticket mit `slickfab:ready` (dann liest der Mensch) holt ein neuer Kommentar es zurück: Runde mit Anlass `comment`, Label ab, nie ein Merge; `needs-human` und `replan` bleiben still | `PrWatch.test_merge_with_red_ci_is_reworked_not_ready`, `test_red_ci_rework_even_when_auto_merge_is_excluded_anyway`, `test_conflicting_pr_is_brought_onto_main_whatever_else_holds`, `test_red_ci_and_conflict_are_one_round`, `PrComments.test_comment_of_allowed_author_goes_back_to_implementer_instead_of_merge`, `test_author_match_ignores_case`, `test_comment_after_implementer_done_comes_before_the_review`, `test_comment_with_rework_verdict_is_the_same_round`, `test_comment_during_review_is_not_lost_behind_the_reviewer`, `test_comment_with_red_ci_or_conflict_names_every_cause`, `ReadyComments.test_comment_on_ready_ticket_goes_back_and_takes_the_label_off`; Ausführung `test_dispatch_tick.PrWatch.*` | `PrWatch.test_red_ci_rework_respects_the_rework_cap`, `test_unclear_mergeability_is_never_merged`, `test_mergeable_outside_contract_needs_human`, `PrComments.test_comments_of_other_authors_are_ignored`, `test_agent_report_under_same_login_is_not_a_human_comment`, `test_comment_the_implementer_already_got_is_not_fresh`, `test_comment_while_reviewer_works_waits_for_the_verdict`, `test_comment_rounds_respect_the_cap_and_then_go_to_the_human`, `test_no_comment_ever_leads_to_a_merge`, `test_replan_keeps_its_label_despite_a_comment`, `test_comment_on_merged_pr_does_nothing`, `test_unreadable_comment_fields_need_human`, `ReadyComments.test_ready_ticket_without_fresh_comment_stays_with_the_human`, `test_ticket_back_from_ready_by_comment_never_auto_merges`, `test_unreadable_human_gate_needs_human`, Tick `test_ready_label_stays_when_booking_fails`, `test_marked_ticket_goes_to_ready_again_instead_of_merge`, `test_ready_comment_respects_the_cap_and_never_merges`, `test_ready_comment_waits_while_an_agent_works_and_ignores_merged_prs`, `test_other_halt_labels_stay_halted`; `ReadFailures.test_github_comment_with_odd_date_is_a_read_error` |
| **Nach dem Merge:** neue main-SHA → Prüfung; frei gewordene Tickets starten; je 10 Merges Retro; Spec fertig → Verify; main rot → Debug | `AfterMerge.test_new_main_commit_gets_post_merge_check_once`, `test_merged_blocker_frees_waiting_ticket`, `test_every_tenth_merge_starts_retro`, `test_all_tickets_of_spec_done_starts_verify`, `test_red_main_starts_debug_once_per_commit` | dieselben Tests (geprüft/laufend/unter 10/grün → nichts), `test_verify_waits_for_open_tickets_and_runs_once`, `test_closed_spec_gets_no_verify`, `test_verify_only_for_specs_of_own_project`, `test_dead_verify_agent_of_foreign_project_is_not_restarted` |
| **Wächter:** toter Agent einmal neu mit Übergabe, dann `needs_human`; `BLOCKED` → `needs_human`; `NEEDS_CONTEXT` → einmal Neustart, dann `needs_human` | `Watcher.test_dead_agent_first_restart_then_needs_human`, `test_dead_reviewer_is_restarted_too`, `test_needs_context_restarts_once_with_handoff`, `StartRule.test_dead_implementer_on_todo_ticket_is_watched`, `AfterMerge.test_dead_project_agent_restarts_once`, `test_dead_project_agent_is_watched_even_without_due_work` | `test_restart_cap_counts_per_ticket_and_role`, `test_restart_cap_is_per_role`, `test_obsolete_dead_terminal_is_never_restarted`, `AfterMerge.test_project_agent_restart_cap_and_obsolete_terminals`, `test_living_agent_is_not_restarted`, `test_blocked_marker_needs_human`, `test_garbled_restart_counter_needs_human`, `test_unknown_role_on_ticket_needs_human`, `test_unknown_terminal_status_needs_human` |
| **Grenzen:** nur `enabled`-Projekte, nur Terminals mit `slickfab.dispatch=1` | `Boundaries.test_busy_state_has_work_for_every_rule` | `test_project_without_enabled_gets_no_action`, `test_ticket_of_unknown_project_gets_no_action`, `test_terminals_without_dispatch_label_get_no_action`, `test_foreign_terminal_on_todo_ticket_blocks_start`, `test_foreign_terminal_with_odd_labels_is_ignored` |
| **Kein Raten:** fehlender/unbekannter Marker, Reviewer ohne VERDICT, widersprüchliche Labels, unbekannte Größe, kaputter Zustand → `needs_human` mit Grund | `Markers.test_marker_with_trailing_whitespace_is_read` | `Markers.*`, `Labels.*`, `StartRule.test_unknown_or_missing_size_needs_human_instead_of_start`, `Robustness.*`, `Robustness.test_error_inside_one_project_does_not_stop_another` |
| **Idempotent und rein** | `Idempotence.test_same_state_twice_gives_same_actions`, `test_order_of_input_lists_does_not_matter` | `test_started_actions_are_not_planned_again`, `test_state_is_not_modified`, `Robustness.test_no_network_no_processes_no_files` |

**Auto-Merge-Bedingungen** (alle müssen zutreffen, sonst `slickfab:ready` mit allen verletzten Gründen): Größe S · kein `door:one-way` · PR-CI `green` (bei `red` → Nachbessern statt ready; bei `pending` oder `None` keine Aktion, Auto-Merge wartet; ein Wert außerhalb des Vertrags wie `failure` oder `GREEN` ist ein Lesefehler → `needs_human` mit Grund; außer eine andere Bedingung schließt ihn ohnehin aus → sofort ready; Entscheidung des Masters) · geänderte Pfade bekannt und keiner sensibel · Projekt `auto_merge` genau `True` · Reviewer-STATUS `DONE` (nicht `DONE_WITH_CONCERNS`) · PR-Head = vom Reviewer geprüfter Head (`slickfab.head`) · `mergeable` genau `MERGEABLE` (`CONFLICTING` → Nachbessern; `UNKNOWN` oder fehlend → keine Aktion wie bei CI `pending`, außer eine andere Bedingung schließt Auto-Merge aus → ready) · kein neuer Kommentar eines erlaubten Autors (sonst Nachbessern) · `human_gate` nicht gesetzt (Ticket war nie per Kommentar aus `ready` zurückgeholt; sonst ready).
Sensible Pfade (Groß/klein egal): enthält `auth` oder `migrat`; Segment beginnt mit `.env`; `rls` als eigenes Wortstück; `.github/workflows/`, `.githooks/`, `.slickrails/`, `.claude/`, `.codex/`, das ganze Plugin-Verzeichnis `hooks/` (Hook-Konfiguration und Wächter wie `docs_lookup_guard.py`) und der Autopilot selbst: `runtime/herdr/slickfab_dispatch.py` (Regeln) und sein ausführender Teil `runtime/herdr/slickfab-dispatch` und `runtime/herdr/slickfab-run`, dazu `runtime/herdr/slickfab-worktree` (Baseline, Vergleich der Testanzahl) und `runtime/herdr/slickfab_templates.py`/`runtime/herdr/gen-templates` (übersetzen `disallowedTools` in `claude --disallowedTools`), außerdem die Rollen in `agents/` (nur auf Repo-Ebene, ein `src/agents/` in einem App-Projekt gilt nicht) und die erzeugten Vorlagen in `runtime/herdr/templates/`, weil dort die Werkzeuggrenzen stehen. Ebenso `skills/review/` (dort steht, wann der Reviewer `MERGE` schreibt), der Prüfbefehl `tests/run.sh` mit `tests/check_*.py` und `.slickfab/` (Fabrik-Konfiguration); normale Testdateien wie `tests/test_*.py` bleiben nicht sensibel. RLS wird nur am Pfadnamen erkannt: eine Policy-Datei ohne `rls` im Namen (z. B. `supabase/policies.sql`) geht durch, wenn sie nicht unter `migrations/` liegt.

## Entscheidungen

- **Reine Funktion über Dicts statt Klassen:** Das Folgeticket baut den Zustand aus JSON (Linear, `hc get --json`); Dicts lassen sich als Fixture schreiben und ins Log kippen. Verworfen: Dataclasses (zusätzliche Umwandlung ohne Gewinn in 3.9).
- **Idempotenz aus dem Zustand, nicht aus einem Gedächtnis:** Läuft für ein Ticket ein Terminal (`working`/`blocked`), wird nichts geplant. Für Projekt-Aktionen merkt sich die Ausführung SHA bzw. Zählerstand (`checked_sha`, `debugged_sha`, `retro_at`, `verified`).
- **Jüngstes Terminal entscheidet** (`seq`): löst „wessen Marker gilt?“ ohne Zeitstempel-Vergleich mit Linear-Kommentaren. Ein Reviewer, der ohne VERDICT endet, ist das jüngste Terminal → `needs_human` (Hinweis aus dem Ticket).
- **Ticket in Arbeit ohne eigenes Dispatch-Terminal** wird nicht angefasst (Handbetrieb, z. B. ein vom Master gestarteter Umsetzer). Ein fremdes Terminal am Todo-Ticket verhindert auch den Start.
- **Modelle (vom Maintainer entschieden am 2026-11-24):** S → Sonnet 5.5, M und L → Opus 5.5. Runde 3 der Nachbesserung: frischer Umsetzer auf Opus 5.5 mit höherer Reasoning-Effort (`effort: "high"`); bei S also Wechsel Sonnet → Opus, bei M/L gleiches Modell mit mehr Effort. Ersetzt das erste Ruling (S/M → Sonnet).
- **Strenger als die Spec** (Ruling am Issue): Auto-Merge zusätzlich nur bei Reviewer-STATUS `DONE` und unverändertem PR-Head, und `.githooks/`, `.slickrails/` gelten als sensibel, weil sie die Bremsen selbst sind; `.claude/`, `.codex/` und `hooks/hooks.json` kamen auf Entscheidung des Masters dazu, nach dem Rebase auf main das ganze `hooks/` und der Dispatcher selbst (Pre-Push-Review, vom Master freigegeben). Kosten falls falsch: ein paar PRs mehr warten auf den Menschen.
- **Wirft nie:** Erst Typprüfung je Ticket/Terminal/Projekt (falsche Typen → `needs_human` für genau dieses Ticket, die anderen laufen weiter), dazu ein Sicherheitsnetz je Projekt und eines um alles (`needs_human` ohne Ticket, Grund „Zustand unlesbar“). Doppelte Ticket-IDs halten nur ihr Projekt an.

- **Umbenennung zählt mit dem alten Pfad** (security-review PR #18): Die GraphQL-Dateiliste nennt nur den neuen Pfad; ein PR, der `hooks/role_bash_guard.py` nach `misc/x.py` verschiebt, hätte die Bremse ausgehebelt. GraphQL liefert dazu `changeType`; meldet ein offener PR eine Umbenennung (`RENAMED`), holt `tick` die REST-Dateiliste (`gh api repos/<o>/<r>/pulls/<n>/files?per_page=100`) und nimmt jedes `previous_filename` in die Pfade auf. Scheitert der Aufruf, ist das ein Lesefehler wie jeder andere GitHub-Fehler (keine Aktion). Fehlt der alte Pfad in der Antwort oder hat sie eine andere Form, gelten die Pfade als unbekannt (kein Auto-Merge). Ohne Umbenennung gibt es keinen zusätzlichen Aufruf.
- **Ausführung getrennt von `decide`**: `slickfab-dispatch` ist das Programm mit allen Aufrufen, `slickfab_dispatch.py` bleibt die reine Funktion. Erst wird alles gelesen; scheitert ein Lesen, wird nichts ausgeführt.
- **Lockdatei mit `flock`:** Die Sperre hängt am offenen Dateideskriptor, das System gibt sie frei, wenn der Prozess stirbt. Eine liegengebliebene Datei blockiert deshalb nie. Verworfen: PID in der Datei prüfen (PID-Wiederverwendung, Rennen).
- **`seq` als Label:** Der Dispatcher setzt `slickfab.seq` (Millisekunden) bei jedem Start und jedem `send_rework`. Nach einem Nachbesserungs-Auftrag (`send_rework`, frischer Umsetzer) ist es der Zeitpunkt vor dem Lesen des ticks, nicht der des Sendens: PR-Kommentare bis `seq` gelten als übergeben, und ein Kommentar zwischen Lesen und Senden wäre sonst verloren (Pre-Push-Review). Herdrs eigene Zeitstempel (`status_ms`, `turn`) ändern sich auch, wenn ein altes Terminal von `done` auf `idle` wechselt, und würden das „jüngste Terminal“ verschieben.
- **Bericht aus Linear statt vom Bildschirm:** Die Rollen schreiben ihren Abschluss als Kommentar (Rollenvertrag). Der jüngste Marker-Kommentar nach `seq` des Terminals ist dessen `report`. Der Bildschirm enthält den Rollentext mit Beispiel-Markern und ist unzuverlässig.
- **Kein stilles `--no-compare`** (Kommentar am Ticket): `add` läuft erst normal. Bricht es ab, weil der Haupt-Checkout nicht vergleichbar ist, folgt ein zweiter Versuch mit `--no-compare`, eine WARNUNG im Log und ein Hinweis am Ticket. Die Referenzzahl je Startcommit zu cachen wäre genauer, braucht aber einen Testlauf im Haupt-Checkout am fremden Commit; verworfen für diesen Schritt.
- **Ruling Post-Merge-Prüfung** (Review PR #16, A2; Entscheidung des Masters): `post_merge_check` verlässt sich nicht auf CI. Der Maintainer nutzt GitHub Actions nur sparsam (Free-Tier), slickfab hat auf main keinen Testlauf. Die Prüfung läuft lokal mit dem Prüfbefehl des Projekts (`.slickrails/config.sh`, liest `slickfab-worktree`; `.slickfab/config` kommt erst mit dem Planungs-Ticket) in einem Worktree am neuen main. CI zählt nur zusätzlich, wenn es Ergebnisse gibt; fehlendes CI ist weder grün noch rot. Kosten: Der tick wartet die Prüfdauer ab (Lock gehalten, andere ticks enden mit 75); bei langen Testläufen später als eigenes Terminal auslagern. Rot wird der aus GitHub gelesenen SHA zugeschrieben; ist main in der Zwischenzeit weitergerückt, prüft der nächste tick die neue SHA ohnehin.
- **Ruling vorher (ersetzt):** `post_merge_check` ohne Rolle, nur CI auf main. Verworfen, weil das Pilotprojekt auf main kein CI hat.
- **Ruling Worktree-Pfad**: Der Dispatcher gibt `--root` immer ausdrücklich an `slickfab-worktree` (aus `worktree_root`, sonst `~/.herdr/worktrees`). Vorher ging ohne `worktree_root` kein `--root` mit; dann galt beim Werkzeug `SLICKFAB_WORKTREE_ROOT` aus der Umgebung, beim Dispatcher (Nachbessern in Runde 3) aber `~/.herdr/worktrees`. `worktree_root` ist das Herdr-Worktree-Verzeichnis für alle Repos, nicht das eines Repos: Der Ordnername des Repos hängt das Werkzeug selbst an. Kosten falls falsch: Wer `worktree_root` auf `~/.herdr/worktrees/<repo>` setzt, bekommt `…/<repo>/<repo>/<name>`; Werkzeug und Dispatcher bleiben dabei einig.
- **Ruling Debug-Worktree:** `start_debug` legt `debug-<sha7>` mit `--check true` an, weil die Baseline auf rotem main erwartungsgemäß rot ist. Kosten falls falsch: Der Debugger startet ohne den Nachweis übersprungener Tests.
- **Ruling erste Sicht:** Sieht der Dispatcher ein Projekt zum ersten Mal, gilt `retro_at = merges`; sonst startete sofort eine Retro über alte Merges. Kosten falls falsch: Die erste Retro kommt erst nach zehn neuen Merges.
- **Rollback nur nach Nachsehen** (Review A1/R2): Ein Fehlercode von `slickfab-run` belegt nicht, dass kein Terminal entstand (Zeitgrenze von `hc run`: „the program may already have run“). Aufgeräumt wird nur, wenn `hc ls` sicher kein Terminal mit dem Namen oder im Ordner zeigt.
- **Doppelter Riegel beim Merge:** Zusätzlich zu `decide` prüft die Ausführung `auto_merge: true` in der Konfiguration selbst.
- **Nur eigene Berichte** (Security-Review): Marker-Kommentare zählen nur, wenn sie vom Dispatch-User (`assignee`) stammen, unter dem die Rollen in Linear schreiben. Sonst könnte jedes Mitglied des Teams per Kommentar ein `MERGE` vortäuschen.
- **Linear-Schlüssel:** nur aus der Datei in `linear_key_file`, nur als `Authorization`-Kopf, Weiterleitungen werden nicht verfolgt (sie bekämen den Kopf mit), der Antworttext einer HTTP-Fehlerantwort wird nicht geloggt, und jede Logzeile ersetzt den Schlüssel durch `***`.

- **PR-Beobachtung statt `/ship`** (Auswertung des Reviews): Rotes CI und Konflikte sind Arbeit für den Umsetzer, nicht für den Menschen; deshalb Nachbessern auch bei M/L oder `door:one-way`, wo früher sofort `ready` kam. Sie laufen unter derselben Obergrenze wie REWORK-Runden (Runde 3 frisch auf Opus, danach `needs_human`).
- **Runde ohne Verdict buchen**: `rework_rounds` zählte nur REWORK-Marker. Eine CI- oder Konflikt-Runde hätte den Zähler nie erhöht, die Schleife wäre ohne Deckel gelaufen. Die Ausführung schreibt nach dem Senden bzw. Starten einen Kommentar mit `SLICKFAB-ROUND: <n>` als Dispatch-User; das Lesen zählt ihn mit. Kein Marker-Block am Ende, deshalb nie ein `report`. Verworfen: Zähler in der Buchführung (ginge beim Neuaufsetzen verloren und wäre für Menschen am Ticket unsichtbar).
- **Erlaubte Autoren nur aus der Konfiguration** (eine frühere Lehre): Ein Kommentar ist kein Ausweis. `pr_comment_authors` steht in der Factory-Konfiguration, `decide` filtert danach; nichts am Ticket oder PR kann die Liste erweitern. Bots und unbekannte Autoren (`author` None) zählen nie.
- **Kommentar → Nachbessern, nie Merge**: Der Inhalt wird nicht gedeutet („LGTM“ heißt nichts). Ein neuer Kommentar geht an den Umsetzer mit seinem Link und dem Hinweis, dass andere PR-Kommentare keine Aufträge sind; ab der Obergrenze an den Menschen. Fragen beantwortet der Umsetzer im Linear-Bericht, nicht am PR: Dort stünde die Antwort unter dem Login des Maintainers und löste die nächste Runde aus. **Auch bei `slickfab:ready`** (Review A1): Genau dann liest der Mensch den PR; ein neuer Kommentar holt das Ticket zurück, das Label kommt erst nach Auftrag und Buchung ab, damit es nie ohne Nachbesserung aus dem Halt fällt. Er überstimmt `MERGE`, wartet aber, solange ein Agent arbeitet. Bei `REPLAN` bleibt es beim Label (der Planer sieht den PR ohnehin). Neu heißt „nach dem letzten Auftrag an den Umsetzer“, damit ein Kommentar, der während des Reviews kam, nicht hinter dem Reviewer verschwindet.
- **Ruling des Masters (Review A3): einmal beim Menschen, immer beim Menschen.** Holt ein Kommentar ein Ticket aus `ready` zurück, wird es danach nie mehr automatisch gemergt; nach Nachbesserung und neuem `MERGE` geht es wieder auf `slickfab:ready`, damit der Mensch den PR selbst sieht. Sonst hätte ein Kommentar bei einem S-Ticket das Menschen-Gate (z. B. wegen `DONE_WITH_CONCERNS`) in einen Auto-Merge verwandelt. Die Markierung `SLICKFAB-GATE: human` steht dauerhaft am Ticket, in derselben Buchung wie die Runde, nicht in einem flüchtigen Zustand (Label, Terminal). Verworfen: Markierung nur am Terminal oder über das Label (geht beim Aufräumen bzw. Abnehmen verloren).
- **Agent-Berichte unter dem Login des Maintainers**: Die Rollen nutzen `gh` mit dem Konto des Maintainers; der Reviewer schreibt seinen Bericht per `gh pr review`. Solche Berichte enden mit dem Marker-Block und zählen deshalb nicht als Kommentar eines Menschen.
- **`mergeable` statt `mergeStateStatus`**: Das Kriterium hängt an `mergeable`; `mergeStateStatus` mischt Konflikt, Branch-Schutz und CI und hätte nur doppelt geprüft. `UNKNOWN` ist bei GitHub häufig (wird nachberechnet) und heißt warten.

## Wo es lebt

- `runtime/herdr/slickfab_dispatch.py`: `decide`, `parse_marker` und die Konstanten (Modelle, Obergrenzen, sensible Pfade).
- `tests/test_dispatch.py`: Fixtures (`ticket`, `terminal`, `project`, `state`, `busy_state`) und je Regel positive und negative Fälle; Zufallstest mit festem Seed gegen Ausnahmen.
- `runtime/herdr/slickfab-dispatch`: `tick` und `watch` (Lesen, Ausführen, Lock, Log).
- `tests/test_dispatch_tick.py`: Tests über die Befehlszeile je Akzeptanzkriterium; `tests/dispatch_fakes.py`: nachgestelltes `hc` und `gh` (Skripte im PATH mit Zustandsdatei), Linear als HTTP-Server auf 127.0.0.1, Wegwerf-Repo für echtes `slickfab-worktree`.

## So testet man es

1. `python3 -m unittest tests.test_dispatch -v` (läuft ohne Netz, Herdr und Linear).
2. Alles: `sh tests/run.sh`.
3. `python3 -m unittest discover -s tests -p 'test_dispatch_tick.py' -v` (Ausführung; ohne Netz, ohne echtes Herdr, Linear oder GitHub, gut 40 s).
4. Von Hand gegen echte Dienste nur mit `--dry-run`: `runtime/herdr/slickfab-dispatch tick --dry-run`.
   Mutationsprobe (`.test-tmp/mutate_127.py`, nicht eingecheckt; jede Mutation in eigener Kopie unter `.test-tmp/mut/`): erster Lauf 47 von 55 getötet. Nachgezogen wurden Tests für Fehlerantwort mit Teildaten, Weiterleitung, fremdes `studio.issue`, Reihenfolge offener/gemergter PR und stilles `hc events`. Dazu kamen der Autor-Filter und der Zombie-Fix: **55 von 58 getötet**, dazu nach den Pre-Push-Reviews 9 von 9 für deren Fixes (`.test-tmp/mutate_fix.py`), zusammen 64 von 67. Drei überleben bewusst: (1) Den HTTP-Fehlertext zu loggen fällt nicht auf, weil die Schwärzung im Log den Schlüssel trotzdem entfernt; das sind zwei Schichten, jede reicht allein. (2) Der zweite Riegel `auto_merge` beim Merge ist über `decide` nicht erreichbar, weil `decide` ohne `auto_merge` nie `merge` plant. (3) Der Zweig `left <= 0` in `watch` ist ein Schutz; der Ersatz-tick kommt schon über die Zeitgrenze von `select`. Die Zahl deckt nur ab, was ich mir ausgedacht habe; belastbar wird sie erst mit einer fremden Probe.
   Die fremde Probe aus dem Review (PR #16) fand dann tatsächlich 8 echte Lücken bei 52 Mutationen, 38 getötet. Nach Rework Runde 1 (`.test-tmp/mutate_r1.py`): 23 Mutationen auf die Fixes A1–A4 und auf diese Lücken, im ersten Lauf 19 getötet. Danach kamen Tests für „nur Name“ bzw. „nur Ordner“ beim Nachsehen und für den leeren Head beim Merge dazu: **22 von 23**. Übrig bleibt „fehlendes CI = grün“ in `combine_ci`. Die Mutation ist äquivalent, weil `decide` `main.ci` nur auf `red` prüft.
   Mutationsprobe (`.test-tmp/mutate_141.py`, nicht eingecheckt; Regel-Mutanten gegen `tests/test_dispatch.py`, Ausführungs-Mutanten gegen `tests/test_dispatch_tick.py`): 36 Mutationen auf CI-, Konflikt- und Kommentarregeln, Buchung, Lesen und Konfiguration. Erster Lauf 31 getötet; überlebt hatten der Vergleich mit dem Umsetzer statt dem jüngsten Terminal, REPLAN trotz Kommentar, Kommentar am gemergten PR, Groß/klein in der Konfiguration und CI/Konflikt zusammen mit Kommentar. Nach Tests dafür **36 von 36**.
   Rework Runde 1 (`.test-tmp/mutate_141_r1.py`): 18 Mutationen auf `ready`-Kommentare, `unlabel`, Buchung beim frischen Start, Schutzsatz, Antwortweg, Fenster `last` und Autoren aus Ticket/PR: **18 von 18**. Jede der Lücken R1–R4 war vorher als überlebender Mutant rot nachgewiesen.
   Rework Runde 2 (`.test-tmp/mutate_141_r2.py`): 8 Mutationen auf die Markierung (`human_gate` im Merge-Blocker, Typprüfung, Schreiben und Lesen von `SLICKFAB-GATE`, Markierung ohne `cause`), die Reihenfolge Buchung vor Label (R5) und `blocked` am `ready`-Ticket (R6, Mutant `== "working"`): **8 von 8**.
5. Mutationsprobe (Skript nicht eingecheckt): handgeschriebene Mutationen an Regeln, Konstanten und Grenzen, je Mutation `python3 -m unittest tests.test_dispatch`, danach `git checkout` der Datei. Erster Lauf 69 von 73 getötet, 4 überlebt (toter Code für Reviewer-Status, fehlender `auto_merge`, unlesbarer Neustart-Zähler, unbekannte Rolle). Nach Nachschärfen 72 von 72 (die tote Stelle ist entfernt), nach den Fixes aus dem Pre-Push-Review 77 von 77. Nach der Nachbesserung Runde 1 (PR #8) passen 14 alte Mutationen nicht mehr auf den umgeschriebenen Code; die Liste hat dafür neue für dieselben Stellen (jüngstes Terminal, Deckel je Rolle, Belegung, CI-Warten, Modelle, sensible Pfade): 85 von 88 getötet, nach drei weiteren Tests 89 von 89. Runde 2: neun weitere Mutationen (Wächter-Projektfilter, Netz je Projekt mit engerem Ausnahmetyp, Statusfilter der Belegung, Rollenfilter im Deckel, ci-Vertrag, Rundenzählung aus Terminals statt Ticket); 98 von 98 getötet. Nach dem Rebase (Pre-Push-Befunde): elf weitere Mutationen an `hooks/`, Dispatcher-Pfad und Stillstellen durch needs-human; 106 von 109, nach einem Test für ready/replan 107 von 109. Zwei überleben und sind bewusst so gelassen: `err and` zu streichen ist äquivalent, weil die nächste Zeile needs-human-Tickets ohnehin überspringt; den Dispatcher-Pfad auf `slickfab_dispatch` irgendwo im Pfad zu verbreitern macht die Regel nur strenger.

## Grenzen & offene Punkte

- Zwischen `send_rework` und dem Statuswechsel des Terminals auf `working` würde ein zweiter Tick erneut senden. Die Lockdatei verhindert nur gleichzeitige ticks; die nachgestellte Herdr-Seite setzt `working` sofort, das echte Herdr nach dem Einfügen. Im Pilot beobachten.
- Dauerbetrieb (`watch` als Dienst), Factory-Konfiguration mit echten Werten und Dry-Run gegen echtes Linear: eigenes Ticket (Umschalten).
- Ein Terminal ohne jede Statusmeldung gilt als `working`; meldet ein Agent nie, wartet der Dispatcher ohne Ende auf ihn.
- Aufräumen nach einem Merge von Hand (Gate `slickfab:ready`) macht der Dispatcher nicht; `decide` kennt dafür keine Aktion.
- Der Rollentext des Reviewers kennt den Marker-Block; die Pflicht zur VERDICT-Zeile steht zusätzlich im Auftrag. Fehlt sie trotzdem, wird das Ticket zum Fall für den Menschen (Beobachtung aus dem Betrieb).
- Ein `ready`-Ticket ohne Dispatch-Terminal (z. B. nach dem Aufräumen in Herdr) wird nicht auf Kommentare beobachtet: Es fehlt `seq` als Vergleichspunkt (Hinweis aus dem Review).
- PR-Kommentare: Gelesen werden je PR die letzten 30 Kommentare und 30 Reviews; mehr als 30 neue Agent-Kommentare könnten einen menschlichen verdrängen. Inline-Kommentare zählen über ihr Review. Kommentiert ein Agent unter dem Login des Maintainers **ohne** Marker-Block am PR, gilt das als Kommentar des Maintainers und kostet eine Runde (nie ein Merge); der Nachbesserungs-Auftrag verlangt deshalb Antworten im Linear-Bericht, das ist aber nur eine Prompt-Regel. Sauber wäre ein eigenes GitHub-Konto für die Rollen.
- Ein neuer Kommentar, während der Umsetzer an einer Runde arbeitet, löst nach dessen `DONE` eine weitere Runde aus, auch wenn er ihn schon gesehen hat.
- Bei M/L-Tickets mit CI `pending` oder `mergeable` `UNKNOWN` gibt es weiter sofort `ready` (Ruling Master zum CI, für `UNKNOWN` gleich behandelt). Wird das CI danach rot oder meldet GitHub danach `CONFLICTING`, liegt der PR trotzdem rot bzw. mit Konflikt beim Menschen; der Dispatcher beobachtet am `ready`-Ticket nur Kommentare (Review A2). Nicht Teil dieses Tickets.
- `files` ist eine Schätzung aus den Agent notes; echte Überschneidungen ohne Eintrag fängt erst der Merge-Konflikt.
- Was `verify`, `retro`, `check` und `debug` melden, wertet `decide` nicht aus; nur Start, Doppelstart-Schutz und Wächter.

## Historie

- 2026-11-24: angelegt
- 2026-11-24: Pre-Push-Review, drei Befunde → Fix:
  - Gestarteter Umsetzer an einem Ticket, das in Linear noch auf Todo stand, zählte nicht als laufend; Dateischutz und Obergrenze griffen nicht, Wächter lief nicht → Ticket mit eigenem Terminal gilt als laufend.
  - Tote Projekt-Agents wurden nur bei fälliger Arbeit gemeldet → Wächter läuft vorab und unabhängig davon.
  - Fremdes Terminal mit nicht-textuellem `studio.issue` legte alles still → solche Terminals werden ignoriert.
- 2026-11-24: Review PR #8, Nachbesserung Runde 1:
  - A1: Ein altes totes Terminal oder das überholte Umsetzer-Terminal nach Runde 3 löste einen zweiten Neustart aus, weil der Deckel am einzelnen Terminal hing → nur das jüngste Terminal zählt, Deckel je Ticket und Rolle.
  - A2: Tickets mit Halt-Label und laufendem Terminal zählten nicht für Obergrenze und Dateischutz → alle eigenen Tickets mit Terminal belegen Platz und Dateien.
  - R1: Projektfilter bei Verify und fehlender Head auf beiden Seiten waren ungetestet → Tests.
  - R2: Ein kaputtes fremdes Projekt oder doppelte IDs dort legten alle Projekte still → Fehler bleiben im Projekt.
  - Master: CI pending/unbekannt wartet statt ready; `.claude/`, `.codex/`, `hooks/hooks.json` sensibel.
  - A3 (Maintainer): Modelle S → Sonnet, M/L → Opus, Runde 3 Opus mit Effort `high`.
- 2026-11-24: Re-Review PR #8, Nachbesserung Runde 2:
  - Drei Testlücken (Mutanten überlebten, Verhalten war richtig): Wächter-Projektfilter, Netz je Projekt, Statusfilter der Belegung → Tests, dazu Deckel je Rolle.
  - Ein `ci`-Wert außerhalb des Vertrags ließ das Ticket still ohne Ende warten → `needs_human` mit Grund (Master).
  - Rundenzähler am Ticket (Master): war schon so umgesetzt, jetzt mit Test über toten und frischen Umsetzer belegt. Ein frischer Umsetzer in Runde 1–2, weil der alte im Leerlauf weg ist, ist ein normaler Start für die Nachbesserung, kein Neustart nach Absturz; er verbraucht keinen Neustart.
- 2026-11-24: Rebase auf main (PR #6) und Pre-Push-Review, zwei Befunde → Fix (vom Master freigegeben):
  - Der Plugin-Wächter `hooks/docs_lookup_guard.py` und der Dispatcher selbst waren nicht sensibel; ein S-PR, der sie aufweicht, wäre auto-gemergt worden → ganzes `hooks/` und `runtime/herdr/slickfab_dispatch.py` sensibel.
  - Ein schon bei needs-human geparktes Ticket mit unlesbaren Daten bekam jeden Tick erneut `needs_human` (Kommentar-Spam) → still, solange das Label steht.
- 2026-11-24: Ausführung gebaut: `tick` mit `--dry-run`, Lockdatei, Log, Buchführung, Wächter-Meldungen, `watch` mit `hc events` und Ersatz-tick. `slickfab-run` bekam `--effort` für Runde 3. Betriebsbeobachtungen als Tests: `done` wie `idle` beim Nachbessern, nie `--if idle`, nie in eine Berechtigungsabfrage tippen, Reviewer ohne VERDICT → needs-human, `--model`/`--effort` nie aus Ticketdaten.
- 2026-11-24 (Stop-Hook): `watch` endete mit Traceback, als SIGTERM in einen laufenden `hc`-Aufruf fiel. Ursache: Stand in der Prozessgruppe von `hc` nur noch ein Zombie, meldete `killpg` unter macOS `PermissionError` statt `ProcessLookupError`, und das Warten auf das Pipe-Ende konnte an einem Enkelprozess hängen. Fix: beide Fehler gelten als „Gruppe weg“, danach Pipes schließen und nur den eigenen Prozess abwarten. Test: `ReadFailures.test_herdr_timeout_with_only_a_zombie_left_ends_cleanly`.
- 2026-11-24 (Security-Review): Marker-Kommentare zählen nur vom Dispatch-User → sonst hätte jedes Team-Mitglied per Kommentar ein `MERGE` vortäuschen können. Test: `Reading.test_marker_comments_of_other_authors_do_not_count`.
- 2026-11-24 (Pre-Push-Review), vier Befunde → Fix:
  - Rollback löschte den Worktree auch, wenn der Agent schon lief (`hc label` gescheitert, Zeitgrenze nach dem Start) → aufgeräumt wird nur bei Fehlercode von `slickfab-run`; `slickfab-run` bekommt eine kürzere `hc`-Zeitgrenze als der Dispatcher für `slickfab-run`.
  - Schlüsseldatei mit zweiter Zeile oder kaputter Kodierung endete mit Traceback, der den Schlüssel ungeschwärzt zeigte → nur eine Zeile sichtbarer ASCII-Zeichen, sonst Konfigurationsfehler; jeder andere Fehler der HTTP-Bibliothek wird ohne Text gemeldet.
  - Nur `ActionError` wurde je Aktion gefangen; ein `OSError` oder `KeyError` brach den tick ab, in `watch` den ganzen Autopiloten → jede Ausnahme bleibt bei ihrer Aktion, `watch` fängt jeden tick ab, nicht schreibbare Buchführung bricht vor der ersten Aktion ab.
  - Gescheitertes `start_debug` ließ `debug-<sha7>` liegen; jeder weitere tick scheiterte daran, ohne dass ein Mensch davon erfuhr → Rollback wie beim Umsetzer, Aktionen ohne Ticket melden sich mit `MENSCH:`.
- 2026-11-24 (Pre-Push-Review Runde 2): Debug, Retro und Verify buchten erst nach vollständigem Erfolg. Scheiterte nach dem Start `hc label`, trug der Verifier noch `studio.role=verifier` statt `verify`, und `verified` fehlte → jeder tick startete einen weiteren Verifier. Fix: Buchung, sobald `slickfab-run` nicht mit Fehlercode endet. Test: `SingleActionFails.test_started_project_roles_are_booked_even_if_labelling_fails`.
- 2026-11-24 (Review PR #16 Runde 1):
  - A1/R2: Bei Zeitgrenze von `hc run` löschte das Rollback den Worktree unter einem schon angelegten Agent → erst per `hc ls` nachsehen; läuft eins oder unklar → Worktree bleibt, needs-human.
  - A2: Post-Merge-Prüfung verließ sich auf CI, das auf main von slickfab nicht läuft → lokal mit dem Prüfbefehl des Projekts, CI nur zusätzlich (Ruling).
  - A3: Die Adresse des neuen Terminals wurde per Regex aus der Textausgabe geraten („the“) → Labels über den selbst vergebenen Namen.
  - A4: `comments(last: 50)` ließ frühe REWORK-Marker fallen, die Runden-Bremse griff nicht → alle Seiten.
  - R1: Tests für die acht Lücken der fremden Probe (unbekannte Aktionsart, fremder CI-Wert, Autorenfilter der Runden, jüngster Bericht, Neustart nur fürs eigene Ticket, Paginierung, `--check true`, Merge nur mit Head und Aufräumen ohne `--force`), dazu Lock-PID und Label-Filter von `watch`.
- 2026-11-25: `runtime/herdr/slickfab-dispatch` und `runtime/herdr/slickfab-run` waren nicht sensibel; ein S-PR, der den ausführenden Teil des Autopiloten ändert, wäre auto-gemergt worden → beide in `SENSITIVE_PATHS`. Im Pre-Push-Review dazu `slickfab-worktree`, `slickfab_templates.py` und `gen-templates`: Ein S-PR, der die Baseline überspringt oder `--disallowedTools` fallen lässt, wäre sonst auto-gemergt worden. Auf Entscheidung des Masters auch `agents/` und `runtime/herdr/templates/`: Dort stehen die `disallowedTools` selbst. Nach Review PR #18 (Entscheidung des Masters) auch `skills/review/`, `tests/run.sh`, `tests/check_*.py` und `.slickfab/`. Test: `MergeRule.test_merge_condition_and_checks_are_never_auto_merged`. Test: `MergeRule.test_executing_part_of_autopilot_is_never_auto_merged`. Dazu: Ohne `worktree_root` legte `slickfab-worktree` Worktrees unter `SLICKFAB_WORKTREE_ROOT` an, der Dispatcher suchte sie unter `~/.herdr/worktrees` → `--root` geht immer mit. Test: `FreshImplementer.test_worktree_lands_where_dispatcher_expects_it_even_with_root_from_environment`.
- 2026-11-25 (nach Re-Review MERGE): Rebase auf main mit #14. `tests/check_fab.py` verlangte „noch nicht nutzbar“ nur, solange der Dispatcher fehlt; mit ihm verlangte es nichts mehr, und README/`docs/betriebsarten.md` beschrieben einen Dispatcher, der „noch kommt“. Jetzt gilt: Mit ausführbarem Dispatcher sagen beide Abschnitte „noch nicht live“ und nicht mehr „noch nicht nutzbar“; das Umschalten hebt die Regel auf. Dazu zwei Tests aus dem Re-Review: unlesbare zweite Kommentar-Seite bricht den tick ab, die lokale Prüfung zählt nur für ihre SHA.
- 2026-11-25 (Punkt 5): Bei einer Umbenennung sah `decide()` nur den neuen Pfad; ein Verschieben aus `hooks/` nach `misc/` wäre auto-gemergt worden → `changeType` in der GraphQL-Abfrage, bei `RENAMED` die REST-Dateiliste mit `previous_filename`, alter Pfad zählt mit. Tests in `Reading` (vorher rot): Umbenennung aus sensiblem Pfad, harmlose Umbenennung mergt weiter, Antwort ohne alten Pfad, falscher Typ oder Fehlerobjekt → Pfade unbekannt, gescheiterter Aufruf → Lesefehler ohne Aktion, ohne Umbenennung kein Zusatzaufruf.
- 2026-11-25: PR-Beobachtung wie `/ship`, ohne `/ship` zu übernehmen. `MERGE` mit rotem CI → Nachbessern statt `ready`; `mergeable` wird gelesen, `CONFLICTING` → Nachbessern „auf main bringen“, `UNKNOWN`/fehlend → kein Merge; Kommentare und Reviews der Autoren aus `pr_comment_authors` → Nachbessern bzw. `needs_human`, nie ein Merge. Runden ohne Verdict bucht die Ausführung als `SLICKFAB-ROUND` am Ticket, damit die Obergrenze greift.
- 2026-11-25 (Pre-Push-Review): `seq` nach dem Senden war „jetzt“; ein PR-Kommentar, der während eines langen ticks (z. B. `worktree add`) zwischen Lesen und Senden kam, galt als übergeben und ging verloren → `seq` = Zeitpunkt vor dem Lesen. Test: `PrWatch.test_handed_over_means_up_to_the_read_not_up_to_the_send`. Dazu stand der Absatz zu den optionalen Aktionsfeldern mitten in der Tabelle.
- 2026-11-25 (Review PR #23 Runde 1): A1: Kommentare an `ready`-Tickets gingen unter, weil Halt-Labels das Ticket vor der Kommentar-Prüfung übersprangen → neuer Kommentar holt das Ticket zurück, Label ab (`unlabel`). R1–R4: Tests für die Buchung beim frischen Start in Runde 3 mit greifendem Deckel, den Schutzsatz gegen fremde Kommentare auf beiden Wegen, das Fenster der neuesten Kommentare (`last`, Fake antwortet jetzt wie GitHub) und Autoren aus Ticket-/PR-Feldern. Risiko Antwort-Schleife: Auftrag verlangt Antworten im Linear-Bericht. A2: Grenze UNKNOWN bei M/L dokumentiert.
- 2026-11-25 (Review PR #23 Runde 2): A3: Ein Kommentar holte ein S-Ticket aus `ready`, nach Nachbesserung und neuem MERGE wurde es automatisch gemergt, ohne dass der Mensch den PR noch einmal sah → Ruling des Masters: Markierung `SLICKFAB-GATE: human` in der Buchung, `human_gate` im Zustand, `_merge_blockers` → wieder `ready`. R5: Test, dass das Label bei gescheiterter Buchung bleibt. R6: `blocked` am `ready`-Ticket getestet.
- 2026-11-25: Beim Umschalten standen die GitHub-Checks in slickfab und slickrails auf `failure`, weil Actions mangels Free-Tier-Kontingent nicht starteten. Da rot gewinnt, plante der Dry-Run `start_debug` auf main trotz grüner lokaler Prüfung, und jeder MERGE wäre in eine CI-Runde gegangen → Schalter `github_ci` je Projekt (`use` Standard, `ignore`). Bei `ignore`: main nur lokale Prüfung (tick), PR-CI ausgeblendet und Auto-Merge wartet nicht auf grün (`decide`); Konflikte und alle anderen Bremsen bleiben. Tests: `test_dispatch.GithubCiIgnore.*`, `test_dispatch_tick.GithubCi.*` (Dry-Run mit rotem GitHub-CI plant weder `start_debug` noch eine CI-Runde). Dazu lehnte die Konfiguration `"space": "-"` ab, obwohl die Doku `-` als Standard nennt (`NAME_RE` verlangt ein Zeichen aus Buchstaben/Ziffern am Anfang) → `-` ist erlaubt, `--`, `-x` und Ähnliches weiter nicht. Tests: `Config.test_documented_space_default_is_accepted`, `test_invalid_space_is_still_refused`. Mutationsprobe (`.test-tmp/mutate142.py`, nicht eingecheckt): 16 Mutationen über Dispatcher und Vorlagen, eine überlebte („nur Tickets des eigenen Projekts ohne CI“), sie war äquivalent, weil jedes Projekt nur seine Tickets liest; die Bedingung ist deshalb raus.
- 2026-11-25: `Watch`-Tests wurden unter Last rot (fester Schlaf von 4,5 s, dann ticks gezählt). Jetzt wartet der Test, bis die erwartete Zahl ticks im Log steht (Obergrenze 30 s, unter `--interval` 60 des Ereignis-Tests), und beendet `watch` erst dann. Damit der Ereignis-Test weiter zu viele ticks erkennt, beobachtet er nach dem zweiten tick ein Ruhefenster von 3 s (länger als `EVENT_SETTLE`); das fragt nur nach dem Ausbleiben eines ticks und kann unter Last nicht fälschlich rot werden (Befund Pre-Push-Review). Mutationsprobe: Ersatz-tick entfernt, Ereignis ignoriert und zwei ticks je Aufwachen werden rot.
- 2026-11-25 (Review PR #24 Runde 1): A1: Mit pauschal 30 s Obergrenze blieb ein um das 5-Fache verspäteter Ersatz-tick grün. Jetzt hält `run_watch` den Zeitpunkt jedes ticks fest, und die Ersatz-tick-Tests prüfen den Abstand gegen `--interval 2` mit Toleranz 4 × Intervall (8 s). Getrennt davon schützt die großzügige Obergrenze nur gegen Hängen. A3: `test_watch_survives_a_failing_tick` wartet auf die zweite Buchführungs-Meldung statt 3,5 s zu schlafen. Mutationsprobe: `interval * 5` und „kaputter tick beendet watch“ werden rot.
- 2026-11-27: Standardpfad der Factory-Konfiguration zeigte in einen privaten Ordner des Maintainers → vor dem öffentlichen Repo neutral: `~/.config/slickfab/factory.json`; `--config` und `SLICKFAB_FACTORY` gehen weiter vor. Wer den alten Ort nutzt, setzt `SLICKFAB_FACTORY` oder legt einen Link. Tests: `Config.test_default_config_path_is_neutral_under_home`, `Config.test_environment_overrides_default_config_path`.
- 2026-11-27: Im Probebetrieb plante jeder tick `start_verify` für eine Spec, die in Linear längst `Done` war. Ursache: `verified` kam nur aus der Buchführung, also nur aus Verify-Läufen, die der Dispatcher selbst gestartet hatte; Specs, die von Hand oder ohne Autopilot abgeschlossen wurden, galten als offen. Fix: Die Linear-Abfrage liest den Statustyp der Spec mit (`state_type`), `decide()` plant für `completed` und `canceled` kein Verify. Tests (vorher rot): `test_dispatch.AfterMerge.test_closed_spec_gets_no_verify`, `test_dispatch_tick.SingleActionFails.test_closed_spec_in_linear_starts_no_verify`. Mutationsprobe: Bedingung entfernt, nur `completed` und Status nicht gelesen werden rot. Dry-Run gegen das echte Linear: Die erledigte Spec bekommt keine Aktion mehr.
