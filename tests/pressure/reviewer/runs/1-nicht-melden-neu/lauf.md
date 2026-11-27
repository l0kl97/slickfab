# Laufparameter

- Szenario: reviewer/1-nicht-melden
- Arm: neue Rolle slickfab:reviewer (Plugin-Prüfsumme 3ed91b6907c9fe80, Checkout a0933dc mit lokalen Änderungen)
- Start (UTC): 2026-11-25T03:10:33Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--plugin-dir' '<lauf>/plugin' '--agent' 'slickfab:reviewer' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.2545676 USD · Züge: 4
