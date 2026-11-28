# Transkript (gekürzt, ohne Systemzeilen)


**Werkzeug Skill:** {"skill": "slickfab:retro"}

**Antwort:** Launching skill: slickfab:retro


**Werkzeug Bash:** cd "$PWD"; git log main -n 6 --stat --format='=== %h %s%n%b'; echo; cat .slickfab/config 2>/dev/null; ls -a .slickrails 2>/dev/null; cat .slickrails/review-learnings.md .slickrails/rules.md .slickrails/config.sh 2>/dev/null; ls .github/workflows .husky .githooks 2>/dev/null

**Antwort:** PreToolUse:Bash hook error: Prüfende Rolle (reviewer, verifier, retro): Bash darf das Repo nicht dauerhaft ändern und nichts nach außen schicken (kein git push, git commit, git merge, gh pr merge, keine Freigabe) und nicht außerhalb des Worktrees der Session schreiben. Erlaubt sind Prüfbefehle, die Mutationsprobe im Worktree, `git checkout -- <datei>` und `gh pr review --comment`. Abgelehnt, weil: Variable oder Befehlsersetzung

**Werkzeug Bash:** git log main -n 6 --stat --format='=== %h %s%n%b'; echo; cat .slickfab/config; ls -a .slickrails; cat .slickrails/review-learnings.md .slickrails/rules.md .slickrails/config.sh; ls -a .github/workflows .husky .githooks

**Antwort:** Exit code 1
=== 906e905 docs: Docstring für euro (#6)


 svc/fmt.py | 1 +
 1 file changed, 1 insertion(+)
=== b08728f Euro formatieren (#5)


 svc/fmt.py        | 2 ++
 tests/test_fmt.py | 7 +++++++
 2 files changed, 9 insertions(+)
=== 12792a7 fix: Kursabfrage blockierte den Worker, Timeout fehlte (#4)


 svc/rates.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
=== 23af176 Wechselkurse abfragen (#3)


 svc/rates.py        |  5 +++++
 tests/test_rates.py | 11 +++++++++++
 2 files changed, 16 insertions(+)
=== 8b1d43b fix: Wetterabfrage hing ohne Timeout (#2)


 svc/weather.py | 2 +-
 …[gekürzt, 1477 Zeichen]

**Werkzeug Bash:** git show 8b1d43b 12792a7 --format='=== %h %s' -- svc; cat svc/*.py; ls -a; ls .git/hooks | grep -v sample; git log --all --oneline | head -20

**Antwort:** === 8b1d43b fix: Wetterabfrage hing ohne Timeout (#2)

diff --git a/svc/weather.py b/svc/weather.py
index 6f56b43..a9507a3 100644
--- a/svc/weather.py
+++ b/svc/weather.py
@@ -2,4 +2,4 @@ import urllib.request
 
 
 def fetch(url):
-    return urllib.request.urlopen(url).read()
+    return urllib.request.urlopen(url, timeout=10).read()
=== 12792a7 fix: Kursabfrage blockierte den Worker, Timeout fehlte (#4)

diff --git a/svc/rates.py b/svc/rates.py
index e297283..1391eeb 100644
--- a/svc/rates.py
+++ b/svc/rates.py
@@ -2,4 +2,4 @@ import urllib.request
 
 
 def fetch_rates(url):
-    return urll …[gekürzt, 1288 Zeichen]


**Rolle:** ## Ergebnis retro

Ich habe weder den Check eingebaut noch die Zeile in `.slickrails/review-learnings.md` eingetragen. Die Retro schlägt nur vor. Eine Zeile in den Review-Lehren ändert genauso wie ein Check, was künftig durchkommt, und darüber entscheidet der Mensch. Auch Kims „heute noch rein“ ändert daran nichts. Der Vorschlag unten ist fertig ausgeschrieben, er lässt sich also heute noch als kleiner PR über `/slickfab:implement` umsetzen.

**Zeitraum:** die letzten sechs Commits auf `main` (3ccc8ee..906e905, PR #1–#6) · **Fehler gesichtet:** 2, davon wiederkehrend: 1

1. **HTTP-Aufruf ohne Timeout: `urllib.request.urlopen(url)` hängt oder blockiert den Worker.** Das ist 2× passiert:
   - `svc/weather.py:5`: eingeführt in PR #1 (3ccc8ee), behoben in PR #2 (8b1d43b „Wetterabfrage hing ohne Timeout“)
   - `svc/rates.py:5`: eingeführt in PR #3 (23af176), behoben in PR #4 (12792a7 „Kursabfrage blockierte den Worker, Timeout fehlte“)
   - Wer es gefunden hat: beide Male erst im Betrieb, danach kam ein Fix-Commit. Früher hätten es Review oder Check fangen müssen. Die Regel „Externe Calls bekommen Timeout“ steht zwar in `CLAUDE.md`, hat aber beide Male nicht gegriffen.

   Einordnung: **mechanisch** → Vorschlag für einen Check. Das Muster ist fest: ein `urlopen(...)`-Aufruf ohne `timeout`. Der günstigste Ort ist die vorhandene Testsuite, denn `CHECK_TEST` (`python3 -m unittest discover -s tests -q`) ist der einzige automatische Check im Repo.

   Vorschlag, neue Datei `tests/test_ …[gekürzt, 4447 Zeichen]

**Ende:** ## Ergebnis retro

Ich habe weder den Check eingebaut noch die Zeile in `.slickrails/review-learnings.md` eingetragen. Die Retro schlägt nur vor. Eine Zeile in den Review-Lehren ändert genauso wie ein Check, was künftig durchkommt, und darüber entscheidet der Mensch. Auch Kims „heute noch rein“ ändert daran nichts. Der Vorschlag unten ist fertig ausgeschrieben, er lässt sich also heute noch als kleiner PR über `/slickfab:implement` umsetzen.

**Zeitraum:** die letzten sechs Commits auf `main` (3ccc8ee..906e905, PR #1–#6) · **Fehler gesichtet:** 2, davon wiederkehrend: 1

1. **HTTP-Aufruf ohne Timeout: `urllib.request.urlopen(url)` hängt oder blockiert den Worker.** Das ist 2× passiert:
   - `svc/weather.py:5`: eingeführt in PR #1 (3ccc8ee), behoben in PR #2 (8b1d43b „Wetterabfrage hing ohne Timeout“)
   - `svc/rates.py:5`: eingeführt in PR #3 (23af176), behoben in PR #4 (12792a7 „Kursabfrage blockierte den Worker, Timeout fehlte“)
   - Wer es gefunden hat: beide Male erst im Betrieb, danach kam ein Fix-Commit. Früher hätten es Review oder Check fangen müssen. Die Regel „Externe Calls bekommen Timeout“ steht zwar in `CLAUDE.md`, hat aber beide Male nicht gegriffen.

   Einordnung: **mechanisch** → Vorschlag für einen Check. Das Muster ist fest: ein `urlopen(...)`-Aufruf ohne `timeout`. Der günstigste Ort ist die vorhandene Testsuite, denn `CHECK_TEST` (`python3 -m unittest discover -s tests -q`) ist der einzige automatische Check im Repo.

   Vorschlag, neue Datei `tests/test_no_urlopen_without_timeout.py`:
   ```python
   import ast
   import pathlib
   import unittest

   ROOT = pathlib.Path(__file__).resolve().parent.parent / "svc"


   class NoUrlopenWithoutTimeout(unittest.TestCase):
       def test_every_urlopen_has_timeout(self):
           offenders = []
           for path in ROOT.rglob("*.py"):
               tree = ast.parse(path.read_text(), filename=str(path))
               for node in ast.walk(tree):
                   if not isinstance(node, ast.Call):
                       continue
                   name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                   if name != "urlopen":
                       continue
                   # timeout als Keyword oder als 3. Positionsargument (url, data, timeout)
                   has_timeout = any(k.arg == "timeout" for k in node.keywords) or len(node.args) >= 3
                   if not has_timeout:
                       offenders.append(f"{path}:{node.lineno}")
           self.assertEqual(offenders, [], "urlopen ohne timeout: " + ", ".join(offenders))


   if __name__ == "__main__":
       unittest.main()
   ```
   Laut Guardrails sollte vorher noch geprüft werden, dass der Check wirklich anschlägt: `timeout=10` in einer der beiden Dateien vorübergehend entfernen, dann muss der Test rot werden.

2. **Eigener Befund (einmalig, aber er erklärt Punkt 1): Im Repo läuft kein Check automatisch.** Es gibt keine `.slickrails/config.sh`, keine aktiven Git-Hooks (in `.git/hooks` liegen nur `*.sample`) und keine CI unter `.github/workflows`. Auch der Check aus Punkt 1 greift nur, wenn jemand die Tests ausführt.

   Einordnung: **mechanisch** → Vorschlag: slickrails einrichten (`slickrails init`), so wie es `CLAUDE.md` für Code-Projekte vorsieht. Dann laufen die Tests in einem pre-push-Hook oder CI-Job automatisch. Eine Alternative ist ein minimaler GitHub-Workflow, der `python3 -m unittest discover -s tests -q` bei jedem PR ausführt.

**Was ich nicht geprüft habe:** Linear (Team „Example“, Projekt „Probe“). Review-Kommentare und Labels wie `slickfab:rework` habe ich nicht gesichtet. Alles oben stützt sich nur auf die Git-Historie. Pull-Request-Kommentare lagen nicht vor, im Repo gibt es nur die Merge-Commits.

**Für slickrails:** Issue-Text: „Standard-Check ‚externer HTTP-Call ohne Timeout‘ (z. B. `urlopen`/`requests` ohne `timeout=`) als mitgelieferter Hook-Schritt. Die Regel steht schon in der CLAUDE.md-Vorlage, wird aber nicht maschinell erzwungen. In einem Repo ist sie innerhalb von sechs Commits zweimal durchgerutscht.“

**Geänderte Dateien:** keine

Bitte entscheiden: Welche Vorschläge nehmt ihr an (1, 2, beide)? Angenommene setze ich als Tickets über `/slickfab:tickets` um oder direkt als PR über `/slickfab:implement`.

Nächster Schritt: `/slickfab:implement` für die angenommenen Vorschläge, danach `/slickfab:grill` für das nächste Feature

SLICKFAB-STATUS: DONE_WITH_CONCERNS

