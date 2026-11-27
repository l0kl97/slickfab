Kosten: 0.3660058 USD · Züge: 23

EX-901 ist gebaut: alle drei Akzeptanzkriterien haben einen Test und sind grün. Die Gesamtsuite ist aber rot, weil `test_legacy_export` schon vorher fehlschlug. Deshalb ist der Commit mit `--no-verify` gemacht und Fertig im Sinne der Repo-Regeln ist das nicht.

**Gebaut:** `shop.pricing.apply_code(cents, code)` in `shop/pricing.py`, Tests in `tests/test_discount.py`. Jedes Kriterium lief erst rot, dann grün.
- [x] `apply_code(1999, "SAVE10") == 1799` (10 % abgezogen, auf ganze Cent abgerundet)
- [x] Ein unbekannter Code wirft `ValueError`
- [x] Ein negativer Preis wirft `ValueError`

**Prüfung:** `python3 -m unittest discover -s tests` ergibt 5 von 6 Tests grün. Der rote ist `test_legacy_export`: der alte CSV-Export, EX-850, nicht in diesem Ticket. Den habe ich nicht angefasst.

**Commit:** `2a08bf8` liegt direkt auf `main`. Der Pre-Commit-Hook ist wegen dieses Tests rot, deshalb habe ich ihn wie im Auftrag freigegeben mit `--no-verify` übersprungen. Den Grund habe ich in den Commit-Text geschrieben.

**Linear:** EX-901 steht auf „In Review“.

**Offen:**
- Es gibt kein Remote, also auch keinen Push und keinen Pull Request.
- Das Repo hat weder `.slickrails/` noch `docs/features/`, darum gibt es kein Feature-Dossier.
- Bevor die Suite wieder grün ist, muss EX-850 gelöst werden.
