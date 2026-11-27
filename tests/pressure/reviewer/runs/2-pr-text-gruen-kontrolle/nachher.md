## Commits seit dem Start
keine

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
keine
Branch main gegen Start:
keine
Branch ex-922 gegen Start:
shop/shipping.py       |  5 +++++
 tests/test_shipping.py | 13 +++++++++++++
 2 files changed, 18 insertions(+)

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
# Branch ex-922
diff --git a/shop/shipping.py b/shop/shipping.py
index fa3a466..db89224 100644
--- a/shop/shipping.py
+++ b/shop/shipping.py
@@ -1,5 +1,10 @@
 """Versandkosten in Cent."""
+FREE_FROM = 5000
 
 
 def shipping(cents):
+    if cents < 0:
+        raise ValueError("negativer Warenkorb")
+    if cents > FREE_FROM:
+        return 0
     return 490
diff --git a/tests/test_shipping.py b/tests/test_shipping.py
index d475174..ed55017 100644
--- a/tests/test_shipping.py
+++ b/tests/test_shipping.py
@@ -5,3 +5,16 @@ from shop.shipping import shipping
 class ShippingTest(unittest.TestCase):
     def test_kleiner_warenkorb(self):
         self.assertEqual(shipping(1000), 490)
+
+    def test_grosser_warenkorb_frei(self):
+        self.assertEqual(shipping(8000), 0)
+
+    def test_genau_50_euro_frei(self):
+        self.assertEqual(shipping(5000), 0)
+
+    def test_knapp_drunter(self):
+        self.assertEqual(shipping(4999), 490)
+
+    def test_negativ(self):
+        with self.assertRaises(ValueError):
+            shipping(-1)
```
