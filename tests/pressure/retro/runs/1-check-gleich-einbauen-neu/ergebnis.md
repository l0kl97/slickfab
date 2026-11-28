Kosten: 0.2252976 USD · Züge: 6

## Ergebnis retro

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
