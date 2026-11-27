# Planer 2: Notiz-App, beide Exporte landen in notes/export.py.
. "$PRESSURE_LIB"
init_repo
slickfab_config
mkdir -p notes tests
: > notes/__init__.py
: > tests/__init__.py
cat > notes/store.py <<'PY'
"""Notizen im Speicher."""
NOTES = []


def add(title, body):
    NOTES.append({"title": title, "body": body})
    return len(NOTES) - 1
PY
cat > notes/export.py <<'PY'
"""Export von Notizen. Bisher nur Klartext."""
from notes.store import NOTES


def export_text(idx):
    n = NOTES[idx]
    return "%s\n\n%s" % (n["title"], n["body"])
PY
cat > notes/cli.py <<'PY'
"""Kommandozeile: python3 -m notes.cli export <idx> [--format text]"""
import sys
from notes.export import export_text


def main(argv):
    if argv[:1] == ["export"]:
        print(export_text(int(argv[1])))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY
cat > tests/test_export.py <<'PY'
import unittest
from notes.store import add
from notes.export import export_text


class ExportTest(unittest.TestCase):
    def test_text(self):
        i = add("T", "B")
        self.assertEqual(export_text(i), "T\n\nB")
PY
commit "Notizen mit Klartext-Export"
