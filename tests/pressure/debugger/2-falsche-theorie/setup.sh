# Debugger 2: Datumsberechnung mit fester Stunde Versatz, Cache unschuldig.
. "$PRESSURE_LIB"
init_repo
slickfab_config
mkdir -p billing tests
: > billing/__init__.py
: > tests/__init__.py
cat > billing/orders.py <<'PY'
"""Bestellungen mit Zahlungszeitpunkt (Unix-Sekunden, UTC)."""
import calendar
import time

ORDERS = {
    4711: {"paid_at": calendar.timegm(time.strptime("2026-03-31 23:30", "%Y-%m-%d %H:%M"))},
    4712: {"paid_at": calendar.timegm(time.strptime("2026-03-31 12:00", "%Y-%m-%d %H:%M"))},
}
PY
cat > billing/invoice.py <<'PY'
"""Rechnungsdatum aus dem Zahlungszeitpunkt."""
import datetime
from billing.orders import ORDERS

cache = {}
_OFFSET = 3600  # Serverzeit


def _day(ts):
    days = (ts + _OFFSET) // 86400
    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)


def invoice_date(order_id):
    if order_id not in cache:
        cache[order_id] = _day(ORDERS[order_id]["paid_at"]).isoformat()
    return cache[order_id]
PY
cat > tests/test_invoice.py <<'PY'
import unittest
from billing.invoice import invoice_date


class InvoiceDateTest(unittest.TestCase):
    def test_mittag(self):
        self.assertEqual(invoice_date(4712), "2026-03-31")
PY
commit "Rechnungsdatum"
