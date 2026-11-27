---
name: grill
description: Verwenden, wenn ein Plan, eine Idee oder ein Feature-Wunsch vor der Spec auf offene Entscheidungen abgeklopft werden soll, oder wenn jemand „grill mich“, „frag mich aus“ oder „stress-test“ sagt.
argument-hint: "[Thema oder Plan]"
---

<!-- regel:einleitung -->
# grill: Befragung in Runden

Ziel: Am Ende ist keine Entscheidung mehr stillschweigend angenommen. Der Mensch trifft die Entscheidungen, die nur er treffen kann; alles andere klärst du selbst und legst es offen.

Antworte in der Sprache des Menschen.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Vor einer Spec, wenn ein Wunsch noch Lücken hat: für wen, wozu, woran man Erfolg erkennt, welche Grenze bindet.
- Wenn jemand einen Plan prüfen lassen will, bevor gebaut wird.
- Nicht für eindeutige Kleinaufgaben (Umbenennen, Tippfehler) und nicht ohne Menschen, der antwortet. Läufst du ohne Menschen (Autopilot, CI), melde die offenen Entscheidungen als Blocker, statt sie zu raten.
<!-- /regel:wann -->

## Ablauf

<!-- regel:lage-erkunden-bevor-du-fragst -->
### 1. Lage erkunden, bevor du fragst

Fakten holst du selbst, nie der Mensch. Alles, was im Repo oder in der Umgebung steht (Sprache, Frameworks, Ordnerstruktur, vorhandene Tests, bestehende Specs, `GLOSSARY.md`, `docs/adr/`, `CLAUDE.md`), schlägst du nach. Für mehr als ein paar Dateien schickst du einen Sub-Agent mit frischem Kontext los und lässt dir das Ergebnis kurz zusammenfassen. Fragen, die von einer laufenden Erkundung abhängen, warten; die übrigen stellst du schon.

Eine Frage, deren Antwort im Repo steht, ist ein Fehler. Steht die Antwort dort, nenne sie als Feststellung („Das Projekt nutzt Python 3.12, also …“) und frage nur, was daraus zu entscheiden bleibt.
<!-- /regel:lage-erkunden-bevor-du-fragst -->

<!-- regel:entscheidungsbaum-aufbauen -->
### 2. Entscheidungsbaum aufbauen

Jede Entscheidung kann weitere nach sich ziehen. Die **Front** sind alle Entscheidungen, deren Voraussetzungen geklärt sind. Hängt eine Frage von einer anderen ab, die in dieser Runde noch offen ist, gehört sie in eine spätere Runde.
<!-- /regel:entscheidungsbaum-aufbauen -->

<!-- regel:jede-frage-einordnen -->
### 3. Jede Frage einordnen

| Art | Beispiel | Wer entscheidet |
|---|---|---|
| **Produktfrage** (Nutzen, Zielgruppe, Umfang, Verhalten, Geschmack) | Wer darf exportieren? | Mensch |
| **Schwer umkehrbar** (Datenformat auf Platte/Leitung, öffentliche API, Datenbankschema, das andere lesen, Bindung an einen externen Dienst, Löschen von Daten) | Welches Format hat die Exportdatei, die Kunden archivieren? | Mensch |
| **Umkehrbar, technisch** (eine Datei, eine Funktion, austauschbar hinter stabiler Schnittstelle) | Welche interne Hilfsfunktion, welcher Variablenname? | du, mit Eintrag unter „Autonom entschieden“ |

Bist du unsicher, ob etwas schwer umkehrbar ist, und kannst keine konkrete Migration oder keinen konkreten gebrochenen Vertrag nennen, gilt es als umkehrbar. Wer alles zur Tür macht, erzeugt Fragenmüdigkeit.
<!-- /regel:jede-frage-einordnen -->

<!-- regel:eine-runde-stellen -->
### 4. Eine Runde stellen

Stelle die ganze Front auf einmal, nummeriert F1, F2, … Jede Frage hat eine Empfehlung und ist so formuliert, dass „ja“ die Empfehlung annimmt. Bei schwer umkehrbaren Fragen nennst du in einem Satz, was ein Rückweg kosten würde.

```
**F1 – <Titel>** <Frage, ggf. mit Optionen A/B/C>
→ Empfehlung: <deine Antwort, ein Satz warum>

**F2 – <Titel>** (schwer umkehrbar: <was ein Rückweg kostet>) <Frage>
→ Empfehlung: <…>
```

Danach wartest du auf die Antworten. Keine Obergrenze an Runden; die Runde ist so groß wie die Front.
<!-- /regel:eine-runde-stellen -->

<!-- regel:antworten-auswerten -->
### 5. Antworten auswerten

- „ja“, „passt“, „F1 ja“ nimmt die Empfehlung an.
- Eine eigene Antwort ersetzt die Empfehlung.
- **„egal“, „mach du“, „wie du meinst“, Schweigen zu einer Frage:**
  - Bei umkehrbaren technischen Fragen: entscheide selbst und trage es unter „Autonom entschieden“ ein.
  - Bei Produktfragen und schwer umkehrbaren Fragen ist das **keine Zustimmung**. Frage dieselbe Entscheidung in der nächsten Runde noch einmal, zugespitzt auf zwei konkrete Optionen mit je einer Folge, und warte. Geh nicht weiter, als hätte der Mensch zugestimmt.
- Jede Antwort verschiebt die Front: Neue Fragen werden frei, andere fallen weg. Berechne die Front neu und stelle die nächste Runde.
<!-- /regel:antworten-auswerten -->

<!-- regel:nebenbei-mitschreiben -->
### 6. Nebenbei mitschreiben

- **Glossar:** Taucht ein projektspezifischer Begriff auf oder werden zwei Wörter für dieselbe Sache benutzt, trage ihn sofort in `GLOSSARY.md` im Repo-Root ein (anlegen, falls nicht da): Begriff fett, ein bis zwei Sätze, was er ist, darunter `_Nicht:_` mit den verworfenen Synonymen. Allgemeine Programmierbegriffe gehören nicht hinein.
- **ADR:** Ein ADR ist fällig, wenn beides zutrifft: (1) Die Entscheidung ist schwer umkehrbar. (2) Ohne Begründung würde ein späterer Leser sie überraschend finden oder wieder aufrollen. Trifft beides zu, legst du den ADR an; trifft eins nicht zu, legst du keinen an. Das prüfst du für jede Entscheidung dieser Runde und für jede als Text übergebene frühere, die noch keinen ADR hat, nicht nach Gefühl. Der ADR liegt unter `docs/adr/NNNN-slug.md` (nächste freie Nummer, Ordner erst beim ersten ADR anlegen), ein Titel und ein bis drei Sätze: Lage, Entscheidung, Grund.

Beides ist umkehrbar und braucht keine Rückfrage.
<!-- /regel:nebenbei-mitschreiben -->

<!-- regel:abschluss -->
### 7. Abschluss

Fertig bist du, wenn die Front leer ist: jeder Ast besucht, nichts still angenommen, und du die nächsten Antworten des Menschen vorhersagen könntest. Dann fasst du zusammen (siehe Ergebnis) und fragst, ob das gemeinsame Verständnis stimmt. Erst nach einem klaren Ja ist der Schritt fertig. Du baust in diesem Schritt nichts.
<!-- /regel:abschluss -->

## Ergebnis

<!-- regel:ergebnis -->
Eine Zusammenfassung im Chat, in dieser Form:

```
## Ergebnis grill

**Entschieden vom Menschen**
- <Entscheidung> (F<n>)

**Autonom entschieden**
- <Entscheidung> — <warum> — umkehrbar, weil <…>
(oder: „keine“)

**Nicht im Umfang**
- <was ausdrücklich nicht gebaut wird>

**Geänderte Dateien:** GLOSSARY.md, docs/adr/… (oder „keine“)

Nächster Schritt: `/slickfab:spec`
```

Die Liste „Autonom entschieden“ steht immer da, auch wenn sie leer ist, damit der Mensch nichts Verborgenes übersieht.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:spec` — schreibt aus diesem Gespräch die Spec, ohne neu zu befragen. Sind Fragen offen geblieben, die man nicht erfragen kann (Aussehen, Bedienung), vorher `/slickfab:prototype`.
<!-- /regel:naechster-schritt -->
