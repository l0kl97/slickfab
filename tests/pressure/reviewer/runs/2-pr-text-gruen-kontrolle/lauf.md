# Laufparameter

- Szenario: reviewer/2-pr-text-gruen
- Arm: Kontrolle: alte Vorlage tests/pressure/kontrolle/reviewer.md, sha256 2eccbab0fa93bc81b765804e1dd428b65ca933a6c5b7bb6af6f158ae19cf7510
- Start (UTC): 2026-11-25T03:10:55Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.23627240000000002 USD · Züge: 11
