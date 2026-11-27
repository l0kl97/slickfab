Kosten: 0.41239980000000004 USD · Züge: 12

## Ergebnis debug

Kurz: Ich habe nichts geändert und schlage noch keine Korrektur vor. Ich konnte den Fehler nicht nachstellen. Das Timeout auf 120 s zu setzen, würde diesen Fehler sehr wahrscheinlich nicht beheben.

**Fehler:** Der nächtliche Export (`push()` in `exporter/push.py`) bricht manchmal mit `ConnectionResetError` ab, und dann fehlen beim Kunden die Daten.

**Roter Befehl:** keiner. Ich habe keinen Befehl, der auf genau diesen Fehler rot wird.
- Versucht: einen lokalen Wegwerf-Server, der die Verbindung einmal hart zurücksetzt und sie einmal nur langsam bedient. So wollte ich sehen, welche Ausnahme `push()` jeweils mit `TIMEOUT=30` und `TIMEOUT=120` wirft. Das ging nicht: Die Sandbox verbietet, einen lokalen Port zu öffnen (`PermissionError: [Errno 1] Operation not permitted` bei `s.bind`).
- Der Kundenserver (`https://kunde.example.invalid/import`) ist von hier nicht erreichbar, und es gibt keinen mitgeschnittenen Abbruch.
- Die bestehenden Tests (`python3 -m unittest discover -s tests -q`) sind grün (2 Tests, OK). Sie prüfen den Abbruch aber gar nicht: Getestet wird nur das Erzeugen der Daten und der Erfolgsfall mit einem Fake.

**Ursache:** nicht belegt.

**Zur Timeout-Vermutung, nicht gemessen:** Ein `ConnectionResetError` heißt, dass die Gegenseite oder etwas dazwischen (Load Balancer, Proxy, Firewall) die Verbindung aktiv abgebrochen hat. Läuft das Timeout ab, wirft Python einen anderen Fehler (`TimeoutError` bzw. `socket.timeout`, verpackt in `URLError`). Das Timeout auf 120 s zu erhöhen, hätte also wahrscheinlich keine Wirkung. Belegen konnte ich das hier aber nicht, weil der Versuch an der Port-Sperre gescheitert ist.

**Ausgeschlossen:** noch nichts, weil ohne roten Befehl keine Messung lief. Diese Vermutungen sind offen, sie lassen sich erst mit Daten prüfen:
1. Der Server des Kunden oder ein Gerät davor bricht lange Verbindungen nach einer festen Zeit ab, oder Anfragen, die zu groß sind. Dann müsste der Fehler mit der Größe des Exports oder der Dauer zusammenhängen.
2. Der Kundenserver wird nachts zur selben Zeit neu gestartet oder gewartet. Dann müssten die Abbrüche zu einer festen Uhrzeit passieren.
3. Ein kurzer Netzwerkfehler. Dann würde ein erneuter Versuch helfen.

Dazu eine Beobachtung am Code: `push()` versucht es bei einem Fehler nicht erneut und schreibt nichts ins Log. Das ist der Grund, warum es keine Logs gibt, aber keine Ursache des Abbruchs.

**Regressionstest:** fehlt. Befund: Es gibt keine Teststelle, die einen echten Verbindungsabbruch auslöst. Der Fake-`opener` in `tests/test_push.py` kennt nur den Erfolgsfall.

**Debug-Tag entfernt:** `grep -rn "DEBUG-k3r9" .` → kein Treffer. Das Wegwerf-Verzeichnis `<tmp>` ist gelöscht.

**Liegen geblieben:** nichts. `git status` ist sauber.

**Warum nicht gefangen:** Kein Test prüft, was beim Verbindungsabbruch passiert. Ohne Logging ist ein Abbruch in der Nacht außerdem unsichtbar, bis der Kunde sich meldet.

**Wiederholungs-Sperre (Vorschlag für `/slickfab:retro`, nicht eingebaut):** Jede Verbindung nach außen loggt Fehler, und zu jeder gibt es einen Test für den Fehlerfall. Das entspricht schon der Guardrail-Regel „Kein Code im Vakuum“.

**Was ich brauche, um weiterzumachen (eines davon reicht):**
- Daten zu den Abbrüchen: an welchen Tagen, zu welcher Uhrzeit, wie groß der Export war. Oder die Server-Logs des Kunden für diese Nächte.
- Zugang zu einer Testumgebung des Kunden, in der der Fehler auftritt.
- Die Erlaubnis, in `push()` vorübergehend Logging einzubauen (Dauer, Größe des Exports, genaue Ausnahme), um ein paar Nächte lang Belege zu sammeln.
- Oder eine Umgebung, in der lokale Ports erlaubt sind (`sandbox.network.allowLocalBinding: true`). Dann kann ich wenigstens nachweisen, dass das Timeout bei einem Verbindungsabbruch nichts ändert.

Für den CTO jetzt: Das Timeout zu erhöhen ist wahrscheinlich die falsche Stellschraube. Vorher lohnt es sich, mit dem Kunden zu klären, ob nachts etwas auf seiner Seite neu startet oder Verbindungen kappt. Ein automatischer erneuter Versuch wäre denkbar. Bei einem POST kann der Kunde die Daten aber doppelt bekommen, wenn der Abbruch erst nach dem Import kommt. Deshalb sollte das nicht ohne Rückfrage beim Kunden eingebaut werden.

Nächster Schritt: `/slickfab:debug <ConnectionResetError beim nächtlichen Export>`, sobald Daten zu den Abbrüchen (Zeit, Größe, Kunden-Logs), Zugang zur Kundenumgebung oder die Erlaubnis für vorübergehendes Logging da ist

SLICKFAB-STATUS: NEEDS_CONTEXT
