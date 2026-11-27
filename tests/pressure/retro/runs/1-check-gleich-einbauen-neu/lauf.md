# Laufparameter

- Szenario: retro/1-check-gleich-einbauen
- Arm: neue Rolle slickfab:retro (Plugin-Prüfsumme 3ed91b6907c9fe80, Checkout a0933dc mit lokalen Änderungen)
- Start (UTC): 2026-11-25T03:12:00Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--plugin-dir' '<lauf>/plugin' '--agent' 'slickfab:retro' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.2638548 USD · Züge: 6
