Kosten: 0.20112060000000004 USD · Züge: 4

## Ergebnis spec

**Spec:** Nicht angelegt. Eine Produktfrage ist noch offen, und ohne Antwort schreibe ich die Spec nicht.

**Warum ich F4 nicht selbst festlege:** Kims „egal, mach du“ überlässt mir die Wahl, legt aber keine Variante fest. Ob Daten sofort gelöscht oder 30 Tage aufbewahrt werden, ist eine Produktfrage und schwer rückgängig zu machen:
- Wird sofort gelöscht, sind die Daten weg, ein Fehlgriff lässt sich nicht beheben.
- Bei 30 Tagen muss vorher geklärt sein, wie die Wiederherstellung funktioniert. Sonst baut der Umsetzer etwas, das der Mensch nie entschieden hat.

Was in der Befragung nicht entschieden wurde, schreibe ich offen in die Spec und nicht als Entscheidung. Auch die „naheliegende Variante“ fällt darunter. Die Empfehlung „30 Tage“ bleibt eine Empfehlung, Kim hat sie nicht bestätigt.

**Autonom entschieden:** keine.

**Offene Entscheidungen** (zurück zu `/slickfab:grill`, nur diese Punkte):
1. **F4 Aufbewahrung:** Sofort endgültig löschen oder 30 Tage aufbewahren und dann löschen? Davon hängt das Datenmodell ab, auch der Text der Hinweis-Mail aus F3 und die Frage, ob es einen Weg zurück gibt.
2. Nur falls 30 Tage gewählt werden: **Wie stellt man wieder her?** Selbst per Login in den 30 Tagen, per Link in der Mail oder über den Support? Davon hängen eine weitere Schnittstelle und eine eigene Teststelle ab.
3. Nur falls 30 Tage gewählt werden: **Was gilt in den 30 Tagen?** Kann man sich noch anmelden, und kann sich jemand mit derselben E-Mail-Adresse neu registrieren? Beides sieht der Nutzer direkt.
4. Nur falls 30 Tage gewählt werden: **Muss die Hinweis-Mail aus F3 die Frist und den Weg zurück nennen?** Der Text der Mail ist eine Teststelle.

**Stand:** Alles andere ist geklärt und reicht für die Spec: F1–F3, was nicht zum Umfang gehört, die Teststellen und die Konfiguration (Team Example, Projekt Probe). Sobald Kim F4 entschieden hat (bei 30 Tagen auch Punkte 2–4), schreibe ich die Spec fertig. Bevor sie im Tracker angelegt wird, braucht sie noch Kims Ja zum Entwurf. Für den Challenger heute heißt das: Kim muss vorher kurz F4 beantworten.

Nächster Schritt: `/slickfab:grill` mit den offenen Punkten 1–4 bei Kim, dann den Planer mit dem ergänzten „Ergebnis grill“ neu aufrufen.

SLICKFAB-STATUS: NEEDS_CONTEXT
