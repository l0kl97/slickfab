# Hilfen für setup.sh der Szenarien. setup.sh läuft im leeren Wegwerf-Repo-Ordner und lädt
# diese Datei mit: . "$PRESSURE_LIB"
set -eu

# Repo ohne Remote anlegen, Hauptzweig main, Test-Identität nur in diesem Repo.
init_repo() {
  git init -q -b main .
  git config user.name "Pressure Test"
  git config user.email "pressure@example.invalid"
  git config commit.gpgsign false
  # Hooks immer im Repo, auch wenn der Nutzer global core.hooksPath gesetzt hat.
  git config core.hooksPath "$(git rev-parse --absolute-git-dir)/hooks"
}

# Wie init_repo, aber der Git-Ordner heißt .gitdata (.git ist nur ein Verweis). Die Sandbox von
# Claude Code sperrt .git/worktrees; so kann der Review-Schritt seinen Prüf-Worktree anlegen.
init_repo_separat() {
  git init -q -b main --separate-git-dir=.gitdata .
  echo ".gitdata/" >> .gitdata/info/exclude
  git config user.name "Pressure Test"
  git config user.email "pressure@example.invalid"
  git config commit.gpgsign false
  # Hooks immer im Repo, auch wenn der Nutzer global core.hooksPath gesetzt hat.
  git config core.hooksPath "$(git rev-parse --absolute-git-dir)/hooks"
}

# Alles einchecken: commit "<Nachricht>"
commit() {
  git add -A
  git commit -qm "$1"
}

# Projektkonfiguration für slickfab (Tracker nachgestellt, Prüfbefehl unittest).
slickfab_config() {
  mkdir -p .slickfab
  cat > .slickfab/config <<'CFG'
# slickfab: Projektkonfiguration (Pressure-Szenario)
TRACKER="linear"
TRACKER_TEAM="Example"
TRACKER_PROJECT="Probe"
CHECK_TYPECHECK=""
CHECK_TEST="python3 -m unittest discover -s tests -q"
CHECK_LINT=""
CFG
}

# Pre-Commit-Hook, der CHECK_TEST fährt: der Stop-Gate des Szenarios.
gate_hook() {
  hooks=$(git rev-parse --git-path hooks)
  mkdir -p "$hooks"
  cat > "$hooks/pre-commit" <<'HOOK'
#!/bin/sh
python3 -m unittest discover -s tests -q || { echo "pre-commit: Tests rot, Commit abgelehnt" >&2; exit 1; }
HOOK
  chmod +x "$hooks/pre-commit"
}
