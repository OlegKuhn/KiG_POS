"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/kig_popup.py

Beschreibung:
    Gemeinsamer Rahmen für alle Dialoge der Anwendung.

    Kivys Popup bringt von Haus aus ein dunkles Aussehen mit:
    ein graues Hintergrundbild, eine weiße Überschrift und einen
    dunklen Trennstrich. Im hellen Modus stach das heraus - der
    Dialog war dunkel, obwohl die Anwendung hell ist.

    Diese Klasse ersetzt den Rahmen durch dieselbe Karte, aus der
    die übrige Oberfläche besteht (theme.CARD mit Rand und
    Eckenradius). Alle Dialoge erben davon, damit sie in beiden
    Farbmodi zur Anwendung passen und nur an einer Stelle gepflegt
    werden müssen.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.popup import Popup

import theme


class KiGPopup(Popup):

    def __init__(self, **kwargs):

        # Kivy zeichnet den Hintergrund als BorderImage aus einer
        # Bilddatei. Ohne Quelle bleibt sie leer - der Platz gehört
        # dann der eigenen Karte weiter unten.
        kwargs.setdefault("background", "")

        kwargs.setdefault("title_color", theme.TEXT_PRIMARY)
        kwargs.setdefault("separator_color", theme.PRIMARY_ORANGE)
        kwargs.setdefault("title_size", "18sp")

        super().__init__(**kwargs)

        self.separator_height = dp(2)

        # canvas.before ist zu diesem Zeitpunkt bereits gefüllt (leerer
        # Hintergrund und Abdunklung dahinter). Was hier hinzukommt,
        # legt sich darüber und bleibt hinter dem Inhalt.
        with self.canvas.before:

            Color(*theme.CARD)
            self._karte = RoundedRectangle(radius=[dp(theme.CARD_RADIUS)])

            Color(*theme.CARD_BORDER)
            self._rand = Line(width=theme.BORDER_WIDTH)

        self.bind(pos=self._karte_zeichnen, size=self._karte_zeichnen)
        self._karte_zeichnen()

    def _karte_zeichnen(self, *_args):

        self._karte.pos = self.pos
        self._karte.size = self.size

        self._rand.rounded_rectangle = (
            self.x, self.y, self.width, self.height,
            dp(theme.CARD_RADIUS),
        )
