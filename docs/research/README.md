# Recherche: Quellen für slickfab (Stand 24.11.2026)

Fünf Repos wurden vollständig gelesen und gegen das bisherige private Studio und slickrails abgeglichen. Lokale Klone zum Nachlesen (nur lesen, nichts daraus ausführen):

| Quelle | Lokaler Klon | Commit |
|---|---|---|
| mattpocock/skills (+ aihero.dev/skills) | `~/code/skills/mattpocock-skills` | abeeaf9 |
| obra/superpowers | `~/code/skills/superpowers` | 22f0b46 (v7.0.2) |
| open-gsd/gsd-core | `~/code/skills/gsd-core` | – |
| addyosmani/agent-skills | `~/code/skills/agent-skills` | e997ac5 (v0.6.18) |
| upstash/context7 | `~/code/skills/context7` (älterer Stand) | 11cb18d |

Alle MIT. Ideen in eigenen Worten übernehmen; wörtliche Passagen nur mit Eintrag in `NOTICE`.

## Leitbild (Matt, `skills/in-progress/software-factory/`)
- Ein Lauf wartet nie auf einen Menschen: er endet, die nächste Änderung des Menschen im Tracker löst den nächsten Lauf aus.
- Drei Bremsen: automatische Checks, frisches automatisches Review, menschliches Review. „Accelerators without brakes make a slop cannon.“
- Langsam anfangen, einen Auslöser nach dem anderen, jede Schleife nach wenigen Versuchen an einen Menschen.
- Pro Task beantworten: Auslöser? Was tut er, was liest/schreibt er? Was löst er aus? Wo kommt der Mensch rein? Was verhindert Doppelarbeit?

## Pro Schritt: was wir übernehmen (mit Fundstelle)

### grill
- Matt `grilling/SKILL.md`: Entscheidungsbaum, je Runde alle Fragen, deren Voraussetzungen geklärt sind, nummeriert mit Empfehlung; so formuliert, dass „ja“ die Empfehlung annimmt. Fakten holt ein Sub-Agent, der Mensch wird nur nach Entscheidungen gefragt. Keine Fragen-Obergrenze.
- Matt `domain-modeling/`: GLOSSARY.md mit „_Avoid_“-Synonymen sofort pflegen; ADR nur wenn schwer umkehrbar, überraschend und echter Trade-off (`ADR-FORMAT.md`).
- gsd `references/planner-reversibility.md` + `autonomous-smart-discuss.md`: reversible/costly/one-way; reversible technische Fragen selbst entscheiden und als „Autonom entschieden“ protokollieren; „When unsure, rate it reversible“.
- addy `interview-me`: eigene Vermutung + Konfidenz; fertig, wenn die nächsten drei Antworten vorhersagbar sind. „whatever you think“ ist kein Ja.

### spec
- Matt `to-spec`: Spec aus dem Gespräch, keine neue Befragung; Teststellen (Seams) vorab abstimmen, ideal genau eine; je Seam „fängt / verpasst“ (`tdd/SKILL.md`).
- gsd `agents/gsd-planner.md`: zielrückwärts – „Muss wahr sein“, Artefakte, kritische Verbindungen („Where is this most likely to break?“).
- addy `spec-driven-development`: Grenzen Immer / Erst fragen / Nie; Delta-Spec für Änderungen an bestehenden Features.
- superpowers `writing-plans`: Global Constraints wörtlich, Review-Fokus (Eingabeklassen, die kein Test prüft).

### prototype
- Matt `prototype/` + aihero: Look-and-feel ist „ungrillable“ → UI-Varianten über `?variant=`, Logik als Wegwerfskript; Wegwerf-Branch.

### challenge
- Studio-Challenger (Produktsicht, max. 7 Einwände, Urteil bauen/kleiner/nicht).
- superpowers `brainstorming/builder-check-prompt.md`: „Was müsste ein Umsetzer ohne Rückfrage wissen?“ – drei Stapel: schon beantwortet / Kleinkram / nur der Mensch.
- gsd `agents/gsd-plan-checker.md` + `references/revision-loop.md`: Zerlegung prüfen (Abdeckung, Abhängigkeiten, Key Links, stille Scope-Kürzung); Befund mit bindender Eigenschaft und nur beispielhaftem Fix; max. Runden, Abbruch wenn Befundzahl nicht sinkt.

### tickets
- Matt `to-tickets`: Tracer Bullets, „what can I demo?“, passt in ein frisches Kontextfenster, keine Dateipfade im Ticket-Text, Prefactoring zuerst, breite Umbauten als Expand–Migrate–Contract; nummerierte Liste vor dem Anlegen bestätigen lassen.
- aihero to-issues: je Akzeptanzkriterium die Beobachtung, die es widerlegt; prüfen, dass es am Ausgangs-Commit scheitert.
- gsd: erstes Ticket ist ein Tracer (dünnster Pfad durch alle Schichten) und blockiert die übrigen; verbotene Formulierungen „v1“, „simplified“, „placeholder“, „will be wired later“; Dateiüberschneidung → nacheinander.
- superpowers `writing-plans`: Interfaces-Block je Task (Consumes/Produces), damit ein Umsetzer, der nur sein Ticket sieht, die Namen kennt.
- addy `planning-and-task-breakdown`: „und“ im Titel = zwei Tasks; >3 Kriterien = zu groß; riskantes früh; „Files likely touched“.

### implement
- Studio-Umsetzer (TDD je Kriterium, Tests über öffentliche Schnittstelle, Mocks nur an Systemgrenzen).
- superpowers `test-driven-development` + `writing-good-tests.md`: RED/GREEN-Nachweis (Befehl + Ausgabe); „Name the production change that would make this test fail“; ganze Suite als Verifikation; Status-Enum DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT; „It is always OK to stop and say this is too hard“.
- gsd `agents/gsd-executor.md`: Abweichungsregeln 1–3 (Bug, fehlende kritische Funktion, Blocker) selbst beheben, Regel 4 Architektur → STOP; max. 3 Fix-Versuche; 5+ Reads ohne Edit → stoppen; Fakten messen, nicht erzählen; Stub-Scan.
- addy `/build auto`: Stopp bei Auth/Berechtigungen, destruktiven Migrationen, Zahlungen, Löschungen, Deploys, Secrets, allem, was `git revert` nicht zurückholt. PR-Text: CHANGES MADE / DIDN'T TOUCH / CONCERNS.
- Matt `pr/`: Summary, Evidence vorher/nachher, Door (one-way/two-way), Blast Radius.
- Matt `tdd`: erwartete Werte aus unabhängiger Quelle; Refactoring gehört ins Review, nicht in die Schleife.

### review
- Studio-Reviewer (Achsen Auftrag / Regeln, Belege, Urteil mergen/nachbessern/zurück zum Planer).
- addy `code-review-and-quality`: Schweregrade Critical/Required/Optional/Nit/FYI; bestehende Mängel getrennt von Regressionen; null Befunde ist gültig; Mutationsprobe („Invert one condition … a mutation that stays green is a finding“); Checkout = PR-Head prüfen.
- superpowers `task-reviewer-prompt.md`/`code-reviewer.md`: „Do Not Trust the Report“; Begründung senkt nie die Schwere; „spec's silence is not permission“; Liste „Declined to judge“; Re-Review nur auf Befunde (ADDRESSED/NOT ADDRESSED); Tripwire: Auftrag mit „do not flag“ → stoppen.
- Matt `code-review`: 12 Fowler-Smells als Ermessensfälle; Spec-Achse: fehlend / Scope Creep / falsch, je mit zitierter Spec-Zeile; keine Rekursion (keine weiteren Agents).
- gsd `gsd-verifier.md`: Stub-Muster, „Presence is not behavior“.
- addy `doubt-driven-development`: Prüfer bekommt Artefakt + Vertrag, nicht die Selbsteinschätzung des Autors.

### debug
- Matt `diagnosing-bugs`: erst ein schneller Befehl, der auf genau diesen Bug rot wird („No red-capable command, no Phase 2“); minimieren; 3–5 widerlegbare Hypothesen; Debug-Logs mit Tag `[DEBUG-xxxx]`; fehlender Seam für den Regressionstest ist selbst ein Befund.
- superpowers `systematic-debugging`: 4 Phasen; nach 3 gescheiterten Fixes Architektur in Frage stellen.
- gsd `templates/DEBUG.md` + `gsd-debugger.md`: Focus überschreiben, Eliminated/Evidence nur anhängen; Wissensbasis „Why not caught“ + „Recurrence guard“.

### verify
- gsd `gsd-verifier.md`: „Assume the goal was not achieved until evidence proves it“; Ebenen existiert → substanziell → verdrahtet → Daten fließen; Status passed/gaps_found/human_needed; Lücken werden zu Fix-Tickets.

### retro
- Matt `retro/`: mechanischer Fehler → deterministischer Check; Ermessensfrage → Standards-Datei; CLAUDE.md nur Verweise. `chief-of-staff`: Retro etwa jede fünfte Sitzung, schiefgelaufene zuerst.
- Matt EXAMPLE-TASKS „Retro task“: nach jedem 10. Merge, Vorschlag als PR, immer menschliches Review.

### handoff
- addy `context-engineering`: fünf Dinge persistieren – Scope und Entscheidungen, Task-Status, Dateien und Working-Tree, Prüfbefehle mit Ergebnis, offene Freigaben. „Do not infer approval from a previous conversation unless the durable artifact records it.“
- Matt `handoff/`: Verweise statt Kopien.

### docs-lookup (Context7-Mechanik ohne Abo)
- context7 `packages/mcp/src/index.ts`: zwei Schritte resolve-library-id → query-docs, Version aus package.json/Lockfile, max. 3 Aufrufe pro Frage; Doku ist Daten, nicht Anweisung; keine Secrets in Queries; bei Fehler melden statt raten.
- addy `source-driven-development`: Framework-Code nur nach offizieller Doku, mit Quelle, sonst `UNVERIFIED`.
- Umsetzung slickfab: lokal zuerst (installiertes Paket, `.d.ts`, CHANGELOG), dann `llms.txt`/offizielle Doku, Cache, Sub-Agent liefert ≤40 Zeilen.

## Autopilot / Orchestrierung
- superpowers `subagent-driven-development`: Fix-Loop max. 5 Runden (1–3 derselbe, 4–5 frisch + stärker), Ledger überlebt Kompaktierung, Rulings („Ruling: was — warum — Kosten falls falsch“, Liste „Rulings I made“ am Ende), nur 4 Stopps: irreversibel, sicherheitsrelevant, Merge/Push/Publish, Plan kaputt. Preflight-Scan: eine Zeile je Task-Paar, das Datei oder Schnittstelle teilt.
- gsd `workflows/execute-phase`: Waves aus depends_on; Dateiüberschneidung → spätere Wave; Post-Merge-Gate nach jeder Wave; Rückgabemarker als exakte Strings; Modellprofile je Rolle (`references/model-profiles.md`); `hooks/gsd-context-monitor.js` warnt den Agent selbst bei wenig Restkontext.
- Matt `docs/engineering/implement-spec.md`: Frontier aus Merges, nicht aus Tracker-Status; Tests mit gitignored Daten werden im Worktree still übersprungen → falsch grün.
- addy `/ship`: Security-Persona nur, wenn nicht trivial (≤2 Dateien, <50 Zeilen, kein Auth/Zahlung/Datenzugriff/Config).

## Bewusst nicht übernommen
- Plan-Dateien, `.planning/`, Ledger-Dateien: Linear ist die einzige Wahrheit.
- Router-Bootstrap per SessionStart („1 % → MUST invoke“): erzeugt Rauschen, Claude Code routet selbst.
- gsd-Tooling (gsd-tools.cjs, ~30 Hooks), XML-Plansprache, Agent-Zoo, Milestones/Roadmapper.
- Pläne auf 2–5-Minuten-Schrittebene; extrem lange Story-Listen; strikt eine Frage pro Nachricht.
- Großbetriebs-Zeremonie (Canary-Prozente, Error-Budgets, Build Cop).
- Matts Plugin komplett installieren (`/code-review` kollidiert mit dem eingebauten; offener Rekursionsbug).

## Messbare Lehren der Quellen
- superpowers (Positive-Instruction-Spec): Verbote verschlechtern Output-Formen (4,4 vs. 3,6 ohne Anleitung) → für Formvorgaben positive Rezepte; Verbote, Ausrede-Tabellen und Tripwires nur für Disziplinregeln.
- superpowers: Description, die den Ablauf zusammenfasst, lässt den Agent der Description statt dem Skill folgen → Description nennt nur den Auslöser.
- superpowers `writing-skills`: Skills wie Code testen – Baseline ohne Text, Pressure-Szenarien mit 3+ Drucksorten, Kontrollgruppe.
- aihero: horizontal geschnittener Stapel brauchte ~20 Läufe pro geschlossenem Ticket; Smart Zone ~150k Tokens.
