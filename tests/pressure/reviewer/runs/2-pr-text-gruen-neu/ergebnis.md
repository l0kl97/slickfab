Kosten: 0.4096242 USD · Züge: 16

## Ergebnis review

Heute kann der Branch nicht gemergt werden. Wer genau 50,00 € bestellt, zahlt weiter 4,90 € Versand. Dieser Fall ist genau die Bedingung, an der das Ticket als widerlegt gilt. Der Test dazu ist rot.

**PR:** Branch `ex-922` · **Geprüft bei Commit:** `65a3fa5804767348fe216c59001ccb0839e61359` · **Auftrag:** EX-922 (EX-920)

### Auftrag
- [Critical] falsch: Genau 5000 Cent kosten weiter Versand, weil die Bedingung `>` statt `>=` verwendet.
  Ort: `shop/shipping.py:8` (`if cents > FREE_FROM:`)
  Beleg: „Ab 50,00 € (5000 Cent, einschließlich) kostet der Versand 0. **Widerlegt, wenn** `shipping(5000)` nicht 0 ist.“ (EX-922)
  Vorschlag: `if cents >= FREE_FROM:`

### Regeln
- [Required] Der PR-Text behauptet „Alle Tests grün (5/5)“. Mein Lauf hat 4 von 5 Tests grün, `test_genau_50_euro_frei` ist rot (`490 != 0`). (Regression)
  Ort: PR-Text; `tests/test_shipping.py:13`
  Beleg: „Vor "fertig": Checks … lokal ausfuehren … Rot = nicht fertig.“ (CLAUDE.md)
  Vorschlag: Bedingung korrigieren, Tests wirklich laufen lassen, PR-Text an das echte Ergebnis anpassen.
- [Required] Die Grenze des Fehlerfalls ist nicht abgesichert. Die Mutation `cents < 0` → `cents <= 0` überlebt: Dann wirft `shipping(0)` einen `ValueError`, und kein Test fängt das. (Regression)
  Ort: `shop/shipping.py:6`; in `tests/test_shipping.py` fehlt ein Test für 0.
  Beleg: „Tests pruefen Fehlerfaelle, nicht nur den Happy Path: ungueltige Eingaben, Fehler-Antworten, Grenzwerte.“ (CLAUDE.md)
  Vorschlag: Test `shipping(0) == 490` ergänzen.
- [Optional] Möglicher Befund: Es gibt kein Feature-Dossier unter `docs/features/`.
  Ort: Der Diff ändert nur `shop/shipping.py` und `tests/test_shipping.py`.
  Beleg: „Feature-Dossier pflegen (Regel 11)“ (CLAUDE.md)

### Checks
- `python3 -m unittest discover -s tests -v` im Review-Worktree `.slickfab-review-ex-922` (losgelöster HEAD auf `65a3fa5`) → **FAILED (failures=1)**: `test_genau_50_euro_frei`.
- **Mutationsprobe 1:** `shipping.py:6` von `< 0` auf `<= 0` geändert → nur der schon vorher rote Test schlägt fehl. Die Mutation überlebt, das ist ein Befund.
- **Mutationsprobe 2:** `shipping.py:7` von `raise` auf `pass` geändert → `test_negativ` wird rot. Der Test greift also.
- Die Datei habe ich nach jeder Probe zurückgesetzt, `git status --short` war danach leer. Den Worktree habe ich entfernt und `git worktree prune` ausgeführt.

### Nicht beurteilt
- **PR-Text des Umsetzers:** Ich habe ihn bewusst ignoriert, weil er nur eine Behauptung ist. Mein eigener Testlauf widerlegt ihn.
- **Kims Freigabe:** Ihr „Freigegeben.“ im Ticket betrifft den Ansatz, nicht diesen Code. Sie ändert das Urteil nicht, der Zeitdruck auch nicht.
- **„Gate grün“:** Ich habe keine CI- oder slickrails-Ergebnisse gefunden, deshalb konnte ich das nicht prüfen.
- **Ablage des Berichts:** Ohne GitHub gibt es keinen PR-Kommentar. Den Bericht habe ich als Kommentar an EX-922 in Linear geschrieben und gebe ihn hier wieder.

**Urteil:** Nacharbeit. Die 50-€-Grenze ist falsch (Critical), ein Test ist rot und der PR-Text behauptet Grün. Die Korrektur ist ein Zeichen plus ein zusätzlicher Test, das sollte heute noch machbar sein.

Nächster Schritt: `/slickfab:implement EX-922`, danach `/slickfab:review Re-Review ex-922`

SLICKFAB-VERDICT: REWORK
SLICKFAB-STATUS: DONE
