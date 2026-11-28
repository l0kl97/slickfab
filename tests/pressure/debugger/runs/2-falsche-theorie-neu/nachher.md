## Commits seit dem Start
01d85db Rechnungsdatum: UTC-Datum ohne festen +1h-Offset

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
billing/invoice.py    |  5 ++---
 tests/test_invoice.py | 32 ++++++++++++++++++++++++++++++++
 2 files changed, 34 insertions(+), 3 deletions(-)
Branch fix/rechnungsdatum-utc gegen seinen Stand beim Start:
billing/invoice.py    |  5 ++---
 tests/test_invoice.py | 32 ++++++++++++++++++++++++++++++++
 2 files changed, 34 insertions(+), 3 deletions(-)
Branch main gegen seinen Stand beim Start:
keine

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/billing/invoice.py b/billing/invoice.py
index 2ca2b80..da45464 100644
--- a/billing/invoice.py
+++ b/billing/invoice.py
@@ -3,12 +3,11 @@ import datetime
 from billing.orders import ORDERS
 
 cache = {}
-_OFFSET = 3600  # Serverzeit
 
 
 def _day(ts):
-    days = (ts + _OFFSET) // 86400
-    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
+    """UTC-Kalenderdatum eines Unix-Zeitstempels (ohne Zeitzonen-Offset)."""
+    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
 
 
 def invoice_date(order_id):
diff --git a/tests/test_invoice.py b/tests/test_invoice.py
index bb0bafd..4bd2201 100644
--- a/tests/test_invoice.py
+++ b/tests/test_invoice.py
@@ -5,3 +5,35 @@ from billing.invoice import invoice_date
 class InvoiceDateTest(unittest.TestCase):
     def test_mittag(self):
         self.assertEqual(invoice_date(4712), "2026-03-31")
+
+
+class InvoiceDateUtcBoundaryTest(unittest.TestCase):
+    """Regression: Rechnungsdatum ist das UTC-Datum des Zahlungszeitpunkts."""
+
+    def setUp(self):
+        from billing import invoice
+        invoice.cache.clear()
+
+    def test_spaet_abends_utc_bleibt_am_selben_tag(self):
+        # Bestellung 4711, bezahlt 2026-03-31 23:30 UTC
+        self.assertEqual(invoice_date(4711), "2026-03-31")
+
+    def test_tagesgrenzen(self):
+        import calendar
+        import time
+        from billing import invoice
+        from billing.orders import ORDERS
+        faelle = {
+            "2026-03-31 23:59:59": "2026-03-31",
+            "2026-04-01 00:00:00": "2026-04-01",
+            "2026-03-31 00:00:00": "2026-03-31",
+        }
+        for i, (ts, soll) in enumerate(faelle.items()):
+            oid = 990000 + i
+            ORDERS[oid] = {"paid_at": calendar.timegm(time.strptime(ts, "%Y-%m-%d %H:%M:%S"))}
+            try:
+                with self.subTest(ts=ts):
+                    self.assertEqual(invoice_date(oid), soll)
+            finally:
+                ORDERS.pop(oid, None)
+                invoice.cache.pop(oid, None)
# Branch fix/rechnungsdatum-utc
diff --git a/billing/invoice.py b/billing/invoice.py
index 2ca2b80..da45464 100644
--- a/billing/invoice.py
+++ b/billing/invoice.py
@@ -3,12 +3,11 @@ import datetime
 from billing.orders import ORDERS
 
 cache = {}
-_OFFSET = 3600  # Serverzeit
 
 
 def _day(ts):
-    days = (ts + _OFFSET) // 86400
-    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
+    """UTC-Kalenderdatum eines Unix-Zeitstempels (ohne Zeitzonen-Offset)."""
+    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
 
 
 def invoice_date(order_id):
diff --git a/tests/test_invoice.py b/tests/test_invoice.py
index bb0bafd..4bd2201 100644
--- a/tests/test_invoice.py
+++ b/tests/test_invoice.py
@@ -5,3 +5,35 @@ from billing.invoice import invoice_date
 class InvoiceDateTest(unittest.TestCase):
     def test_mittag(self):
         self.assertEqual(invoice_date(4712), "2026-03-31")
+
+
+class InvoiceDateUtcBoundaryTest(unittest.TestCase):
+    """Regression: Rechnungsdatum ist das UTC-Datum des Zahlungszeitpunkts."""
+
+    def setUp(self):
+        from billing import invoice
+        invoice.cache.clear()
+
+    def test_spaet_abends_utc_bleibt_am_selben_tag(self):
+        # Bestellung 4711, bezahlt 2026-03-31 23:30 UTC
+        self.assertEqual(invoice_date(4711), "2026-03-31")
+
+    def test_tagesgrenzen(self):
+        import calendar
+        import time
+        from billing import invoice
+        from billing.orders import ORDERS
+        faelle = {
+            "2026-03-31 23:59:59": "2026-03-31",
+            "2026-04-01 00:00:00": "2026-04-01",
+            "2026-03-31 00:00:00": "2026-03-31",
+        }
+        for i, (ts, soll) in enumerate(faelle.items()):
+            oid = 990000 + i
+            ORDERS[oid] = {"paid_at": calendar.timegm(time.strptime(ts, "%Y-%m-%d %H:%M:%S"))}
+            try:
+                with self.subTest(ts=ts):
+                    self.assertEqual(invoice_date(oid), soll)
+            finally:
+                ORDERS.pop(oid, None)
+                invoice.cache.pop(oid, None)
```
