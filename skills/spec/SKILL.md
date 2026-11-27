---
name: spec
description: Verwenden, wenn aus einem geklärten Gespräch (nach grill) eine Spezifikation im Tracker entstehen soll, oder wenn jemand „schreib die Spec“ sagt.
argument-hint: "[Feature-Name oder Spec-Issue zum Überarbeiten]"
---

<!-- regel:einleitung -->
# spec: Spezifikation aus dem Gespräch

Ziel: Eine Spec, aus der Umsetzer und Prüfer dasselbe Ziel lesen, ohne das Gespräch gesehen zu haben. Du schreibst auf, was entschieden ist. Du befragst nicht neu: Inhaltliche Entscheidungen fallen in `grill`, nicht hier.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Nach `/slickfab:grill`, wenn die Zusammenfassung „Ergebnis grill“ bestätigt ist.
- Zum Überarbeiten einer bestehenden Spec, wenn der Mensch über Einwände aus `challenge` entschieden hat (Argument: das Spec-Issue).
- Nicht, solange Produktfragen offen sind; dann zuerst `grill`.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Voraussetzung prüfen

Du brauchst eine geklärte Grundlage. Suche in dieser Reihenfolge:

1. eine bestätigte Zusammenfassung „Ergebnis grill“ in diesem Gespräch,
2. ein als Argument genanntes Spec-Issue (dann liest du es samt Kommentaren und arbeitest die dort genannten Entscheidungen ein),
3. ein Gespräch, in dem der Mensch Problem, Nutzer, Umfang und Erfolgskriterium ausdrücklich entschieden hat.

Findest du nichts davon, hörst du hier auf: Sag, dass die Grundlage fehlt, und empfiehl `/slickfab:grill <Thema>`. Schreib keine Spec auf Verdacht.

Lies dann `.slickfab/config` (Format und Regeln: Projektkonfiguration). Fehlt sie oder ist der Tracker nicht erreichbar, sag das gleich jetzt: Du kannst die Spec im Chat zeigen, aber nicht anlegen.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:lage-im-repo-lesen -->
### 2. Lage im Repo lesen

Lies, was die Spec binden muss: `CLAUDE.md`/`AGENTS.md`, `.slickrails/` (falls vorhanden), `GLOSSARY.md`, `docs/adr/`, bestehende Feature-Doku zum Thema. Benutze die Begriffe aus `GLOSSARY.md` und widersprich keinem ADR, ohne es zu nennen. Bei mehr als ein paar Dateien schickst du einen Sub-Agent und lässt dir das Ergebnis kurz geben.
<!-- /regel:lage-im-repo-lesen -->

<!-- regel:jede-aussage-auf-ihre-herkunft-pruefen -->
### 3. Jede Aussage auf ihre Herkunft prüfen

Geh Abschnitt für Abschnitt durch die Vorlage (Schritt 4). Jede Aussage, die du schreiben willst, stammt aus einer dieser Quellen:

- vom Menschen entschieden (im Gespräch oder in „Ergebnis grill“),
- „Autonom entschieden“ aus `grill`,
- eine Tatsache aus dem Repo.

Passt eine Aussage zu keiner Quelle, ist sie eine **offene Entscheidung**. Ordne sie ein wie in `grill`:

- **Umkehrbar, technisch** (austauschbar hinter stabiler Schnittstelle): entscheide selbst und trag sie unter „Autonom entschieden“ ein, mit Grund.
- **Produktfrage oder schwer umkehrbar:** Hier hörst du auf. Liste die offenen Entscheidungen auf, je ein Satz, warum die Spec sie braucht, und empfiehl `/slickfab:grill` mit genau diesen Punkten. Du schreibst die Spec erst weiter, wenn sie entschieden sind.

Diese Regel hat keine Ausnahme:

| Ausrede | Realität |
|---|---|
| „Die Antwort ist doch offensichtlich.“ | Dann kostet die Rückfrage in `grill` eine Minute. Eine stille Annahme kostet ein falsch gebautes Feature. |
| „Ich markiere es als Annahme in der Spec.“ | Eine markierte Annahme ist trotzdem eine Entscheidung, die der Mensch nicht getroffen hat. |
| „Ich frage hier kurz selbst nach.“ | `spec` stellt keine Inhaltsfragen; die Befragung mit Empfehlung und Einordnung gehört zu `grill`. |
<!-- /regel:jede-aussage-auf-ihre-herkunft-pruefen -->

<!-- regel:spec-schreiben -->
### 4. Spec schreiben

Füll diese Vorlage. Schreib in Verhalten und Begriffen der Domäne: Module und Schnittstellen beim Namen, aber ohne Dateipfade und ohne Code, weil beides schnell veraltet. Wo ein Pfad naheläge, nenne das Modul oder das Verhalten.

```markdown
## Bitte (wörtlich)

> „<die ursprüngliche Bitte des Menschen, wörtlich zitiert, auch mit Tippfehlern>“

## Problem

<aus Sicht der Nutzer: wer hat welches Problem, woran merkt man es heute>

## Lösung

<aus Sicht der Nutzer: was ist danach anders. Bei Änderungen an einem bestehenden Feature als Delta: vorher → nachher>

## User Stories

1. Als <Rolle> möchte ich <Fähigkeit>, damit <Nutzen>.
(lieber zu viele als zu wenige; Fehlerfälle und Randfälle eigene Stories)

## Entscheidungen

- <Entscheidung> (vom Menschen)
- Autonom entschieden: <Entscheidung> — <warum> — umkehrbar, weil <…> (oder „keine“)

## Muss wahr sein

- <beobachtbare Wahrheit aus Nutzersicht, die nach dem Bauen gilt; 3–7 Punkte>

## Kritische Verbindungen

- <Teil A> ↔ <Teil B>: <was zwischen beiden fließen muss; woran man merkt, dass es verdrahtet ist>
(die Stellen, an denen es am ehesten bricht)

## Grenzen

- **Immer:** <was jeder Umsetzer immer tut>
- **Erst fragen:** <was nur mit Ja des Menschen passiert>
- **Nie:** <was ausgeschlossen ist>

## Global Constraints

- <Regel, die jedes Ticket einhalten muss, wörtlich aus CLAUDE.md, slickrails-Regeln, Versionen, Konventionen>

## Review-Fokus

- <Eingabeklasse oder Risiko, das kein Test prüft und auf das der Prüfer schauen soll>

## Teststellen

- <öffentliche Schnittstelle, an der das Verhalten geprüft wird> — fängt: <…> — verpasst: <…>
(möglichst weit oben, möglichst wenige, bestehende bevorzugt; ideal genau eine)

## Nicht im Umfang

- <was ausdrücklich nicht gebaut wird>
```

Waren die Teststellen in `grill` nicht entschieden, schlägst du sie vor und trägst sie unter „Autonom entschieden“ ein; der Mensch sieht sie in Schritt 5.
<!-- /regel:spec-schreiben -->

<!-- regel:selbstpruefung-dann-zeigen -->
### 5. Selbstprüfung, dann zeigen

Prüf den Entwurf, bevor der Mensch ihn sieht:

- alle Abschnitte der Vorlage da, keiner leer (leer = „keine“ mit einem Satz warum),
- die Bitte steht wörtlich da, nicht umformuliert,
- kein Dateipfad, kein Dateiname, kein Code im Text,
- jede Aussage hat eine Quelle aus Schritt 3.

Zeig die Spec im Chat und frag, ob du sie so anlegen sollst. Das ist eine Freigabe, keine Inhaltsfrage: Will der Mensch etwas anders, übernimm es; öffnet seine Antwort eine neue Produktfrage, zurück zu Schritt 3.
<!-- /regel:selbstpruefung-dann-zeigen -->

<!-- regel:im-tracker-anlegen -->
### 6. Im Tracker anlegen

Erst nach dem Ja. Wie im Tracker-Vertrag: Dubletten prüfen, dann Issue `Spec: <Feature>` im Projekt aus `.slickfab/config`, Status `Backlog`. Beim Überarbeiten aktualisierst du das bestehende Spec-Issue statt ein neues anzulegen und schreibst einen Kommentar, dessen erste Zeile genau `## Spec überarbeitet` lautet; darunter steht, was sich geändert hat, am Ende die Marker-Zeile. An dieser ersten Zeile erkennt `fab`, dass die Spec nach einem `challenge`-Urteil geändert wurde.

Ist der Tracker nicht erreichbar oder fehlt die Konfiguration, meldest du das mit der Fehlermeldung und lässt die Spec im Chat stehen. Du legst keine Spec-, Plan- oder Ticket-Datei im Repo an.
<!-- /regel:im-tracker-anlegen -->

## Vertrag

<!-- regel:vertrag-quelle -->
Wörtlich aus `tracker/linear.md` und `docs/projektkonfiguration.md` des slickfab-Plugins. Es steht hier, damit du nichts außerhalb des Projekts lesen musst; es gilt genau so.
<!-- /regel:vertrag-quelle -->

### Projektkonfiguration: Format

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

### Projektkonfiguration: wenn sie fehlt

<!-- vertrag:config-fehlt -->
Fehlt `.slickfab/config`, fehlt ein Pflichtwert oder steht bei `TRACKER=` ein unbekannter Tracker, meldet der Schritt genau das (welche Datei, welcher Schlüssel) und hört an der Stelle auf, an der er den Tracker bräuchte. Er schreibt keine Plan-, Ledger- oder State-Datei und keine Ticket-Liste ins Repo als Ersatz; bereits Erarbeitetes zeigt er im Chat.

Er bietet an, `.slickfab/config` anzulegen, und zeigt den Inhalt mit den Werten, die er im Repo oder im Tracker gefunden hat. Angelegt wird sie erst, wenn der Mensch Team und Projekt bestätigt hat.
<!-- /vertrag:config-fehlt -->

### Tracker: Zugang

<!-- vertrag:zugang -->
- Linear wird über die Linear-Werkzeuge der Session angesprochen (in Claude Code per Werkzeugsuche `+linear` laden).
- Ist Linear nicht erreichbar (keine Werkzeuge, keine Anmeldung, Fehlerantwort, Team oder Projekt aus der Konfiguration existiert nicht), meldet der Schritt genau das mit der Fehlermeldung und hört auf. Er schreibt **keine** Plan-, Ledger-, State- oder Ticket-Datei ins Repo als Ersatz. Was schon erarbeitet ist, zeigt er im Chat, damit nichts verloren geht.
- Ausnahme `verify`: Liegt die Spec als Text vor, prüft verify dagegen weiter, statt aufzuhören. Es schreibt nichts in den Tracker, zeigt Ergebnis und Fix-Ticket-Vorschläge nur im Chat, und das Ergebnis endet mit `SLICKFAB-STATUS: DONE_WITH_CONCERNS` und nennt darüber „Tracker nicht geprüft“, auch wenn jede Aussage erfüllt ist; das gilt, sofern geprüft werden konnte, sonst mit `BLOCKED`. Liegt die Spec nicht als Text vor, gilt der Punkt davor.
<!-- /vertrag:zugang -->

### Tracker: Issues

<!-- vertrag:issues -->
| Art | Titel | Ort | Anfangsstatus |
|---|---|---|---|
| Spec | `Spec: <Feature>` | Projekt aus der Konfiguration | `Backlog` |
| Ticket | Verb + Ergebnis, ohne „und“ | Sub-Issue der Spec | `Backlog` |

- Vor jedem Anlegen auf Dubletten prüfen: offene und erledigte Issues im Projekt mit ähnlichem Titel suchen. Gibt es einen Treffer, nennen und fragen, statt doppelt anzulegen.
- Abhängigkeiten sind Linear-Relationen „blockiert von“, nicht Text in der Beschreibung.
- Details für Agents (betroffene Dateien, Fundstellen) stehen in einem einklappbaren Abschnitt „Agent notes“ am Ende der Beschreibung.
<!-- /vertrag:issues -->

### Tracker: Marker

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

## Ergebnis

<!-- regel:ergebnis -->
Ein Spec-Issue im Tracker (oder, ohne Tracker, die Spec im Chat und die klare Meldung, warum sie nicht angelegt ist). Im Chat zum Schluss:

```
## Ergebnis spec

**Spec:** <Issue-ID und Link> (oder: nicht angelegt, weil <Grund>)
**Autonom entschieden:** <Liste oder „keine“>
**Offene Entscheidungen:** <Liste, dann zurück zu grill, oder „keine“>

Nächster Schritt: `/slickfab:challenge <Issue-ID>`
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:challenge <Issue-ID>` — frischer Blick auf Produkt, Baubarkeit und später die Zerlegung; am besten in einer neuen Session, damit der Prüfer das Gespräch nicht kennt. Gibt es Fragen, die man nicht erfragen kann (Aussehen, Bedienung, ob eine Logik sich richtig anfühlt), vorher `/slickfab:prototype`. Fehlen Entscheidungen, zurück zu `/slickfab:grill`.
<!-- /regel:naechster-schritt -->
