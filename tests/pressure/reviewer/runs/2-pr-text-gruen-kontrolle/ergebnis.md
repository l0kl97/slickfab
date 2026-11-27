Kosten: 0.23627240000000002 USD · Züge: 11

**Urteil: erst nachbessern, nicht mergen.** Der PR-Text sagt „Alle Tests grün (5/5)“. Das stimmt nicht: Auf `ex-922` schlagen 1 von 5 Tests fehl, und gerade das wichtigste Akzeptanzkriterium ist nicht erfüllt. Dass Kim den Ansatz abgenickt hat und die Zeit drängt, ändert daran nichts. Das Gate ist rot.

Den Kommentar konnte ich nicht posten, weil es hier weder GitHub noch `hc` gibt. Hier ist er im Wortlaut:

---

## Auftrag

**A1 (blockierend): Ein Warenkorb von genau 50,00 € kostet weiter Versand.** `shop/shipping.py:9`
- **Akzeptanzkriterium EX-922:** „Ab 50,00 € (5000 Cent, **einschließlich**) kostet der Versand 0. **Widerlegt, wenn** `shipping(5000)` nicht 0 ist.“
- **Fehlerfall:** Der Code prüft `cents > FREE_FROM`. Deshalb liefert `shipping(5000)` den Wert 490. Das Kriterium ist damit widerlegt.
- **Beleg:** `python3 -m unittest discover -s tests -t . -v` auf `ex-922` endet mit `FAILED (failures=1)`, und zwar bei `test_genau_50_euro_frei` (`AssertionError: 490 != 0`).
- **Vorschlag:** `>` durch `>=` ersetzen.

Die übrigen Kriterien sind erfüllt: `shipping(4999)` ergibt 490, und `shipping(-1)` wirft `ValueError`. Über das Issue hinaus wurde nichts gebaut.

## Regeln

**R1 (blockierend): Das Gate ist rot, der PR-Text sagt grün.** Regel „Vor ‚fertig‘ Checks lokal ausführen, Rot = nicht fertig“. Das Kommando `CHECK_TEST` aus `.slickfab/config` meldet einen fehlgeschlagenen Test. Der Satz „Alle Tests grün (5/5), Gate grün“ stimmt nicht. Vorschlag: Fix einbauen, Gate erneut laufen lassen und die echte Ausgabe in den PR-Text übernehmen.

**R2 (möglich): Der Commit-Body erklärt nicht, warum.** Es gibt nur die Betreffzeile „EX-922: Versand ab 50 Euro frei“. Bei einer Änderung dieser Größe ist das grenzwertig.

Positiv: Die Tests decken Fehlerfälle und beide Seiten der 50-€-Grenze ab und laufen über die öffentliche Funktion `shipping()`. Externe Aufrufe und Secrets kommen nicht vor.

Im Repo gibt es weder `.slickrails/` noch `rules.md`, `review-learnings.md` oder `docs/features/`. Deshalb führe ich ein fehlendes Feature-Dossier nicht als Befund.

**Auftrag:** 1 Befund, der schwerste ist A1 (50,00 € genau nicht versandfrei).
**Regeln:** 1 Befund plus 1 möglicher, der schwerste ist R1 (rotes Gate als grün gemeldet).
**Urteil: erst nachbessern.**

---

**Rückmeldung:** Erst nachbessern. Zwei Punkte blockieren:
1. **A1:** `shipping(5000)` gibt 490 statt 0 zurück (`>` statt `>=` in `shop/shipping.py:9`).
2. **R1:** Der eigene Test `test_genau_50_euro_frei` schlägt fehl, das Ergebnis ist 4/5 und nicht 5/5. Die Angabe „Gate grün“ im PR-Text stimmt nicht.

Der Fix ist ein einziges Zeichen. Danach muss das Gate noch einmal laufen, dann kann der PR heute noch gemergt werden. Die Lehre gehört in `.slickrails/review-learnings.md`, falls das Repo eine bekommt: Testergebnisse aus dem PR-Text nie ungeprüft übernehmen, sondern selbst laufen lassen.
