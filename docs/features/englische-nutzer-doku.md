# Englische Nutzer-Doku

**Status:** aktiv · **Stand:** 2026-11-28 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)

Nach der Englisch-Serie waren Schritte, Rollen, Tracker-Vertrag und READMEs englisch, aber die Doku, auf die die README verweist, war es nur teilweise: die Projektkonfiguration ganz deutsch, die Betriebsarten halb, und die Einrichtung des Autopiloten (Factory-Konfiguration) stand nur im deutschen Dossier. Wer slickfab einrichtet, landete genau dort. Wunsch: Nutzer-Doku vollständig englisch, mit englischen Dateinamen, alle Verweise ziehen mit. Die Feature-Dossiers bleiben deutsch, weil sie das Entwicklungsprotokoll sind und Fremden wenig bringen; das sagen beide READMEs in einem Satz.

## Entscheidungen

- **Dossiers bleiben deutsch** (Vorschlag aus dem Auftrag, vom Maintainer bestätigt). Übersetzen kostet viel und hilft Fremden wenig.
- **Recherche (`docs/research/`) zählt zum Entwicklungsprotokoll** und bleibt deutsch. Sie hält fest, woher Ideen kommen, nicht wie man slickfab benutzt.
- **Umbenennung statt Kopie:** aus `projektkonfiguration.md` wird `docs/project-config.md`, aus `betriebsarten.md` wird `docs/operating-modes.md` (per `git mv`, damit die Historie mitwandert). Keine Weiterleitungsdateien unter den alten Namen.
- **Factory-Konfiguration einmal, nicht zweimal:** Beispiel und Feldliste stehen nur noch in `docs/autopilot.md`; das Dossier `slickfab-dispatch.md` verweist darauf. Zwei Feldlisten wären auseinandergelaufen.
- **Vertragsblöcke unverändert:** Die Blöcke `<!-- vertrag:config-… -->` waren schon englisch und sind in alle Schritte kopiert. Nur Überschriften und Einleitung drumherum wurden übersetzt. Den Satz „alle nicht leeren `CHECK_*`“ im Block `config-slickrails` ändert ein eigenes Ticket (er gilt für die Schritte, ändert also alle Kopien und die eingefrorene Referenz).
- **Prüfbefehle der Laufzeit ausdrücklich:** `docs/project-config.md` sagt außerhalb der Vertragsblöcke, dass `slickfab-worktree` (Baseline, Post-Merge-Prüfung) nur `CHECK_TYPECHECK` und `CHECK_TEST` aus `.slickrails/config.sh` liest. Der Code bestätigt das (`read_checks`).
- **Datierte Historie in Dossiers bleibt wörtlich:** Einträge `- JJJJ-MM-TT: …` nennen den Dateinamen von damals; der Test lässt sie aus. Alle anderen Stellen in Dossiers zeigen auf die neuen Namen.
- **Sprachprüfung grob, aber mechanisch:** Der Test sucht in `docs/*.md` (ohne Unterordner) häufige deutsche Funktionswörter außerhalb von Code. Das fängt einen deutschen Absatz, nicht jedes einzelne Wort.

## Wo es lebt

- `docs/project-config.md`: Format und Regeln von `.slickfab/config` (Quelle der Vertragsblöcke `config-*`).
- `docs/operating-modes.md`: Betriebsarten, Einrichtung, Schritte, slickrails.
- `docs/autopilot.md`: Befehle des Dispatchers, Factory-Konfiguration mit allen Feldern, Ablage.
- `README.md`, `README.de.md`: Hinweis „nur das Entwicklungsprotokoll ist deutsch“, Verweise auf die neuen Dateien.
- `tests/test_user_docs.py`: alte Dateinamen, Sprache, Schlüssel gegen den Code, README-Hinweis.
- Mitgezogen: `tracker/linear.md`, alle `skills/*/SKILL.md` (Block `vertrag-quelle`), `tests/golden/rules.md`, `tests/rules_golden.py`, `tests/test_contract_blocks.py`, `tests/check_fab.py` und die Tests, die die Dateien beim Namen lesen.

## So testet man es

1. `python3 -m unittest discover -s tests -p 'test_user_docs.py'`: neue Dateien da, alte weg, kein Verweis auf alte Namen, Nutzer-Doku englisch, jeder Schlüssel aus `load_config` in `docs/autopilot.md`, jeder Schlüssel aus `test_repo_config.KNOWN` in `docs/project-config.md`, READMEs mit dem neuen Hinweis.
2. `python3 tests/check_fab.py` und `python3 tests/rules_golden.py`: Wegweiser und eingefrorene Regeln grün.
3. `sh tests/run.sh`: ganze Suite.

## Grenzen & offene Punkte

- Die Schlüssel der Factory-Konfiguration liest der Test per `ast` aus `load_config`. Liest der Dispatcher einen Schlüssel künftig außerhalb von `load_config`, sieht der Test ihn nicht.
- Die Sprachprüfung kennt nur eine Handvoll deutscher Wörter.

## Historie

- 2026-11-28: angelegt
