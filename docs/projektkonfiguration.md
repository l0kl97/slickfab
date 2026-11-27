# Projektkonfiguration `.slickfab/config`

Jedes Repo, in dem slickfab-Schritte den Tracker benutzen, hat eine Datei `.slickfab/config` im Repo-Root. Sie sagt, wo Specs und Tickets liegen und mit welchen Befehlen geprüft wird. Sie wird eingecheckt und enthält keine Zugangsdaten.

Diese Datei ist die Quelle. Die Schritte tragen die Teile, die sie brauchen, wörtlich in ihrer `SKILL.md` (Blöcke `<!-- vertrag:config-… -->`); `tests/test_contract_blocks.py` prüft, dass die Kopien gleich sind.

## Format

<!-- vertrag:config-format -->
`.slickfab/config` im Repo-Root: eine Zeile je Wert, `SCHLÜSSEL="wert"`. Leerzeilen und Zeilen mit `#` am Anfang zählen nicht.

```sh
# slickfab: Projektkonfiguration
TRACKER="linear"
TRACKER_TEAM="Example"
TRACKER_PROJECT="Example"
# Prüfbefehle, nur ohne slickrails (sonst gelten die aus .slickrails/config.sh)
CHECK_TYPECHECK="npm run typecheck"
CHECK_TEST="npm test"
CHECK_LINT=""
```

| Schlüssel | Pflicht | Bedeutung |
|---|---|---|
| `TRACKER=` | ja | Welcher Tracker-Vertrag gilt. Heute nur `linear`. |
| `TRACKER_TEAM=` | ja | Name oder Kürzel des Linear-Teams. |
| `TRACKER_PROJECT=` | ja | Name des Linear-Projekts, in dem Specs und Tickets liegen. |
| `CHECK_TYPECHECK=` | nein | Typprüfung; leer = gibt es nicht. |
| `CHECK_TEST=` | ja, ohne slickrails | Alle Tests; leer = gibt es nicht (dann sagt jeder Schritt, der prüfen soll, dass er es nicht kann). |
| `CHECK_LINT=` | nein | Lint; leer = gibt es nicht. |

Die Datei wird als Text gelesen, nicht als Shell-Skript ausgeführt (kein `source`), damit eine Konfiguration keinen Code einschleusen kann.
<!-- /vertrag:config-format -->

## Prüfbefehle mit slickrails

<!-- vertrag:config-slickrails -->
Liegt im Repo `.slickrails/config.sh`, kommen die Prüfbefehle von dort: alle nicht leeren `CHECK_*`-Werte, so wie sie slickrails auch in seinen Hooks benutzt. `CHECK_*`-Einträge in `.slickfab/config` werden dann nicht benutzt; stehen dort andere Werte, nennt der Schritt den Widerspruch einmal und folgt slickrails. Auch `.slickrails/config.sh` wird nur als Text gelesen.
<!-- /vertrag:config-slickrails -->

## Wenn die Konfiguration fehlt

<!-- vertrag:config-fehlt -->
Fehlt `.slickfab/config`, fehlt ein Pflichtwert oder steht bei `TRACKER=` ein unbekannter Tracker, meldet der Schritt genau das (welche Datei, welcher Schlüssel) und hört an der Stelle auf, an der er den Tracker bräuchte. Er schreibt keine Plan-, Ledger- oder State-Datei und keine Ticket-Liste ins Repo als Ersatz; bereits Erarbeitetes zeigt er im Chat.

Er bietet an, `.slickfab/config` anzulegen, und zeigt den Inhalt mit den Werten, die er im Repo oder im Tracker gefunden hat. Angelegt wird sie erst, wenn der Mensch Team und Projekt bestätigt hat.
<!-- /vertrag:config-fehlt -->
