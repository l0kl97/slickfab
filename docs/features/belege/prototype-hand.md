# Belege: Hand-Durchlauf prototype

Endausgaben der Läufe, wörtlich aus `claude -p --output-format json` (Feld `result`), Kosten aus `total_cost_usd`. Protokoll und Bewertung: `docs/features/planungs-schritte.md`. Die Wegwerf-Repos selbst sind nicht eingecheckt; ihr Aufbau steht im Dossier.

Laufparameter (prototype): `claude -p "<Eingabe>" --model sonnet --plugin-dir <kopie> --setting-sources user,local --permission-mode acceptEdits --allowedTools "Bash(git:*)" "Bash(python3:*)" "Bash(make:*)" "Bash(ls:*)" "Bash(cat:*)" Read Write Edit Glob Grep --strict-mcp-config --mcp-config '{"mcpServers":{}}' --output-format json`, Claude Code 2.1.332. Für fab: `--permission-mode default --allowedTools Read Grep Glob "Bash(git:*)" "Bash(ls:*)" "Bash(cat:*)"`.

## proto-ui lauf1: UI, vor dem Fix

Eingabe: `/slickfab:prototype Wie soll die Notizliste auf der Startseite aussehen: als Karten, als Tabelle oder als kompakte Liste mit Tags?`

Kosten: 0.163 USD · Züge: 12 · abgelehnte Befehle: ['for f in Makefile README.md app.js index.html notes.json style.css; do echo "===']

```text
Der Prototyp ist gebaut. Er liegt ungepusht auf dem Branch `prototype/notizliste-layout`, `main` ist unberührt.

**Starten:** `make serve` im Projektordner, dann im Browser öffnen:
- http://localhost:8000/?variant=cards (Karten)
- http://localhost:8000/?variant=table (Tabelle)
- http://localhost:8000/?variant=compact (kompakte Liste mit Tags)

Die schwebende Leiste unten rechts schaltet zwischen den drei Varianten um. Alle drei zeigen deine vier echten Notizen aus `notes.json`.

**Was du vergleichen sollst:**
- **Karten:** Wie gut lässt sich der Inhalt auf einen Blick erfassen? Wie viel Platz braucht die Liste bei vielen Notizen?
- **Tabelle:** Eignet sie sich zum Scannen und Sortieren? Wirkt sie für Notizen zu nüchtern?
- **Kompakt mit Tags:** Passt viel auf den Bildschirm, aber ist der Inhalt noch lesbar? Fallen die Tags genug auf?

Sag mir, welche Variante es wird oder was du aus mehreren übernimmst. Danach committe ich auf dem Wegwerf-Branch mit Frage und Urteil und wechsle zurück auf `main`.
```

## proto-logik lauf1: Logik, vor dem Fix

Eingabe: `/slickfab:prototype Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist? Fühlt sich unser Zustandsmodell in ausleihe.py dafür richtig an?`

Kosten: 0.179 USD · Züge: 7 · abgelehnte Befehle: ["git switch -c prototype/vormerker-gesperrt && cat > prototype_vormerker.py <<'EO"]

```text
Der Prototyp läuft. Er liegt auf dem Wegwerf-Branch `prototype/vormerker-gesperrt`, noch nicht committed, weil ich zuerst dein Urteil brauche.

**Starten:** `python3 prototype_vormerker.py` im Repo-Root. Es spielt drei Fälle durch: erster gesperrt und zweiter ok, alle gesperrt, und erster ok als Kontrolle. Dazu kommen vier Varianten.

**Ergebnis**
- **Das Zustandsmodell trägt nicht, und das hat nichts mit der Sperre zu tun.** `zurueckgeben()` setzt den Zustand auf `vorgemerkt`, aber `ausleihen()` erlaubt nur `verfuegbar`. Auch der erste Vormerker kann das Exemplar deshalb nie abholen (Fehler „nicht verfügbar“). `gesperrt()` wird nirgends aufgerufen.
- **A, Gesperrte überspringen, in der Queue lassen:**
  - Das Exemplar wird für den ersten Berechtigten bereitgelegt.
  - Sind alle gesperrt, wird es `verfuegbar`.
  - Wird die Sperre später aufgehoben, rückt der Vormerker wieder an seine alte Stelle.
- **B, Gesperrte aus der Queue streichen:** Das ist einfach, aber der Vormerker verliert seinen Platz. Wer die Gebühr zahlt, muss neu vormerken.
- **C, Queue blockiert:** Ein einzelner gesperrter Leser hält das Exemplar für alle dahinter fest. Das ist mein Favorit gegen.

**Meine Empfehlung:** A, mit einem eigenen Zustand `bereitgelegt` für den Berechtigten. Den braucht es ohnehin, damit der erste Vormerker das Exemplar abholen kann.

**Dein Urteil:**
1. Welche Variante: A, B oder C, oder eine Mischung?
2. Soll bei „alle gesperrt“ das Exemplar frei für jeden werden (A), oder soll die Queue es weiter halten?

Danach committe ich Frage und Urteil auf dem Prototyp-Branch und wechsle zurück auf `main`. Gepusht wird nichts.
```

## proto-ui lauf2: UI, nach dem Fix (neu angelegtes Repo)

Eingabe: `wie Lauf 1 UI`

Kosten: 0.174 USD · Züge: 9 · abgelehnte Befehle: ["git switch -c prototype/notizliste-darstellung && cat > prototype-app.js <<'EOF'"]

```text
Der Prototyp ist gebaut und committet. Ich schließe jetzt das Vorführen ab und warte auf dein Urteil.

## Ergebnis prototype (wartet auf Urteil)

**Frage:** Wie soll die Notizliste auf der Startseite aussehen: als Karten, als Tabelle oder als kompakte Liste mit Tags?
**Start:** `make serve`, dann http://localhost:8000. Mit `?variant=karten`, `?variant=tabelle` oder `?variant=kompakt` wählst du die Variante. Du kannst auch unten die schwebende Leiste benutzen. Ohne Parameter startet `karten`.
**Vergleichen:**
- **Karten:** Jede Notiz ist eine Karte mit Titel, Text, Tags und Datum. Das ist gut zum Überfliegen, braucht aber am meisten Platz.
- **Tabelle:** Spalten für Titel, Inhalt, Tags und Geändert. Das ist am besten zum Vergleichen und Sortieren, wirkt aber nüchtern.
- **Kompakt + Tags:** Eine Zeile pro Notiz mit Titel, Tags und Datum, ohne Text. Das ist am dichtesten, zeigt aber keinen Inhalt.

Die Daten sind die vier echten Notizen aus `notes.json`. Ich habe nur `index.html` auf `prototype-app.js` und `prototype.css` umgestellt. `app.js` und `style.css` sind unverändert. Ich habe den Prototyp nicht im Browser angesehen und keine Tests ausgeführt.

**Repo steht auf:** `prototype/notizliste-darstellung` (Prototyp committet) — zurück mit `git switch main`

Nächster Schritt: Urteil hier geben, dann hält prototype es fest. In einer neuen Session `/slickfab:prototype <Frage und Urteil>`.

SLICKFAB-STATUS: NEEDS_CONTEXT
```

## proto-logik lauf2: Logik, nach dem Fix (neu angelegtes Repo)

Eingabe: `wie Lauf 1 Logik`

Kosten: 0.167 USD · Züge: 9 · abgelehnte Befehle: ['git switch -c prototype/vormerker-gesperrt && cat > prototype_vormerker_gesperrt']

```text
## Ergebnis prototype (wartet auf Urteil)

**Frage:** Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist, und passt das Zustandsmodell in `ausleihe.py` dafür?

**Start:** `python3 prototype_vormerker_gesperrt.py`

**Was der Lauf zeigt:** Das Modell passt dafür nicht, und der Fall „gesperrt“ ist nicht der einzige Fehler.
- **Szenario A (erster Vormerker ok):** Nach der Rückgabe steht das Exemplar auf `vorgemerkt`. Dann scheitert aber auch `bob`, der berechtigte Vormerker, mit „nicht verfügbar“. `ausleihen` akzeptiert nur `verfuegbar`, also kommt aus `vorgemerkt` niemand mehr heraus.
- **Szenario B (erster gesperrt, zweiter ok):** `carl!` und `dora` scheitern beide. Das Exemplar bleibt für immer `vorgemerkt`. `dora` müsste eigentlich nachrücken.
- **Szenario C (einziger Vormerker gesperrt):** Das Exemplar bleibt `vorgemerkt` und wartet auf jemanden, der nie ausleihen darf.
- **Sperre:** `gesperrt()` wird weder in `ausleihen` noch in `zurueckgeben` aufgerufen. Die Sperre prüft heute niemand.

**Zu entscheiden (das Urteil):** Was soll bei Szenario B und C passieren?
1. **Überspringen:** Der gesperrte Vormerker wird übergangen und der nächste rückt nach. Ist die Liste leer, wird das Exemplar `verfuegbar`.
2. **Vormerkung verfällt:** Der gesperrte Vormerker wird aus der Liste gestrichen, sonst wie bei 1.
3. **Er bleibt vorn, aber blockiert nicht:** Er behält seinen Platz, das Exemplar wird für den nächsten freigegeben.
4. Etwas anderes.

Außerdem: Soll `vorgemerkt` ein eigener Zustand mit „Abholer“ bleiben (etwa mit einer Frist)? Dann braucht `ausleihen` eine Regel dafür, dass nur der erste berechtigte Vormerker aus `vorgemerkt` ausleihen darf.

**Repo steht auf:** `prototype/vormerker-gesperrt` (Prototyp committet, Commit `cf862e6`). Zurück mit `git switch main`.

Nächster Schritt: Urteil hier geben, dann hält prototype es fest. In einer neuen Session `/slickfab:prototype <Frage und Urteil>`.

SLICKFAB-STATUS: NEEDS_CONTEXT
```

## proto-ui lauf3: UI, Urteil in neuer Session

Eingabe: `/slickfab:prototype Frage: Wie soll die Notizliste auf der Startseite aussehen (Karten, Tabelle oder kompakte Liste mit Tags)? Urteil: Karten.`

Kosten: 0.107 USD · Züge: 3 · abgelehnte Befehle: keine

```text
## Ergebnis prototype

**Frage:** Wie soll die Notizliste auf der Startseite aussehen: Karten, Tabelle oder kompakte Liste mit Tags?
**Urteil:** Karten.
**Branch:** prototype/notizliste-darstellung (nicht gemergt, nicht gepusht). Das Repo steht wieder auf `main`.
**Festgehalten:** im Chat und als Commit `93c2ce3` auf dem Wegwerf-Branch. Es gibt keine `.slickfab/config` und damit kein Spec-Issue, an das ein Kommentar gehen könnte.

Nächster Schritt: `/slickfab:spec`

SLICKFAB-STATUS: DONE
```

## proto-logik lauf3: Logik, Urteil in neuer Session

Eingabe: `/slickfab:prototype Frage: Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist? Urteil: Überspringen, der gesperrte Vormerker behält seinen Platz (Variante 3); zusätzlich bekommt vorgemerkt eine Abholfrist, deren Länge noch offen ist.`

Kosten: 0.108 USD · Züge: 3 · abgelehnte Befehle: keine

```text
## Ergebnis prototype

**Frage:** Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist?
**Urteil:** Überspringen, der gesperrte Vormerker behält seinen Platz (Variante 3). Zusätzlich bekommt der Zustand `vorgemerkt` eine Abholfrist. Wie lang sie ist, ist noch offen.
**Branch:** prototype/vormerker-gesperrt (nicht gemergt) — zurück auf main
**Festgehalten:** im Chat und als Commit auf dem Prototyp-Branch. Es gibt keine `.slickfab/config` und kein Spec-Issue, deshalb gibt es keinen Kommentar.

Das Urteil wirft neue Entscheidungen auf. Dazu gehören die Länge der Abholfrist und ihr Ablauf: Wer kommt danach dran? Verfällt die Vormerkung des Gesperrten, oder behält er weiter seinen Platz?

Nächster Schritt: `/slickfab:grill`

SLICKFAB-STATUS: DONE
```

## self fab: fab in Kopie des Repos slickfab mit .slickfab/config

Eingabe: `/slickfab:fab`

Kosten: 0.130 USD · Züge: 5 · abgelehnte Befehle: ['git rev-parse --show-toplevel; echo ---; git branch --show-current; echo ---; gi', 'gh pr list --state open --json number,title,headRefName,url']

```text
## Ergebnis fab

**Stand:** Das Repo ist `<worktree>/.test-tmp/self` auf `main` und sauber (`git status --short` ist leer). `git remote -v` liefert keinen Remote. `.slickfab/config` ist vollständig (`TRACKER=linear`, Team „Example“, Projekt „Example“, `CHECK_TEST="sh tests/run.sh"`), und `.slickrails/` mit `config.sh` ist vorhanden. Von Specs, Tickets oder PRs habe ich nichts gesehen.
**Gelesen:** Repo ja, Pull Requests nein: `gh pr list` wurde nicht freigegeben, und ohne Remote gäbe es vermutlich auch nichts zu lesen. Tracker nein: Die Linear-Werkzeuge sind in dieser Session nicht geladen (die Werkzeugsuche `+linear` fand nichts). Offene Specs, Tickets und `SLICKFAB-VERDICT`-Zeilen sind daher unbekannt.
**Fehlt zur Einrichtung:** Linear-Werkzeuge in der Session, die Freigabe für `gh` (oder ein Remote am Repo) und ein Git-Remote. Die Config selbst ist vollständig.

Nächster Schritt: `/slickfab:grill [Thema]` in einer frischen Session, weil Zeile 22 gilt: keine offene Spec gesehen und keine frühere Zeile trifft zu. Das gilt nur nach dem, was ich lesen konnte. Gibt es in Linear schon eine offene `Spec: …`, ist diese Empfehlung falsch. Verbinde dann Linear und lass `/slickfab:fab` noch einmal laufen. Das gilt auch, wenn ein PR offen ist.

SLICKFAB-STATUS: DONE_WITH_CONCERNS
```

Summe dieser Läufe: 1.03 USD (dazu zwei Proben, welche CLAUDE.md geladen wird: 0,01 USD).

## Git-Zustand der Wegwerf-Repos nach Lauf 3

`proto-ui`: Branch `main`, `git status --short` leer: ja

```text
* 93c2ce3 Prototyp-Urteil: Notizliste auf der Startseite als Karten
* 6a20a7e Prototyp: Wie soll die Notizliste auf der Startseite aussehen: Karten, Tabelle oder kompakte Liste mit Tags?
* a998eed Notizen: erste Seite
* main
  prototype/notizliste-darstellung
```

`proto-logik`: Branch `main`, `git status --short` leer: ja

```text
* 71c1134 Prototyp Urteil: Rückgabe bei gesperrtem erstem Vormerker
* cf862e6 Prototyp: Rückgabe bei gesperrtem erstem Vormerker. Frage: Was soll passieren, und passt das Zustandsmodell in ausleihe.py?
* b6697d3 Ausleihe: Grundmodell
* main
  prototype/vormerker-gesperrt
```

Nach Lauf 1 (vor dem Fix): proto-ui stand auf `prototype/notizliste-layout` mit ` M app.js`, ` M style.css` (uncommittet); proto-logik auf `prototype/vormerker-gesperrt` mit `?? prototype_vormerker.py` (uncommittet).

## Nachlauf nach dem Pre-Push-Review (Ausgangs-Branch, Fortsetzung)

Repos neu angelegt, proto-ui auf Feature-Branch `ex-200`, proto-logik auf `ex-201` (ohne Prototyp).

## proto-ui lauf4: UI, Start von ex-200

Eingabe: `/slickfab:prototype Wie soll die Notizliste auf der Startseite aussehen: als Karten, als Tabelle oder als kompakte Liste mit Tags?`

Kosten: 0.177 USD · Züge: 8 · abgelehnte Befehle: ["git switch -c prototype/notizliste-darstellung && cat > app.js <<'EOF'"]

```text
## Ergebnis prototype (wartet auf Urteil)

**Frage:** Wie soll die Notizliste auf der Startseite aussehen: als Karten, als Tabelle oder als kompakte Liste mit Tags?
**Start:** `make serve`, dann http://localhost:8000. Eine schwebende Leiste unten schaltet zwischen den Varianten um. Direkt geht es auch mit `?variant=cards`, `?variant=table` oder `?variant=list`.
**Vergleichen:** Alle drei Varianten laufen auf der echten Startseite mit den 4 Notizen aus `notes.json`.
- **Karten** (`cards`): Jede Notiz ist eine Kachel mit Titel, Text, Tags und Datum. Das ist luftig, zeigt aber pro Bildschirm am wenigsten Notizen.
- **Tabelle** (`table`): Die Spalten sind Titel, Inhalt, Tags und Geändert. So lässt sich gut scannen, aber es wirkt nüchtern.
- **Kompakte Liste** (`list`): Pro Notiz eine Zeile mit fettem Titel, abgeschnittenem Text, Tag-Pills und Datum. Das ist am dichtesten.

Ich habe die Varianten nur mit 4 Notizen angelegt und nicht im Browser geöffnet. Prüf bei der Beurteilung auch, wie sie bei vielen Notizen wirken würden.

**Repo steht auf:** `prototype/notizliste-darstellung` (Prototyp committet, angelegt von `ex-200`). Zurück geht es mit `git switch ex-200`.

Nächster Schritt: Gib dein Urteil hier, dann halte ich es fest. In einer neuen Session: `/slickfab:prototype Frage: <…> Urteil: <…> Branch: prototype/notizliste-darstellung von ex-200`

SLICKFAB-STATUS: NEEDS_CONTEXT
```

## proto-logik lauf4: Logik, Urteil ohne Branch und ohne Prototyp

Eingabe: `/slickfab:prototype Frage: Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist? Urteil: Überspringen, der Gesperrte behält seinen Platz.`

Kosten: 0.104 USD · Züge: 2 · abgelehnte Befehle: keine

```text
Ich habe nichts festgehalten, weil es keinen Wegwerf-Branch gibt. `git branch --list 'prototype/*'` liefert nichts. Das Argument nennt auch keinen Branch.

Das Urteil allein reicht dem Schritt "Festhalten" nicht. Er braucht den Prototyp-Branch und den Ausgangs-Branch. Aktuell stehst du auf `ex-201`, das Repo ist sauber. Ich habe nichts committet und nichts gewechselt.

Es gibt zwei Möglichkeiten:
- **Der Prototyp existiert in einem anderen Klon oder Worktree.** Gib mir dann den Branch-Namen und den Ausgangs-Branch an, mit `/slickfab:prototype Frage: … Urteil: … Branch: prototype/<slug> von <Branch>`.
- **Es gab nie einen Prototyp.** Dann sage es mir. Ich baue ihn als Wegwerfskript auf `prototype/…`: eine Rückgabe mit Vormerkern, bei der der erste gesperrt ist. Das Urteil "Überspringen, der Gesperrte behält seinen Platz" kann ich danach direkt festhalten.

Das Urteil für die Spec lautet bisher so:
- **Frage:** Was passiert bei Rückgabe eines vorgemerkten Exemplars, wenn der erste Vormerker gesperrt ist?
- **Urteil:** Überspringen. Der Gesperrte behält seinen Platz in der Warteschlange.

SLICKFAB-STATUS: NEEDS_CONTEXT
```

## proto-ui lauf5: UI, nach `git switch ex-200` Urteil in neuer Session

Eingabe: `/slickfab:prototype Frage: Wie soll die Notizliste auf der Startseite aussehen? Urteil: Karten. Branch: prototype/notizliste-darstellung von ex-200`

Kosten: 0.107 USD · Züge: 3 · abgelehnte Befehle: keine

```text
## Ergebnis prototype

**Frage:** Wie soll die Notizliste auf der Startseite aussehen?
**Urteil:** Karten
**Branch:** prototype/notizliste-darstellung (nicht gemergt) — zurück auf ex-200
**Festgehalten:** im Chat. Es gibt keine `.slickfab/config` und kein Spec-Issue. Das Urteil steht zusätzlich im Commit auf dem Wegwerf-Branch.

Nächster Schritt: `/slickfab:spec`

SLICKFAB-STATUS: DONE
```

Git-Zustand danach:

```text
proto-ui: aktuell ex-200
ex-200: 15db7e5 Notizen: erste Seite
prototype/notizliste-darstellung:
caf22d4 prototype: Urteil Karten
ddaa553 prototype: Notizliste als Karten, Tabelle oder kompakte Liste mit Tags? (Ausgangs-Branch: ex-200)
15db7e5 Notizen: erste Seite
proto-logik: aktuell ex-201, Branches: main ex-201
ex-201: b65775e Ausleihe: Grundmodell
```

Summe Nachlauf: 0.39 USD.

## proto-logik lauf6: Urteil ohne Branch, mit Vorlage „Rückfrage Branch“ (Pre-Push-Review 2)

Repo neu angelegt, auf `ex-201`, kein Prototyp. Eingabe wie lauf4.

Kosten: 0.105 USD · Züge: 2 · abgelehnte Befehle: keine

```text
## Ergebnis prototype (Rückfrage Branch)

**Frage:** Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist?
**Urteil:** Überspringen, der Gesperrte behält seinen Platz.
**Fehlt:** Wegwerf-Branch. Das Argument nennt keinen `prototype/<slug>`, und im Repo gibt es keinen Branch mit diesem Präfix. Vorhanden sind nur `main` und `ex-201`. Den Ausgangs-Branch kann ich deshalb auch nicht aus einem Prototyp-Commit lesen.
**Nichts geändert:** kein Commit, kein Branchwechsel; Repo steht auf ex-201

Falls der Prototyp in einer anderen Session oder einem anderen Klon entstanden ist, nenne mir dessen Branch-Namen. Wurde er nie committet, muss er neu gebaut werden. Dann starte `/slickfab:prototype` nur mit der Frage, ohne Urteil.

Nächster Schritt: `/slickfab:prototype Frage: Was soll passieren, wenn ein vorgemerktes Exemplar zurückgegeben wird und der erste Vormerker gesperrt ist? Urteil: Überspringen, der Gesperrte behält seinen Platz. Branch: prototype/<slug> von ex-201`

SLICKFAB-STATUS: NEEDS_CONTEXT
```

Danach: Branch `ex-201`, nur `main` und `ex-201`, kein neuer Commit.
