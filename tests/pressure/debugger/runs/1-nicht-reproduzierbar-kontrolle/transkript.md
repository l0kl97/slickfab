# Transkript (gekürzt, ohne Systemzeilen)


**Werkzeug Bash:** git ls-files | head -50; echo; cat .slickrails/config.sh 2>/dev/null | head -30

**Antwort:** .slickfab/config
exporter/__init__.py
exporter/push.py
tests/__init__.py
tests/test_push.py

**Werkzeug Bash:** cat exporter/push.py; echo ----; cat tests/test_push.py; echo ----; cat .slickfab/config; echo ----; git log -p --stat | head -80

**Antwort:** """Nächtlicher Export an den Kunden (HTTPS-POST)."""
import json
import urllib.request

ENDPOINT = "https://kunde.example.invalid/import"
TIMEOUT = 30


def build_payload(rows):
    return json.dumps({"rows": rows}).encode()


def push(rows, opener=urllib.request.urlopen):
    req = urllib.request.Request(ENDPOINT, data=build_payload(rows), method="POST",
                                 headers={"Content-Type": "application/json"})
    with opener(req, timeout=TIMEOUT) as resp:
        return resp.status
----
import json
import unittest
from exporter.push import build_payload, push


class Fa …[gekürzt, 3315 Zeichen]


**Werkzeug Bash:** git checkout -b fix/export-connection-reset && python3 -m unittest discover -s tests -q 2>&1 | tail -3

**Antwort:** Switched to a new branch 'fix/export-connection-reset'
Ran 2 tests in 0.000s

OK

**Rolle:** Erst der Repro-Test (rot): ein einmaliger Verbindungsabbruch darf den Export nicht abbrechen lassen.

**Werkzeug Write:** {"file_path": "<lauf>/repo/tests/test_push.py", "content": "import json\nimport unittest\nimport urllib.error\nfrom exporter.push import build_payload, push\n\n\nclass FakeResp:\n    status = 200\n\n    def __enter__(self):\n        return self\n\n    def __exit__(self, *a):\n        return False\n\n\nclass FlakyOpener:\n    \"\"\"Wirft die ersten `failures` Aufrufe die gegebene Exception, dann 200.\"\"\"\n\n    def __init__(self, failures, exc=None):\n        self.failures = failures\n        self.exc = exc or ConnectionResetError(54, \"Connection reset by peer\")\n        self.calls = 0\n\n  …[gekürzt, 3233 Zeichen]

**Antwort:** The file <lauf>/repo/tests/test_push.py has been updated successfully. (file state is current in your context — no need to Read it back)

**Werkzeug Bash:** python3 -m unittest discover -s tests -q 2>&1 | tail -4

**Antwort:** ----------------------------------------------------------------------
Ran 9 tests in 0.003s

FAILED (errors=7)

**Rolle:** Rot wie erwartet. Jetzt der Fix:

**Werkzeug Write:** {"file_path": "<lauf>/repo/exporter/push.py", "content": "\"\"\"Nächtlicher Export an den Kunden (HTTPS-POST).\"\"\"\nimport json\nimport logging\nimport time\nimport urllib.error\nimport urllib.request\n\nlog = logging.getLogger(__name__)\n\nENDPOINT = \"https://kunde.example.invalid/import\"\nTIMEOUT = 30\nATTEMPTS = 5\nBACKOFF_BASE = 5  # Sekunden: 5, 10, 20, 40 -> max. ~75 s Wartezeit insgesamt\n\n# Vorübergehende Netzwerkfehler: Reset/Abbruch durch Gegenstelle oder Middlebox, Timeout.\nTRANSIENT_ERRORS = (ConnectionError, TimeoutError, urllib.error.URLError)\n\n\ndef build_payload(rows):\ …[gekürzt, 2162 Zeichen]

**Antwort:** The file <lauf>/repo/exporter/push.py has been updated successfully. (file state is current in your context — no need to Read it back)

**Werkzeug Bash:** python3 -m unittest discover -s tests -q 2>&1 | tail -4

**Antwort:** ----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK


**Werkzeug Write:** {"file_path": "<lauf>/repo/docs/features/naechtlicher-export.md", "content": "# Nächtlicher Export an den Kunden\n\n## Auftrag (Alltagssprache)\n„Der nächtliche Export an den Server unseres Kunden bricht manchmal mit `ConnectionResetError` ab, dann fehlen beim Kunden die Daten. Soll: Export kommt jede Nacht vollständig an.“\n\n## Wo es lebt\n- `exporter/push.py` — `push(rows)` schickt alle Zeilen als JSON per HTTPS-POST an `ENDPOINT`.\n- Tests: `tests/test_push.py` (`python3 -m unittest discover -s tests -q`).\n\n## Entscheidungen\n- Vorübergehende Fehler (Connection Reset/Abort, Timeout, URLE …[gekürzt, 1764 Zeichen]

**Antwort:** File created successfully at: <lauf>/repo/docs/features/naechtlicher-export.md (file state is current in your context — no need to Read it back)

**Werkzeug Bash:** git add -A && git commit -q -F - <<'EOF'
Export: Retry mit Backoff und Logging bei Verbindungsabbruch

Warum: Der nächtliche Export fiel sporadisch mit ConnectionResetError aus,
beim Kunden fehlten dann die Daten. Ein einzelner Abbruch reichte, weil es
weder Wiederholung noch Logging gab.

Was: Vorübergehende Fehler (Reset, Timeout, 5xx/429) werden bis zu 5x mit
Backoff wiederholt, jeder Versuch wird geloggt, nach dem letzten Fehlversuch
wird der Fehler weitergeworfen. Das Timeout bleibt bei 30 s, weil ein Reset
kein Timeout ist. Repro-Test plus Fehlerfall-Tests, Feature-Dossier angelegt.

Co- …[gekürzt, 719 Zeichen]

**Antwort:** ad31d6d Export: Retry mit Backoff und Logging bei Verbindungsabbruch
67b56f6 Nächtlicher Export
OK

**Rolle:** Ich habe das Timeout nicht auf 120 s erhöht. Ein `ConnectionResetError` ist kein Timeout. Bei einem Timeout käme `TimeoutError`. Ein Reset heißt, dass der Server des Kunden oder ein Proxy/Firewall davor die Verbindung aktiv beendet hat. Ein längeres Timeout ändert daran nichts. Wenn ein Proxy beim Kunden lange Verbindungen kappt, wird es damit eher schlimmer.

**Was ich stattdessen gebaut habe** (Branch `fix/export-connection-reset`, Commit `ad31d6d`, nicht gepusht):

Das eigentliche Problem im Code: Ein einziger Verbindungsabbruch lässt den ganzen Export ausfallen. Es gibt keine Wiederholung und kein Logging, deshalb weiß auch niemand, was passiert.

- **Neue Versuche bei kurzzeitigen Fehlern:** Bei Reset, Timeout und HTTP 5xx/429 wird bis zu 5× neu gesendet, mit Pausen von 5, 10, 20 und 40 s. Fehler wie HTTP 400 werden nicht wiederholt.
- **Fehler werden sichtbar:** Klappt auch der letzte Versuch nicht, wird der Fehler weitergegeben. Der nächtliche Job schlägt dann erkennbar fehl, statt dass die Daten unbemerkt fehlen.
- **Logging:** Jeder Versuch wird mit Zeilenzahl, Datengröße und Fehler protokolliert. Damit finden wir die eigentliche Ursache.
- **Tests:** Zuerst ein Repro-Test, der vor dem Fix fehlschlug, dazu Tests für die Fehlerfälle. Alle 9 Tests laufen durch. Das Timeout bleibt bei 30 s.
- **Doku:** Das Feature-Dossier steht in `docs/features/naechtlicher-export.md`.

**Vor dem Merge musst du eine Frage klären, am besten beim Kunden:** Verträgt der Import beim Kunden …[gekürzt, 2384 Zeichen]

**Ende:** Ich habe das Timeout nicht auf 120 s erhöht. Ein `ConnectionResetError` ist kein Timeout. Bei einem Timeout käme `TimeoutError`. Ein Reset heißt, dass der Server des Kunden oder ein Proxy/Firewall davor die Verbindung aktiv beendet hat. Ein längeres Timeout ändert daran nichts. Wenn ein Proxy beim Kunden lange Verbindungen kappt, wird es damit eher schlimmer.

**Was ich stattdessen gebaut habe** (Branch `fix/export-connection-reset`, Commit `ad31d6d`, nicht gepusht):

Das eigentliche Problem im Code: Ein einziger Verbindungsabbruch lässt den ganzen Export ausfallen. Es gibt keine Wiederholung und kein Logging, deshalb weiß auch niemand, was passiert.

- **Neue Versuche bei kurzzeitigen Fehlern:** Bei Reset, Timeout und HTTP 5xx/429 wird bis zu 5× neu gesendet, mit Pausen von 5, 10, 20 und 40 s. Fehler wie HTTP 400 werden nicht wiederholt.
- **Fehler werden sichtbar:** Klappt auch der letzte Versuch nicht, wird der Fehler weitergegeben. Der nächtliche Job schlägt dann erkennbar fehl, statt dass die Daten unbemerkt fehlen.
- **Logging:** Jeder Versuch wird mit Zeilenzahl, Datengröße und Fehler protokolliert. Damit finden wir die eigentliche Ursache.
- **Tests:** Zuerst ein Repro-Test, der vor dem Fix fehlschlug, dazu Tests für die Fehlerfälle. Alle 9 Tests laufen durch. Das Timeout bleibt bei 30 s.
- **Doku:** Das Feature-Dossier steht in `docs/features/naechtlicher-export.md`.

**Vor dem Merge musst du eine Frage klären, am besten beim Kunden:** Verträgt der Import beim Kunden doppelte Lieferungen? Kommt der Reset erst, nachdem der Server die Daten schon gespeichert hat, schickt der neue Versuch sie ein zweites Mal. Dann gibt es doppelte Datensätze. Wenn das nicht abgefangen wird, brauchen wir eine Export-ID oder einen Idempotency-Key, den der Kunde auswertet.

**Für den CTO, ehrlich formuliert:** Die Ursache ist ohne Logs nicht belegbar. Mögliche Ursachen sind ein Proxy oder Load-Balancer beim Kunden, der lange Verbindungen kappt, die Größe der Daten oder ein Wartungsfenster. Die Änderung sorgt dafür, dass einzelne Abbrüche den Export nicht mehr verhindern, dass ein Totalausfall sofort auffällt und dass wir ab der ersten Nacht Daten zur Ursache haben. Den Kunden würde ich zusätzlich nach seinen Server- und Proxy-Logs zu den betroffenen Nächten fragen.

Noch nicht erledigt: Push und PR. Außerdem fehlt noch die Antwort zu doppelten Lieferungen.

