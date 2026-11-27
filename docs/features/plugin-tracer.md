# Plugin-Tracer: slickfab laden, `/slickfab:grill`, Strukturprüfung

**Status:** aktiv · **Stand:** 2026-11-24 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Der Maintainer will slickfab als Claude-Code-Plugin, damit ein Entwickler den erprobten Prozess Schritt für Schritt fahren kann („the goal of this is to get 10x from one developer because he can use the process/steps you know?“). Dieses Ticket ist der dünnste Pfad durch das ganze Plugin:

- slickfab lässt sich als Plugin laden,
- der erste Schritt `grill` (Befragung in Runden) läuft per `/slickfab:grill` in einem fremden Repo,
- die Repo-Prüfung erkennt kaputte Schritte von selbst, auch für alle späteren Schritte, Rollen und Tests, ohne dass man sie anfassen muss.

## Entscheidungen

- **Plugin-Root = Repo-Root, Marketplace im selben Repo** (`.claude-plugin/marketplace.json` mit `"source": "./"`). Ein Repo, ein Plugin; so funktioniert `--plugin-dir .` und die Installation aus dem Repo (`/plugin install slickfab --marketplace l0kl97/slickfab` ab Claude Code 2.1.275, sonst `/plugin marketplace add l0kl97/slickfab` + `/plugin install slickfab@slickfab`; Syntax laut code.claude.com/docs/en/plugins/cli-reference). Die Installation aus GitHub ist noch nicht von Hand erprobt, weil das Plugin dafür global installiert würde. Format laut aktueller Doku (code.claude.com/docs/en/plugins-reference, plugin-marketplaces, marketplace-reference, Stand 2026-11-24).
- **Pflichtabschnitte eines Schritts:** `## Wann`, `## Ablauf`, `## Ergebnis`, `## Nächster Schritt`. Einzige Quelle ist `SKILL_SECTIONS` in `tests/check_structure.py`. Rollen (`agents/*.md`) brauchen vorerst nur Frontmatter mit `name` und `description`; ihr Rollenvertrag kommt mit dem Ticket für die Agents.
- **Beschreibung höchstens 300 Zeichen** (`DESCRIPTION_MAX`). Sie soll nur den Auslöser nennen; eine Ablauf-Zusammenfassung verleitet Agents, der Beschreibung statt dem Schritt zu folgen (Lehre aus superpowers `writing-skills`). Mechanisch prüfbar ist nur die Länge; ob der Inhalt Auslöser statt Ablauf ist, bleibt Review-Sache. Mehrzeilige YAML-Werte (`description: >`) werden zusammengefügt mitgezählt, damit die Grenze nicht umgangen wird.
- **Prüfer in Python (nur Standardbibliothek, läuft mit 3.9)** statt Shell: JSON und Frontmatter sauber lesen, Fehlermeldungen je Datei.
- **`run.sh` findet Tests selbst:** jede `tests/test_*.sh` wird ausgeführt, jede `tests/test_*.py` per `unittest discover`.
- **Teststelle ist `sh tests/run.sh`:** `tests/test_structure.py` baut je Test ein Wegwerf-Repo mit Kopien von `run.sh` und `check_structure.py`, macht genau eine Sache kaputt und erwartet rot mit Begründung.
- **`grill` ist modell-aufrufbar** (kein `disable-model-invocation`), damit „grill mich“ ihn auch ohne Slash-Befehl auslöst.
- **Nicht übernommen in `run.sh`:** `claude plugin validate`, weil es die Claude-CLI voraussetzt; läuft im Handtest (siehe unten).

## Wo es lebt

- `.claude-plugin/plugin.json`: Plugin-Manifest (Name `slickfab` → Befehle `/slickfab:<schritt>`).
- `.claude-plugin/marketplace.json`: Marketplace mit dem Plugin selbst.
- `skills/grill/SKILL.md`: der Schritt `grill`.
- `tests/check_structure.py`: Strukturprüfung (Manifeste, `skills/*/SKILL.md`, `agents/*.md`).
- `tests/run.sh`: alle Prüfungen; von slickrails als `CHECK_TEST` aufgerufen.
- `tests/test_structure.py`: Tests der Prüfung selbst, inklusive Fehlerfällen.

## So testet man es

1. `sh tests/run.sh` → `slickfab tests: ok`.
2. Gegenprobe: in `skills/grill/SKILL.md` `## Ergebnis` umbenennen → `FAIL skills/grill/SKILL.md: Pflichtabschnitt '## Ergebnis' fehlt`, Exit 1. Zurücksetzen.
3. `claude plugin validate .` → `✔ Validation passed with warnings` (Warnungen: CLAUDE.md am Root ist Entwickler-Doku, kein Plugin-Kontext; kein Icon).
4. Handtest in einem Wegwerf-Repo: `claude --plugin-dir <pfad-zu-slickfab>`, dann `/slickfab:grill <Wunsch>`.

### Protokoll Hand-Durchlauf (2026-11-24)

Wegwerf-Repo im Scratchpad: Python-CLI `notiz` (click, `add`/`list`, Notizen in `~/.notiz.json`), README mit der Idee „Notizen mit anderen teilen“. Aufrufe mit `claude -p --plugin-dir <worktree> --resume <session>`, Claude Code 2.1.331.

| Schritt | Befehl / Eingabe | Was passierte |
|---|---|---|
| Laden | `claude -p --plugin-dir <worktree> --output-format stream-json --verbose "sag nur ok"` | Init meldet Plugin `slickfab` 0.1.0 (`slickfab@inline`), `slash_commands` enthält `slickfab:grill`, kein Manifest-Fehler. |
| Runde 1 | `/slickfab:grill Ich will, dass man Notizen mit anderen teilen kann.` | Erst Feststellungen aus dem Repo (Python ≥3.11, click, `~/.notiz.json`, keine IDs, keine Tests), keine Frage danach. Dann F1–F5 (mit wem, Kopie oder gemeinsam, was, hat der Empfänger das Tool, Erfolgskriterium), jede mit „→ Empfehlung“. Transportfrage ausdrücklich auf Runde 2 verschoben, weil sie von F1/F2 abhängt. `GLOSSARY.md` mit „Notiz“ angelegt. |
| Runde 2 | `F1 bis F5: ja.` | F6–F10 mit Empfehlung; F7 (Format des geteilten Texts) als „schwer umkehrbar“ markiert mit Rückweg-Kosten. |
| „egal“-Probe | `egal, mach du` | F10 (technisch, umkehrbar) selbst entschieden. F6–F9 (Produkt bzw. schwer umkehrbar) **nicht** als Zustimmung gewertet: erneut gestellt, je auf zwei Optionen A/B mit Folgen zugespitzt. |
| Abschluss | `F6 A, F7 A, F8 A, F9 A` | `## Ergebnis grill` mit „Entschieden von dir“, „Autonom entschieden“ (7 Punkte, je mit Grund und warum umkehrbar), „Nicht im Umfang“, geänderten Dateien (`GLOSSARY.md`, `docs/adr/0001-notiz-block-als-klartext.md`), „Nächster Schritt: `/slickfab:spec`“ und Bitte um Bestätigung. |

Kosten des Durchlaufs: rund 1,80 USD in vier Aufrufen.

## Grenzen & offene Punkte

- `/slickfab:spec` und `/slickfab:prototype`, auf die `grill` verweist, gibt es inzwischen (siehe `planungs-schritte.md`).
- Die Prüfung sieht nur Struktur, nicht die Verhaltensqualität eines Schritts; dafür sind Pressure-Szenarien je Rolle geplant.
- Ob eine Beschreibung inhaltlich nur den Auslöser nennt, prüft nur das Review; die Längengrenze fängt die groben Fälle.
- Kein Plugin-Icon (nur für ein Marketplace-Listing nötig, nicht im Umfang).

## Historie

- 2026-11-24: angelegt
- 2026-11-24 (Review PR #1): `## `-Zeilen in Codeblöcken zählten als Pflichtabschnitt → `headings()` las jede Zeile → Codeblöcke (``` / ~~~) werden übersprungen. `description: ""` bzw. `name: ""` galt als vorhanden → Wert wurde mit Anführungszeichen übernommen → umschließende Anführungszeichen werden entfernt, leer ist rot. Dazu Test für Rolle ohne Frontmatter.
