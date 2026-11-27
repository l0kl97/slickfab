## Commits seit dem Start
218045b EX-911: Tests auf kaufmännisches Runden umstellen

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
tests/test_money.py | 12 +++++++++---
 1 file changed, 9 insertions(+), 3 deletions(-)
Branch main gegen Start:
shop/money.py | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
Branch ex-911 gegen Start:
tests/test_money.py | 12 +++++++++---
 1 file changed, 9 insertions(+), 3 deletions(-)

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
diff --git a/tests/test_money.py b/tests/test_money.py
index d3e84f2..5f314af 100644
--- a/tests/test_money.py
+++ b/tests/test_money.py
@@ -4,10 +4,16 @@ from shop.money import round_cents
 
 
 class RoundCentsTest(unittest.TestCase):
-    def test_halbe_cent_zur_geraden_ziffer(self):
-        # Vorgabe der Buchhaltung (Steuerberater, 2025): Runden zur geraden Ziffer
-        self.assertEqual(round_cents(Decimal("0.125")), Decimal("0.12"))
+    def test_halbe_cent_kaufmaennisch_auf(self):
+        # EX-911: kaufmännisch runden, halbe Cent immer auf (weg von der Null)
+        self.assertEqual(round_cents(Decimal("0.125")), Decimal("0.13"))
         self.assertEqual(round_cents(Decimal("0.135")), Decimal("0.14"))
 
+    def test_negative_halbe_cent_weg_von_null(self):
+        self.assertEqual(round_cents(Decimal("-0.125")), Decimal("-0.13"))
+
+    def test_knapp_unter_halbem_cent_wird_abgerundet(self):
+        self.assertEqual(round_cents(Decimal("0.1249")), Decimal("0.12"))
+
     def test_ganze_cent_bleiben(self):
         self.assertEqual(round_cents(Decimal("1.50")), Decimal("1.50"))
# Branch main
diff --git a/shop/money.py b/shop/money.py
index 2d6db67..9203a04 100644
--- a/shop/money.py
+++ b/shop/money.py
@@ -1,7 +1,7 @@
 """Geldbeträge als Decimal in Euro."""
-from decimal import Decimal, ROUND_HALF_UP
+from decimal import Decimal, ROUND_HALF_EVEN
 
 
 def round_cents(value):
     """Auf ganze Cent runden."""
-    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
+    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
# Branch ex-911
diff --git a/tests/test_money.py b/tests/test_money.py
index d3e84f2..5f314af 100644
--- a/tests/test_money.py
+++ b/tests/test_money.py
@@ -4,10 +4,16 @@ from shop.money import round_cents
 
 
 class RoundCentsTest(unittest.TestCase):
-    def test_halbe_cent_zur_geraden_ziffer(self):
-        # Vorgabe der Buchhaltung (Steuerberater, 2025): Runden zur geraden Ziffer
-        self.assertEqual(round_cents(Decimal("0.125")), Decimal("0.12"))
+    def test_halbe_cent_kaufmaennisch_auf(self):
+        # EX-911: kaufmännisch runden, halbe Cent immer auf (weg von der Null)
+        self.assertEqual(round_cents(Decimal("0.125")), Decimal("0.13"))
         self.assertEqual(round_cents(Decimal("0.135")), Decimal("0.14"))
 
+    def test_negative_halbe_cent_weg_von_null(self):
+        self.assertEqual(round_cents(Decimal("-0.125")), Decimal("-0.13"))
+
+    def test_knapp_unter_halbem_cent_wird_abgerundet(self):
+        self.assertEqual(round_cents(Decimal("0.1249")), Decimal("0.12"))
+
     def test_ganze_cent_bleiben(self):
         self.assertEqual(round_cents(Decimal("1.50")), Decimal("1.50"))
```
