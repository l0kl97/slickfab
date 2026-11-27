#!/bin/sh
# Prüfungen für slickfab. Findet Schritte, Rollen und Testdateien selbst:
# neue Dateien werden mitgeprüft, ohne dieses Skript zu ändern.
set -eu
cd "$(dirname "$0")/.."
fail=0
# 1. Struktur: Manifeste, Schritte (skills/*/SKILL.md), Rollen (agents/*.md)
python3 tests/check_structure.py . || fail=1
# 2. Shell-Skripte sind syntaktisch korrekt
for f in $(find runtime hooks tests -name '*.sh' 2>/dev/null); do sh -n "$f" || { echo "FAIL $f: Syntax"; fail=1; }; done
# 3. Shell-Tests: jede tests/test_*.sh läuft, Exit != 0 ist rot
for f in tests/test_*.sh; do
  [ -f "$f" ] || continue
  sh "$f" || { echo "FAIL $f"; fail=1; }
done
# 4. Python-Unittests: jede tests/test_*.py
if ls tests/test_*.py >/dev/null 2>&1; then python3 -m unittest discover -s tests -q || fail=1; fi
[ $fail -eq 0 ] && echo "slickfab tests: ok"
exit $fail
