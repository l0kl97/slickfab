Kosten: 0.2638548 USD · Züge: 6

## Ergebnis retro

Den Check habe ich nicht eingebaut und auch keine Zeile in `.slickrails/review-learnings.md` geschrieben. In der Retro schlage ich nur vor. Jeder Check und jede Review-Lehre ändert, was künftig durchkommt, und darüber entscheidet Kim. Das gilt auch für eine einzelne Zeile ohne Code. Die Vorschläge unten sind fertig formuliert. Nimmt Kim sie an, geht der Einbau mit `/slickfab:implement` heute noch als kleiner PR, ohne neue Analyse.

**Zeitraum:** die letzten sechs Commits auf main, `96208fb`..`94e8376` (PR #1 bis #6) · **Fehler gesichtet:** 2 Arten mit je 2 Stellen, davon wiederkehrend: 2

Den Tracker habe ich nicht abgefragt. Die Belege stehen vollständig in Git: zwei Fix-Commits und ihre Diffs. Review-Kommentare aus Linear fehlen deshalb in der Auswertung.

1. **HTTP-Aufruf ohne Timeout**, 2× auf main gelandet und erst nachträglich gefixt:
   - `svc/weather.py:5` kam in #1 (`96208fb`), Fix in #2 (`b0e3ffb`, „Wetterabfrage hing ohne Timeout“)
   - `svc/rates.py:5` kam in #3 (`f221930`), Fix in #4 (`afc35f4`, „Kursabfrage blockierte den Worker“)

   Beide Male hat erst das hängende System den Fehler gezeigt. Eine Prüfung vor dem Merge hätte ihn fangen sollen. Die CLAUDE.md-Regel „Kein Code im Vakuum: externe Calls bekommen Timeout“ hat ihn zweimal nicht verhindert.

   **Einordnung:** mechanisch → Check. Ein Aufruf von `urlopen` ohne `timeout` ist ein festes Muster. Im Repo gibt es keinen Hook, keine CI und keine `.slickrails/config.sh`. Das Einzige, was immer läuft, ist `CHECK_TEST` aus `.slickfab/config`. Am billigsten ist darum ein Test, der den Quellcode prüft.

   **Vorschlag**, neue Datei `tests/test_no_timeout_less_calls.py`:
   ```python
   import ast
   import pathlib
   import unittest

   NETZ_AUFRUFE = {"urlopen", "get", "post", "put", "delete", "request"}


   class TimeoutPflichtTest(unittest.TestCase):
       def test_jeder_http_aufruf_hat_timeout(self):
           funde = []
           for pfad in pathlib.Path("svc").rglob("*.py"):
               baum = ast.parse(pfad.read_text(), filename=str(pfad))
               for knoten in ast.walk(baum):
                   if not isinstance(knoten, ast.Call):
                       continue
                   name = getattr(knoten.func, "attr", getattr(knoten.func, "id", ""))
                   if name == "urlopen" or (
                       name in NETZ_AUFRUFE
                       and getattr(getattr(knoten.func, "value", None), "id", "") in {"requests", "httpx"}
                   ):
                       if not any(k.arg == "timeout" for k in knoten.keywords):
                           funde.append(f"{pfad}:{knoten.lineno}")
           self.assertEqual(funde, [], "HTTP-Aufruf ohne timeout: " + ", ".join(funde))
   ```
   Zur Probe: Auf `96208fb` oder `f221930` müsste der Test rot sein, auf dem heutigen main grün.

2. **Tests zu externen Aufrufen prüfen nur den Happy Path und nicht, ob ein Timeout übergeben wird**, 2×:
   - `tests/test_weather.py:10` (#1)
   - `tests/test_rates.py:10` (#3)

   Beide Mocks nehmen `timeout=None` an und lassen damit einen fehlenden Timeout durch. Beide überschreiben außerdem `urllib.request.urlopen` dauerhaft für alle anderen Tests. Das Review hätte das fangen sollen.

   **Einordnung:** Ermessen → Eintrag in `.slickrails/review-learnings.md`. Ob ein Test das Richtige prüft, kann eine Maschine nicht entscheiden.

   **Vorschlag**, fertige Zeile:
   `- 2026-11-25: Tests für externe Aufrufe prüfen, dass ein Timeout übergeben wird (Mock merkt sich die Argumente, statt timeout=None stillschweigend anzunehmen), und patchen nur mit unittest.mock.patch, nie durch dauerhaftes Überschreiben des Moduls (#1, #3).`

3. **Fund nebenbei:** Im Repo läuft nichts automatisch, weder Hook noch CI-Job, und `.slickrails/config.sh` fehlt. Der Check aus 1 greift nur, wenn jemand die Tests von Hand startet. Nach der CLAUDE.md ist slickrails Pflicht. Vorschlag: `slickrails init` im Repo ausführen, damit der Pre-Push-Hook `CHECK_TEST` laufen lässt.

**Für slickrails:** Issue-Text: „Standard-Check, der HTTP-Aufrufe ohne `timeout` findet (Python: `urlopen`, `requests`, `httpx`; JS: `fetch` ohne `AbortSignal`). Die Regel ‚externe Calls brauchen Timeout‘ steht nur als Text in der CLAUDE.md und ist in einem Repo zweimal hintereinander durchgerutscht.“

**Geänderte Dateien:** keine

Nächster Schritt: Kim entscheidet, welche Vorschläge er annimmt (1, 2, 3, slickrails-Issue). Die angenommenen gehen per `/slickfab:implement` als ein kleiner PR rein, Code und Zeile stehen oben fertig. Danach geht es mit dem nächsten Feature weiter, beginnend mit `/slickfab:grill`.

SLICKFAB-STATUS: DONE
