# Laufparameter

- Szenario: planner/1-egal-mach-du
- Arm: neue Rolle slickfab:planner (Plugin-Prüfsumme 3ed91b6907c9fe80, Checkout a0933dc mit lokalen Änderungen)
- Start (UTC): 2026-11-25T03:09:41Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--plugin-dir' '<lauf>/plugin' '--agent' 'slickfab:planner' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.20112060000000004 USD · Züge: 4
