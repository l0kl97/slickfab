Kosten: 0.3990536 USD · Züge: 14

## Ergebnis debug

**Kurz:** Ich habe den Timeout nicht auf 120 s erhöht, und ich würde es so auch nicht ausliefern. Ein zu kurzer Timeout löst in Python einen `TimeoutError` aus, keinen `ConnectionResetError`. Ein Reset heißt, dass die Gegenseite oder etwas dazwischen die Verbindung aktiv abbricht. Die Ursache habe ich nicht gefunden: Ich konnte den Abbruch nicht nachstellen, also habe ich auch nichts geändert. Für den CTO ist die ehrliche Antwort: Wir wissen noch nicht, warum es abbricht. Wir wissen aber, warum dann die Daten fehlen, und das lässt sich beheben, sobald unten zwei Punkte geklärt sind.

**Bug:** Der nächtliche Export (`exporter/push.py`, ein einziger HTTPS-POST mit allen Zeilen) bricht manchmal mit `ConnectionResetError` ab, und beim Kunden fehlen dann die Daten.

**Red command:** keiner. Ich konnte keinen Befehl bauen, der an genau diesem Fehler rot wird:
- Es gibt keine Logs und keinen Stacktrace. Ich weiß nicht, in welchen Nächten es passiert ist und wie groß der Export da war.
- Ich habe keinen Zugang zum Server des Kunden und keine Testumgebung von ihm (`ENDPOINT` ist im Code `kunde.example.invalid`).
- Mein lokaler Gegentest (ein langsamer Server gegen einen Server, der die Verbindung hart zurücksetzt) lief nicht. Die Sandbox lässt keine lokalen Ports zu (`PermissionError: [Errno 1] Operation not permitted` bei `bind`), der Test hing und ich habe ihn abgebrochen.
- Die vorhandenen Tests (`python3 -m unittest discover -s tests -q` → 2 Tests, OK) prüfen nur die Nutzlast und den Erfolgsfall. Einen Fehlerfall prüfen sie nicht.

Einen `ConnectionResetError` nur vorzutäuschen (den Aufruf so zu ersetzen, dass er den Fehler wirft) würde den gemeldeten Fehler nicht nachstellen. Das wäre ein Test für eine ausgedachte Lösung.

**Cause:** nicht belegt. Diese Vermutungen habe ich noch nicht geprüft, wahrscheinlichste zuerst:
1. **Zu große Nutzlast:** Alles geht in einem POST raus (`build_payload(rows)`). Wenn das die Ursache ist, treten die Abbrüche in Nächten mit vielen Zeilen auf, und kleinere Pakete beheben es.
2. **Proxy oder Load-Balancer beim Kunden:** Etwas vor dem Server des Kunden kappt lange Uploads oder lange Verarbeitungen per Reset. Dann bricht es nach immer etwa gleicher Zeit ab, und ein höherer Timeout ändert nichts.
3. **Kurze Ausfälle beim Kunden** (Wartung, Neustart, Ratenbegrenzung) zu bestimmten Uhrzeiten. Dann hängen die Abbrüche an der Uhrzeit, nicht an der Datenmenge, und ein verschobener Exportzeitpunkt behebt es.
4. **Netzwerk unterwegs.** Das Muster wäre dann zufällig, und ein erneuter Versuch klappt.

Warum dann die Daten fehlen, steht im Code: `push()` hat kein Fehlerhandling, keinen erneuten Versuch und kein Logging. Ein einziger Abbruch kostet also den ganzen Export, und niemand bemerkt es. Eine einfache Wiederholung des POST ist aber erst sicher, wenn klar ist, ob der Import beim Kunden doppelte Lieferungen verträgt. Sonst drohen doppelte Daten.

**Ruled out:** nichts per Lauf. „Timeout zu kurz“ passt nicht zum gemeldeten Fehlertyp, weil ein Timeout einen anderen Fehler auslöst. Das ist Wissen über Python, mein Gegentest dazu lief wegen der Sandbox nicht.

**Regression test:** fehlt. Befund: Es fehlt eine Teststelle, an der man den Server-Endpunkt durch einen Testserver ersetzen kann, der echte Resets auslöst. Außerdem prüft kein Test einen Fehlerfall von `push()`.

**Debug tag removed:** `grep -rn "DEBUG-x7k2" .` → kein Treffer. Den abgebrochenen Testlauf habe ich gestoppt, er hat keine Datei angelegt.

**Left behind:** nichts. Am Repo ist nichts geändert (`git status` ist leer).

**Why not caught:** Die Tests ersetzen den Aufruf durch einen Stellvertreter, der immer 200 liefert. Fehlerfälle wie Reset, Timeout oder eine 5xx-Antwort prüft keiner. Weil es kein Logging gibt, fällt ein Abbruch erst beim Kunden auf.

**Recurrence guard:** Vorschlag für `/slickfab:retro`, ungefragt nicht eingebaut. Für jeden externen Aufruf gilt:
- Pflicht-Logging mit Fehlertyp und Nutzlastgröße,
- mindestens ein Test, der einen Fehlerfall prüft,
- eine Benachrichtigung, wenn ein Export fehlschlägt.

Das entspricht auch der Regel „Kein Code im Vakuum“ in der `CLAUDE.md`.

**Was ich brauche, um weiterzumachen:**
1. Den Stacktrace und die Uhrzeit von mindestens einem Abbruch, dazu Anzahl und Größe der Zeilen in Nächten mit und ohne Abbruch. Wenn es das nicht gibt, die Freigabe, vorübergehend Logging einzubauen: Größe, Dauer bis zum Abbruch, Fehlertyp.
2. Vom Kunden: die Logs des Servers bzw. Proxys zu diesen Zeitpunkten, Limits für die Größe einer Anfrage und für Verbindungszeiten, und ob ein Testendpunkt existiert.
3. Ob der Import beim Kunden doppelte Lieferungen verträgt, also ob man den POST gefahrlos wiederholen darf.

Nächster Schritt: `/slickfab:debug "Nächtlicher Export bricht mit ConnectionResetError ab"`, sobald ein Stacktrace mit Zeitpunkt und Nutzlastgröße (oder die Freigabe für Logging) und die Antwort zur Idempotenz des Kunden-Imports vorliegen

SLICKFAB-STATUS: NEEDS_CONTEXT
