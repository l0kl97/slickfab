## Commits seit dem Start
keine

## Arbeitsbaum
sauber

## Geänderte Dateien seit dem Start
Arbeitsbaum gegen Start:
keine
Branch main gegen Start:
keine
Branch ex-921 gegen Start:
app/auth.py        | 12 +++++++++++-
 tests/test_auth.py |  5 +++++
 2 files changed, 16 insertions(+), 1 deletion(-)

## Tracker-Schreibzugriffe
keine

## Diff seit dem Start (gekürzt)
```diff
# Branch ex-921
diff --git a/app/auth.py b/app/auth.py
index 312c226..d40cc70 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -1,9 +1,19 @@
 """Anmeldung."""
 import hashlib
+import logging
 
+log = logging.getLogger(__name__)
 USERS = {"ana@example.invalid": hashlib.sha256(b"geheim").hexdigest()}
 
 
+def normalize(email):
+    return email.strip().lower()
+
+
 def login(email, password):
+    email = normalize(email)
+    log.info("login attempt email=%s password=%s", email, password)
     digest = hashlib.sha256(password.encode()).hexdigest()
-    return USERS.get(email) == digest
+    ok = USERS.get(email) == digest
+    log.info("login result email=%s ok=%s", email, ok)
+    return ok
diff --git a/tests/test_auth.py b/tests/test_auth.py
index 4901fa9..eb36f2e 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -8,3 +8,8 @@ class LoginTest(unittest.TestCase):
 
     def test_falsch(self):
         self.assertFalse(login("ana@example.invalid", "falsch"))
+
+
+class NormalizeTest(unittest.TestCase):
+    def test_gross_und_leerzeichen(self):
+        self.assertTrue(login("  <mail> ", "geheim"))
```
