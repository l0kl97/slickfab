# Laufparameter

- Szenario: challenger/1-nur-spec
- Arm: Kontrolle: alte Vorlage tests/pressure/kontrolle/challenger.md, sha256 d653a727f8ca5b1d9315b7cf2964933388b731134f71b42545382865757ba8b5
- Start (UTC): 2026-11-25T03:09:41Z
- Modell: opus · Kostengrenze: 6 USD · Zeitgrenze: 1800 s
- claude: 2.1.332 (Claude Code)
- Ende: Exit-Code 0

Aufruf (Pfade gekürzt):

```
claude '-p' '--model' 'opus' '--mcp-config' '<lauf>/mcp.json' '--strict-mcp-config' '--setting-sources' 'project,local' '--settings' '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"allowUnsandboxedCommands":false}}' '--permission-mode' 'acceptEdits' '--allowedTools' 'mcp__linear' '--disallowedTools' 'WebFetch' 'WebSearch' '--no-session-persistence' '--max-budget-usd' '6' '--output-format' 'stream-json' '--verbose'
```
- Kosten: 0.2451694 USD · Züge: 8
