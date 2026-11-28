# Regelreferenz: alle Schritte eingefroren

**Status:** aktiv · **Stand:** 2026-11-24 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

„Es gibt ein einziges Werkzeug, das die Regelabschnitte aller Schritte einfriert: `tests/rules_golden.py`. Das parallel entstandene `tests/regelreferenz.py` mit `tests/regelreferenz/` verschwindet. Alle Schritte, die Regeln enthalten, sind markiert und eingefroren.“ Dazu die Lücke aus den Re-Reviews von PR #6 und #7: Außerhalb der Marker überlebten Mutationen, darunter eine neu eingefügte Ausnahme („Ticket verlangt es = Freigabe“). „Künftig darf in den Regel-Abschnitten eines Schritts (mindestens `## Ablauf`) kein Text außerhalb der Marker stehen, und die Prüfung erzwingt das.“ Regeltexte ändern sich dabei nicht.

## Entscheidungen

- **Ein Werkzeug, eine Referenz.** `tests/rules_golden.py` findet alle `skills/*/SKILL.md` selbst (neue Schritte werden mitgeprüft) und schreibt eine Datei `tests/golden/rules.md` (vorher `build-steps-rules.md`; der Name passte nicht mehr). Ein Marker-Format: `<!-- regel:NAME -->`. Die alten `regeln:`-Marker in review, verify und retro sind umbenannt, ihr Text ist unverändert.
- **Kein freier Text im ganzen Schritt, nicht nur im Ablauf.** Außerhalb der Regelblöcke stehen nur Frontmatter, Leerzeilen und die festen Überschriften `## Wann`, `## Ablauf`, `## Vertrag`, `## Ergebnis`, `## Nächster Schritt`. Warum mehr als der Ablauf: Auch „Wann“ („Nicht ohne Ticket“), Einleitung („du mergst nicht“) und „Nächster Schritt“ (frische Session) tragen Stopp- und Abschlussregeln. Vorbild ist `tests/check_roles.py`: Dort sind außerhalb der Blöcke nur feste Überschriften erlaubt.
- **Unterabschnitte des Ablaufs samt Überschrift im Block.** Eine `### `-Überschrift außerhalb der Marker ließe sich zu „### 5. Stopp-Liste (entfällt, wenn das Ticket es verlangt)“ mutieren. Deshalb liegt jede Überschrift im Block ihres Unterabschnitts. Bestehende Blöcke wurden dafür nur erweitert, nie geteilt; ihre Namen bleiben.
- **Vertrag:** Die Vertragsblöcke hält `test_contract_blocks` gleich der Quelle. Die Blöcke der Quellen (`tracker/linear.md`, `docs/project-config.md`) stehen zusätzlich ganz in der Referenz (Einträge `vertrag:NAME` je Quelle); eine Schwächung, die gleichmäßig in Quelle und alle Kopien wandert, wird so rot. Dazwischen sind nur `### `-Überschriften erlaubt; der Einleitungssatz („es gilt genau so“) steht im Block `vertrag-quelle`. Das kam aus der eigenen Mutationsprobe (siehe Historie).
- **Frontmatter und Gliederung sind mit eingefroren** (Einträge `frontmatter` und `gliederung` je Schritt). Die Gliederung hält Überschriften und Blockanfänge (`[regel:NAME]`, `[vertrag:NAME]`) in Datei-Reihenfolge fest. Sonst gäbe ein eingeschobenes zweites `## Vertrag` den Text danach frei. Außerdem könnte eine feste Überschrift an einem Block vorbeiwandern, und eine Abschlussregel stünde dann im Vertrag (Review PR #12, A1). Die `description` steuert, wann ein Schritt startet.
- **Verworfen:** die ganze SKILL.md als eine Referenz. Dann wären die Vertragsblöcke doppelt eingefroren, und ein Diff sagt nicht mehr, welcher Abschnitt sich geändert hat.

## Wo es lebt

- `tests/rules_golden.py`: liest Marker (Codeblöcke ausgenommen), prüft freien Text (`free_text_problems`), sammelt die Regionen (`skill_regions`, Agent-Rollen wie bisher) und vergleicht mit der Referenz. `--update` schreibt sie neu.
- `tests/golden/rules.md`: die Referenz, erzeugt, nicht von Hand bearbeiten.
- `tests/test_rule_golden.py`: Pflichtabschnitte je Schritt (`REQUIRED`), Gleichheit mit der Referenz, Fehlerfälle der Markerprüfung, Freitext-Prüfung an einem kleinen Beispiel-Schritt.
- `skills/*/SKILL.md`: die Marker.

## So testet man es

1. `python3 tests/rules_golden.py` → „Regelabschnitte gleich der Referenz (182)“.
2. Einen Satz in einem Regelblock ändern oder eine Zeile irgendwo außerhalb der Marker einfügen (außer Leerzeilen) → Exit 1 mit Diff bzw. `freier Text außerhalb der Regel-Marker (## Ablauf): „…“`.
3. Gewollte Regeländerung: SKILL.md ändern, `python3 tests/rules_golden.py --update`, Referenz mitcommitten. Im Review die Referenzänderung als Regeländerung lesen.
4. Ganze Suite: `sh tests/run.sh`.

**Beleg, dass nichts verloren ging:** Alle 74 bisher eingefrorenen Abschnitte (63 aus `build-steps-rules.md`, davon 21 Schritt- und 42 Rollen-Abschnitte, 11 aus `tests/regelreferenz/`, Stand `main` 7f46286) stehen weiter in der Referenz, unter demselben Namen. 54 sind unverändert, 20 wurden um bisher freie Zeilen erweitert: 18 um ihre `### `-Überschrift, `review/grenzen` und `verify/grenzen` um die `# `-Titelzeile und den Satz „Antworte in der Sprache des Menschen …“. Der Diff der SKILL.md gegen `main` enthält nur Markerzeilen (0 andere Zeilen).

**Mutationsprobe** (im Worktree, an den echten SKILL.md, jede Mutation einzeln, danach zurückgesetzt; gefangen heißt: `rules_golden.py` oder `test_contract_blocks` rot):

- Erster Lauf: 40 Mutationen über alle 12 Schritte (Stopp-, Freigabe-, Urteils- und Abschlussregeln in Markern, Frontmatter, entfernter Marker, eingefügte Zeilen und Überschriften außerhalb der Marker in Einleitung, Wann, Ablauf, Ergebnis, Nächster Schritt, dazu Vertrag). **37 rot, 3 überlebt**, alle drei im freien Text unter `## Vertrag`: „es gilt genau so“ → „…, außer das Ticket sagt etwas anderes“, eine eingefügte Zeile „Für debug gilt der Zugang-Vertrag nicht.“ und ein eingefügter Codeblock vor `## Ergebnis` in handoff.
- Nach dem Fix (Vertrag wie oben): dieselben 40 plus 2 weitere im Vertrag (geänderte `### `-Überschrift, Zeile nach einem Vertragsblock) → **42 von 42 rot**, 0 überlebt.
- Das Pre-Push-Review fand danach trotzdem einen Weg, den meine Liste nicht hatte: eine Ausnahme in einem selbst gesetzten Vertragsblock (siehe Historie). Nach dem Fix: 4 von 4 Szenarien des Reviews rot.

## Grenzen & offene Punkte

- Eingefroren heißt nicht richtig: Die Referenz hält fest, was dasteht. Ob die Schritte sich danach verhalten, prüfen die Pressure-Szenarien.
- Die Probe deckt die Mutationen ab, die ich gewählt habe. Weil jetzt die ganze SKILL.md außer Leerzeilen unter Referenz oder Vertragstest steht, sollte auch eine fremde Probe nichts finden. Eine Ausnahme ist Weißraum: Leerzeilen außerhalb der Blöcke sind frei, das ändert keine Regel.
- Andere Dateien in `skills/*/` (z. B. `docs-lookup/lookup.py`) sind Code und haben ihre eigenen Tests.

## Historie

- 2026-11-24: angelegt. Werkzeug vereinheitlicht, alle 12 Schritte markiert, Freitext-Prüfung.
- 2026-11-24 (eigene Mutationsprobe): 3 von 40 überlebten im freien Text unter `## Vertrag`. Ursache: Die erste Fassung ließ den Vertrag-Abschnitt ganz frei, weil die Blöcke dort schon einen Gleichheitstest haben; Text zwischen den Blöcken deckt der aber nicht ab. Fix: Im Vertrag sind außerhalb der Blöcke nur `### `-Überschriften erlaubt (mit eingefroren), der Einleitungssatz steht im Block `vertrag-quelle`. Tests dazu vorher rot.
- 2026-11-24 (Pre-Push-Review): Ein `<!-- vertrag:NAME -->`-Block an beliebiger Stelle (etwa im Ablauf, mit Ziffern im Namen, mit falschem Schlussnamen oder nie geschlossen) gab den Text darin frei, und `test_contract_blocks` sah ihn nicht. Ursache: Die Freitext-Prüfung nahm jeden Vertragsmarker als Block an. Fix: Vertragsblöcke gelten nur unter `## Vertrag`, mit dem Namensmuster des Vertragstests und paarig; sonst ist der Marker ein Fund und der Inhalt freier Text. Vier Tests vorher rot, die vier Szenarien des Reviews an `implement` danach 4 von 4 rot.
- 2026-11-24 (Pre-Push-Review, Runde 2): Ein Vertragsmarker mit Leerzeichen davor oder danach galt bei der Freitext-Prüfung als Block, `test_contract_blocks` erkennt ihn aber nicht. Der Text darin blieb also frei und ungeprüft. Ursache: Der Marker wurde vor dem Vergleich getrimmt. Fix: Der Vergleich läuft gegen die ungekürzte Zeile, sonst gibt es einen Fund. Ein Test mit drei Fällen war vorher rot, das Szenario des Reviews an `implement` danach rot.
- 2026-11-24 (Pre-Push-Review, Runde 3): Dieselbe Klasse wie in Runde 2. `str.splitlines` trennt auch an \x0c, \u2028 und weiteren Zeichen, der Vertragstest nur an \n. Ein Marker vor einem solchen Zeichen war für die Freitext-Prüfung ein Block, für den Vertragstest aber unsichtbar. Fix: `outline()` trennt nur an \n, und jedes andere Zeilentrennzeichen im Schritt ist ein Fund (heute in keinem Schritt vorhanden). Der Test mit sechs Zeichen war vorher rot, das Szenario des Reviews an `implement` danach rot.
- 2026-11-24 (Review PR #12): A1: Eine feste `##`-Überschrift ließ sich an einem Regelblock vorbeischieben (z. B. `## Vertrag` vor `### 8. Abschluss`), und die Prüfung blieb grün. Ursache: Eingefroren war nur die Folge der Überschriften untereinander, nicht ihre Lage zwischen den Blöcken. Fix: Die Gliederung (`gliederung` statt `ueberschriften`) enthält auch die Blockanfänge. Zwei Tests waren vorher rot. Probe an den echten Dateien: Jede feste Überschrift wanderte in jedem Schritt einen Block nach vorn und einen nach hinten, dazu kam „`## Ablauf` hinter die Stopp-Liste“. Ergebnis: 117 von 117 rot. A2: Die Aufteilung im Beleg war falsch (59 + 15). Richtig ist 63 + 11, die Summe 74 stimmte.
- 2026-11-27 (Review der englischen Übersetzung): 12 Schwächungen von Vertragsregeln überlebten, wenn man sie gleichmäßig in Quelle und alle Kopien einbaute (etwa „always a human gate, never auto-merge“ → „usually a human gate“, „with no text after it“ gestrichen, Gruppe erlaubt „several“). Ursache: Die Referenz kannte vom Vertrag nur die Blocknamen in der Gliederung, der Gleichheitstest vergleicht nur Kopie mit Quelle, Einzelanker decken nur ihre Sätze. Fix: `rules_golden.py` friert die Quellblöcke ganz ein; `ContractBlocksFrozenTest` und die Pflichtliste vorher rot, die 12 Mutationen danach 12 von 12 rot.
