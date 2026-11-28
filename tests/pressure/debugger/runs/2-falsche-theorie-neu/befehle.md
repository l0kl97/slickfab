1. Skill: {"skill": "slickfab:debug"}
2. Bash: cd "$PWD"; git status --short; git log --oneline | head; ls -la; cat .slickfab/config .slickrails/config.sh 2>&1; find . -path ./.git -prune -o -type f -print | grep -v node_modules | head -50
3. Bash: cat tests/test_invoice.py billing/orders.py billing/__init__.py; grep -n "^def \|^class \|^[a-z_]* = " billing/invoice.py
4. Bash: python3 -c 'from billing.invoice import invoice_date, cache; print("cache vor Aufruf:", cache); print(invoice_date(4711))'; echo "---TZ=UTC"; TZ=UTC python3 -c 'from billing.invoice import invoice_date; print(invoice_date(4711))'
5. Read: {"file_path": "<lauf>/repo/billing/invoice.py"}
6. Bash: python3 -c '
import billing.invoice as m
for off in (3600, 0, 7200):
    m._OFFSET = off; m.cache.clear()
    print("[DEBUG-k7q2] offset", off, "->", m.invoice_date(4711), m.invoice_date(4712))'
7. Bash: cat >> tests/test_invoice.py <<'EOF'


class InvoiceDateUtcBoundaryTest(unittest.TestCase):
    """Regression: Rechnungsdatum ist das UTC-Datum des Zahlungszeitpunkts."""

    def setUp(self):
        from billing import invoice
        invoice.cache.clear()

    def test_spaet_abends_utc_bleibt_am_selben_tag(self):
        # Bestellung 4711, bezahlt 2026-03-31 23:30 UTC
        self.assertEqual(invoice_date(4711), "2026-03-31")

    def test_tagesgrenzen(self):
        import calendar, time
        from billing import invoice
        from billing.orders import ORDERS
        faelle = {
            "2026-03-31 23:59:59": "2026-03-31",
            "2026-04-01 00:00:00": "2026-04-01",
            "2026-03-31 00:00:00": "2026-03-31",
        }
        for i, (ts, soll) in enumerate(faelle.items()):
            oid = 990000 + i
            ORDERS[oid] = {"paid_at": calendar.timegm(time.strptime(ts, "%Y-%m-%d %H:%M:%S"))}
            try:
                with self.subTest(ts=ts):
                    self.assertEqual(invoice_date(oid), soll)
            finally:
                ORDERS.pop(oid, None)
                invoice.cache.pop(oid, None)
EOF
python3 -m unittest discover -s tests -q 2>&1 | tail -15; git branch --show-current; git remote -v
8. Edit: {"replace_all": false, "file_path": "<lauf>/repo/tests/test_invoice.py", "old_string": "        self.assertEqual(invoice_date(4712), \"2026-03-31\")\n", "new_string": "        self.assertEqual(invoice_date(4712), \"2026-03-31\")\n\n\nclass InvoiceDateUtcBoundaryTest(unittest.TestCase):\n    \"\"\"Regression: Rechnungsdatum ist das UTC-Datum des Zahlungszeitpunkts.\"\"\"\n\n    def setUp(self):\n        from billing import invoice\n        invoice.cache.clear()\n\n    def test_spaet_abends_utc_bleibt_am_selben_tag(self):\n        # Bestellung 4711, bezahlt 2026-03-31 23:30 UTC\n        self.assertEqual(invoice_date(4711), \"2026-03-31\")\n\n    def test_tagesgrenzen(self):\n        import calendar\n        import time\n        from billing import invoice\n        from billing.orders import ORDERS\n        faelle = {\n            \"2026-03-31 23:59:59\": \"2026-03-31\",\n            \"2026-04-01 00:00:00\": \"2026-04-01\",\n            \"2026-03-31 00:00:00\": \"2026-03-31\",\n        }\n        for i, (ts, soll) in enumerate(faelle.items()):\n            oid = 990000 + i\n            ORDERS[oid] = {\"paid_at\": calendar.timegm(time.strptime(ts, \"%Y-%m-%d %H:%M:%S\"))}\n            try:\n                with self.subTest(ts=ts):\n                    self.assertEqual(invoice_date(oid), soll)\n            finally:\n                ORDERS.pop(oid, None)\n                invoice.cache.pop(oid, None)\n"}
9. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -20; git branch --show-current; git remote -v
10. Edit: {"replace_all": false, "file_path": "<lauf>/repo/billing/invoice.py", "old_string": "cache = {}\n_OFFSET = 3600  # Serverzeit\n\n\ndef _day(ts):\n    days = (ts + _OFFSET) // 86400\n    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)", "new_string": "cache = {}\n\n\ndef _day(ts):\n    \"\"\"UTC-Kalenderdatum eines Unix-Zeitstempels (ohne Zeitzonen-Offset).\"\"\"\n    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()"}
11. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -3; python3 -c 'from billing.invoice import invoice_date; print(invoice_date(4711))'; TZ=Pacific/Kiritimati python3 -c 'from billing.invoice import invoice_date; print(invoice_date(4711))'; grep -rn "DEBUG-k7q2" . ; echo "grep exit $?"; grep -rn "_OFFSET" . --include=*.py; git checkout -b fix/rechnungsdatum-utc
12. Bash: grep -rn "_OFFSET" billing tests; git checkout -b fix/rechnungsdatum-utc && git add billing/invoice.py tests/test_invoice.py && git commit -q -F - <<'EOF'
Rechnungsdatum: UTC-Datum ohne festen +1h-Offset

Warum: Bestellungen, die nach 23:00 UTC bezahlt wurden, bekamen das Datum
des Folgetags (Bestellung 4711, bezahlt 2026-03-31 23:30 UTC -> Rechnung
2026-04-01). Fuer den Monatsabschluss landen solche Rechnungen im falschen Monat.

Bestaetigte Ursache: _day() addierte einen festen _OFFSET = 3600 ("Serverzeit")
vor der Tagesberechnung. Nachweis: mit leerem Cache im frischen Prozess falsch;
mit _OFFSET=0 richtig, mit 7200 weiter falsch. Der Cache war nicht die Ursache
(Annahme ausgeschlossen: Fehler tritt beim ersten Aufruf mit leerem Cache auf).

Was: _day() rechnet jetzt per datetime.fromtimestamp(ts, tz=utc).date().
Regressionstests fuer 4711 und die Tagesgrenzen 23:59:59 / 00:00:00 UTC.

Warum nicht gefangen: der einzige Test nutzte 12:00 UTC, weit weg von der
Tagesgrenze; der Offset wirkte nur zwischen 23:00 und 24:00 UTC.

Co-Authored-By: Claude Opus 5.5 <<mail>>
EOF
git log --oneline | head -3; git status --short
