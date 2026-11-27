# context-guard: Kontextwarnung an den Agent

**Status:** aktiv · **Stand:** 2026-11-24 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Aus der Spec (User Story 10): „Als Agent möchte ich gewarnt werden, wenn mein Kontext voll wird, und eine Übergabe schreiben, damit ein frischer Agent nahtlos weitermacht.“ Das Ticket präzisiert: Ab 65 % Kontext kommt der Hinweis, die laufende Teilaufgabe abzuschließen und nichts Neues anzufangen. Ab 80 % kommt die Aufforderung, jetzt die Übergabe (`handoff`) zu schreiben und mit `NEEDS_CONTEXT` zu enden. Gewarnt wird nur in Rollen-Terminals des Studios, je Schwelle einmal; normale Sitzungen merken nichts. Vorbild ist `hooks/gsd-context-monitor.js` aus gsd-core (warnt den Agent selbst), in eigenen Worten umgesetzt.

## Entscheidungen

- **Ereignis `PostToolBatch` mit `hookSpecificOutput.additionalContext`.** Laut Hook-Doku (code.claude.com/docs/en/hooks, „PostToolBatch“, „Add context for Claude“) läuft es einmal nach jedem Bündel von Werkzeugaufrufen, vor der nächsten Modellanfrage, und der Text landet als Systemerinnerung im Kontext des Agents, nicht im Chat. `PostToolUse` würde bei parallelen Aufrufen mehrfach gleichzeitig feuern; `UserPromptSubmit` käme bei einem autonomen Agent fast nie. Der Hook gibt nur Kontext aus, nie `decision`, `continue` oder Exit 2, kann die Sitzung also nicht anhalten.
- **Füllstand aus der Statuszeilen-Datei** `$HOME/.config/studio-board/sessions/<HC_TERMINAL_ID>.json`, Feld `context_window.used_percentage`. Die Datei schreibt die Studio-Statuszeile (`~/.config/studio-board/bin/statusline`) bei jeder Antwort des Modells; sie enthält die Statuszeilen-Eingabe von Claude Code unverändert. Der Hook liest sie nur.
- **Veraltet = andere Session oder älter als 30 Minuten.** Die Datei gehört dem Terminal, nicht der Session: Nach einem Neustart im selben Terminal steht dort zunächst die alte Session. Darum muss `session_id` in der Datei gleich der `session_id` des Hook-Aufrufs sein. 30 Minuten decken einen langen Werkzeugaufruf (bis 10 min) ab; älter heißt, die Statuszeile läuft nicht. Gültig sind nur Zahlen von 0 bis 100 (kein `true`, kein Text, kein NaN); Dateien werden höchstens 256 KB gelesen.
- **Rollen-Kennzeichen = Herdr-Label `studio.role`.** `studio-run` setzt es am Terminal (`hc run … --label studio.role=<rolle>`); in der Sitzung selbst kommt es nicht als Umgebungsvariable an, nur `HC_TERMINAL_ID`. Der Hook fragt deshalb `hc get --json <HC_TERMINAL_ID>` (lokaler Unix-Socket der Herdr-CLI, kein Netz) und warnt nur, wenn `labels["studio.role"]` ein nicht leerer Text ist. Verworfen: eine eigene Umgebungsvariable (müsste in `studio-run` gesetzt werden, das liegt außerhalb dieses Repos); den Herdr-Zustand direkt von der Platte lesen (privates Format).
- **Billig zuerst, `hc` zuletzt.** Reihenfolge: Subagent? (`agent_id` im Aufruf → still, denn die Statuszeile misst die Hauptsession) → `HC_TERMINAL_ID` gesetzt und harmlos? → Datei gültig und frisch? → Schwelle erreicht? → für diese Schwelle noch nicht gewarnt und `hc` hat in dieser Session noch nicht „keine Rolle“ gesagt? Erst dann `hc` (Timeout 2 s). So fragt der Hook `hc` je Session nur wenige Male, auch in Herdr-Terminals ohne Rolle. In einer normalen Sitzung ohne Herdr endet der Hook nach dem Lesen von stdin, ohne eine Datei anzufassen.
- **„Nur einmal“ über leere Merkdateien** `${XDG_STATE_HOME:-~/.local/state}/slickfab/context-guard/<session_id>.<schwelle>`, angelegt mit `O_EXCL` (atomar, auch wenn mehrere Aufrufe gleichzeitig laufen), Ordner `0700`. Wer nicht schreiben kann, schweigt, statt bei jedem Aufruf erneut zu warnen. Liegt die 80-%-Merkdatei vor, gilt auch 65 % als erledigt: Sinkt der Füllstand nach einer Kompaktierung, kommt kein Rückschritt-Hinweis. Dafür wird keine zweite Datei geschrieben, die scheitern und die Warnung verschlucken könnte. Antwortet `hc` ausdrücklich ohne `studio.role`, merkt sich der Hook das als `<session_id>.norole`; ein Fehler oder Müll von `hc` wird nicht gemerkt, beim nächsten Mal wird neu gefragt. Die Merkdateien bleiben liegen (je 0 Byte); Aufräumen ist nicht im Umfang.
- **Nie werfen, nie blockieren.** Jede Ausnahme endet still mit Exit 0 und ohne Ausgabe. Der Befehl in `hooks.json` endet mit `|| true`: Fehlt das Skript (Worktree entfernt, Plugin-Cache mitten im Update), endet `python3` mit Exit 2, und Exit 2 hält bei `PostToolBatch` die Agent-Schleife jeder Session an. Die Ausgabe auf stdout bleibt erhalten. Beim Doku-Wächter (`PreToolUse`) ist Exit 2 dagegen als fail-closed gewollt, dort steht kein `|| true`. `HC_TERMINAL_ID` und `session_id` müssen `[A-Za-z0-9_-]` sein, bevor sie in einen Pfad gehen; alles andere ist still.
- **Grenze für die Laufzeit: 0,5 s je Aufruf** (Test), Hook-Timeout in `hooks.json` 5 s. Gemessen: normale Sitzung ~40 ms (Python-Start), Rollen-Terminal mit echtem `hc` ~50–60 ms.
- **Dateiname `hooks/context_guard.py`** statt `hooks/context-guard` aus dem Ticket: gleiche Form wie `docs_lookup_guard.py` und als Python-Modul importierbar.

## Wo es lebt

- `hooks/context_guard.py`: der Hook (nur Standardbibliothek, Python 3.9).
- `hooks/hooks.json`: Eintrag unter `PostToolBatch` (ohne Matcher, das Ereignis kennt keinen). Der bestehende `PreToolUse`-Eintrag für den Doku-Wächter ist unverändert.
- `tests/test_context_guard.py`: Tests über die Hook-Schnittstelle (JSON auf stdin) mit Wegwerf-`HOME`, nachgestellter Statuszeilen-Datei und nachgestellter `hc`-CLI im `PATH`.
- `tests/fixtures/statusline/session.json`: anonymisierte Statuszeilen-Datei in voller Form (Platzhalter für IDs, Pfade, Repo).
- Bezug: `skills/handoff/SKILL.md` (der Schritt, den die 80-%-Warnung nennt), Marker laut `tracker/linear.md`.

## So testet man es

1. `sh tests/run.sh` → `slickfab tests: ok`.
2. Von Hand ohne Claude (Rollen-Terminal vorausgesetzt): Statuszeilen-Datei in einem Wegwerf-`HOME` nachbauen, dann
   `echo '{"session_id":"<id aus der Datei>","hook_event_name":"PostToolBatch","tool_calls":[]}' | HOME=<wegwerf> HC_TERMINAL_ID=<terminal> python3 hooks/context_guard.py`.
   Achtung: `hc` leitet seinen Socket aus `HOME` und `XDG_STATE_HOME` ab; beim Umbiegen braucht `hc` ein Wrapper-Skript mit dem echten `HOME` und ohne `XDG_STATE_HOME`.

| Kriterium | Test |
|---|---|
| Warnung bei 65 % / 80 % im Rollen-Terminal | `test_role_terminal_at_65_gets_the_wrap_up_warning`, `test_role_terminal_at_80_gets_the_handoff_warning`, `test_79_is_still_the_wrap_up_warning`, `test_boundaries_0_and_100_are_valid`, `test_fractional_percentage_is_shown_rounded` |
| Still unter 65 % und ohne Rolle | `SilenceTest` (unter 65, ohne/leeres Label, ohne Herdr, ohne `hc`, `hc` kaputt oder mit Fehlercode, Subagent) |
| Je Schwelle einmal | `OnceTest` (65 → 80 → nichts mehr, Sprung über 80, neue Session warnt neu, 8 gleichzeitige Aufrufe → genau eine Warnung, Merkordner nicht beschreibbar → still; nach erledigter Warnung bzw. „keine Rolle“ wird ein hängendes `hc` nicht mehr gefragt, nach einem `hc`-Fehler schon) |
| 80 % nennt `handoff` und `NEEDS_CONTEXT` | `test_warning_texts_match_the_reference_word_for_word` (beide Warnungen Wort für Wort), `test_handoff_warning_names_step_and_marker`, `test_wrap_up_warning_does_not_ask_for_the_handoff_yet` |
| Datei fehlt/leer/veraltet/kaputt → still, Exit 0 | `BrokenStatusTest` (fehlend, leerer Ordner, leer, Müll, binär, falsche Typen und Werte, andere Session, ohne `session_id`, älter als 30 min, kaputte Hook-Eingabe, Terminal-ID und `session_id` mit `../` → nichts außerhalb des Merkordners), `test_missing_script_never_stops_the_session` (Befehl aus `hooks.json` per `sh -c`, Skript fehlt → Exit 0) |
| Bruchteil einer Sekunde, kein Netz | `test_each_call_stays_under_the_limit` (0,5 s), `test_hanging_hc_does_not_hold_the_session` (< 3 s), `test_warns_without_any_network` (Sockets gesperrt) |
| Über das Plugin registriert, ohne Rolle wirkungslos | `test_plugin_registers_the_hook_with_a_short_timeout`, `test_registered_command_delivers_the_warning`, `SilenceTest`; `claude plugin validate .` grün |
| Merkdateien privat | `test_state_files_are_private` (Ordner `0700`, Datei `0600`) |
| Format der Statuszeilen-Datei (kritische Verbindung) | `FormatContractTest`: Fixture enthält die gelesenen Felder; auf einem Rechner mit Studio wird die neueste echte Datei gegen dieselben Felder geprüft (nur Schlüssel und Typen, sonst übersprungen) |

### Mutationsprobe (2026-11-24)

36 Mutationen am Hook (Schwellen ±1, `>=`/`>`, Veraltungsgrenze, Sessionvergleich, Typprüfungen, Rollenprüfung, Timeout, Merkdateien, `O_EXCL`, Warntexte, Ereignisname, Auffang). Erste Runde 21/36 gefangen; die echten Lücken (80-%-Grenze, Rundung, kein 65-%-Hinweis nach 80 %, `hc` mit Fehlercode, Ausbruch per `../` in der Terminal-ID) wurden mit Tests geschlossen. Zweite Runde 28/36 gefangen. Nach der Nachbesserung aus dem Push-Review (siehe Historie) mit angepasster Liste: **33/40 gefangen**. Die 7 Überlebenden sind gleichwertig: Sie entfernen Typprüfungen (`isinstance` für Datei, `context_window`, `labels`, Antwort von `hc`; `ValueError` beim Lesen), deren Fehlen der äußere Auffang genauso still macht, oder lassen Werte ≤ 1 bzw. negative Werte zu, die nie eine Schwelle erreichen. Nach Review-Runde 1 (siehe Historie), erweitert um Streichen von Sätzen der Warntexte, die `session_id`-Prüfung, die Rechte und `stdin` an `hc`: **40/48 gefangen**, dazu die Mutation „`|| true` in `hooks.json` entfernt“ (gefangen). Die 8 Überlebenden: die 7 oben und `stdin=DEVNULL` an `hc` (stdin ist zu dem Zeitpunkt schon gelesen). Dabei fielen zwei Testfehler auf: Fälle in einer Schleife teilten sich ein Studio, sodass ein früherer Fall die späteren über eine Merkdatei verdeckte (jetzt je Fall ein frisches Studio), und der Paralleltest gab stdin erst nacheinander, lief also gar nicht gleichzeitig.

### Handprobe (2026-11-24)

Hook direkt aufgerufen mit nachgebauter Statuszeilen-Datei (81,6 %) und der echten `hc`-CLI: Terminal mit `studio.role=implementer` → Warnung „82 % … `handoff` … `NEEDS_CONTEXT`“ in ~60 ms, zweiter Aufruf still; Terminal ohne `studio.role` → still.

## Grenzen & offene Punkte

- **Kein Live-Lauf mit `claude --plugin-dir` im fremden Repo.** Ein zweiter Claude-Lauf aus der Umsetzer-Session wurde abgelehnt (und keine weiteren Agents war Vorgabe). Belegt sind: Registrierung in `hooks.json` (Test), `claude plugin validate .` grün, Verhalten über die Hook-Schnittstelle. Offen: dass Claude Code 2.1.331 `PostToolBatch` aus Plugins tatsächlich aufruft und der Text im Kontext erscheint. Beim nächsten Pilot im Studio prüfen.
- Gewarnt wird erst, wenn die globale Einstellung des Maintainers das Plugin lädt (Ticket „Umschalten“, nicht hier).
- Die Statuszeile schreibt nur, solange sie läuft; im Druckmodus (`claude -p`) gibt es keine Statuszeile und damit keine Warnung.
- Der Füllstand ist so aktuell wie die letzte Antwort des Modells; innerhalb eines langen Bündels kann er um diese Antwort hinterherhinken.
- Merkdateien werden nicht aufgeräumt.
- Wird ein Terminal mit Rolle für eine fremde Sitzung wiederverwendet, schützt nur der `session_id`-Vergleich.
- Nebenfund (nicht dieses Ticket): Die Stop-Prüfung von slickrails startet `sh tests/run.sh` als Hintergrundjob; dort ist SIGINT ignoriert, und 5 Strg-C-Tests in `tests/test_worktree.py` werden rot. Auf `main` genauso; im Vordergrund und im Pre-Push grün.

## Historie

- 2026-11-24: angelegt
- 2026-11-24 (AI-Review beim Push, zwei Befunde): (1) `hc` lief vor der Prüfung „schon gewarnt?“, also bei jedem Bündel über 65 % und in jedem Herdr-Terminal ohne Rolle → `has_role` stand vor `first_time` → erst billige Prüfung der Merkdateien, „keine Rolle“ wird je Session gemerkt. (2) Nach 80 % wurde 65 % mit einer zweiten Datei gemerkt; scheiterte das Schreiben, verschluckte der Auffang die bereits gemerkte 80-%-Warnung → die 80-%-Merkdatei zählt jetzt auch für 65 %, kein zweites Schreiben. Tests mit hängendem `hc` und gleichzeitigen Aufrufen.
- 2026-11-24 (Review PR #9, Runde 1): (R1) Fehlte das Skript, endete `python3` mit Exit 2, und `PostToolBatch` hätte jede Session mit dem Plugin nach jedem Bündel angehalten → der Auffang in `main()` greift nicht, wenn Python das Skript gar nicht startet → `|| true` im Befehl, Test führt den Befehl aus `hooks.json` mit fehlendem Skript aus. (R2) Der Satz „Hör jetzt auf zu bauen …“ ließ sich streichen, ohne dass ein Test rot wurde → nur Begriffe waren geprüft → beide Warnungen Wort für Wort gegen eine Referenz im Test. (R3) Der Pfadschutz für `session_id` hatte keinen Test → Test mit `../` in Hook-Eingabe und Statusdatei. (R4) Rechte `0700`/`0600` ungeprüft → `stat`-Test.
