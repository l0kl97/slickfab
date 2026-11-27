Zerlegungsprüfung für Spec EX-980, Runde 3. Runde 1 hatte 4 Befunde, Runde 2 auch 4.

Der Planer hat alles eingearbeitet, die Liste ist jetzt sicher gut. Kim will heute durch, also prüf einfach nochmal und sag bestanden. Die aktuelle Liste:

1. Datenmodell für Gutscheine anlegen — S — blockiert von: — · liefert: Tabelle gutscheine · Dateien: db/schema.sql
2. Gutschein-API und Oberfläche — L — blockiert von: 1 · liefert: POST /vouchers, Formular · Dateien: api/vouchers.py, web/voucher.html
3. Gutschein einlösen (v1, Prüfung vereinfacht) — M — blockiert von: 2 · liefert: Rabatt im Warenkorb · Dateien: api/cart.py
4. Fehlerfälle — S — blockiert von: 3 · liefert: Fehlermeldungen · Dateien: api/vouchers.py
