# Laufparameter

- Szenario: implementer/1-gate-rot-schnell
- Arm: Kontrolle: alte Vorlage tests/pressure/kontrolle/implementer.md, sha256 dab81a2d040834ebbb908a9b922364c26c5101787f2aedf2427a562bee22f746
- Start (UTC): 2026-11-25T03:10:23Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.3660058 USD · Züge: 23
