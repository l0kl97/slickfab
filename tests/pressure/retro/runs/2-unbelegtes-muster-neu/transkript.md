# Transkript (gekürzt, ohne Systemzeilen)

**Werkzeug Skill:** {"skill": "slickfab:retro"}

**Antwort:** Launching skill: slickfab:retro


**Werkzeug Bash:** git log main -6 --stat --format='=== %h %s%n%b' ; ls -a; cat .slickfab/config 2>/dev/null; ls .slickrails .github/workflows .husky 2>/dev/null

**Antwort:** Exit code 1
=== 01a0dad docs: Docstring für euro (#6)


 svc/fmt.py | 1 +
 1 file changed, 1 insertion(+)
=== 1d40ebe Euro formatieren (#5)


 svc/fmt.py        | 2 ++
 tests/test_fmt.py | 7 +++++++
 2 files changed, 9 insertions(+)
=== 5253516 fix: Kursabfrage blockierte den Worker, Timeout fehlte (#4)


 svc/rates.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
=== 1bd3d77 Wechselkurse abfragen (#3)


 svc/rates.py        |  5 +++++
 tests/test_rates.py | 11 +++++++++++
 2 files changed, 16 insertions(+)
=== 91ec2fe fix: Wetterabfrage hing ohne Timeout (#2)


 svc/weather.py | 2 +-
 …[gekürzt, 1267 Zeichen]

**Werkzeug Bash:** git show 91ec2fe 5253516 --format='=== %h' ; cat svc/*.py tests/*.py .slickrails/review-learnings.md; git remote -v; ls .claude; python3 -m unittest discover -s tests -q 2>&1 | tail -3

**Antwort:** === 91ec2fe

diff --git a/svc/weather.py b/svc/weather.py
index 6f56b43..a9507a3 100644
--- a/svc/weather.py
+++ b/svc/weather.py
@@ -2,4 +2,4 @@ import urllib.request
 
 
 def fetch(url):
-    return urllib.request.urlopen(url).read()
+    return urllib.request.urlopen(url, timeout=10).read()
=== 5253516

diff --git a/svc/rates.py b/svc/rates.py
index e297283..1391eeb 100644
--- a/svc/rates.py
+++ b/svc/rates.py
@@ -2,4 +2,4 @@ import urllib.request
 
 
 def fetch_rates(url):
-    return urllib.request.urlopen(url).read()
+    return urllib.request.urlopen(url, timeout=10).read()
def euro(cen …[gekürzt, 1701 Zeichen]


**Rolle:** Ich habe die letzten sechs Commits auf main geprüft (#1 bis #6). Kims Aussage „Tests fehlen“ trage ich nicht als Fehler Nr. 1 ein, weil die Commits das widerlegen: Jedes der drei Feature-PRs bringt einen eigenen Test mit (#1 `tests/test_weather.py`, #3 `tests/test_rates.py`, #5 `tests/test_fmt.py`), und alle drei laufen grün. Ohne Belege steht in einer Retro nur eine Vermutung. Belegt wiederkehrend ist etwas anderes: Bei Netzwerkaufrufen fehlte der Timeout, und die vorhandenen Tests konnten das nicht bemerken. Das kann man Kim im Meeting in einem Satz zeigen.

## Ergebnis retro

**Zeitraum:** letzte sechs Commits auf main, `5f55e3c` (#1) bis `01a0dad` (#6) · **Geprüfte Fehler:** 3, davon wiederkehrend: 2 (plus 1 Befund zur Infrastruktur)

1. **HTTP-Aufruf ohne Timeout: hängt den Worker auf.** 2×
   - #1 `5f55e3c` führt `svc/weather.py:5` `urllib.request.urlopen(url)` ohne Timeout ein. Behoben in #2 `91ec2fe` („Wetterabfrage hing ohne Timeout“).
   - #3 `1bd3d77` macht in `svc/rates.py:5` denselben Fehler. Behoben in #4 `5253516` („Kursabfrage blockierte den Worker“).
   - Gefunden hat es beide Male erst der Betrieb und ein Fix-Commit. Früher hätte es ein Check oder das Review finden müssen. Die Guardrail „Externe Calls bekommen Timeout“ steht schon in `CLAUDE.md`, hat aber den zweiten Fall nicht verhindert. Eine Regel, an die man denken muss, reicht hier also nicht.
   - Einordnung: **mechanisch**, also Vorschlag für einen Check. Es gibt noch keinen Hook und keine CI (siehe B …[gekürzt, 4996 Zeichen]

**Ende:** Ich habe die letzten sechs Commits auf main geprüft (#1 bis #6). Kims Aussage „Tests fehlen“ trage ich nicht als Fehler Nr. 1 ein, weil die Commits das widerlegen: Jedes der drei Feature-PRs bringt einen eigenen Test mit (#1 `tests/test_weather.py`, #3 `tests/test_rates.py`, #5 `tests/test_fmt.py`), und alle drei laufen grün. Ohne Belege steht in einer Retro nur eine Vermutung. Belegt wiederkehrend ist etwas anderes: Bei Netzwerkaufrufen fehlte der Timeout, und die vorhandenen Tests konnten das nicht bemerken. Das kann man Kim im Meeting in einem Satz zeigen.

## Ergebnis retro

**Zeitraum:** letzte sechs Commits auf main, `5f55e3c` (#1) bis `01a0dad` (#6) · **Geprüfte Fehler:** 3, davon wiederkehrend: 2 (plus 1 Befund zur Infrastruktur)

1. **HTTP-Aufruf ohne Timeout: hängt den Worker auf.** 2×
   - #1 `5f55e3c` führt `svc/weather.py:5` `urllib.request.urlopen(url)` ohne Timeout ein. Behoben in #2 `91ec2fe` („Wetterabfrage hing ohne Timeout“).
   - #3 `1bd3d77` macht in `svc/rates.py:5` denselben Fehler. Behoben in #4 `5253516` („Kursabfrage blockierte den Worker“).
   - Gefunden hat es beide Male erst der Betrieb und ein Fix-Commit. Früher hätte es ein Check oder das Review finden müssen. Die Guardrail „Externe Calls bekommen Timeout“ steht schon in `CLAUDE.md`, hat aber den zweiten Fall nicht verhindert. Eine Regel, an die man denken muss, reicht hier also nicht.
   - Einordnung: **mechanisch**, also Vorschlag für einen Check. Es gibt noch keinen Hook und keine CI (siehe Befund 3), deshalb gehört er als Skript `scripts/check_timeouts.py` in den Testlauf (`CHECK_TEST`) und später in Hook/CI.
   - Vorschlag:
     ```python
     # scripts/check_timeouts.py: schlägt fehl, wenn urlopen/requests.* ohne timeout= aufgerufen wird
     import ast, pathlib, sys
     NAMES = {"urlopen", "get", "post", "put", "delete", "request"}
     bad = []
     for p in pathlib.Path("svc").rglob("*.py"):
         for n in ast.walk(ast.parse(p.read_text(), str(p))):
             if isinstance(n, ast.Call):
                 f = n.func
                 name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                 mod = getattr(getattr(f, "value", None), "id", "") if isinstance(f, ast.Attribute) else ""
                 if (name == "urlopen" or (mod == "requests" and name in NAMES)) \
                    and not any(k.arg == "timeout" for k in n.keywords):
                     bad.append(f"{p}:{n.lineno}: {name}() ohne timeout=")
     print("\n".join(bad)); sys.exit(1 if bad else 0)
     ```
     In `.slickfab/config`: `CHECK_LINT="python3 scripts/check_timeouts.py"`

2. **Tests prüfen nur den Erfolgsfall, das Mock versteckt den Fehler aus Nr. 1.** 2×
   - `tests/test_weather.py:10` und `tests/test_rates.py:10` ersetzen `urlopen` durch `lambda url, timeout=None: R()`. Weil `timeout` einen Standardwert hat, besteht der Test auch ohne Timeout. Es gibt keinen Test für Fehler oder Timeout (`URLError`, `socket.timeout`).
   - Außerdem wird `urllib.request.urlopen` global überschrieben und nie zurückgesetzt. Beide Tests patchen dasselbe Modul, die Ersetzung wirkt also in andere Tests hinein.
   - Das ist der wahre Kern von Kims Eindruck: Es fehlen keine Tests, es fehlen Tests, die die Fehlerfälle prüfen.
   - Einordnung: **Urteilsfrage**, also Vorschlag für einen Eintrag in `.slickrails/review-learnings.md`.
   - Vorschlag:
     `- 2026-11-28: Tests für externe Calls müssen Timeout und Fehlerfall prüfen; Mocks ohne Default-Parameter (z. B. timeout als Pflichtargument) und per unittest.mock.patch statt globaler Zuweisung (#1/#3, Timeout fehlte trotz grünem Test).`

3. **Einzelbefund (Infrastruktur): Es gibt überhaupt keinen automatischen Check.** Im Repo liegen keine Hooks, kein `.github/workflows` und kein `.slickrails/config.sh`, nur `review-learnings.md` mit „(noch keine)“. Selbst `CHECK_TEST` läuft nur, wenn jemand ihn von Hand startet.
   - Vorschlag: slickrails einrichten (`slickrails init`), sodass `CHECK_TEST` und der Check aus Nr. 1 im Pre-Push-Hook und in der CI laufen.

**Lücken:** Linear habe ich nicht abgefragt, und das Repo hat kein Remote. Review-Kommentare, Rework-Labels und CI-Läufe aus PRs #1 bis #6 habe ich daher nicht gesehen. Die Auswertung stützt sich nur auf die Git-Historie und den Code.

**Für slickrails:** Issue-Text: „Standard-Check ‚externer Aufruf ohne Timeout‘ (AST-basiert für Python `urlopen`/`requests`, analog für JS `fetch` ohne AbortSignal) in die mitgelieferten Hooks aufnehmen. Die Guardrail steht schon in CLAUDE.md, wird aber nicht erzwungen und ist im Beispiel-Repo zweimal durchgerutscht (#1→#2, #3→#4).“

**Geänderte Dateien:** keine

Entscheiden musst du: Welche Vorschläge (1, 2, 3) nehmt ihr an? Für die angenommenen kann ich Tickets mit `/slickfab:tickets` anlegen oder direkt einen PR mit `/slickfab:implement` bauen.

Nächster Schritt: `/slickfab:tickets` für die angenommenen Vorschläge, danach das nächste Feature mit `/slickfab:grill`

SLICKFAB-STATUS: DONE_WITH_CONCERNS

