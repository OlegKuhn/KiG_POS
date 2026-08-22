"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/feldausrichtung.py

Beschreibung:
    Linksbündige Beschriftung für Felder.

    Eingabefelder schreiben von Haus aus links. Auswahlfelder
    (Spinner) und Felder, hinter denen ein Kalender oder der
    Nummernblock steckt, sind dagegen Schaltflächen - und die
    setzen ihren Text mittig. In einem Formular springt das
    Auge dadurch bei jeder Zeile an eine andere Stelle.

    links_ausrichten() rückt die Beschriftung solcher Felder
    an den linken Rand, mit demselben Innenabstand wie in den
    Eingabefeldern.

    Bewusst NICHT angewendet auf Kacheln (Startseite, Artikel
    an der Kasse) und auf Schaltflächen, die eine Aktion
    auslösen ("Speichern", "Abbrechen"): Dort ist mittig
    richtig.

Version:
    1.0.0
=========================================================
"""

from kivy.metrics import dp


# Derselbe Innenabstand wie in RoundedInput - so stehen Eingabe- und
# Auswahlfelder untereinander auf einer Linie.
RAND = 12


def links_ausrichten(widget, rand=RAND):
    """Stellt die Beschriftung eines Button-artigen Widgets links.

    halign allein genügt nicht: Ohne text_size füllt die Textur nur
    den Text selbst und wird mittig gesetzt. Erst mit einer text_size
    über die volle Feldbreite wirkt die Ausrichtung.

    Der Innenabstand schrumpft, wenn der Wert sonst nicht mehr in
    eine Zeile passt. Ohne das brach ein Datum in einer schmalen
    Spalte plötzlich um ("01.07.202" / "6") - vorher fiel das nicht
    auf, weil der Text ohne text_size einfach über den Rahmen
    hinauslief. Passt der Wert auch ohne Abstand nicht, wird er
    gekürzt statt umgebrochen: eine Zeile, die zur Hälfte unter dem
    Feldrand verschwindet, ist schlechter zu lesen als eine mit
    Auslassungspunkten.
    """

    widget.halign = "left"
    widget.valign = "middle"
    widget.shorten_from = "right"

    def anpassen(instanz, _wert=None):

        # Natürliche Breite messen: dafür die Begrenzung kurz
        # aufheben, sonst misst Kivy den bereits umgebrochenen Text.
        instanz.text_size = (None, None)
        instanz.shorten = False
        instanz.texture_update()

        noetig = instanz.texture_size[0]

        wirksamer_rand = min(
            dp(rand),
            max(0, (instanz.width - noetig) / 2),
        )

        instanz.shorten = noetig > instanz.width
        instanz.text_size = (
            max(0, instanz.width - 2 * wirksamer_rand),
            instanz.height,
        )

    widget.bind(size=anpassen, text=anpassen, font_size=anpassen)

    anpassen(widget)

    return widget
