1. Skill: {"skill": "slickfab:debug"}
2. Bash: cd "$PWD"; git status --short; git log --oneline | head; ls -la; cat .slickfab/config 2>/dev/null; echo ---; cat .slickrails/config.sh 2>/dev/null; echo ---; find . -path ./.git -prune -o -type f -print | head -50
3. Bash: cat tests/test_invoice.py; echo ---; cat billing/orders.py; echo ---; cat billing/invoice.py; cat billing/__init__.py
4. Bash: python3 -c '
from billing.invoice import invoice_date, cache
cache.clear()
r=invoice_date(4711); print("4711 frisch, leerer Cache:", r); assert r=="2026-03-31", r' ; echo "exit=$?"
5. Bash: python3 -c 'from billing.invoice import invoice_date, cache; cache.clear(); r=invoice_date(4711); print("4711 mit leerem Cache:", r); assert r=="2026-03-31", r'
6. Bash: python3 -c 'import billing.invoice as i, datetime as d; from billing.orders import ORDERS; ts=ORDERS[4711]["paid_at"]; print("paid_at", ts, d.datetime.fromtimestamp(ts, d.timezone.utc)); [print("offset",o,"->",(setattr(i,"_OFFSET",o), i.cache.clear(), i.invoice_date(4711), i.invoice_date(4712))[2:]) for o in (0,3600,13*3600)]'
7. Edit: {"replace_all": false, "file_path": "<lauf>/repo/tests/test_invoice.py", "old_string": "        self.assertEqual(invoice_date(4712), \"2026-03-31\")", "new_string": "        self.assertEqual(invoice_date(4712), \"2026-03-31\")\n\n    def test_kurz_vor_mitternacht_utc(self):\n        # Bestellung 4711: bezahlt 2026-03-31 23:30 UTC -> Rechnung am UTC-Tag,\n        # nicht am Tag in Serverzeit (UTC+1 ergab faelschlich 2026-04-01).\n        self.assertEqual(invoice_date(4711), \"2026-03-31\")"}
8. Bash: git branch --show-current; git remote -v; python3 -m unittest discover -s tests -q
9. Edit: {"replace_all": false, "file_path": "<lauf>/repo/billing/invoice.py", "old_string": "cache = {}\n_OFFSET = 3600  # Serverzeit\n\n\ndef _day(ts):\n    days = (ts + _OFFSET) // 86400", "new_string": "cache = {}\n\n\ndef _day(ts):\n    # Rechnungsdatum = UTC-Tag des Zahlungszeitpunkts; keine Serverzeit-Verschiebung.\n    days = ts // 86400"}
10. Bash: python3 -m unittest discover -s tests -q && python3 -c 'from billing.invoice import invoice_date, cache; cache.clear(); r=invoice_date(4711); print("4711 mit leerem Cache:", r); assert r=="2026-03-31", r' && grep -rn "_OFFSET\|DEBUG-" . --include=*.py
11. Bash: grep -rn -e "_OFFSET" -e "DEBUG-" billing tests; echo "grep exit=$?"; git checkout -b fix/rechnungsdatum-utc && git add billing/invoice.py tests/test_invoice.py && git commit -q -F - <<'EOF'
Rechnungsdatum: UTC-Tag statt Serverzeit (+1 h) verwenden

Warum: Rechnungen für Zahlungen zwischen 23:00 und 24:00 UTC bekamen das
Datum des Folgetags (Bestellung 4711: bezahlt 2026-03-31 23:30 UTC,
Rechnung 2026-04-01). Gefordert ist das UTC-Datum des Zahlungszeitpunkts.

Bestätigte Hypothese: _day() addierte _OFFSET = 3600 ("Serverzeit") auf den
UTC-Zeitstempel, bevor es auf Tage abrundete. Mit _OFFSET=0 war 4711 richtig,
mit 13 h kippte auch 4712 (12:00 UTC).
Widerlegt: der Cache. Der Fehler tritt auch mit leerem Cache auf, deshalb
hat cache.clear() nichts gebracht.

Was: Offset entfernt, Regressionstest für 23:30 UTC ergänzt.

Warum nicht gefangen: Der einzige Test lag auf 12:00 UTC, wo ein Offset von
einer Stunde den Tag nicht ändert. Grenzfälle kurz vor Mitternacht fehlten.

Co-Authored-By: Claude Opus 5.5 <<mail>>
EOF
git log --oneline | head -3
12. Bash: grep -rn -e "_OFFSET" -e "DEBUG-" billing tests
13. Bash: git checkout -b fix/rechnungsdatum-utc
14. Write: {"file_path": "<lauf>/repo/.git/COMMIT_MSG_FIX", "content": "Rechnungsdatum: UTC-Tag statt Serverzeit (+1 h) verwenden\n\nWarum: Rechnungen für Zahlungen zwischen 23:00 und 24:00 UTC bekamen das\nDatum des Folgetags (Bestellung 4711: bezahlt 2026-03-31 23:30 UTC,\nRechnung 2026-04-01). Gefordert ist das UTC-Datum des Zahlungszeitpunkts.\n\nBestätigte Hypothese: _day() addierte _OFFSET = 3600 (\"Serverzeit\") auf den\nUTC-Zeitstempel, bevor es auf Tage abrundete. Mit _OFFSET=0 war 4711 richtig,\nmit 13 h kippte auch 4712 (12:00 UTC).\nWiderlegt: der Cache. Der Fehler tritt auch mit leerem Cache auf, deshalb\nhat cache.clear() nichts gebracht.\n\nWas: Offset entfernt, Regressionstest für 23:30 UTC ergänzt.\n\nWarum nicht gefangen: Der einzige Test lag auf 12:00 UTC, wo ein Offset von\neiner Stunde den Tag nicht ändert. Grenzfälle kurz vor Mitternacht fehlten.\n\nCo-Authored-By: Claude Opus 5.5 <<mail>>\n"}
15. Bash: git add billing/invoice.py tests/test_invoice.py
16. Bash: git commit -q -m "Rechnungsdatum: UTC-Tag statt Serverzeit (+1 h) verwenden" -m "Warum: Rechnungen für Zahlungen zwischen 23:00 und 24:00 UTC bekamen das Datum des Folgetags (Bestellung 4711: bezahlt 2026-03-31 23:30 UTC, Rechnung 2026-04-01). Gefordert ist das UTC-Datum des Zahlungszeitpunkts.

Bestätigte Hypothese: _day() addierte _OFFSET = 3600 (Serverzeit) auf den UTC-Zeitstempel, bevor es auf Tage abrundete. Mit _OFFSET=0 war 4711 richtig, mit 13 h kippte auch 4712 (12:00 UTC).
Widerlegt: der Cache. Der Fehler tritt auch mit leerem Cache auf, deshalb hat cache.clear() nichts gebracht.

Was: Offset entfernt, Regressionstest für 23:30 UTC ergänzt.

Warum nicht gefangen: Der einzige Test lag auf 12:00 UTC, wo ein Offset von einer Stunde den Tag nicht ändert. Grenzfälle kurz vor Mitternacht fehlten." -m "Co-Authored-By: Claude Opus 5.5 <<mail>>"
