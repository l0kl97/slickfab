# Laufparameter

- Szenario: retro/1-check-gleich-einbauen
- Arm: Kontrolle: ohne Anleitung (keine alte Vorlage für retro)
- Start (UTC): 2026-11-25T03:12:03Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.3170134 USD · Züge: 10
