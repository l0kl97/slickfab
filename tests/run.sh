#!/bin/sh
# Prüfungen für slickfab. Findet Schritte, Rollen und Testdateien selbst:
# neue Dateien werden mitgeprüft, ohne dieses Skript zu ändern.
#
#   sh tests/run.sh          volle Suite (Standard, Pflicht in CI)
#   sh tests/run.sh --fast   ohne die langsamsten Module, nennt am Ende, was fehlt
set -eu
cd "$(dirname "$0")/.."
fast=""
for arg in "$@"; do
  case "$arg" in
    --fast) fast="--fast" ;;
    *) echo "run.sh: unknown option $arg (usage: sh tests/run.sh [--fast])" >&2; exit 2 ;;
  esac
done
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
# 4. Python-Unittests: jede tests/test_*.py, mit Lebenszeichen (tests/runner.py)
if ls tests/test_*.py >/dev/null 2>&1; then python3 tests/runner.py $fast || fail=1; fi
[ $fail -eq 0 ] && echo "slickfab tests${fast:+ ($fast)}: ok"
exit $fail
