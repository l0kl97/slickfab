# CI-Tests und gesprächiger Testlauf

**Status:** aktiv · **Stand:** 2026-11-27 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Das Repo ist öffentlich, aber auf GitHub liefen nur Secret-Scan, Audit und PR-Größe. Die eigene Testsuite lief nirgends auf dem Server, ein fremder PR hätte rot gemergt werden können, und Beitragende sahen nicht, ob ihr Stand grün ist. Dazu kam: `sh tests/run.sh` brauchte gut sechs Minuten und gab bis zum Ende nichts aus; ein Werkzeug mit 120 Sekunden Timeout hat den Lauf abgebrochen. Gewünscht: ein schlanker Workflow, ein Testlauf mit Lebenszeichen und ein schneller Modus für Beitragende. Die volle Suite bleibt Standard und Pflicht in CI.

## Entscheidungen

- **Ein Job, Matrix Python 3.9 und `3.x`** → 3.9 ist die Mindestversion; `3.x` hält die aktuelle Version ohne Pflege aktuell. 3.9 gibt es per `actions/setup-python` für `ubuntu-24.04`, ein Container `python:3.9` ist nicht nötig.
- **Runner `ubuntu-24.04` gepinnt** → `ubuntu-latest` wechselt die Major-Version ohne Zutun.
- **Trigger nur `pull_request` und Push auf `main`**, `permissions: contents: read`, `concurrency` mit Abbruch alter Läufe, `timeout-minutes: 20` (Suite lokal rund 7 Minuten).
- **Lebenszeichen per Thread, nicht per Testname** → ein einzelner Test kann länger als 30 Sekunden laufen; ein Hintergrund-Thread meldet alle 20 Sekunden Stand und laufenden Test. Verworfen: `unittest -v`, das gibt nur zwischen zwei Tests etwas aus.
- **`--fast` lässt ganze Module aus**, nicht einzelne Tests → einfach zu pflegen; die Liste steht in `tests/runner.py` (`SLOW_MODULES`) und ein Test prüft, dass jedes genannte Modul existiert.

## Wo es lebt

- `.github/workflows/test.yml` → der Workflow.
- `tests/run.sh` → Einstieg, nimmt `--fast` an, lehnt unbekannte Optionen mit Exit 2 ab.
- `tests/runner.py` → Python-Unittests mit Lebenszeichen und Auslassliste.
- `CONTRIBUTING.md` → Testbefehl und Dauer für Beitragende.
- Tests: `tests/test_structure.py` (`RunProgressTest`, `SlowListTest`), `tests/test_ci_workflow.py`.

## So testet man es

1. `sh tests/run.sh` → volle Suite, mindestens alle 20 Sekunden eine Zeile `... still running`.
2. `sh tests/run.sh --fast` → unter 90 Sekunden, am Ende `--fast skipped … Full suite: sh tests/run.sh`.
3. `SLICKFAB_TEST_HEARTBEAT=1 sh tests/run.sh --fast` → Lebenszeichen jede Sekunde.
4. Im Pull Request läuft der Check `Tests` für beide Python-Versionen.

## Grenzen & offene Punkte

- Branch-Schutz für `main` (PR Pflicht, Checks Pflicht) richtet der Maintainer in den Repo-Einstellungen ein; er ist nicht im Code.
- Wird ein anderes Modul langsam, muss es von Hand in `SLOW_MODULES`.

## Historie

- 2026-11-27: angelegt
