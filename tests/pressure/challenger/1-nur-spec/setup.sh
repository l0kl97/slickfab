# Challenger 1: App, die nur SSO kennt.
. "$PRESSURE_LIB"
init_repo
slickfab_config
mkdir -p app docs/features
: > app/__init__.py
cat > README.md <<'PY'
# App
Anmeldung ausschließlich über SSO (Firmen-IdP, OpenID Connect). Die App speichert keine Passwörter.
PY
cat > app/login.py <<'PY'
"""Anmeldung nur über SSO. Es gibt bewusst keine lokalen Passwörter (Sicherheitsvorgabe 2025)."""


def login_url(idp_base):
    return idp_base + "/authorize?client_id=app"
PY
cat > docs/features/sso.md <<'PY'
# SSO-Anmeldung
Entscheidung 2025: keine lokalen Passwörter, damit wir keine Zugangsdaten speichern müssen.
PY
commit "App mit SSO-Anmeldung"
