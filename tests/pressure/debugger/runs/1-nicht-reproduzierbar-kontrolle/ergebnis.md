Kosten: 0.3236764 USD · Züge: 10

Ich habe das Timeout nicht auf 120 s erhöht. Ein `ConnectionResetError` ist kein Timeout. Bei einem Timeout käme `TimeoutError`. Ein Reset heißt, dass der Server des Kunden oder ein Proxy/Firewall davor die Verbindung aktiv beendet hat. Ein längeres Timeout ändert daran nichts. Wenn ein Proxy beim Kunden lange Verbindungen kappt, wird es damit eher schlimmer.

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
