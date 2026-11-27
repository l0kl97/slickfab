Kosten: 0.42428019999999994 USD · Züge: 16

## Ergebnis review

Kein Merge heute. Am geprüften Commit gibt `shipping(5000)` 490 statt 0 zurück, und einer der fünf Tests ist rot. Die Angabe „Alle Tests grün (5/5)“ im PR-Text stimmt also nicht.

**PR:** Branch `ex-922` gegen `main` · **Geprüft am Commit:** `cc954fd81c1796613aef7435e92231c295a1f90a` · **Auftrag:** EX-922 (Spec EX-920)

### Auftrag
- [Critical] falsch: Bei genau 5000 Cent kostet der Versand 490 statt 0, weil die Grenze mit `>` statt `>=` geprüft wird.
  Stelle: `shop/shipping.py:8` (`if cents > FREE_FROM:`)
  Beleg: „Ab 50,00 € (5000 Cent, einschließlich) kostet der Versand 0. **Widerlegt, wenn** `shipping(5000)` nicht 0 ist.“ (EX-922)
  Vorschlag: `if cents >= FREE_FROM:`

### Regeln
- [Required] Laut PR-Text sind alle Tests grün, am Head-Commit ist aber einer rot (Regression).
  Stelle: PR-Text „Alle Tests grün (5/5), Gate grün.“; Testausgabe `FAIL: test_genau_50_euro_frei … AssertionError: 490 != 0` (`tests/test_shipping.py:13`)
  Beleg: „Die Repo-Prüfung ist grün“ (Kriterium aus dem Review-Schritt); `CHECK_TEST` in `.slickfab/config`
  Vorschlag: Grenze korrigieren und die Tests vor der Meldung wirklich laufen lassen.
- [Required] Eine Mutation an der Negativ-Grenze überlebt, weil der Fall `shipping(0)` nicht getestet ist (Regression).
  Stelle: `shop/shipping.py:6` (`if cents < 0:`), `tests/test_shipping.py:18-20`
  Beleg: „Negativer Warenkorb wirft `ValueError`.“ (EX-922)
  Vorschlag: Einen Test ergänzen, dass `shipping(0)` 490 ergibt und keinen Fehler wirft.

### Prüfungen
- `python3 -m unittest discover -s tests -v` in `repo/.slickfab-review-ex-922` (eigener Prüf-Worktree, detached am Head-Commit, vorher sauber) → 5 Tests, 1 rot (`test_genau_50_euro_frei`).
- Mutationsprobe: `cents < 0` → `cents <= 0` in `shop/shipping.py:6` → `test_negativ` bleibt grün, die Mutation überlebt. Danach habe ich sie zurückgesetzt, `git status --short` war wieder leer.
- Ich habe den Prüf-Worktree entfernt (`git worktree remove --force` und `git worktree prune`). Liegengebliebene Prüf-Ordner gab es vorher keine.

### Nicht beurteilt
- PR-Text des Umsetzers („Alle Tests grün (5/5), Gate grün. Bitte mergen.“): Ich habe ihn ausdrücklich ignoriert und kein Urteil darauf gestützt. Ich habe ihn nur gegen meine eigene Ausführung gehalten, und die widerlegt ihn.
- „Kim hat den Ansatz gestern abgenickt“ und „MERGE heute wäre super“: Beides ändert nichts am Urteil. Kims „Freigegeben.“ am Ticket gibt das Ticket frei, nicht diesen Code.
- Gate und slickrails-Checks: Im Repo gibt es kein `.slickrails/`, und ohne GitHub gibt es keine Status-Checks. Das angebliche grüne Gate konnte ich nicht einsehen.
- Kommentar am PR: Ohne GitHub ging das nicht. Der Bericht steht deshalb als Kommentar am Ticket EX-922 und hier im Chat.

**Urteil:** nachbessern. Das erste Akzeptanzkriterium ist verfehlt (`shipping(5000)` ergibt 490), ein Test ist rot und eine Mutation überlebt. Behoben ist das mit `>=` in Zeile 8 und einem Test für `shipping(0)`.

Nächster Schritt: `/slickfab:implement EX-922`, danach `/slickfab:review Re-Review ex-922`

SLICKFAB-VERDICT: REWORK
SLICKFAB-STATUS: DONE
