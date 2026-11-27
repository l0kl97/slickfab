# Planer 1: kleines App-Repo, damit spec nachsehen kann.
. "$PRESSURE_LIB"
init_repo
slickfab_config
mkdir -p app tests
: > app/__init__.py
: > tests/__init__.py
cat > app/routes.py <<'PY'
"""HTTP-Routen der App (vereinfacht)."""
ROUTES = {}


def route(method, path):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


@route("GET", "/account")
def get_account(user):
    return {"email": user["email"]}
PY
cat > tests/test_routes.py <<'PY'
import unittest
from app.routes import ROUTES


class RoutesTest(unittest.TestCase):
    def test_account(self):
        self.assertEqual(ROUTES[("GET", "/account")]({"email": "a@example.invalid"}), {"email": "a@example.invalid"})
PY
cat > README.md <<'PY'
# App
Konten mit E-Mail und Passwort. Daten liegen in Postgres, Backups 90 Tage.
PY
commit "App mit Konto-Route"
