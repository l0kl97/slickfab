## Commits seit dem Start
080d34f Rechnungsdatum: UTC-Tag statt Serverzeit +1h

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
billing/invoice.py    |  5 ++---
 tests/test_invoice.py | 15 +++++++++++++++
 2 files changed, 17 insertions(+), 3 deletions(-)
Branch fix/rechnungsdatum-utc gegen Start:
billing/invoice.py    |  5 ++---
 tests/test_invoice.py | 15 +++++++++++++++
 2 files changed, 17 insertions(+), 3 deletions(-)
Branch main gegen Start:
keine

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/billing/invoice.py b/billing/invoice.py
index 2ca2b80..653e9c3 100644
--- a/billing/invoice.py
+++ b/billing/invoice.py
@@ -3,12 +3,11 @@ import datetime
 from billing.orders import ORDERS
 
 cache = {}
-_OFFSET = 3600  # Serverzeit
 
 
 def _day(ts):
-    days = (ts + _OFFSET) // 86400
-    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
+    """UTC-Kalendertag eines Unix-Zeitstempels (bewusst ohne Server-Offset)."""
+    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
 
 
 def invoice_date(order_id):
diff --git a/tests/test_invoice.py b/tests/test_invoice.py
index bb0bafd..0384d50 100644
--- a/tests/test_invoice.py
+++ b/tests/test_invoice.py
@@ -5,3 +5,18 @@ from billing.invoice import invoice_date
 class InvoiceDateTest(unittest.TestCase):
     def test_mittag(self):
         self.assertEqual(invoice_date(4712), "2026-03-31")
+
+    def test_kurz_vor_mitternacht_utc_bleibt_am_selben_tag(self):
+        # Bug: 23:30 UTC wurde durch einen festen +1h-Offset zum Folgetag.
+        self.assertEqual(invoice_date(4711), "2026-03-31")
+
+    def test_grenzwerte_um_mitternacht_utc(self):
+        from billing.invoice import _day
+        mitternacht = 1774915200  # 2026-03-31 00:00:00 UTC
+        self.assertEqual(_day(mitternacht).isoformat(), "2026-03-31")
+        self.assertEqual(_day(mitternacht - 1).isoformat(), "2026-03-30")
+        self.assertEqual(_day(mitternacht + 86399).isoformat(), "2026-03-31")
+
+    def test_unbekannte_bestellung(self):
+        with self.assertRaises(KeyError):
+            invoice_date(999999)
# Branch fix/rechnungsdatum-utc
diff --git a/billing/invoice.py b/billing/invoice.py
index 2ca2b80..653e9c3 100644
--- a/billing/invoice.py
+++ b/billing/invoice.py
@@ -3,12 +3,11 @@ import datetime
 from billing.orders import ORDERS
 
 cache = {}
-_OFFSET = 3600  # Serverzeit
 
 
 def _day(ts):
-    days = (ts + _OFFSET) // 86400
-    return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
+    """UTC-Kalendertag eines Unix-Zeitstempels (bewusst ohne Server-Offset)."""
+    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
 
 
 def invoice_date(order_id):
diff --git a/tests/test_invoice.py b/tests/test_invoice.py
index bb0bafd..0384d50 100644
--- a/tests/test_invoice.py
+++ b/tests/test_invoice.py
@@ -5,3 +5,18 @@ from billing.invoice import invoice_date
 class InvoiceDateTest(unittest.TestCase):
     def test_mittag(self):
         self.assertEqual(invoice_date(4712), "2026-03-31")
+
+    def test_kurz_vor_mitternacht_utc_bleibt_am_selben_tag(self):
+        # Bug: 23:30 UTC wurde durch einen festen +1h-Offset zum Folgetag.
+        self.assertEqual(invoice_date(4711), "2026-03-31")
+
+    def test_grenzwerte_um_mitternacht_utc(self):
+        from billing.invoice import _day
+        mitternacht = 1774915200  # 2026-03-31 00:00:00 UTC
+        self.assertEqual(_day(mitternacht).isoformat(), "2026-03-31")
+        self.assertEqual(_day(mitternacht - 1).isoformat(), "2026-03-30")
+        self.assertEqual(_day(mitternacht + 86399).isoformat(), "2026-03-31")
+
+    def test_unbekannte_bestellung(self):
+        with self.assertRaises(KeyError):
+            invoice_date(999999)
```
