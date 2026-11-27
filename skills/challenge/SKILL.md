---
name: challenge
description: Verwenden, wenn eine Spec vor dem Zerlegen einen frischen Blick von außen braucht (Produkt, Baubarkeit) oder eine Ticket-Zerlegung vor dem Anlegen geprüft werden soll, oder wenn jemand „challenge das“ sagt.
argument-hint: "<Spec-Issue> | Zerlegung <Spec-Issue> Runde <1|2>"
---

<!-- regel:einleitung -->
# challenge: frischer Blick auf Spec und Zerlegung

Ziel: Fehler fallen auf, bevor gebaut wird. Der Prüfer kennt nur das Ergebnis der Planung, nicht das Gespräch, aus dem es entstand; so sieht er, was im Text fehlt, statt es aus dem Gedächtnis zu ergänzen.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- **Spec-Prüfung:** nach `/slickfab:spec`, bevor zerlegt wird. Prüft Produkt und Baubarkeit.
- **Zerlegungsprüfung:** aus `/slickfab:tickets` heraus, bevor der Mensch die Ticket-Liste sieht. Prüft, ob die Tickets die Spec vollständig und sauber abdecken.
- Nicht für Code-Review; dafür gibt es den Review-Schritt.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Voraussetzung prüfen

- **Spec-Prüfung** braucht eine Spec: als Spec-Issue (Argument) oder, ohne Tracker, als Text im Argument. Gibt es keine, hör auf und empfiehl `/slickfab:spec`.
- **Zerlegungsprüfung** braucht die Spec, die nummerierte Ticket-Liste und die Runde (1 oder 2, ohne Angabe 1). In Runde 2 auch die Zahl der Befunde aus Runde 1. Fehlt die Liste, empfiehl `/slickfab:tickets`.
- Lies `.slickfab/config` und das Spec-Issue samt Kommentaren. Fehlt die Konfiguration oder ist der Tracker nicht erreichbar, sag das; du kannst trotzdem prüfen, wenn die Spec als Text vorliegt, aber das Ergebnis nur im Chat zeigen.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:frischen-blick-herstellen -->
### 2. Frischen Blick herstellen

Der Prüfer bekommt nur die Spec (bei der Zerlegungsprüfung: Spec und Ticket-Liste) und darf das Repo lesen, aber nicht das Planungsgespräch.

- Läuft in dieser Session schon Planung (`grill`, `spec`, `tickets` oder ein Gespräch über das Feature), starte einen frischen Sub-Agent. Gib ihm wörtlich nur die Spec bzw. Spec und Liste, den passenden Prüfauftrag aus Schritt 3 oder 4 und das Ausgabeformat. Keine Zusammenfassung des Gesprächs, keine Begründungen, keine eigene Einschätzung.
- Ist die Session frisch (nur dieser Aufruf), prüfst du selbst.
- Kannst du keinen Sub-Agent starten, sag das und empfiehl, `/slickfab:challenge <Spec-Issue>` in einer neuen Session aufzurufen. Prüf nicht selbst in einer Session, die das Gespräch kennt.
<!-- /regel:frischen-blick-herstellen -->

<!-- regel:spec-pruefung -->
### 3. Spec-Prüfung (Auftrag an den Prüfer)

Lies die Spec und dann im Repo, was es schon gibt (README, Feature-Doku, ADRs, betroffene Stellen).

**A. Produkt.** Prüf aus Nutzersicht, nicht die Technik:

- Wer hat das Problem wirklich, und woran merkt man, dass es gelöst ist?
- Was ist die kleinste Version mit demselben Nutzen? Was kann raus?
- Was gibt es schon, das dasselbe leistet oder dem widerspricht?
- Welche Annahme ist am wackligsten, und was passiert, wenn sie falsch ist?
- Passt es zu früheren Entscheidungen im Repo?

Schreib höchstens 7 Einwände, die wichtigsten zuerst, je mit einem Satz Begründung und einer Empfehlung: streichen, ändern oder behalten. Hast du keinen echten Einwand, sag das; erfinde keinen. Dann ein Urteil, genau eines: `bauen`, `kleiner bauen` oder `nicht bauen`, mit dem einen Grund, der es trägt.

**B. Baubarkeit.** Stell dir vor, du sollst danach Tickets schneiden und bauen, ohne den Autor fragen zu können. Sammle jede Stelle, an der du raten müsstest, und sortiere sie in drei Stapel:

1. **schon beantwortet** (steht in der Spec oder im Repo; streichen),
2. **Kleinkram** (ein Umsetzer kann es selbst entscheiden, ein falscher Griff ist billig),
3. **nur der Mensch** (ein falscher Griff ändert den Plan).

Berichte Stapel 3 vollständig, je Frage mit einem Satz, warum die Antwort den Plan ändert, die wichtigste zuerst. Für Stapel 1 und 2 genügt die Anzahl.
<!-- /regel:spec-pruefung -->

<!-- regel:zerlegungspruefung -->
### 4. Zerlegungsprüfung (Auftrag an den Prüfer)

Die Zerlegung wird in höchstens 2 Runden geprüft. Prüf die Ticket-Liste gegen die Spec:

- **Abdeckung:** Jeder Punkt aus „Muss wahr sein“ und jede User Story hat ein Ticket, das ihn liefert.
- **Kritische Verbindungen:** Jede ist in einem Ticket verdrahtet und geprüft, nicht nur auf beiden Seiten gebaut.
- **Reihenfolge:** Das erste Ticket ist ein Tracer und blockiert alle übrigen; keine Zyklen; Tickets, die dieselbe Datei nennen, haben eine Blockiert-Relation.
- **Schnitt:** Jedes Ticket ist eine durchgehende Scheibe, für sich vorführbar und in einer frischen Session baubar; ein „und“ im Titel heißt meist zwei Tickets.
- **Kriterien:** Jedes Kriterium nennt, was es widerlegt, und wäre am heutigen Stand falsch.
- **Stille Kürzung:** Nichts aus der Spec ist verkleinert oder vertagt, ohne dass es dasteht; keine Formulierungen wie „v1“, „vereinfacht“, „Platzhalter“, „wird später verdrahtet“.

Jeder Befund nennt die **Eigenschaft, die gelten muss** (bindend), den **Beleg**, wo sie verletzt ist, und **einen möglichen Weg** dorthin (nur Beispiel, nicht bindend). Zähl die Befunde.

Auswertung durch den Aufrufer:

- **Runde 1:** keine Befunde → bestanden. Sonst überarbeitet `tickets` die Liste und ruft Runde 2 mit der Befundzahl aus Runde 1.
- **Runde 2:** keine Befunde → bestanden. Wenn die Zahl der Befunde gegenüber Runde 1 nicht sinkt, wird abgebrochen: Die Überarbeitung dreht sich im Kreis. Ist sie gesunken, aber nicht null, ist die Prüfung ebenfalls zu Ende. In beiden Fällen gehen die offenen Befunde an den Menschen, der entscheidet.
- Es gibt keine dritte Runde. Wirst du mit Runde 3 aufgerufen, prüfst du nicht, sondern gibst die letzten Befunde an den Menschen weiter. Die holst du wörtlich aus dem Ergebnis von Runde 2 am Spec-Issue (Kommentare) und nennst sie im Ergebnis; ein Verweis darauf reicht nicht. Steht dort keins, sagst du das. Das Ergebnis endet mit `SLICKFAB-STATUS: NEEDS_CONTEXT`: Ohne Entscheidung des Menschen geht es nicht weiter.
<!-- /regel:zerlegungspruefung -->

<!-- regel:festhalten -->
### 5. Festhalten

- **Spec-Prüfung:** Kommentar am Spec-Issue mit Einwänden, Urteil und Stapel 3, letzte Zeile die Marker-Zeile nach Tracker-Vertrag (`DONE`, oder `DONE_WITH_CONCERNS`, wenn das Urteil nicht `bauen` ist oder Stapel 3 nicht leer). Du änderst die Spec nicht selbst; über Einwände entscheidet der Mensch.
- **Zerlegungsprüfung:** Ergebnis zurück an `tickets` bzw. in den Chat; im Tracker entsteht dabei nichts.
- Ohne Tracker: alles im Chat, mit dem Hinweis, dass nichts gespeichert ist. Keine Datei im Repo als Ersatz.
<!-- /regel:festhalten -->

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
Spec-Prüfung:

```
## Ergebnis challenge

**Urteil:** bauen | kleiner bauen | nicht bauen — <tragender Grund>
**Einwände:** <1–7, je Empfehlung> (oder „keine echten Einwände“)
**Nur der Mensch:** <Fragen> (Stapel 1: <n>, Stapel 2: <n>)
**Kommentar:** <Link> oder „nur im Chat“

Nächster Schritt: `/slickfab:spec <Spec-Issue>` (Entscheidungen einarbeiten) oder `/slickfab:tickets <Spec-Issue>`
```

Zerlegungsprüfung: Runde, Zahl der Befunde, die Befunde, und „bestanden“, „Runde 2 nötig“ oder „an den Menschen“; Nächster Schritt: `/slickfab:tickets` (weiter mit der Bestätigung der Liste).
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
Nach der Spec-Prüfung entscheidet der Mensch über die Einwände und Stapel 3. Ändert sich etwas, `/slickfab:spec <Spec-Issue>` zum Einarbeiten; sonst `/slickfab:tickets <Spec-Issue>`. Lautet das Urteil `nicht bauen` und der Mensch stimmt zu, endet die Planung hier: Der Mensch setzt die Spec auf `Canceled`. Nach der Zerlegungsprüfung geht es in `/slickfab:tickets` weiter.
<!-- /regel:naechster-schritt -->
