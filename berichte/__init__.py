"""
=========================================================
KiG POS
=========================================================

Paket:
    berichte

Beschreibung:
    Alles, was das Programm zum Ausdrucken und Weitergeben
    schreibt: Excel-Mappen und PDF-Berichte.

        excel_layout.py      Kopf mit Logo, Überschriften und
                             Tabellen für jede Excel-Ausgabe
        pdf_bericht.py       PDF-Seiten mit Kopf, Tabellen und
                             Diagrammen
        statistik_bericht.py die Verkaufsstatistik als Excel
                             und als PDF

    Alle Ausgaben sehen gleich aus: oben das Vereinslogo, der
    Titel und wofür die Zahlen gelten, darunter Abschnitte mit
    orangefarbenen Überschriften und Tabellen mit Kopfzeile.
    Gedruckt wird auf weißes Papier - deshalb gilt hier immer
    die helle Farbgebung, auch wenn das Programm dunkel läuft.

    Die PDFs entstehen mit Pillow, nicht mit reportlab: Pillow
    ist auch in der Android-Fassung dabei, reportlab nicht.
=========================================================
"""
