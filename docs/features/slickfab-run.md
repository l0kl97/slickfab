# slickfab-run und gen-templates: Rollen in Herdr starten

**Status:** aktiv · **Stand:** 2026-11-25 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Der Maintainer will den Entwicklungsprozess auch als Autopilot fahren: Rollen laufen parallel in Herdr-Terminals, er greift nur an Entscheidungspunkten ein („the goal of this is to get 10x from one developer because he can use the process/steps you know?“). Dafür braucht es zwei Befehle, und zwar ohne zweite Quelle für die Rollentexte:

- **gen-templates** macht aus den Agent-Hüllen (`agents/*.md`) die Herdr-Vorlagen, je Rolle eine, mit Startbefehl und Modell. Die Vorlagen sind reines Erzeugnis, niemand bearbeitet sie von Hand.
- **slickfab-run** startet eine Rolle als Sitzung, Rollenanweisung und Auftrag als erste Nachricht. Es ist der Nachfolger von dem früheren privaten Startskript `studio-run`, neu mit `--model` und dem Dispatch-Kennzeichen. Die Board-Labels bleiben gleich, damit das Studio-Board weiter funktioniert.

Nicht in diesem Ticket: Die Vorlagen live nach `~/.config/herdr-core/templates/` schreiben und `studio-run` umstellen. Beides gehört zum Umschalten.

## Entscheidungen

- **Eine Quelle, ein Renderer.** `runtime/herdr/slickfab_templates.py` liest eine Hülle und baut daraus die Vorlage. `gen-templates` schreibt das Ergebnis als Datei. `slickfab-run` nimmt denselben Text direkt aus der Hülle und braucht keinen Vorlagenordner. So ist die erste Nachricht in Herdr genau der Body der erzeugten Vorlage.
- **Format wie die heutigen Herdr-Vorlagen**, damit `studio-run` und Herdr sie lesen können: Frontmatter mit `name`, `description` und `command: claude [--disallowedTools <liste>] --model <modell>`, danach der Text der Hülle ohne ihr Frontmatter. Die erste Zeile im Frontmatter ist das Feld `generated: erzeugt von gen-templates aus agents/<rolle>.md, nicht bearbeiten (Hülle ändern, neu erzeugen)`. Herdr (`hc templates`) nimmt im Frontmatter nur Zeilen der Form `key: value` und lehnt sonst die ganze Vorlage ab (`not key: value`); deshalb kein Kommentar. Unter dem Frontmatter ginge es auch nicht, denn der Body ist die erste Nachricht an den Agenten.
- **Modell als Alias aus der Hülle** (`opus`, `sonnet`), keine Tabelle mit Modell-IDs. Claude Code löst den Alias auf. Eine zweite Tabelle würde veralten. Das Modell muss ein einzelnes harmloses Wort sein (`[A-Za-z0-9._[]-]`, nicht mit `-` am Anfang), weil es in einer Befehlszeile landet.
- **Werkzeuggrenze kommt mit** (Pre-Push-Review). `disallowedTools` aus der Hülle wird zu `claude --disallowedTools Write,NotebookEdit` usw., in der Vorlage und bei `slickfab-run`. Ohne das wäre die Grenze aus dem Ticket in Herdr nur eine Prompt-Regel. Die Option nimmt mehrere Werte und steht deshalb vor `--model`, sonst würde sie den Auftrag als Werkzeugnamen schlucken. Werkzeugnamen sind einzelne Wörter (keine Muster wie `Bash(git *)`). Eine `tools`-Allowlist in einer Rolle bricht ab, statt still zu verschwinden.
- **Nur bekannte Frontmatter-Schlüssel** (Review PR #13, R1): `name`, `description`, `model`, `schritt`, `skills`, `disallowedTools`. Jeder andere Schlüssel (`tools`, `permissionMode`, `hooks`, `mcpServers` …) bricht ab. Er hätte in Claude Code eine Wirkung, die in Herdr sonst still wegfiele. Ein neues Feld braucht also zuerst eine Übersetzung hier. `skills` wird bewusst nicht übersetzt: Herdr lädt keinen Skill vor, und jede Hülle sagt selbst, dass sie ihren Schritt sonst mit dem Skill-Werkzeug lädt.
- **Ein Wert steht in einer Zeile.** YAML-Blockskalare (`description: >`, `|`, `>-` …) brechen ab, weil der einfache Leser die eingerückten Folgezeilen nicht liest und sonst eine leere Beschreibung entstünde. Eine gequotete `description` wird so übernommen, wie sie dasteht.
- **Pflichtfelder:** `name`, `description`, `model`, `schritt`, jeweils nicht leer. Ein Paar äußerer Anführungszeichen gehört nicht zum Wert wie in YAML, also gilt `schritt: ""` als leer. Eine Hülle mit kaputter Kodierung endet mit Meldung statt Traceback. Fehlt eins in irgendeiner Hülle, bricht `gen-templates` ab, bevor eine Datei geschrieben wird. Alle Vorlagen entstehen zuerst im Speicher.
- **Welche Hüllen Rollen sind:** alle `agents/*.md` außer `docs-reader` (ein Werkzeug von `docs-lookup`, siehe `agent-rollen.md`). Eine neue Rolle ist damit automatisch dabei und muss die Pflichtfelder haben. Eine Liste, die man nachpflegen muss, gibt es nicht.
- **Kein Standardziel.** `gen-templates` verlangt `--out` oder `--check`. Ohne Angabe schreibt es nirgends hin, auch nicht ins Herdr-Vorlagenverzeichnis. Es löscht nie Dateien im Ziel, weil dort auch fremde Vorlagen liegen können.
- **Eingecheckte Vorlagen** unter `runtime/herdr/templates/`. `gen-templates --check` vergleicht sie mit den Hüllen und meldet abweichende, fehlende und überzählige Dateien. Der Test dazu läuft in der Repo-Prüfung. Eine Änderung an einer Hülle ohne `gen-templates --out runtime/herdr/templates` ist damit rot.
- **Kein Shell-Aufruf.** `slickfab-run` übergibt `hc` eine Argumentliste. Der Auftrag kommt als ein Argument an, mit Anführungszeichen, Zeilenumbrüchen, `$` und Backticks unverändert. `studio-run` zerlegte `command:` noch per Shell in Wörter.
- **Eingaben streng geprüft, bevor `hc` läuft:** Rolle (Kleinbuchstaben, muss eine Rolle sein), Name (Regel von `hc run --name`: 1–32 Zeichen `a-z 0-9 - _`), Ordner existiert, Space- und Issue-ID ohne `=` und Leerzeichen und nicht mit `-` am Anfang, `--model` wie oben, der Auftrag nicht leer (auch nicht nur Leerzeichen; Review A1). Grund: Ein Fehler im Dispatcher soll kein falsch beschriftetes Terminal erzeugen.
- **Zeitgrenze für `hc`:** 30 Sekunden (`SLICKFAB_HC_TIMEOUT`, eine endliche Zahl über 0; `nan`, `inf`, `0` und Text enden vor dem Start von `hc` mit Exit 2), eigene Prozessgruppe. Bei Überschreitung und bei jedem anderen Abbruch (Strg-C) wird die Gruppe beendet, damit `hc` nicht später doch noch ein Terminal startet, während der Aufrufer von einem Fehlschlag ausgeht. `hc run --bg` kommt sofort zurück. Hängt es trotzdem, antwortet der Core nicht.
- **Dispatch-Kennzeichen immer.** `slickfab.dispatch=1` sitzt an jedem Start, auch beim Start von Hand. Laut Plan fasst der Dispatcher nur Terminals mit diesem Label an. Ein Schalter zum Abwählen war nicht verlangt.
- **Fehlercodes:** 2 = falscher Aufruf (mit Usage), 1 = Hülle kaputt oder `hc` fehlt, scheitert oder hängt, 130 = Strg-C, 0 = gestartet.

## Schnittstelle für slickfab-dispatch

```
slickfab-run [--model <modell>] [--effort <stufe>] [--agents <ordner>] <rolle> <name> <ordner> <space-id|-> "<auftrag>" [issue-id]
```

- `--effort low|medium|high|xhigh|max` geht als `claude --effort <stufe>` nach `--model` an Claude (Nachbessern Runde 3); ohne die Option gilt der Standard von Claude.
- Optionen nur vor den Positionsargumenten, in beliebiger Reihenfolge, je höchstens einmal. Ohne `--model` gilt `model` aus `agents/<rolle>.md`. `--agents` nimmt andere Hüllen als `agents/` dieses Repos (für Tests und andere Repos).
- Ein leerer Auftrag ist ein falscher Aufruf (Exit 2).
- Aufruf an Herdr: `hc run --bg --name <name> --cwd <ordner absolut> --label studio.role=<rolle> [--label studio.issue=<issue-id>] [--label herdr.space=<space-id>] --label slickfab.dispatch=1 claude [--disallowedTools <liste der Hülle>] --model <modell> [--effort <stufe>] "<Text der Hülle>\n\n## Auftrag\n<auftrag>"`
- Label-Namen: `studio.role`, `studio.issue`, `herdr.space`, `slickfab.dispatch=1`.
- stdout ist bei Erfolg die Ausgabe von `hc run --bg`, Meldungen gehen nach stderr mit dem Präfix `slickfab-run:`.

```
gen-templates --out <ordner> | --check <ordner> [--agents <ordner>]
```

## Wo es lebt

- `runtime/herdr/slickfab_templates.py`: Hülle lesen, Pflichtfelder prüfen, Vorlage bauen.
- `runtime/herdr/gen-templates`: Vorlagen schreiben (`--out`) oder prüfen (`--check`).
- `runtime/herdr/slickfab-run`: Rolle in Herdr starten.
- `runtime/herdr/templates/*.md`: eingecheckte, erzeugte Vorlagen (nicht bearbeiten).
- `tests/test_gen_templates.py`, `tests/test_slickfab_run.py`: Tests über die Befehlszeile. `hc` ist durch ein Skript im PATH ersetzt, das seinen Aufruf als JSON ablegt. Wegwerf-Ordner liegen unter `.test-tmp/` im Repo (ignoriert), `HOME` zeigt in einen davon.

## So testet man es

1. `sh tests/run.sh` → `slickfab tests: ok`.
2. Nach einer Änderung an `agents/*.md`: `runtime/herdr/gen-templates --out runtime/herdr/templates` und das Ergebnis mit einchecken. Prüfen mit `runtime/herdr/gen-templates --check runtime/herdr/templates`.
3. Mutationsprobe im Worktree (`.test-tmp/mutate.py`, nicht eingecheckt): Jede Mutation wird in die Datei geschrieben, dann laufen `test_gen_templates` und `test_slickfab_run`, danach wird das Original zurückgeschrieben. **Am finalen Stand (Rework-Runde 1) 60 Mutationen, 0 überlebt.** Verlauf: Erst waren es 36, im ersten Lauf überlebte 1 („leeres Feld erlaubt“: Beim Modell fing der Wort-Check das leere Feld ab, für ein leeres `schritt` gab es keinen Test). Nach dem Test für leeres `schritt` überlebte keine. Zu den Fixes aus dem Pre-Push-Review kamen 8 dazu (Werkzeuggrenze fehlt, steht nach `--model`, `tools` still verworfen, Werkzeugnamen beliebig, Anführungszeichen bleiben, Strg-C lässt `hc` laufen, Kodierung in Hülle und in `--check` ungefangen), damit 44, 0 überlebt. Die fremde Probe des Reviewers fand am Head `80d1c9c` 6 von 47 Überlebenden, davon war 1 äquivalent. Die 5 echten (R2 bis R5) und R1, A1, R6 brachten in Rework-Runde 1 16 neue Mutationen. Davon überlebte eine („Option doppelt erlaubt“: Der Code verspricht „je höchstens einmal“, ein Test fehlte), der Test ist nachgezogen. Die Mutationen decken Hinweis und Quelle, Ausnahme `docs-reader`, Pflichtfelder, Modellwort, Frontmatter, „alles oder nichts“, `--check` (Inhalt, fehlend, Exit), kein Standardziel, jedes Label, `--model`, jede Eingabeprüfung, Zeitgrenze, `hc`-Fehler, Auftrag (fehlt, gekürzt) und Frontmatter im Prompt ab. Die Zahl deckt nur ab, was ich mir ausgedacht habe; belastbar wird sie erst mit einer fremden Probe.
4. Kein Test startet ein echtes Terminal oder einen Agent.

## Grenzen & offene Punkte

- Echte Herdr-Vorlagen und `studio-run` bleiben unverändert.
- Ob `hc run` den Auftrag selbst unverändert an `claude` weiterreicht, prüft der Test nicht. Er endet an der Systemgrenze `hc`. `studio-run` verlässt sich heute auf dasselbe Verhalten.
- Der Text der Hülle sagt „Du läufst als frischer Subagent“. In Herdr ist es eine eigene Session, die ebenfalls niemanden fragen kann. Inhaltlich passt das, der Wortlaut gehört den Hüllen.
- `hc run` setzt ohne `--outlive-parent` den startenden Terminal als Eltern, wie bei `studio-run`. Ob der Dispatcher das braucht, entscheidet der Dispatcher.

## Historie

- 2026-11-24: angelegt.
- 2026-11-24: Pre-Push-Review fand vier Fehler. Die Werkzeuggrenze `disallowedTools` der Hüllen ging beim Start in Herdr verloren, weil nur Modell und Text übersetzt wurden. Strg-C ließ `hc` in seiner eigenen Prozessgruppe weiterlaufen. `""` galt als nicht leer. Eine kaputte Kodierung endete mit Traceback. Fix: `--disallowedTools` vor `--model` in Vorlage und Start, `tools` bricht ab. Die Prozessgruppe wird bei jedem Abbruch beendet. Anführungszeichen werden wie in YAML entfernt, `UnicodeDecodeError` wird als Meldung ausgegeben. Zu allen vier gibt es Tests, die Lehre steht in `.slickrails/review-learnings.md`.
- 2026-11-24: Review PR #13, Rework-Runde 1. R1: Nur `tools` brach ab, andere Schlüssel mit Wirkung (`permissionMode`, `hooks`, `mcpServers`) fielen still weg. Fix: Allowlist bekannter Schlüssel. R2 bis R5: Fehlerpfade ohne Kaputt-Test (Hülle nicht lesbar in `slickfab-run`, `SLICKFAB_HC_TIMEOUT`, verwaiste Vorlage, fehlendes `name` bzw. `description`). `nan` und `inf` als Zeitgrenze endeten nach dem Start von `hc` mit Traceback. Fix: `isfinite`, `--agents` für `slickfab-run`, damit der Kaputt-Fall über die Befehlszeile testbar ist, dazu die Tests. A1: Ein leerer Auftrag startete eine Rolle, jetzt Exit 2. R6: Ein Blockskalar ergab eine leere Beschreibung, jetzt bricht er ab. Für gequotete Beschreibungen gibt es jetzt einen Test.
- 2026-11-24: `--effort` für den frischen Umsetzer in Runde 3 der Nachbesserung; ungültige Werte enden vor `hc` mit Exit 2.
- 2026-11-25: `test_hc_hangs` prüfte eine Laufzeit unter 15 s, `test_ctrl_c_also_stops_hc` las die PID-Datei nach festem Schlaf und gab `hc` 5 s zum Sterben. Unter Last wackelte beides. Jetzt schreibt das Test-`hc` seine PID atomar, der Test wartet auf die Datei und darauf, dass der Prozess weg ist (Obergrenze 30 s). `test_hc_hangs` prüft zusätzlich, dass `hc` nach der Zeitgrenze beendet ist. Mutationsprobe: kein Beenden bei Strg-C, kein Beenden bei Zeitgrenze und ignorierte Zeitgrenze werden rot.
- 2026-11-25 (Review PR #24 Runde 1): A2: `test_hc_hangs` las die PID-Datei, die das Test-`hc` erst nach dem Python-Start schrieb. Brauchte der Start länger als die Zeitgrenze von 1 s, endete der Test mit `FileNotFoundError`. Jetzt ist das Test-`hc` ein Shell-Wrapper, der die PID vor `exec python` schreibt, und die Zeitgrenze im Test liegt bei 5 s. Fehlt die Datei, meldet der Test „hc startete nicht vor der Zeitgrenze“. Gegenprobe: 1,5 s Verzögerung vor der PID bzw. beim Python-Start bleibt grün. Das hängende Test-`hc` endet von selbst, sobald der Test-Ordner weg ist.
- 2026-11-25: Herdr (`hc templates`) lehnte jede erzeugte Vorlage ab (`not key: value`), weil die erste Frontmatter-Zeile ein `#`-Kommentar war; der Master setzte live die alten Vorlagen zurück. Ursache: Die Entscheidung „Hinweis ohne Doppelpunkt“ schützte einfache Leser, nicht Herdrs strengere Regel. Fix: Hinweis als Feld `generated: …`, Vorlagen neu erzeugt. Test: `test_frontmatter_follows_herdr_rule` bildet Herdrs Regel nach (an frisch erzeugten und eingecheckten Vorlagen), `test_herdr_rule_rejects_comment_line` zeigt, dass die Nachbildung den alten Fehler fängt, `test_studio_run_still_reads_command` liest `command:` mit dem awk-Ausdruck aus `studio-run`. Gegen das echte `hc templates` ließ sich nicht testen: Es liest fest `~/.config/herdr-core/templates`, und mit anderem `HOME` scheitert es am Socket-Pfad. Nachtrag nach Review: Der Master hat live geprüft, dass Herdr eine erzeugte Vorlage mit `generated:` annimmt (`hc templates`: ok). Der Drift-Test (`--check`) bleibt scharf.
