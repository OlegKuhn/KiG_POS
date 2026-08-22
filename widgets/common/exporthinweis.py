"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/exporthinweis.py

Beschreibung:
    Rückmeldung nach einem Export.

    Bisher stand dort nur der Dateiname - und damit die
    Anschlussfrage: "Und wo liegt die jetzt?" Auf dem Tablet
    ist das keine rhetorische Frage, dort führt kein Weg am
    Ordner vorbei.

    Deshalb nennt der Hinweis beides: den Dateinamen in der
    ersten Zeile, den Ordner darunter. Zwei Zeilen, weil ein
    vollständiger Pfad in einer Zeile neben dem Export-Knopf
    keinen Platz hat.

    hinweisfeld_vorbereiten() lässt das Textfeld mitwachsen,
    damit die zweite Zeile nicht unter dem Rand verschwindet.

Version:
    1.0.0
=========================================================
"""

from pathlib import Path


def export_hinweis(pfad, was="Export erstellt"):
    """Zweizeilige Rückmeldung: Datei, darunter der Ordner."""

    pfad = Path(pfad)

    return f"{was}: {pfad.name}\nOrdner: {pfad.parent}"


def hinweisfeld_vorbereiten(label, mindesthoehe):
    """Lässt ein Hinweisfeld mit der Anzahl seiner Zeilen wachsen.

    Der übliche Weg (text_size = size) schneidet alles ab, was nicht
    in die eingestellte Höhe passt - bei einem zweizeiligen Hinweis
    also den Ordner. Hier wird stattdessen nur die Breite vorgegeben;
    die Höhe ergibt sich aus dem umbrochenen Text.
    """

    label.size_hint_y = None
    label.height = mindesthoehe

    def breite_uebernehmen(instanz, breite):
        instanz.text_size = (breite, None)

    def hoehe_anpassen(instanz, groesse):
        instanz.height = max(mindesthoehe, groesse[1])

    label.bind(width=breite_uebernehmen, texture_size=hoehe_anpassen)

    breite_uebernehmen(label, label.width)

    return label
