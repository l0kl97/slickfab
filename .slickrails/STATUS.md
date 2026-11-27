# Guardrails-Status

Stand: 2026-11-24 (von install.sh erzeugt; bei jeder Aenderung nachfuehren — Regel 10)

| # | Regel | Status | Notiz |
|---|---|---|---|
| 1 | Repro-Test vor Bugfix | ☐ | Arbeitsregel — gilt ab sofort |
| 2 | Browser-Smoke-Tests fuer kritische Flows | ☐ | Flows auflisten + Playwright-Tests anlegen |
| 3 | pre-push: Typecheck + Tests | ☑ | |
| 4 | Secrets-Scan (pre-commit + CI) | ☑ | gitleaks lokal installieren: `brew install gitleaks` |
| 5 | Branch Protection auf main | ☐ | `slickrails protect` (braucht gh) |
| 6 | AI-Review vor dem Merge | ☑ | Lokal vor jedem Push mit deinem claude- oder codex-CLI (`CHECK_PREPUSH_REVIEW="1"`); zusätzlich serverseitig auf GitHub: `slickrails github-review` |
| 7 | Dependabot + Audit im CI | ☑ | |
| 8 | Definition of Done gelebt | ☐ | Arbeitsregel |
| 9 | Standard-Test-Stack (generic) | ☐ | pruefen/migrieren |
| 10 | Dieses Dokument aktuell halten | ☑ | |
| 11 | Feature-Dossiers + Commit-Bodies (Kontext bleibt) | ☑ | Bestehende Kern-Features nach und nach nachdokumentieren |
| 12 | PR-Groessen-Limit (pr-size.yml) | ☑ | Label `size-ok` fuer bewusste Ausnahmen anlegen |

## Offene Luecken (mit Datum)

- 2026-11-24: Initial-Install — offene Punkte siehe Tabelle.
