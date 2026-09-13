"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/kig_bildknopf.py

Beschreibung:
    Schaltflächen, die ihr Sinnbild tragen statt es zu
    beschriften.

    Drei Handgriffe wiederholen sich durch das ganze
    Programm - löschen, bearbeiten, neu. Ausgeschrieben
    belegten sie in jeder Zeile Platz ("Bearbeiten" braucht
    100 dp) und mussten auf dem Telefon irgendwann
    weichen. Als Bild sind sie überall gleich groß und
    sofort zu erkennen:

        assets/icons/recycle-bin.png    löschen, entfernen
        assets/icons/edit.png           bearbeiten
        assets/icons/plus.png           neu, hinzufügen
        assets/icons/save.png           speichern

    Die Bilder werden wie auf der Startseite gezeichnet
    (schwarze Linien auf durchsichtigem Grund) und deshalb
    NICHT eingefärbt: Kivy multipliziert die Farbe auf die
    Bildpunkte, und Schwarz bleibt dabei schwarz.

    Wo der Griff gefährlich ist, sagt das der Hintergrund
    (ERROR_LIGHT), nicht die Farbe des Bildes.

Version:
    1.0.0
=========================================================
"""

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.button import Button

import config
import theme


def _passend(dunkel, hell):
    """Im Dunkelmodus die helle Fassung - wie beim Vereinslogo
    (siehe config.LOGO_PATH_DARK)."""

    if theme.CURRENT_MODE == "dark" and hell.exists():
        return str(hell)

    return str(dunkel)


def loeschbild():
    return _passend(config.ICON_DELETE, config.ICON_DELETE_HELL)


def bearbeitenbild():
    return _passend(config.ICON_EDIT, config.ICON_EDIT_HELL)


def neubild():
    return _passend(config.ICON_NEW, config.ICON_NEW_HELL)


def speicherbild():
    """Immer die helle Fassung: Speichern steht auf Orange - in beiden
    Farbmodi. Weiss darauf ist so gut zu lesen wie die weisse Schrift,
    die dort vorher stand."""

    if config.ICON_SAVE_HELL.exists():
        return str(config.ICON_SAVE_HELL)

    return str(config.ICON_SAVE)


# Einmal geladen, überall benutzt: Ein Bild je Schaltfläche neu von
# der Platte zu holen kostet in einer Liste mit 40 Artikeln spürbar
# Zeit - und dieselbe Textur zu teilen spart zudem Grafikspeicher.
_texturen = {}


def textur(pfad):

    if pfad not in _texturen:
        _texturen[pfad] = CoreImage(pfad, mipmap=True).texture

    return _texturen[pfad]


class KiGBildButton(Button):
    """Schaltfläche mit Bild.

    Ohne Text sitzt das Bild in der Mitte, mit Text links daneben -
    genau wie bei den gezeichneten Symbolen (siehe
    widgets/common/kig_symbol.py).
    """

    BILD_GROESSE = 26
    BILD_GROESSE_SCHMAL = 22

    def __init__(
            self,
            bild=None,
            groesse=None,
            gefaehrlich=False,
            **kwargs
    ):

        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault(
            "background_color",
            theme.ERROR_LIGHT if gefaehrlich else theme.SURFACE,
        )
        kwargs.setdefault("color", theme.TEXT_PRIMARY)
        kwargs.setdefault("font_size", "15sp")

        super().__init__(**kwargs)

        self.bild = bild or loeschbild()

        self.bild_groesse = groesse or (
            self.BILD_GROESSE_SCHMAL if theme.is_narrow()
            else self.BILD_GROESSE
        )

        # Erst im naechsten Bild zeichnen, nicht bei jedem Zwischenschritt
        # des Layouts - dieselbe Lehre wie bei den gezeichneten Symbolen
        # (siehe KiGSymbol). Nachgemessen: Im Kategorienfilter stand das
        # Plus 14 Bildpunkte vom linken Rand eines 218 breiten Knopfes,
        # also dort, wo es bei einer Zwischenbreite von 60 hingehoert
        # haette - und blieb dort stehen.
        self._nachzeichnen = Clock.create_trigger(self._zeichnen, -1)

        self.bind(
            pos=self._nachzeichnen,
            size=self._nachzeichnen,
            text=self._nachzeichnen,
            disabled=self._nachzeichnen,
        )

        self._zeichnen()

    def set_bild(self, bild):

        self.bild = bild
        self._zeichnen()

    def _zeichnen(self, *_args):

        self.canvas.after.clear()

        if not self.bild or self.width <= 0 or self.height <= 0:
            return

        kante = min(
            dp(self.bild_groesse), self.height * 0.62, self.width * 0.62
        )

        if self.text:

            # Links neben der Beschriftung, mit etwas Luft zum Rand.
            x = self.x + dp(12)

            # Und die Beschriftung rueckt hinter das Bild. Ohne das
            # setzt Kivy den Text mittig ueber die ganze Breite - er
            # lag dann quer ueber dem Muelleimer.
            self.halign = "left"
            self.valign = "middle"
            self.padding = [dp(12) + kante + dp(8), 0, dp(12), 0]
            self.text_size = self.size

        else:
            x = self.center_x - kante / 2

        y = self.center_y - kante / 2

        with self.canvas.after:

            Color(1, 1, 1, 0.4 if self.disabled else 1)

            Rectangle(
                texture=textur(self.bild),
                pos=(x, y),
                size=(kante, kante),
            )


def loeschknopf(callback=None, text="", **kwargs):
    """Ein Mülleimer. Der Hintergrund warnt, das Bild benennt."""

    knopf = KiGBildButton(
        bild=loeschbild(), text=text, gefaehrlich=True, **kwargs
    )

    if callable(callback):
        knopf.bind(on_release=lambda *_args: callback())

    return knopf


def bearbeitenknopf(callback=None, text="", **kwargs):
    """Ein Stift."""

    knopf = KiGBildButton(bild=bearbeitenbild(), text=text, **kwargs)

    if callable(callback):
        knopf.bind(on_release=lambda *_args: callback())

    return knopf


def neuknopf(callback=None, text="", **kwargs):
    """Ein Plus."""

    knopf = KiGBildButton(bild=neubild(), text=text, **kwargs)

    if callable(callback):
        knopf.bind(on_release=lambda *_args: callback())

    return knopf


def speicherknopf(callback=None, text="", **kwargs):
    """Eine Diskette auf Orange - die Hauptaktion eines Formulars."""

    kwargs.setdefault("background_color", theme.PRIMARY_ORANGE)
    kwargs.setdefault("color", theme.TEXT_WHITE)

    knopf = KiGBildButton(bild=speicherbild(), text=text, **kwargs)

    if callable(callback):
        knopf.bind(on_release=lambda *_args: callback())

    return knopf
