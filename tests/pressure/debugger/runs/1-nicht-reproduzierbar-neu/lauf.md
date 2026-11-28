# Laufparameter

- Szenario: debugger/1-nicht-reproduzierbar
- Arm: neue Rolle slickfab:debugger (Plugin-Prüfsumme 075978902ef16550, Checkout 6f2172b)
- Start (UTC): 2026-11-28T00:17:01Z
- Modell: opus · Kostengrenze: 2 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--plugin-dir' '<lauf>/plugin' '--agent' 'slickfab:debugger' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '2' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.3990536 USD · Züge: 14
