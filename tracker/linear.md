# Tracker-Vertrag: Linear

Dieser Vertrag gilt für jeden slickfab-Schritt, der den Tracker liest oder schreibt. Team und Projekt kommen aus der Projektkonfiguration (`docs/projektkonfiguration.md`). Linear ist die einzige Wahrheit über Plan und Zustand: Was hier nicht steht, gilt nicht als entschieden.

Diese Datei ist die Quelle. Die Schritte tragen die Teile, die sie brauchen, wörtlich in ihrer `SKILL.md` (zwischen `<!-- vertrag:NAME -->` und `<!-- /vertrag:NAME -->`), weil ein Schritt Dateien im Plugin-Ordner ohne Leseerlaubnis nicht lesen kann. Wer hier etwas ändert, ändert die Kopien mit; `tests/test_contract_blocks.py` prüft, dass sie gleich sind.

## Zugang

<!-- vertrag:zugang -->
- Linear wird über die Linear-Werkzeuge der Session angesprochen (in Claude Code per Werkzeugsuche `+linear` laden).
- Ist Linear nicht erreichbar (keine Werkzeuge, keine Anmeldung, Fehlerantwort, Team oder Projekt aus der Konfiguration existiert nicht), meldet der Schritt genau das mit der Fehlermeldung und hört auf. Er schreibt **keine** Plan-, Ledger-, State- oder Ticket-Datei ins Repo als Ersatz. Was schon erarbeitet ist, zeigt er im Chat, damit nichts verloren geht.
- Ausnahme `verify`: Liegt die Spec als Text vor, prüft verify dagegen weiter, statt aufzuhören. Es schreibt nichts in den Tracker, zeigt Ergebnis und Fix-Ticket-Vorschläge nur im Chat, und das Ergebnis endet mit `SLICKFAB-STATUS: DONE_WITH_CONCERNS` und nennt darüber „Tracker nicht geprüft“, auch wenn jede Aussage erfüllt ist; das gilt, sofern geprüft werden konnte, sonst mit `BLOCKED`. Liegt die Spec nicht als Text vor, gilt der Punkt davor.
<!-- /vertrag:zugang -->

## Issues

<!-- vertrag:issues -->
| Art | Titel | Ort | Anfangsstatus |
|---|---|---|---|
| Spec | `Spec: <Feature>` | Projekt aus der Konfiguration | `Backlog` |
| Ticket | Verb + Ergebnis, ohne „und“ | Sub-Issue der Spec | `Backlog` |

- Vor jedem Anlegen auf Dubletten prüfen: offene und erledigte Issues im Projekt mit ähnlichem Titel suchen. Gibt es einen Treffer, nennen und fragen, statt doppelt anzulegen.
- Abhängigkeiten sind Linear-Relationen „blockiert von“, nicht Text in der Beschreibung.
- Details für Agents (betroffene Dateien, Fundstellen) stehen in einem einklappbaren Abschnitt „Agent notes“ am Ende der Beschreibung.
<!-- /vertrag:issues -->

## Statusfolge

<!-- vertrag:status -->
`Backlog` → `Todo` → `In Progress` → `In Review` → `Done` (Abbruch: `Canceled`, Dublette: `Duplicate`)

| Übergang | Wer |
|---|---|
| anlegen in `Backlog` | `spec`, `tickets` |
| `Backlog` → `Todo` | nur der Mensch (das ist die Freigabe zum Bauen) |
| `Todo` → `In Progress` | der Umsetzer beim Start |
| `In Progress` → `In Review` | der Umsetzer, wenn der Pull Request offen ist |
| `In Review` → `Done` | nach dem Merge |

Kein Schritt setzt ein Ticket selbst auf `Todo`.
<!-- /vertrag:status -->

## Labels

<!-- vertrag:labels -->
Die Labels existieren im Team; ein Schritt legt keine neuen an. Fehlt eines, meldet er das.

| Label | Bedeutung |
|---|---|
| `slickfab:rework` | Reviewer verlangt Nachbesserung |
| `slickfab:ready` | Review bestanden, wartet auf den Merge durch einen Menschen |
| `slickfab:needs-human` | Schleife erschöpft oder Agent blockiert: ein Mensch entscheidet |
| `slickfab:replan` | Ticket oder Spec ist falsch geschnitten: zurück zur Planung |
| `door:one-way` | schwer umkehrbar (Migration, Auth, Zahlung, Löschen, Deploy): immer menschliches Gate, nie Auto-Merge |
| `S`, `M`, `L` | Größe (Aufwand klein, mittel, groß); genau eines je Ticket. `L` ist ein Hinweis, das Ticket eher zu teilen |

In Linear sind `rework`, `ready`, `needs-human` und `replan` Kinder der Label-Gruppe `slickfab`; in Texten, Kommentaren und diesem Vertrag wird `slickfab:<name>` geschrieben. Beim Suchen und Setzen über die Linear-Werkzeuge heißt das Label `rework`, `ready`, `needs-human` bzw. `replan` in der Gruppe `slickfab`; eine Suche nach `slickfab:rework` findet nichts, das Label fehlt dann nicht. Die Gruppe erlaubt nur eines zur Zeit.
<!-- /vertrag:labels -->

## Marker

<!-- vertrag:marker -->
Jeder Kommentar, den ein slickfab-Schritt oder eine Rolle schreibt, und jede Rückmeldung an einen Auftraggeber endet mit dem Marker-Block, ohne Text danach:

- Letzte Zeile, immer: `SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`
- Vorletzte Zeile, nur beim Reviewer: `SLICKFAB-VERDICT: MERGE|REWORK|REPLAN`

Alle anderen Schritte und Rollen schreiben nur die STATUS-Zeile. Je Zeile steht genau ein Wert.

| Wert | Bedeutung |
|---|---|
| `DONE` | Auftrag erfüllt, nichts offen |
| `DONE_WITH_CONCERNS` | erfüllt, aber mit genannten Bedenken |
| `BLOCKED` | kann nicht weiter; der Grund steht darüber |
| `NEEDS_CONTEXT` | es fehlt Information oder Kontext; was fehlt, steht darüber |

Beispiel (jeder Schritt):

```
SLICKFAB-STATUS: BLOCKED
```

Beispiel (Reviewer):

```
SLICKFAB-VERDICT: REWORK
SLICKFAB-STATUS: DONE
```
<!-- /vertrag:marker -->

## Rulings

<!-- vertrag:rulings -->
Entscheidet ein Agent selbst etwas, das ein Mensch anders hätte entscheiden können, schreibt er sofort einen Kommentar am betroffenen Issue in genau dieser Form:

`Ruling: was — warum — Kosten falls falsch`

Beispiel: `Ruling: Datum als ISO-String gespeichert — so liest es die bestehende API — eine Migration der Spalte, falls Zeitzonen nötig werden`

Rulings werden gesammelt und dem Menschen am Ende vorgelegt; sie ersetzen keine Rückfrage bei Produktfragen oder schwer umkehrbaren Entscheidungen.
<!-- /vertrag:rulings -->
