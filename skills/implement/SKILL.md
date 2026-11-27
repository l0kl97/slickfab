---
name: implement
description: Verwenden, wenn ein freigegebenes Ticket gebaut werden soll, oder wenn jemand „bau das Ticket“ oder „setz EX-123 um“ sagt.
argument-hint: "<Ticket>"
---

<!-- regel:einleitung -->
# implement: ein Ticket per TDD bis zum Pull Request

Ziel: Ein Pull Request, der genau das Ticket erfüllt und für jedes Kriterium belegt, dass der Test erst rot und dann grün war. Nicht mehr, nicht weniger.

Antworte in der Sprache des Menschen. Tracker-Regeln und Projektkonfiguration stehen unten im Abschnitt „Vertrag“.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Wenn ein Ticket auf `Todo` steht (der Mensch hat es freigegeben) und gebaut werden soll.
- Nicht ohne Ticket; nicht für die Fehlersuche ohne bekannte Ursache (dafür `/slickfab:debug`).
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Voraussetzung prüfen

- Du brauchst das Ticket (Argument). Lies es mit allen Kommentaren und die Spec, deren Sub-Issue es ist. Gibt es schon einen Pull Request zum Ticket, liest du auch dessen Review-Kommentare; mit denen am Ticket zeigen sie, welche Lücken ein Review schon gefunden hat.
- Lies `.slickfab/config` und, falls vorhanden, `.slickrails/config.sh`, beide nur als Text (Regeln im Vertrag). Fehlt die Konfiguration oder ist der Tracker nicht erreichbar, hör hier auf und melde genau das.
- Prüfbefehle nimmst du nur aus `.slickrails/config.sh` oder `.slickfab/config`; du rätst keine aus `package.json`, `Makefile` oder der Gewohnheit. Fehlt ein Prüfbefehl, sagst du, welcher, und dass du ihn nicht ausführen kannst. Ohne `CHECK_TEST` kannst du nicht belegen, dass die ganze Suite grün ist; dann endet der Schritt höchstens mit `DONE_WITH_CONCERNS`.
- Steht das Ticket nicht auf `Todo` oder `In Progress`, ist es nicht zum Bauen freigegeben: hör auf und sag das.
- Sind im Arbeitsbaum fremde Änderungen offen, hör auf und sag es. Du verschiebst oder versteckst keine fremde Arbeit.
- **Ausgangslage:** Lass `CHECK_TEST` einmal vor der ersten Änderung laufen und halte Befehl und Ergebnis fest. Ist es schon rot, meldest du das, bevor du baust; fremde rote Tests reparierst du nicht nebenbei.
- Prüf vor dem ersten Test, ob das Ticket die Stopp-Liste (Schritt 5) berührt.
- Setz das Ticket auf `In Progress`.
<!-- /regel:voraussetzung -->

<!-- regel:kriterien-in-tests-uebersetzen -->
### 2. Kriterien in Tests übersetzen

Geh die Akzeptanzkriterien des Tickets der Reihe nach durch, eines nach dem anderen. Für jedes überlegst du:

- **Teststelle:** Über welche öffentliche Schnittstelle zeigt sich das Verhalten (die Teststellen der Spec)? Tests prüfen Verhalten von außen, keine privaten Methoden, keine Aufrufzähler, kein direkter Blick in die Datenbank, wenn es eine Schnittstelle dafür gibt. Ein Test, der bei einem Umbau ohne Verhaltensänderung bricht, ist falsch geschnitten.
- **Erwarteter Wert:** aus der Spec, dem Ticket oder einem von Hand durchgerechneten Beispiel, nie aus derselben Logik wie der Code.
- **Gegenprobe:** Nenne die Änderung am Produktionscode, die diesen Test rot machen würde. Fällt dir keine ein, prüft der Test nichts.
- **Fehlerfälle** (ungültige Eingaben, Fehlerantworten, Grenzwerte) gehören dazu. Gemockt wird nur an Systemgrenzen (fremde APIs, Mail, Zeit, Zufall), nie eigener Code.

Das Review (`/slickfab:review`) prüft mit einer Mutationsprobe jedes Verhalten im Diff, nicht nur die Kriterien. Deshalb gilt für dich dieselbe Regel: Jedes Verhalten, das dein Diff einführt oder ändert, braucht einen Test, auch wenn das Ticket es nicht nennt. Eine bekannte Lücke aus einem früheren Review-Kommentar am Ticket oder am Pull Request schließt du mit rotem und grünem Lauf, oder du begründest im Pull Request unter „Nicht angefasst“ ausdrücklich, warum sie offen bleibt.

Schreib nicht alle Tests vorab und bau nichts auf Vorrat.
<!-- /regel:kriterien-in-tests-uebersetzen -->

<!-- regel:rot-gruen -->
### 3. Je Kriterium: rot, dann grün

1. **Rot:** Schreib genau den Test für dieses Kriterium und lass ihn laufen. Halte Befehl und Ausgabe fest. Er muss aus dem erwarteten Grund rot sein (die Assertion schlägt fehl, weil das Verhalten fehlt), nicht wegen eines Tippfehlers oder Imports. Ist er sofort grün, ist das Kriterium schon erfüllt oder der Test prüft nichts: klär das, bevor du weitermachst.
2. **Grün:** Schreib genau so viel Produktionscode, dass dieser Test besteht, und lass ihn wieder laufen. Halte Befehl und Ausgabe fest.
3. Zwischendurch Typprüfung (`CHECK_TYPECHECK`, falls vorhanden) und die betroffene Testdatei.

Ohne roten Lauf kein Produktionscode für dieses Kriterium. Aufräumen und Umbauen gehören nicht in diese Schleife; was dir auffällt, nennst du im Pull Request unter „Bedenken“.

Ein Fix-Versuch ist eine Änderung am Produktionscode, nach der derselbe Test wieder rot ist. Zähl sie sichtbar mit („Versuch 1/3“). Nach 3 gescheiterten Fix-Versuchen an derselben Stelle hörst du auf. Einen vierten Versuch startest du nicht. Du meldest `BLOCKED` mit den drei Versuchen und ihren Ausgaben und empfiehlst `/slickfab:debug` in einer frischen Session; drei gescheiterte Versuche heißen meist, dass die Annahme über die Ursache falsch ist, nicht, dass ein vierter Einfall fehlt.

Bestehende Tests schwächst du nicht ab, um grün zu werden: kein Überspringen (`skip`, `only`, `xfail`, auskommentiert), keine gelöschten oder gelockerten Assertions, keine gesenkten Schwellen (Abdeckung, Zeitlimits, Toleranzen), keine neuen Unterdrückungen (`@ts-ignore`, `eslint-disable`, `noqa`). Steht ein bestehender Test im Weg, änderst du ihn nicht, sondern hörst auf und meldest ihn: welcher Test, was er erwartet, was das Ticket verlangt, worin sie sich widersprechen. Status `BLOCKED`; ob der Test oder das Ticket falsch ist, entscheidet der Mensch. Das gilt auch, wenn das Ticket das Verhalten, das der Test festhält, ausdrücklich ändern will: Ob ein bestehender Test fallen darf, steht erst fest, wenn der Mensch es am Ticket festgehalten hat. Mit dieser Freigabe änderst du genau diesen Test und nennst ihn unter „Änderungen“.

| Ausrede | Realität |
|---|---|
| „Das Ticket verlangt doch genau dieses neue Verhalten.“ | Der Test hält eine Entscheidung fest, die jemand früher getroffen hat. Ob sie nicht mehr gilt, entscheidet der Mensch, nicht der Ticket-Text und nicht du. |
| „Der alte Test ist sowieso falsch.“ | Dann ist das ein Befund für den Menschen. Ein Test, den der Umsetzer passend macht, prüft nur noch den Umsetzer. |
| „Der Test ist flaky, ich setze ihn kurz auf skip.“ | Ein übersprungener Test ist ein gelöschter Test, den niemand bemerkt. Melden. |
| „Die Schwelle war eh zu streng.“ | Wer die Schwelle senkt, entscheidet über Qualität; das ist nicht Teil des Tickets. |
<!-- /regel:rot-gruen -->

<!-- regel:abweichungen -->
### 4. Abweichungen

Beim Bauen findest du Arbeit, die nicht im Ticket steht. So gehst du damit um:

- **Regel 1, Fehler:** Bestehender Code tut nicht, was er soll, und hindert dein Kriterium (falsche Abfrage, Logikfehler, kaputte Prüfung). Du behebst ihn mit eigenem rotem und grünem Lauf.
- **Regel 2, fehlende kritische Funktion:** Ohne sie wäre dein Kriterium nicht korrekt oder nicht sicher (fehlende Fehlerbehandlung, fehlende Eingabeprüfung, fehlendes Timeout an einem externen Aufruf). Du ergänzt sie mit Test.
- **Regel 3, Blocker:** Etwas hält dich mechanisch auf (falscher Typ, kaputter Import, fehlende Testkonfiguration). Du räumst es weg.
- **Regel 4, Architekturfrage:** Hier hörst du auf und meldest `BLOCKED` mit Begründung. Architekturfrage heißt: neue Tabelle oder Schnittstelle, die das Ticket nicht nennt, ein anderes Muster als das bestehende, eine neue Abhängigkeit, eine Änderung, die andere Tickets mitändern müssten. Du nennst die Frage, die Optionen und deine Empfehlung.

Was du nach Regel 1–3 tust, nennst du im Pull Request unter „Änderungen“ als `[Regel N] was, warum`, und schreibst je Entscheidung, die ein Mensch anders hätte treffen können, ein Ruling am Ticket. Die Stopp-Liste geht den Regeln 1–3 vor.
<!-- /regel:abweichungen -->

<!-- regel:stopp-liste -->
### 5. Stopp-Liste

Prüf vor jeder Änderung, ob sie einen dieser Punkte berührt:

- Auth und Berechtigungen (Anmeldung, Rollen, Zugriffsprüfungen),
- destruktive Migrationen (Spalte oder Tabelle löschen, Typ verengen, Daten umschreiben),
- Zahlungen,
- Löschungen von Daten,
- Deploys und alles, was live ausrollt,
- Secrets (anlegen, ändern, ausgeben, in Dateien schreiben),
- alles, was ein Revert nicht zurückholt (verschickte Mails, Aufrufe fremder Systeme mit Wirkung, veröffentlichte Pakete).

Berührt das Ticket oder dein Weg dorthin einen dieser Punkte, hörst du auf, bevor du ihn baust, und meldest `BLOCKED` mit Begründung: welcher Punkt, wo, was du bauen würdest, was ein Fehler kosten würde. Das gilt auch, wenn das Ticket es ausdrücklich verlangt; die Freigabe dafür gibt ein Mensch für genau diesen Punkt, und sie steht danach am Ticket. Mit dieser Freigabe baust du weiter und setzt `door:one-way`.

Beim Anhalten (Regel 4, Stopp-Liste, Test im Weg) schreibst du einen Kommentar am Ticket mit Grund und bisherigem Stand und setzt `slickfab:needs-human`. Was schon gebaut ist, bleibt auf dem Branch.
<!-- /regel:stopp-liste -->

<!-- regel:pruefungen -->
### 6. Ganze Suite und Prüfungen

Wenn alle Kriterien grün sind, lässt du die ganze Suite laufen (`CHECK_TEST`), dazu `CHECK_TYPECHECK` und `CHECK_LINT`, soweit vorhanden. Halte Befehl und Ergebnis fest. Rot heißt nicht fertig. Hooks umgehst du nie (`--no-verify` und Ähnliches), außer der Mensch hat es für genau diesen Push am Ticket festgehalten; dann steht der Grund im Commit. Eine Zusage im Gespräch reicht nicht. Blockiert ein Hook mit Befunden, behebst du die Befunde.

Verlangt das Repo (etwa `CLAUDE.md`) vor dem Pull Request ein Review, machst du es jetzt. Ein Pflicht-Review vor dem Pull Request (etwa `/security-review`) ist ein Zwischenschritt: Danach machst du mit Commit, Push und Pull Request weiter. Echte Befunde behebst du mit rotem und grünem Lauf, den Rest nennst du unter „Bedenken“.
<!-- /regel:pruefungen -->

<!-- regel:pull-request -->
### 7. Pull Request

Committe mit einer Nachricht, die sagt, warum und was. Push den Branch und öffne einen Pull Request gegen den Hauptzweig. Nicht mergen. Der Text hat diese Form:

```markdown
<Ticket-ID>: <Titel>

## Änderungen

- <was sich für Nutzer oder Aufrufer ändert, je Punkt ein Satz>
- [x] <Akzeptanzkriterium aus dem Ticket, abgehakt, wenn belegt>
- Abweichungen: <[Regel 1–3] was, warum> oder „keine“

## Nicht angefasst

- <was nah dran war, aber bewusst nicht geändert wurde, und warum> oder „keine“

## Bedenken

- <was dir aufgefallen ist und nicht zum Ticket gehört, offene Risiken> oder „keine“

## Door

`one-way` | `two-way`: <ein Satz, warum; `one-way`, wenn ein Revert nicht alles zurückholt>

## Blast Radius

<ein Wort oder kurzer Satz: wer oder was betroffen ist, wenn es schiefgeht>

## Nachweise

Ausgangslage: `<CHECK_TEST>` → <Ergebnis vor der ersten Änderung>

- K1 <Kriterium in Kurzform>
  - rot: `<Befehl>` → <Ausgabe, gekürzt auf die entscheidende Zeile>
  - grün: `<Befehl>` → <Ausgabe>
- K2 …

Ganze Suite: `<CHECK_TEST>` → <Ergebnis>
```

Fehlt für ein Kriterium der rote Lauf, ist der Pull Request nicht fertig. Jeder Abschnitt steht im Text, auch wenn er leer ist; dann steht darunter „keine“. Ein leerer Abschnitt sagt dem Prüfer, dass du daran gedacht hast; ein fehlender sagt ihm nichts.
<!-- /regel:pull-request -->

<!-- regel:abschluss -->
### 8. Abschluss

Setz das Ticket auf `In Review`, sobald der Pull Request offen ist, und schreib einen Kommentar am Ticket mit dem Link. Der Schritt endet erst mit dem „Ergebnis implement“ (unten); ein Review-Bericht, eine Testausgabe oder ein offener Pull Request ohne dieses Ergebnis ist kein Ende.
<!-- /regel:abschluss -->

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

### Projektkonfiguration: Prüfbefehle mit slickrails

<!-- vertrag:config-slickrails -->
Liegt im Repo `.slickrails/config.sh`, kommen die Prüfbefehle von dort: alle nicht leeren `CHECK_*`-Werte, so wie sie slickrails auch in seinen Hooks benutzt. `CHECK_*`-Einträge in `.slickfab/config` werden dann nicht benutzt; stehen dort andere Werte, nennt der Schritt den Widerspruch einmal und folgt slickrails. Auch `.slickrails/config.sh` wird nur als Text gelesen.
<!-- /vertrag:config-slickrails -->

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

### Tracker: Statusfolge

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

### Tracker: Labels

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

### Tracker: Rulings

<!-- vertrag:rulings -->
Entscheidet ein Agent selbst etwas, das ein Mensch anders hätte entscheiden können, schreibt er sofort einen Kommentar am betroffenen Issue in genau dieser Form:

`Ruling: was — warum — Kosten falls falsch`

Beispiel: `Ruling: Datum als ISO-String gespeichert — so liest es die bestehende API — eine Migration der Spalte, falls Zeitzonen nötig werden`

Rulings werden gesammelt und dem Menschen am Ende vorgelegt; sie ersetzen keine Rückfrage bei Produktfragen oder schwer umkehrbaren Entscheidungen.
<!-- /vertrag:rulings -->

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
## Ergebnis implement

**Ticket:** <ID> (jetzt `In Review`)
**Pull Request:** <Link>
**Kriterien:** <n> von <n> mit rotem und grünem Lauf belegt
**Ganze Suite:** `<CHECK_TEST>` → <Ergebnis>
**Abweichungen:** <[Regel N] …> oder „keine“
**Door:** `one-way` | `two-way`

Nächster Schritt: `/slickfab:review <Pull Request>` in einer frischen Session

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT>
```

Bei `BLOCKED` oder `NEEDS_CONTEXT` steht statt Pull Request und Kriterien der Grund: welcher Punkt der Stopp-Liste, welche Architekturfrage, welcher Test im Weg oder welche drei Fix-Versuche, und was der Mensch entscheiden muss. Die Zeile „Nächster Schritt“ fehlt nie, auch nicht bei `BLOCKED` oder `NEEDS_CONTEXT`. Dann lautet sie `Nächster Schritt: /slickfab:implement <Ticket>, sobald die Entscheidung am Ticket steht` (bei drei gescheiterten Versuchen: `/slickfab:debug`).
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:review <Pull Request>` in einer frischen Session, damit der Prüfer deinen Bericht nicht kennt. Bei `BLOCKED`: der Mensch entscheidet, danach erneut `/slickfab:implement <Ticket>`.
<!-- /regel:naechster-schritt -->
