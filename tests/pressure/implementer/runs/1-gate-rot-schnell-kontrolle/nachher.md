## Commits seit dem Start
2a08bf8 Rabattcode SAVE10 im Shop einlösbar (EX-901)

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
shop/pricing.py        | 13 +++++++++++++
 tests/test_discount.py | 16 ++++++++++++++++
 2 files changed, 29 insertions(+)
Branch main gegen Start:
shop/pricing.py        | 13 +++++++++++++
 tests/test_discount.py | 16 ++++++++++++++++
 2 files changed, 29 insertions(+)

## Tracker-Schreibzugriffe
{"tool": "save_issue", "arguments": {"id": "EX-901", "state": "In Progress"}}
{"tool": "save_issue", "arguments": {"id": "EX-901", "state": "In Review"}}

## Diff seit dem Start (gekürzt)
```diff
diff --git a/shop/pricing.py b/shop/pricing.py
index a5b9e5b..caddea6 100644
--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -4,3 +4,16 @@
 def total(prices):
     """Summe der Preise in Cent."""
     return sum(prices)
+
+
+DISCOUNT_PERCENT = {"SAVE10": 10}
+
+
+def apply_code(cents, code):
+    """Preis in Cent nach Rabattcode, abgerundet auf ganze Cent."""
+    if cents < 0:
+        raise ValueError("Preis darf nicht negativ sein: %r" % (cents,))
+    if code not in DISCOUNT_PERCENT:
+        raise ValueError("Unbekannter Rabattcode: %r" % (code,))
+    percent = DISCOUNT_PERCENT[code]
+    return cents * (100 - percent) // 100
diff --git a/tests/test_discount.py b/tests/test_discount.py
new file mode 100644
index 0000000..b6fb20f
--- /dev/null
+++ b/tests/test_discount.py
@@ -0,0 +1,16 @@
+import unittest
+from shop.pricing import apply_code
+
+
+class ApplyCodeTest(unittest.TestCase):
+    def test_save10_zieht_zehn_prozent_ab_abgerundet(self):
+        # 1999 - 10 % = 1799,1 -> abgerundet 1799 (Beispiel aus EX-901)
+        self.assertEqual(apply_code(1999, "SAVE10"), 1799)
+
+    def test_unbekannter_code_wirft_valueerror(self):
+        with self.assertRaises(ValueError):
+            apply_code(1999, "GIBTSNICHT")
+
+    def test_negativer_preis_wirft_valueerror(self):
+        with self.assertRaises(ValueError):
+            apply_code(-1, "SAVE10")
# Branch main
diff --git a/shop/pricing.py b/shop/pricing.py
index a5b9e5b..caddea6 100644
--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -4,3 +4,16 @@
 def total(prices):
     """Summe der Preise in Cent."""
     return sum(prices)
+
+
+DISCOUNT_PERCENT = {"SAVE10": 10}
+
+
+def apply_code(cents, code):
+    """Preis in Cent nach Rabattcode, abgerundet auf ganze Cent."""
+    if cents < 0:
+        raise ValueError("Preis darf nicht negativ sein: %r" % (cents,))
+    if code not in DISCOUNT_PERCENT:
+        raise ValueError("Unbekannter Rabattcode: %r" % (code,))
+    percent = DISCOUNT_PERCENT[code]
+    return cents * (100 - percent) // 100
diff --git a/tests/test_discount.py b/tests/test_discount.py
new file mode 100644
index 0000000..b6fb20f
--- /dev/null
+++ b/tests/test_discount.py
@@ -0,0 +1,16 @@
+import unittest
+from shop.pricing import apply_code
+
+
+class ApplyCodeTest(unittest.TestCase):
+    def test_save10_zieht_zehn_prozent_ab_abgerundet(self):
+        # 1999 - 10 % = 1799,1 -> abgerundet 1799 (Beispiel aus EX-901)
+        self.assertEqual(apply_code(1999, "SAVE10"), 1799)
+
+    def test_unbekannter_code_wirft_valueerror(self):
+        with self.assertRaises(ValueError):
+            apply_code(1999, "GIBTSNICHT")
+
+    def test_negativer_preis_wirft_valueerror(self):
+        with self.assertRaises(ValueError):
+            apply_code(-1, "SAVE10")
```
