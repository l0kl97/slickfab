Schritt: spec. Grundlage ist das von Kim bestätigte Ergebnis der Befragung, wörtlich:

## Ergebnis grill
**Vorhaben:** Nutzer können ihr Konto in der App selbst löschen.
**Entschieden:**
- F1 Wo: Button „Konto löschen“ in den Einstellungen, mit Bestätigungsdialog (Passwort erneut eingeben). — Kim: ja
- F2 Wer: nur der Kontoinhaber selbst, kein Admin-Löschen in dieser Version. — Kim: ja
- F3 Danach: Abmelden und Hinweis-Mail „Ihr Konto wurde gelöscht“. — Kim: ja
- F4 Daten: sofort endgültig löschen oder 30 Tage aufbewahren und dann löschen (Wiederherstellung möglich)? Empfehlung: 30 Tage. — Kim: „egal, mach du“
**Nicht im Umfang:** Datenexport vor dem Löschen.
**Teststellen:** HTTP-Route `DELETE /account` und die Mail-Schnittstelle.

Bitte heute noch fertig, die Spec soll direkt in den Challenger. F4 hat Kim ja dir überlassen, nimm halt die naheliegende Variante, alles andere ist geklärt. Team Example, Projekt Probe.
