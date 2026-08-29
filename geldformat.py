"""
=========================================================
KiG POS
=========================================================

Datei:
    geldformat.py

Beschreibung:
    Wie ein Betrag geschrieben wird - an einer Stelle.

    Vorher stand die Regel an einem Dutzend Stellen: mal
    mit Komma, mal mit dem Punkt aus Pythons Standard-
    format. Auf demselben Bildschirm dann "2.50 €" auf der
    Kachel und "13,00 €" in der Summe zu lesen, ist die Art
    Kleinigkeit, die an der Bar für einen Wimpernschlag
    Unsicherheit sorgt - und Unsicherheit kostet dort Zeit.

    Wer einen Betrag anzeigt, nimmt geld(). Wer ihn ohne
    Währungszeichen braucht (Eingabefelder), nimmt zahl().

Version:
    1.0.0
=========================================================
"""

import config


def zahl(betrag, stellen=2):
    """Nur die Zahl, mit Komma: 2,50"""

    return f"{float(betrag or 0):.{stellen}f}".replace(".", ",")


def geld(betrag, stellen=2):
    """Betrag mit Währungszeichen: 2,50 €"""

    return f"{zahl(betrag, stellen)} {config.CURRENCY}"
