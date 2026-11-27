## Commits seit dem Start
keine

## Arbeitsbaum
M  billing/invoice.py
M  tests/test_invoice.py

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
billing/invoice.py    | 4 ++--
 tests/test_invoice.py | 5 +++++
 2 files changed, 7 insertions(+), 2 deletions(-)
Branch fix/rechnungsdatum-utc gegen Start:
keine
Branch main gegen Start:
keine

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/billing/invoice.py b/billing/invoice.py
index 2ca2b80..fcde91d 100644
--- a/billing/invoice.py
+++ b/billing/invoice.py
@@ -3,11 +3,11 @@ import datetime
 from billing.orders import ORDERS
 
 cache = {}
-_OFFSET = 3600  # Serverzeit
 
 
 def _day(ts):
-    days = (ts + _OFFSET) // 86400
+    # Rechnungsdatum = UTC-Tag des Zahlungszeitpunkts; keine Serverzeit-Verschiebung.
+    days = ts // 86400
     return datetime.date(1970, 1, 1) + datetime.timedelta(days=days)
 
 
diff --git a/tests/test_invoice.py b/tests/test_invoice.py
index bb0bafd..ac15472 100644
--- a/tests/test_invoice.py
+++ b/tests/test_invoice.py
@@ -5,3 +5,8 @@ from billing.invoice import invoice_date
 class InvoiceDateTest(unittest.TestCase):
     def test_mittag(self):
         self.assertEqual(invoice_date(4712), "2026-03-31")
+
+    def test_kurz_vor_mitternacht_utc(self):
+        # Bestellung 4711: bezahlt 2026-03-31 23:30 UTC -> Rechnung am UTC-Tag,
+        # nicht am Tag in Serverzeit (UTC+1 ergab faelschlich 2026-04-01).
+        self.assertEqual(invoice_date(4711), "2026-03-31")
```
