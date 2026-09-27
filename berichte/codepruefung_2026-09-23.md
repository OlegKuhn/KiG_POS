# Codeprüfung KiG POS – 23.09.2026

Geprüft wurden insbesondere Zahlungsabschluss, Lagerabzug, Löschung von
Statistikpositionen, Event-Zuordnung und Statistik/Export. Dies ist keine
vollständige Prüfung aller Bedienwege oder ein Android-Gerätetest.

## Bestehende Befunde (noch nicht korrigiert)

1. **Hohe Priorität: Verkaufsabschluss nicht atomar.**
   `screens/cash_screen.py`, `payment_confirmed`, ruft erst `save_paid_sale`
   und danach `reduce_stock_for_paid_cart` auf. `database.py`, `save_sale`,
   bestätigt seine Transaktion selbst; die einzelnen Lagerbewegungen werden
   danach gespeichert. Schlägt ein späterer Lagerzugriff fehl, bleibt ein
   bezahlter Bon mit fehlenden/teilweisen Bestandsbewegungen zurück. Der
   Warenkorb ist dann noch vorhanden, ein erneuter Abschluss kann doppelt
   zählen. Abhilfe: Bon und sämtliche Bestandsbewegungen in einer gemeinsamen
   Transaktion speichern und den Abschluss gegen Wiederholung absichern.

2. **Hohe Priorität: 0-Euro-Restbon wird fälschlich gelöscht.**
   `database.py`, `delete_sale_item`, entscheidet mit `if total == 0`, ob
   der Bon leer ist. Nach dem Entfernen einer bezahlten Position können aber
   noch kostenlose Positionen oder sich aufhebende Beträge vorhanden sein.
   Das Löschen des Bons scheitert dann bei aktivem Fremdschlüsselschutz;
   ohne diesen Schutz bleiben verwaiste Positionen. Entscheidend muss die
   Anzahl der verbleibenden Positionen sein, nicht deren Gesamtwert.

3. **Hohe Priorität: Einzelauswahl einer Stornoposition löscht zu viel.**
   `database.py`, `delete_sale_units`, rechnet `row['quantity'] - quantity`
   und entfernt bei einem Ergebnis <= 0 die komplette Position. Bei einer
   Stornomenge von -5 und einer ausgewählten Einheit ergibt das -6: Alle
   fünf stornierten Einheiten werden entfernt, obwohl nur eine gewählt war.
   Die Reduktion muss die Richtung des ursprünglichen Vorzeichens beachten.

4. **Mittlere Priorität: Event-Zuordnung ist bei mehreren Events mehrdeutig.**
   `database.py`, `get_event_for_date`, nimmt mit `ORDER BY id LIMIT 1`
   stets das zuerst angelegte Event mit identischem Startdatum. Mehrere
   Events am selben Tag können so keine getrennten Kassenumsätze erhalten.
   Ein mehrtägiges Event wird an Folgetagen ebenfalls nicht gefunden.
   Eine explizite Event-Auswahl in der Kasse wäre eindeutig.

## Umgesetzte Erweiterung

- Statistik → Manuelle Buchungen: Einnahme/Ausgabe, positiver Eurobetrag,
  Bezeichnung, Belegnummer, Geschäftstag und optionales Kalender-Event.
- Nachträgliches Bearbeiten und Entfernen mit Bestätigung.
- Beträge werden als ganze Cent gespeichert. Ungültige Daten, nicht endliche
  Beträge, negative Beträge und mehr als zwei Nachkommastellen werden abgewiesen.
- Datum ist ausdrücklich der Geschäftstag; es wird nicht durch eine künstliche
  Uhrzeit auf den Vortag verschoben.
- Einnahmen/Ausgaben/Ergebnis enthalten die manuellen Beträge. Verkaufszahlen,
  Topseller, Bestände, Kassenbuch und Barumsatz der Kassenverkäufe bleiben davon
  unabhängig. Ein Artikelkategoriefilter schließt manuelle Buchungen aus, da
  diese keiner Artikelkategorie angehören. Beim Öffnen der manuellen Buchungen
  wird die Kategorieauswahl deshalb auf „Alle Kategorien“ gestellt.
- Excel enthält ein separates Buchungsblatt, PDF eine Buchungstabelle; auch
  reine manuelle Buchungen ohne Artikelverkäufe sind exportierbar.
- Neue Buchungen und spätere Korrekturen sind in die Geräte-Zusammenführung
  integriert. Korrekturen nutzen den Änderungszeitpunkt (lokale Gerätezeit).

Hinweis zur Auswertung: Die bisherigen Ausgaben sind kalkulierter Wareneinsatz
der verkauften Artikel. Eine zusätzliche Einkaufsrechnung für genau dieselbe
Ware darf nicht nochmals als Aufwand gerechnet werden. Sponsoring, Raummiete
und andere zusätzliche Beträge können unabhängig davon erfasst werden.

## Prüfung

- 119 Python-Projektdateien syntaktisch geprüft.
- Isolierte Datenbanktests für Validierung, Datum/Event-Filter, Summen,
  Bearbeitung und Entfernung bestanden.
- Excel- und PDF-Ausgabe mit ausschließlich manuellen Buchungen erfolgreich.
- Kivy-Dialog mit Testdaten konstruiert; keine produktiven Vereinsdaten geöffnet.
- Kein vollständiger Touch-/Android-Test; keine Fehlerfreiheit des Gesamtprojekts zugesichert.
