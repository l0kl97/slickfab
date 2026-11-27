# Transkript (gekürzt, ohne Systemzeilen)


**Werkzeug Skill:** {"skill": "slickfab:retro"}

**Antwort:** Launching skill: slickfab:retro


**Werkzeug Bash:** git log main -6 --stat --format='=== %h %s%n%b' ; echo ---; ls -la; cat .slickfab/config 2>/dev/null; ls .slickrails .github/workflows .git/hooks 2>/dev/null

**Antwort:** Exit code 1
=== dafc122 docs: Docstring für euro (#6)


 svc/fmt.py | 1 +
 1 file changed, 1 insertion(+)
=== 3216164 Euro formatieren (#5)


 svc/fmt.py        | 2 ++
 tests/test_fmt.py | 7 +++++++
 2 files changed, 9 insertions(+)
=== 7eecf57 fix: Kursabfrage blockierte den Worker, Timeout fehlte (#4)


 svc/rates.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
=== f7bb12f Wechselkurse abfragen (#3)


 svc/rates.py        |  5 +++++
 tests/test_rates.py | 11 +++++++++++
 2 files changed, 16 insertions(+)
=== ab6728e fix: Wetterabfrage hing ohne Timeout (#2)


 svc/weather.py | 2 +-
 …[gekürzt, 1958 Zeichen]

**Werkzeug Bash:** git show ab6728e 7eecf57 --format='=== %h %s'; cat .slickrails/review-learnings.md; for f in svc/*.py tests/*.py; do echo "## $f"; cat -n $f; done; python3 -m unittest discover -s tests -q 2>&1 | tail -3

**Antwort:** PreToolUse:Bash hook error: Prüfende Rolle (reviewer, verifier, retro): Bash darf das Repo nicht dauerhaft ändern und nichts nach außen schicken (kein git push, git commit, git merge, gh pr merge, keine Freigabe) und nicht außerhalb des Worktrees der Session schreiben. Erlaubt sind Prüfbefehle, die Mutationsprobe im Worktree, `git checkout -- <datei>` und `gh pr review --comment`. Abgelehnt, weil: Variable oder Befehlsersetzung

**Werkzeug Bash:** git show ab6728e 7eecf57 --format='=== %h %s' && cat -n .slickrails/review-learnings.md svc/weather.py svc/rates.py svc/fmt.py tests/test_weather.py tests/test_rates.py tests/test_fmt.py

**Antwort:** === ab6728e fix: Wetterabfrage hing ohne Timeout (#2)

diff --git a/svc/weather.py b/svc/weather.py
index 6f56b43..a9507a3 100644
--- a/svc/weather.py
+++ b/svc/weather.py
@@ -2,4 +2,4 @@ import urllib.request
 
 
 def fetch(url):
-    return urllib.request.urlopen(url).read()
+    return urllib.request.urlopen(url, timeout=10).read()
=== 7eecf57 fix: Kursabfrage blockierte den Worker, Timeout fehlte (#4)

diff --git a/svc/rates.py b/svc/rates.py
index e297283..1391eeb 100644
--- a/svc/rates.py
+++ b/svc/rates.py
@@ -2,4 +2,4 @@ import urllib.request
 
 
 def fetch_rates(url):
-    return urll …[gekürzt, 2092 Zeichen]

**Werkzeug Bash:** python3 -m unittest discover -s tests -q 2>&1 | tail -3

**Antwort:** Ran 3 tests in 0.000s

OK


**Rolle:** ## Ergebnis retro

**Den Fehler „Tests fehlen“ habe ich nicht als Nr. 1 eingetragen, weil die Commits ihn nicht belegen.** Beide Feature-Commits mit Code haben einen Test im selben Commit: `169c791` (#1) mit `tests/test_weather.py` und `f7bb12f` (#3) mit `tests/test_rates.py`. `3216164` (#5) hat `tests/test_fmt.py`. Alle 3 Tests laufen grün. Der wiederkehrende Fehler ist ein anderer, und er braucht nur zwei Belegzeilen.

**Zeitraum:** die letzten 6 Commits auf `main` (`169c791`..`dafc122`, PR #1–#6) · **Fehler gesichtet:** 3, davon wiederkehrend: 1

1. **Netzwerkaufruf ohne Timeout: der Dienst hängt bzw. blockiert den Worker** — 2× (`ab6728e` #2 behebt `svc/weather.py:5` aus #1; `7eecf57` #4 behebt `svc/rates.py:5` aus #3). Beide Male wurde es erst nach dem Merge gefunden, durch einen Fix-Commit. Früher hätte es ein Check vor dem Merge finden sollen. Die Regel steht schon in `CLAUDE.md` („Externe Calls bekommen Timeout …“), wurde aber zweimal gebrochen. Eine Regel, an die man sich erinnern muss, reicht hier also nicht.
   Einordnung: **mechanisch** → Vorschlag für einen Check. Den Hook bzw. CI-Job dafür gibt es noch nicht (siehe Punkt 2).
   Vorschlag (`scripts/check_timeouts.py`, im Pre-Commit-Hook und in CI aufrufen):
   ```python
   import ast, pathlib, sys
   CALLS = {"urlopen", "get", "post", "put", "delete", "request"}
   bad = []
   for p in pathlib.Path("svc").rglob("*.py"):
       for n in ast.walk(ast.parse(p.read_text())):
           if isinstance(n, ast.Call):
    …[gekürzt, 4151 Zeichen]

**Ende:** ## Ergebnis retro

**Den Fehler „Tests fehlen“ habe ich nicht als Nr. 1 eingetragen, weil die Commits ihn nicht belegen.** Beide Feature-Commits mit Code haben einen Test im selben Commit: `169c791` (#1) mit `tests/test_weather.py` und `f7bb12f` (#3) mit `tests/test_rates.py`. `3216164` (#5) hat `tests/test_fmt.py`. Alle 3 Tests laufen grün. Der wiederkehrende Fehler ist ein anderer, und er braucht nur zwei Belegzeilen.

**Zeitraum:** die letzten 6 Commits auf `main` (`169c791`..`dafc122`, PR #1–#6) · **Fehler gesichtet:** 3, davon wiederkehrend: 1

1. **Netzwerkaufruf ohne Timeout: der Dienst hängt bzw. blockiert den Worker** — 2× (`ab6728e` #2 behebt `svc/weather.py:5` aus #1; `7eecf57` #4 behebt `svc/rates.py:5` aus #3). Beide Male wurde es erst nach dem Merge gefunden, durch einen Fix-Commit. Früher hätte es ein Check vor dem Merge finden sollen. Die Regel steht schon in `CLAUDE.md` („Externe Calls bekommen Timeout …“), wurde aber zweimal gebrochen. Eine Regel, an die man sich erinnern muss, reicht hier also nicht.
   Einordnung: **mechanisch** → Vorschlag für einen Check. Den Hook bzw. CI-Job dafür gibt es noch nicht (siehe Punkt 2).
   Vorschlag (`scripts/check_timeouts.py`, im Pre-Commit-Hook und in CI aufrufen):
   ```python
   import ast, pathlib, sys
   CALLS = {"urlopen", "get", "post", "put", "delete", "request"}
   bad = []
   for p in pathlib.Path("svc").rglob("*.py"):
       for n in ast.walk(ast.parse(p.read_text())):
           if isinstance(n, ast.Call):
               name = getattr(n.func, "attr", getattr(n.func, "id", ""))
               if name in CALLS and not any(k.arg == "timeout" for k in n.keywords):
                   bad.append(f"{p}:{n.lineno}: {name}() ohne timeout=")
   print("\n".join(bad)); sys.exit(1 if bad else 0)
   ```

2. **Es gibt keine automatische Prüfung im Repo** (Fund nach Schritt 3). In `.git/hooks` liegen nur `*.sample`-Dateien. Es gibt kein `.slickrails/config.sh` und kein `.github/workflows`. `CHECK_TEST` aus `.slickfab/config` läuft deshalb nie von selbst.
   Einordnung: **mechanisch** → Vorschlag: `slickrails init` ausführen, damit Hooks und `config.sh` entstehen. Danach `CHECK_TEST="python3 -m unittest discover -s tests -q"` dort eintragen und den Timeout-Check aus Punkt 1 als weiteren `CHECK_*` aufnehmen.

3. **Die vorhandenen Tests prüfen den Timeout nicht.** Das ist der wahre Kern hinter „Tests fehlen“: Sie fehlen nicht, sie decken nur den Happy Path ab. Die Mocks in `tests/test_weather.py:10` und `tests/test_rates.py:10` nehmen `timeout=None` an, deshalb wäre auch der Code vor den Fixes grün gewesen. Bisher ist das ein Ursachenbündel mit Fehler 1 und kein eigener dritter Vorfall.
   Einordnung: **Ermessen** → Vorschlag für einen Eintrag in `.slickrails/review-learnings.md`:
   `- 2026-11-25: Mocks für externe Calls müssen die Aufruf-Argumente prüfen (z. B. timeout gesetzt), nicht nur den Rückgabewert; sonst ist der Test auch ohne Timeout grün (#2, #4).`

Nicht wiederkehrend und nicht schwer, daher nur am Rand: `svc/weather.py` und `svc/rates.py` haben weiterhin kein Error-Handling und kein Logging. `CLAUDE.md` verlangt beides, ein Fehler ist daraus aber noch nicht entstanden.

**Für slickrails:** Issue-Text: „Timeout-Check als Standard-Check für Python-Repos: ein AST-Scan, der `urlopen`/`requests.*` ohne `timeout=` meldet. `CLAUDE.md` nennt die Regel, aber ohne Check rutscht sie durch (in einem Repo 2× in 6 Commits).“

**Geänderte Dateien:** keine. Den Eintrag habe ich nicht geschrieben, ich schlage nur vor.

**Lücke:** Linear habe ich nicht gelesen. Es gab hier keine Pull-Request-Seiten und keine Review-Kommentare, die ich hätte lesen können. Ausgewertet habe ich nur die Git-Historie. Falls Reviewer im Tracker „Tests fehlen“ gemeldet haben, sehe ich das nicht. Dann bitte die Ticket-IDs nennen, und ich prüfe sie nach.

Welche Vorschläge nimmst du an? Für die angenommenen lege ich Tickets mit `/slickfab:tickets` an oder baue einen Pull Request mit `/slickfab:implement`.

Nächster Schritt: Kim entscheidet über die Vorschläge 1–3, danach `/slickfab:tickets` bzw. `/slickfab:implement`.

SLICKFAB-STATUS: DONE_WITH_CONCERNS

