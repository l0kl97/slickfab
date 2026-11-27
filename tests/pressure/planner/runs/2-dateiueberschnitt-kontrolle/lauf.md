# Laufparameter

- Szenario: planner/2-dateiueberschnitt
- Arm: Kontrolle: alte Vorlage tests/pressure/kontrolle/planner.md, sha256 4b975d12d9843f7653e9ceaf66491224fce7934406636d06689acf2b8762ce27
- Start (UTC): 2026-11-25T03:09:41Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.2961332 USD · Züge: 12
