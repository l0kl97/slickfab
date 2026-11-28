# Öffentliche Bereinigung

**Status:** aktiv · **Stand:** 2026-11-27 · **Gebaut von:** Claude Code

## Auftrag (Alltagssprache)
slickfab soll öffentlich werden. Vorher kommt alles Private aus dem Arbeitsstand: Name und Adressen des Maintainers, Werte seines Linear-Teams und -Projekts, Ticket-IDs des privaten Trackers, private Pfade und Repos, interne Terminals und Projekte sowie interne Abläufe aus den Dossiers. Linear bleibt der unterstützte Tracker; raus kommen nur die konkreten privaten Werte, Beispiele werden neutral (`Team Example`, `example@example.com`). Ein Test soll dafür sorgen, dass nichts Privates zurückkommt.

## Entscheidungen
- **Ein Test über alle getrackten Dateien** (`tests/test_public_scrub.py`): `git ls-files`, jede Zeile und jeder Dateiname gegen eine Liste privater Muster, Groß- und Kleinschreibung egal. Die Muster sind so geschrieben, dass die Testdatei sich selbst nicht findet; so braucht sie keine eigene Ausnahme.
- **Ausnahme nur für den Rechteinhaber:** `LICENSE` und `NOTICE` dürfen seinen Namen tragen, alle anderen Muster gelten auch dort.
- **README ohne Ausnahme:** Die README bereinigte ein eigenes, parallel laufendes Paket (öffentlich machen 2/3); bis dahin war sie per `PENDING_README` ausgenommen. Seit dieses Paket gemergt ist, ist die Ausnahme gestrichen: `README.md` und `README.de.md` werden geprüft wie jede Datei.
- **Ticket-IDs ersatzlos:** Verweise in Prosa und Kommentaren fallen weg, der Satz wird so umgestellt, dass er ohne ID trägt („inzwischen“, „im Pre-Push-Review“). Wo eine ID ein Wert ist (Testdaten, Pressure-Läufe, Beispiele in Doku und Schritten), steht eine Beispiel-ID `EX-<n>`. Review-Terminals (`rev-<n>`) tragen die Ticketnummer im Namen und heißen jetzt nur „Review“.
- **Person in Szenarien und Testdaten:** Der Mensch, für den gearbeitet wird, heißt dort „Kim“, damit Sätze und Zitate grammatisch bleiben. In Dossiers und Code heißt er „der Maintainer“ oder „der Mensch“, je nach Rolle im Satz.
- **Pressure-Läufe einheitlich bereinigt:** Transkripte, Befehle, Ergebnisse, Bewertungen, Szenarien, Fake-Tracker (`fake_linear_mcp.py` vergibt jetzt `EX-<n>`) und die Kontroll-Vorlagen mit denselben Ersetzungen, damit jedes Zitat aus einer Bewertung wörtlich im Lauf steht (`check_pressure` prüft das). Die Kontroll-Vorlagen weichen dadurch vom Original ab; `tests/pressure/kontrolle/README.md` nennt beide Prüfsummen.
- **`docs/plan.md` entfernt:** Es war ein internes Planungsdokument (private Pfade, Projektreihenfolge, Rollout auf private Repos). Was davon fachlich gilt, steht schon in `docs/operating-modes.md` und den Dossiers. Ein neutrales Design-Dokument hätte nur diese Texte doppelt geführt.
- **Dispatcher-Standardpfad:** `slickfab-dispatch` liest ohne `--config` und ohne `SLICKFAB_FACTORY` jetzt `~/.config/slickfab/factory.json`. Der alte Standard zeigte in einen privaten Ordner.
- **`.slickfab/config` des Repos:** Team per Linear-Kürzel statt Personenname, Projekt mit dem Namen des Produkts. So läuft der eigene Prozess weiter, ohne dass ein Name im Repo steht. Verworfen: `Example` (der eigene Prozess fände kein Team mehr) und die Datei aus dem Repo nehmen (die Projektkonfiguration ist laut `docs/project-config.md` eingecheckt).
- **Plugin-Manifeste:** Autor und Owner heißen „slickfab maintainers“.
- **Regeltexte unverändert:** In Schritten, Rollen und Vertrag änderten sich nur Beispielwerte (`TRACKER_TEAM`, `TRACKER_PROJECT`, eine Beispiel-ID in der Beschreibung von `implement`). Referenz neu per `python3 tests/rules_golden.py --update`, Vorlagen per `runtime/herdr/gen-templates`.

## Wo es lebt
- `tests/test_public_scrub.py`: Muster, Ausnahme für den Rechteinhaber, Scanner und seine Fehlerfall-Tests.
- `tests/pressure/kontrolle/README.md`: Abweichungen der Kontroll-Vorlagen vom Original, Prüfsummen.
- `runtime/herdr/slickfab-dispatch` (`DEFAULT_CONFIG`) und `tests/test_dispatch_tick.py` (`Config`): Standardpfad der Factory-Konfiguration.

## So testet man es
1. `python3 -m unittest tests.test_public_scrub`: grün, wenn keine getrackte Datei ein privates Muster enthält; die Meldung nennt Datei, Zeile und Muster.
2. Gegenprobe: eine Ticket-ID des privaten Trackers oder den Namen des Maintainers in eine beliebige getrackte Datei schreiben, Test wird rot.
3. `sh tests/run.sh`: ganze Suite, dazu `check_pressure` für die bereinigten Läufe.

## Grenzen & offene Punkte
- Der Test kennt nur die Muster seiner Liste. Ein neuer privater Wert (neues internes Projekt, neue Terminal-Adresse) muss dort ergänzt werden.
- Der GitHub-Login des Maintainers steht weiter in Testdaten (`pr_comment_authors`) und in der Repo-Adresse der Manifeste; beides ändert sich mit dem Repo-Umzug.
- Die Git-Historie enthält die alten Stände weiter; das betrifft den Umzug des Repos, nicht diesen Stand.

## Historie
- 2026-11-27: angelegt
- 2026-11-27 (Review PR #27, Rework 1): Die README-Ausnahme war nur im Code auf `README.md` im Wurzelordner begrenzt; eine Mutation auf den Basisnamen blieb grün, damit wäre jede README in Unterordnern ungeprüft geblieben → Test `test_readme_exception_only_for_root_readme` (README in `docs/` und `tests/pressure/` muss treffen). Dazu zwei Satzreste der Ersetzung geglättet (`role_bash_guard.py`, `fab-wegweiser.md`).
- 2026-11-27 (öffentlich machen 2/3): README englisch und deutsch bereinigt, Ausnahme `PENDING_README` samt `stale_exceptions` und den zwei Tests, die nur die Ausnahme prüften, gestrichen. `test_readme_exception_only_for_root_readme` heißt jetzt `test_root_readmes_are_scanned_like_any_file` und verlangt Treffer auch in `README.md` und `README.de.md` im Wurzelordner.
