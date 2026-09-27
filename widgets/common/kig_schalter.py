"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/kig_schalter.py

Beschreibung:
    Ein Regler zum Umlegen: Beschriftung links, daneben
    eine Bahn mit einem Knopf darin.

    Wo zwei Zustaende einander ausschliessen, brauchte es
    bisher zwei Schaltflaechen nebeneinander - jede so
    breit wie ihr laengster Text. Ein Regler sagt dasselbe
    in einer Handbreit und passt damit in eine Zeile mit
    den uebrigen Schaltflaechen.

    Der Regler ist kein Kaestchen zum Anhaken
    (widgets/common/kig_checkbox.py): Das Kaestchen steht in
    einem Formular und gehoert zu einem Wert, der Regler
    schaltet die Ansicht sofort um.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

import theme

from widgets.kig_label import KiGLabel


class _Bahn(Widget):
    """Die Bahn mit dem Knopf - gezeichnet, nicht aus Bildern."""

    BAHN_BREITE = 52
    BAHN_HOEHE = 26
    KNOPF = 20

    def __init__(self, **kwargs):

        super().__init__(
            size_hint=(None, 1),
            width=dp(self.BAHN_BREITE),
            **kwargs
        )

        self.an = False

        with self.canvas:

            self._bahnfarbe = Color(*theme.BUTTON_DISABLED)
            self._bahn = RoundedRectangle(radius=[dp(self.BAHN_HOEHE) / 2])

            self._knopffarbe = Color(*theme.CARD)
            self._knopf = Ellipse()

        self.bind(pos=self._zeichnen, size=self._zeichnen)

    def setzen(self, an):
        self.an = an
        self._zeichnen()

    def _zeichnen(self, *_args):

        breite = dp(self.BAHN_BREITE)
        hoehe = dp(self.BAHN_HOEHE)

        self._bahn.pos = (self.x, self.center_y - hoehe / 2)
        self._bahn.size = (breite, hoehe)
        self._bahn.radius = [hoehe / 2]

        self._bahnfarbe.rgba = (
            theme.PRIMARY_ORANGE if self.an else theme.BUTTON_DISABLED
        )

        knopf = dp(self.KNOPF)
        rand = (hoehe - knopf) / 2

        self._knopf.pos = (
            self.x + (breite - knopf - rand if self.an else rand),
            self.center_y - knopf / 2,
        )
        self._knopf.size = (knopf, knopf)


class KiGSchalter(ButtonBehavior, BoxLayout):
    """Beschriftung und Regler. `an` sagt, ob er umgelegt ist."""

    an = BooleanProperty(False)

    def __init__(self, text="", an=False, on_change=None, **kwargs):

        super().__init__(
            orientation="horizontal",
            spacing=dp(theme.LABEL_SPACING),
            **kwargs
        )

        self.on_change = on_change

        self.lbl = KiGLabel(text=text)
        self.lbl.set_font_size(14)
        self.lbl.set_bold(True)
        self.lbl.set_alignment("right")
        self.lbl.set_color(theme.TEXT_PRIMARY)
        self.add_widget(self.lbl)

        self.bahn = _Bahn()
        self.add_widget(self.bahn)

        self.an = an
        self.bahn.setzen(an)

    @property
    def text(self):
        return self.lbl.text

    @text.setter
    def text(self, wert):
        self.lbl.text = wert

    def on_an(self, _instanz, wert):
        self.bahn.setzen(wert)

    def setzen(self, an):
        """Legt den Regler um, OHNE on_change zu rufen.

        So kann der Bildschirm den Regler nachziehen, nachdem er die
        Ansicht selbst gewechselt hat, ohne dass sich beide
        gegenseitig aufrufen.
        """

        self.an = an

    def umschalten(self):

        self.an = not self.an

        if callable(self.on_change):
            self.on_change(self.an)

    def on_release(self):

        if self.disabled:
            return

        self.umschalten()
