---
name: prototype
description: Verwenden, wenn eine Frage nicht durch Fragen zu klären ist, etwa wie etwas aussehen soll oder ob sich eine Logik oder ein Zustandsmodell richtig anfühlt, oder wenn jemand „bau mal schnell einen Prototyp“ sagt.
argument-hint: "[die offene Frage]"
---

<!-- regel:einleitung -->
# prototype: Wegwerf-Code, der eine Frage beantwortet

Ziel: Eine Frage, die man nicht erfragen kann, ist danach entschieden. Der Prototyp ist Mittel zum Zweck; er wird weggeworfen, nur die Entscheidung bleibt.

Antworte in der Sprache des Menschen.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Aussehen und Bedienung: „Wie soll die Seite aussehen?“, „Welche Anordnung ist besser?“
- Logik und Zustand: „Fühlt sich dieser Ablauf richtig an?“, „Was passiert in diesem Randfall?“
- Typisch zwischen `grill` und `spec`, wenn `grill` eine Frage als nicht erfragbar markiert hat.
- Nicht für Fragen, die ein Satz des Menschen klärt (dann `grill`), und nicht als erster Bauabschnitt des echten Features.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Voraussetzung prüfen

- **Die Frage:** Steht eine konkrete, offene Frage im Gespräch oder im Argument? Formuliere sie in einem Satz. Gibt es keine, frag den Menschen, welche Frage der Prototyp beantworten soll. Lässt sie sich mit einem Satz beantworten, ist kein Prototyp nötig: zurück zu `/slickfab:grill`.
- **Das Repo:** Es muss ein Git-Repo mit sauberem Arbeitsstand sein (`git status` ohne Änderungen). Sind Änderungen offen, hör auf und sag es. Du verschiebst oder versteckst keine fremden Änderungen.

Hörst du hier auf, endest du mit der Vorlage „Halt“ (unten).
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:form-waehlen -->
### 2. Form wählen

Die Frage bestimmt die Form:

- **Aussehen → UI-Varianten.** Standard sind 3, höchstens 5 deutlich verschiedene Varianten auf derselben Seite, umschaltbar über den URL-Parameter `?variant=` und eine kleine schwebende Leiste. Bevorzugt auf einer bestehenden Seite mit echten Daten und echtem Rahmen, weil Varianten im leeren Raum alle gut aussehen. Nur wenn es keine passende Seite gibt, eine neue Wegwerf-Route nach der Routing-Konvention des Projekts.
- **Logik → Wegwerfskript.** Eine Datei, die den Ablauf durch die schwierigen Fälle schiebt und nach jedem Schritt den ganzen Zustand ausgibt, oder eine einzelne HTML-Datei mit Knöpfen, die auch ein Nicht-Entwickler bedienen kann.

Ist unklar, welche Form passt, und der Mensch nicht da: Liegt die Frage an einem Backend-Modul, nimm Logik; an einer Seite oder Komponente, nimm UI. Schreib die Annahme oben in den Prototyp.
<!-- /regel:form-waehlen -->

<!-- regel:wegwerf-branch-anlegen -->
### 3. Wegwerf-Branch anlegen

Merke dir den aktuellen Branch. Dann `git switch -c prototype/<kurzer-slug>`. Der ganze Prototyp entsteht nur auf diesem Wegwerf-Branch; Datei- und Routennamen enthalten `prototype`, damit niemand ihn für echten Code hält.
<!-- /regel:wegwerf-branch-anlegen -->

<!-- regel:schnell-bauen -->
### 4. Schnell bauen

- Startet mit einem Befehl aus dem Task-Runner des Projekts oder per Doppelklick auf die HTML-Datei.
- Zustand im Speicher; keine Datenbank, außer die Frage dreht sich genau darum (dann eine Wegwerf-Datenbank mit `prototype` im Namen).
- Zustand nach jeder Aktion bzw. jedem Variantenwechsel sichtbar.
- Keine Tests, keine Fehlerbehandlung über das Lauffähige hinaus, keine Abstraktionen.
<!-- /regel:schnell-bauen -->

<!-- regel:vorfuehren-und-urteil-holen -->
### 5. Vorführen und Urteil holen

Bevor du vorführst, committe den Prototyp auf dem Wegwerf-Branch; der Commit-Text nennt die Frage und den Ausgangs-Branch (den gemerkten Branch aus Schritt 3). So liegt nichts uncommittet herum, wenn die Sitzung vor dem Urteil endet. Prüf vor diesem Commit mit `git branch --show-current`, dass du auf `prototype/<slug>` stehst. Sonst committest du nichts und endest mit der Vorlage „Halt“.

Sag dem Menschen, wie er den Prototyp startet und was er vergleichen soll. Warte auf sein Urteil: welche Variante, welches Verhalten, oder was er aus mehreren übernimmt.

Schließ das Vorführen mit der Vorlage „wartet auf Urteil“ (unten, `NEEDS_CONTEXT`). Endet die Sitzung vor dem Urteil, weiß der Mensch damit, wie es weitergeht. Das Repo bleibt auf dem Wegwerf-Branch, damit er den Prototyp starten kann.
<!-- /regel:vorfuehren-und-urteil-holen -->

<!-- regel:festhalten-und-zurueck -->
### 6. Festhalten und zurück

- Kommt das Urteil in einer neuen Session (im Argument, mit der Frage), ist der Prototyp schon committet. Dann entfallen die Schritte 2 bis 5: wechsle auf den Wegwerf-Branch aus dem Argument (`git switch prototype/<slug>`); den Ausgangs-Branch nimmst du aus dem Argument oder dem Commit-Text des Prototyps; dann hältst du nur noch fest. Fehlt einer der beiden oder gibt es den Wegwerf-Branch nicht, hör auf und frag danach (Vorlage „Rückfrage Branch“ unten, `NEEDS_CONTEXT`).
- Du committest nie auf einem Branch, der nicht mit `prototype/` beginnt.
- Commit auf dem Wegwerf-Branch (bei unverändertem Prototyp mit `--allow-empty`); der Commit-Text nennt Frage und Urteil.
- Zurück auf den gemerkten Branch (in einer neuen Session: den Ausgangs-Branch). Vom Prototyp kommt nichts in den Hauptzweig, nur die Entscheidung.
- Gibt es schon ein Spec-Issue und eine `.slickfab/config` (siehe „Vertrag“), schreib Frage, Urteil und Branch-Namen als Kommentar dorthin, mit Marker-Zeile wie im Abschnitt „Vertrag“. Sonst steht beides im Chat und wandert mit in die Spec.
- Den Branch pushst du nur, wenn der Mensch das will.
<!-- /regel:festhalten-und-zurueck -->

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
```
## Ergebnis prototype

**Frage:** <ein Satz>
**Urteil:** <was der Mensch entschieden hat>
**Branch:** prototype/<slug> (nicht gemergt) — zurück auf <Branch>
**Festgehalten:** <Kommentar an Issue …> oder „im Chat“

Nächster Schritt: `/slickfab:spec`

SLICKFAB-STATUS: DONE
```

Wirft das Urteil neue Entscheidungen auf, lautet der nächste Schritt `/slickfab:grill`.

Vor dem Urteil (Schritt 5):

```
## Ergebnis prototype (wartet auf Urteil)

**Frage:** <ein Satz>
**Start:** <ein Befehl oder Doppelklick auf …>
**Vergleichen:** <was der Mensch ansehen oder durchspielen soll, je Variante ein Satz>
**Repo steht auf:** prototype/<slug> (Prototyp committet, angelegt von <Branch>) — zurück mit `git switch <Branch>`

Nächster Schritt: Urteil hier geben, dann hält prototype es fest; in einer neuen Session `/slickfab:prototype Frage: <…> Urteil: <…> Branch: prototype/<slug> von <Branch>`

SLICKFAB-STATUS: NEEDS_CONTEXT
```

Urteil in neuer Session, aber Branch fehlt (Schritt 6):

```
## Ergebnis prototype (Rückfrage Branch)

**Frage:** <ein Satz>
**Urteil:** <wie im Argument>
**Fehlt:** <Wegwerf-Branch | Ausgangs-Branch | `prototype/<slug>` gibt es nicht>
**Nichts geändert:** kein Commit, kein Branchwechsel; Repo steht auf <Branch>

Nächster Schritt: `/slickfab:prototype Frage: <…> Urteil: <…> Branch: prototype/<slug> von <Branch>`

SLICKFAB-STATUS: NEEDS_CONTEXT
```

Halt vor dem Bauen oder vor dem Commit:

```
## Ergebnis prototype (Halt)

**Wo:** <Schritt>
**Grund:** <Grund aus der Tabelle>
**Stand:** Repo auf <Branch>, kein Commit; <kein Branch angelegt | uncommittete Prototyp-Dateien: …>

Nächster Schritt: <aus der Tabelle>

SLICKFAB-STATUS: <NEEDS_CONTEXT | BLOCKED>
```

| Wo | Grund | Nächster Schritt | Status |
|---|---|---|---|
| Schritt 1 | keine Frage | `/slickfab:prototype <Frage>` | `NEEDS_CONTEXT` |
| Schritt 1 | Frage mit einem Satz zu klären | `/slickfab:grill <Frage>` | `NEEDS_CONTEXT` |
| Schritt 1 | offene Änderungen im Repo | Mensch committet oder legt sie selbst beiseite, dann `/slickfab:prototype <Frage>` erneut | `BLOCKED` |
| Schritt 5 | nicht auf `prototype/<slug>` | Mensch prüft den Branch, dann `/slickfab:prototype <Frage>` erneut | `BLOCKED` |

Die Marker-Zeile steht als letzte Zeile deiner Antwort, außerhalb jedes Codeblocks.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:spec` — übernimmt das Urteil als Entscheidung des Menschen. Hat der Prototyp neue offene Fragen aufgeworfen, zuerst `/slickfab:grill`.
<!-- /regel:naechster-schritt -->
