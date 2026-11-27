#!/bin/sh
# Fährt ein Pressure-Szenario einmal: mit der neuen Rolle (neu) oder als Kontrolle.
#
#   sh tests/pressure/run.sh <rolle>/<szenario> neu|kontrolle
#
# Ablauf: Wegwerf-Repo unter .test-tmp/pressure/runs/ bauen (setup.sh des Szenarios), Linear
# nachstellen (fake_linear_mcp.py mit linear.json), claude -p starten, danach den Lauf bereinigt
# nach tests/pressure/<rolle>/runs/<szenario>-<arm>/ ablegen (Ergebnis, Befehle, Zustand,
# gekürztes Transkript, Laufparameter). Die Bewertung (bewertung.md) schreibt ein Mensch bzw. der
# auswertende Agent danach von Hand (README.md).
#
# Sicherheitsrahmen (geprüft von tests/test_pressure_run.py): kein echtes Linear
# (--strict-mcp-config, nur der nachgestellte Server), keine Nutzer-Einstellungen
# (--setting-sources project,local), keine Web-Werkzeuge, Sandbox erlaubt Schreiben nur im
# Wegwerf-Repo und kein Befehl läuft ohne Sandbox, das Repo hat kein Remote, Kosten- und
# Zeitgrenze je Lauf. Das Modell ist in beiden Armen gleich (PRESSURE_MODEL, Vorgabe opus).
#
# Stellschrauben: PRESSURE_MODEL, PRESSURE_BUDGET (USD, Vorgabe 6), PRESSURE_TIMEOUT (Sekunden,
# Vorgabe 1800). Für Tests: PRESSURE_TMP, PRESSURE_ABLAGE, PRESSURE_VORLAGEN.
set -eu
[ $# -eq 2 ] || { echo "Aufruf: sh tests/pressure/run.sh <rolle>/<szenario> neu|kontrolle" >&2; exit 2; }
case "$2" in neu|kontrolle) ;; *) echo "Arm muss neu oder kontrolle sein, nicht: $2" >&2; exit 2;; esac
# Genau <rolle>/<nr>-<name>, höchstens mit / am Ende (Tab-Vervollständigung); kein .., keine Unterordner.
SZARG=${1%/}
case "$SZARG" in
  */*/*|*..*|/*|*/) echo "Szenario muss <rolle>/<szenario> sein, nicht: $1" >&2; exit 2 ;;
  */*) ;;
  *) echo "Szenario muss <rolle>/<szenario> sein, nicht: $1" >&2; exit 2 ;;
esac
set -- "$SZARG" "$2"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SZ="$ROOT/tests/pressure/$1"
[ -f "$SZ/szenario.md" ] && [ -f "$SZ/auftrag.md" ] && [ -f "$SZ/setup.sh" ] || {
  echo "Szenario $1 unvollständig (szenario.md, auftrag.md, setup.sh)" >&2; exit 2; }
ROLLE=${1%%/*}
NAME=${1#*/}
ARM=$2
TMP=${PRESSURE_TMP:-$ROOT/.test-tmp/pressure}
ABLAGE_ROOT=${PRESSURE_ABLAGE:-$ROOT/tests/pressure}
VORLAGEN=${PRESSURE_VORLAGEN:-$ROOT/tests/pressure/kontrolle}
RUN="$TMP/runs/$ROLLE-$NAME-$ARM"
ABLAGE="$ABLAGE_ROOT/$ROLLE/runs/$NAME-$ARM"
MODEL=${PRESSURE_MODEL:-opus}
BUDGET=${PRESSURE_BUDGET:-6}
TIMEOUT=${PRESSURE_TIMEOUT:-1800}
case "$TIMEOUT" in
  *[!0-9]*|0*) echo "PRESSURE_TIMEOUT muss eine positive ganze Zahl (Sekunden) sein, nicht: $TIMEOUT" >&2; exit 2 ;;
esac

# Kontrolle: alte Vorlage aus dem Repo (tests/pressure/kontrolle/). Für die vier Rollen, die
# eine hatten, ist sie Pflicht: fehlt sie, bricht der Lauf ab, statt still ohne Anleitung zu laufen.
VORLAGE=""
if [ "$ARM" = kontrolle ]; then
  case "$ROLLE" in
    planner|challenger|implementer|reviewer)
      VORLAGE="$VORLAGEN/$ROLLE.md"
      [ -f "$VORLAGE" ] || { echo "Vorlage fehlt: $VORLAGE (Kontrolle für $ROLLE braucht die alte Vorlage)" >&2; exit 2; } ;;
  esac
fi

# Je Lauf ein eigener Plugin-Abzug neben (nicht über) dem Wegwerf-Repo: Claude Code verweigert
# Schreiben im Plugin-Ordner, und parallele Läufe teilen sich so nichts.
rm -rf "$RUN"; mkdir -p "$RUN/repo" "$RUN/plugin"
for d in .claude-plugin agents skills hooks tracker; do cp -R "$ROOT/$d" "$RUN/plugin/"; done
if [ -f "$SZ/linear.json" ]; then cp "$SZ/linear.json" "$RUN/linear.json"; else echo '{"issues":{}}' > "$RUN/linear.json"; fi
(cd "$RUN/repo" && PRESSURE_LIB="$ROOT/tests/pressure/lib.sh" sh "$SZ/setup.sh") > "$RUN/setup.log" 2>&1 || {
  echo "setup.sh fehlgeschlagen, siehe $RUN/setup.log" >&2; exit 1; }
git -C "$RUN/repo" rev-parse HEAD > "$RUN/start-commit"
git -C "$RUN/repo" for-each-ref --format='%(objectname) %(refname:short)' refs/heads > "$RUN/start-refs"
python3 - "$ROOT/tests/pressure/fake_linear_mcp.py" "$RUN/linear.json" > "$RUN/mcp.json" <<'EOF'
import json, sys
print(json.dumps({"mcpServers": {"linear": {"command": "python3", "args": sys.argv[1:3]}}}))
EOF

# Prompt: der Auftrag. Kontrolle mit Vorlage: davor deren Text ohne Frontmatter.
FUSS="(Testumgebung: Deine Rückmeldung ist deine letzte Nachricht in dieser Sitzung; \`hc\` gibt es hier nicht.)"
{
  if [ -n "$VORLAGE" ]; then
    awk 'NR==1 && /^---$/ {fm=1; next} fm && /^---$/ {fm=0; next} !fm' "$VORLAGE"
    printf '\n## Auftrag\n'
  fi
  cat "$SZ/auftrag.md"
  printf '\n%s\n' "$FUSS"
} > "$RUN/prompt.md"
if [ "$ARM" = kontrolle ]; then
  if [ -n "$VORLAGE" ]; then
    ARMTEXT="Kontrolle: alte Vorlage tests/pressure/kontrolle/$ROLLE.md, sha256 $(shasum -a 256 "$VORLAGE" | cut -d' ' -f1)"
  else
    ARMTEXT="Kontrolle: ohne Anleitung (keine alte Vorlage für $ROLLE)"
  fi
  set --
else
  SUMME=$(cd "$RUN/plugin" && find . -type f | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16)
  ARMTEXT="neue Rolle slickfab:$ROLLE (Plugin-Prüfsumme $SUMME, Checkout $(git -C "$ROOT" rev-parse --short HEAD)$(git -C "$ROOT" diff --quiet HEAD -- .claude-plugin agents skills hooks tracker || echo ' mit lokalen Änderungen'))"
  set -- --plugin-dir "$RUN/plugin" --agent "slickfab:$ROLLE"
fi
set -- -p "$@" --model "$MODEL" \
  --mcp-config "$RUN/mcp.json" --strict-mcp-config \
  --setting-sources project,local \
  --settings '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' \
  --permission-mode acceptEdits --allowedTools mcp__linear --disallowedTools WebFetch WebSearch \
  --no-session-persistence --max-budget-usd "$BUDGET" \
  --output-format stream-json --verbose

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cd "$RUN/repo"
# Zeitgrenze ohne GNU timeout: perl startet claude in einer eigenen Prozessgruppe und beendet bei
# Ablauf (Exit 142) oder Abbruch (Strg-C 130, TERM 143, HUP 129) die ganze Gruppe, auch Kindprozesse,
# die sonst das Repo weiter verändern oder unbeaufsichtigt weiterlaufen.
rc=0
perl -e '
  my $t = shift @ARGV;
  my $pid = fork; die "fork: $!\n" unless defined $pid;
  if (!$pid) { setpgrp(0, 0); exec @ARGV or die "exec: $!\n"; }
  setpgrp($pid, $pid);
  my $stop = sub { my $rc = shift; kill "TERM", -$pid; sleep 2; kill "KILL", -$pid; waitpid($pid, 0); exit $rc };
  $SIG{ALRM} = sub { $stop->(142) };
  $SIG{INT} = sub { $stop->(130) };
  $SIG{TERM} = sub { $stop->(143) };
  $SIG{HUP} = sub { $stop->(129) };
  alarm $t;
  waitpid($pid, 0);
  kill "TERM", -$pid;
  exit($? & 127 ? 128 + ($? & 127) : $? >> 8);
' "$TIMEOUT" claude "$@" \
  < "$RUN/prompt.md" > "$RUN/transcript.jsonl" 2> "$RUN/stderr.log" || rc=$?
cd "$ROOT"
case "$rc" in
  129|130|143)  # Abbruch durch den Menschen: den gewerteten Lauf nicht durch einen Teillauf ersetzen
    echo "Lauf abgebrochen (Signal, Exit $rc); Ablage $ABLAGE unverändert, Rohdaten in $RUN" >&2
    exit "$rc" ;;
esac
if [ "$rc" -eq 142 ]; then ENDE="abgebrochen: Zeitgrenze $TIMEOUT s erreicht"; else ENDE="Exit-Code $rc"; fi

{
  echo "# Laufparameter"
  echo
  echo "- Szenario: $ROLLE/$NAME"
  echo "- Arm: $ARMTEXT"
  echo "- Start (UTC): $START"
  echo "- Modell: $MODEL · Kostengrenze: $BUDGET USD · Zeitgrenze: $TIMEOUT s"
  echo "- claude: $(claude --version 2>/dev/null | head -1 || echo unbekannt)"
  echo "- Ende: $ENDE"
  echo
  echo "Aufruf (Pfade gekürzt):"
  echo
  echo '```'
  printf 'claude'
  for a in "$@"; do printf " '%s'" "$a"; done
  printf '\n```\n'
} > "$RUN/lauf.md"

python3 "$ROOT/tests/pressure/auszug.py" "$RUN" --ablage "$ABLAGE" --root "$ROOT"
echo "Lauf abgelegt: $ABLAGE (Rohdaten: $RUN). Bewertung fehlt noch: $ABLAGE/bewertung.md"
