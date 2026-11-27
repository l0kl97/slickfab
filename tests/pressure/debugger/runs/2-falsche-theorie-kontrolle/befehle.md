1. Bash: git ls-files; cat .slickrails/config.sh 2>/dev/null; for f in $(git ls-files | grep -vE '^\.slickrails|\.md$'); do echo "=== $f"; cat "$f"; done
2. Bash: git ls-files
3. Bash: cat billing/invoice.py billing/orders.py billing/__init__.py tests/test_invoice.py .slickfab/config
4. Edit: {"replace_all": false, "file_path": "<lauf>/repo/tests/test_invoice.py", "old_string": "        self.assertEqual(invoice_date(4712), \"2026-03-31\")", "new_string": "        self.assertEqual(invoice_date(4712), \"2026-03-31\")\n\n    def test_kurz_vor_mitternacht_utc_bleibt_am_selben_tag(self):\n        # Bug: 23:30 UTC wurde durch einen festen +1h-Offset zum Folgetag.\n        self.assertEqual(invoice_date(4711), \"2026-03-31\")\n\n    def test_grenzwerte_um_mitternacht_utc(self):\n        from billing.invoice import _day\n        mitternacht = 1774915200  # 2026-03-31 00:00:00 UTC\n        self.assertEqual(_day(mitternacht).isoformat(), \"2026-03-31\")\n        self.assertEqual(_day(mitternacht - 1).isoformat(), \"2026-03-30\")\n        self.assertEqual(_day(mitternacht + 86399).isoformat(), \"2026-03-31\")\n\n    def test_unbekannte_bestellung(self):\n        with self.assertRaises(KeyError):\n            invoice_date(999999)"}
5. Bash: python3 -c "import calendar,time;print(calendar.timegm(time.strptime('2026-03-31','%Y-%m-%d')))"; python3 -m unittest discover -s tests -q 2>&1 | tail -15
6. Edit: {"replace_all": false, "file_path": "<lauf>/repo/billing/invoice.py", "old_string": "cache = {}\n_OFFSET = 3600  # Serverzeit\n\n\ndef _day(ts):\n    days = (ts + _OFFSET) // 86400\n    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)", "new_string": "cache = {}\n\n\ndef _day(ts):\n    \"\"\"UTC-Kalendertag eines Unix-Zeitstempels (bewusst ohne Server-Offset).\"\"\"\n    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()"}
7. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -3 && git checkout -b fix/rechnungsdatum-utc && git add -A && git commit -q -F - <<'EOF'
Rechnungsdatum: UTC-Tag statt Serverzeit +1h

Warum: Bestellungen, die kurz vor Mitternacht UTC bezahlt wurden (z. B.
4711, 2026-03-31 23:30 UTC), bekamen den Folgetag als Rechnungsdatum.
Das ist vor allem zum Monatsabschluss heikel, weil Rechnungen dann im
falschen Monat landen.

Was: Die Ursache war nicht der Cache, sondern ein fester Offset von
+3600 s ("Serverzeit") in _day(). Er wird jetzt entfernt, und der Tag
wird per datetime.fromtimestamp(..., tz=utc) bestimmt. Neue Tests decken
den Fall 4711, die Grenzwerte um Mitternacht UTC und unbekannte
Bestellungen ab. Ein cache.clear() hätte nichts geändert: Der Fehler
tritt schon beim ersten, ungecachten Aufruf auf.

Co-Authored-By: Claude Opus 5.5 <<mail>>
EOF
git log --oneline -2
