"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/kig_checkbox.py

Beschreibung:
    Kästchen zum Anhaken, mit Beschriftung daneben.

    Kivys eigene CheckBox bringt ihre eigenen Bilder mit
    und passt weder zur Farbgebung noch zur Größe der
    übrigen Bedienelemente - auf dem E-Ink-Tablet ist sie
    zudem kaum zu treffen.

    Hier: dasselbe gezeichnete Häkchen wie in den
    Checklisten (widgets/common/kig_symbol.py), ein Kästchen
    in Fingergröße, und die ganze Zeile reagiert auf
    Berührung - nicht nur das Kästchen.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import theme

from widgets.common.kig_symbol import HAKEN, KiGSymbolButton


class KiGCheckbox(BoxLayout):
    """Ein Kästchen mit Beschriftung. aktiv sagt, ob es angehakt ist."""

    aktiv = BooleanProperty(False)

    BOX_SIZE = 46
    HEIGHT = 52

    def __init__(
            self,
            text="",
            aktiv=False,
            on_change=None,
            **kwargs
    ):

        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(self.HEIGHT),
            spacing=dp(theme.ROW_SPACING),
            **kwargs
        )

        self.on_change = on_change

        self.kaestchen = KiGSymbolButton(
            symbol=HAKEN if aktiv else None,
            size_hint=(None, 1),
            width=dp(self.BOX_SIZE),
            line_width=2.6,
        )
        self.kaestchen.bind(on_release=lambda *_a: self.umschalten())

        # Rand wie an den Eingabefeldern: Ohne ihn ist ein leeres
        # Kaestchen auf hellem Grund kaum als Kaestchen zu erkennen.
        with self.kaestchen.canvas.before:
            Color(*theme.BORDER_COLOR)
            self._rand = Line(width=theme.BORDER_WIDTH)

        self.kaestchen.bind(pos=self._rand_nachfuehren,
                            size=self._rand_nachfuehren)

        self.add_widget(self.kaestchen)

        # Die Beschriftung ist selbst eine Schaltfläche: Wer den Text
        # antippt, meint das Kästchen.
        self.beschriftung = Button(
            text=text,
            background_normal="", background_down="",
            background_color=(0, 0, 0, 0),
            color=theme.TEXT_PRIMARY,
            font_size="16sp",
            halign="left", valign="middle",
        )
        self.beschriftung.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            ),
            on_release=lambda *_a: self.umschalten(),
        )

        self.add_widget(self.beschriftung)

        self.aktiv = aktiv

        self._darstellen()

    # =====================================================

    def umschalten(self):

        self.aktiv = not self.aktiv

        self._darstellen()

        if callable(self.on_change):
            self.on_change(self.aktiv)

    def setzen(self, aktiv):

        self.aktiv = bool(aktiv)

        self._darstellen()

    def _rand_nachfuehren(self, *_args):

        self._rand.rounded_rectangle = (
            *self.kaestchen.pos, *self.kaestchen.size, theme.INPUT_RADIUS
        )

    def _darstellen(self):

        self.kaestchen.set_symbol(HAKEN if self.aktiv else None)

        self.kaestchen.background_color = (
            theme.PRIMARY_ORANGE if self.aktiv else theme.SURFACE
        )
        self.kaestchen.set_symbol_color(
            theme.TEXT_WHITE if self.aktiv else theme.TEXT_PRIMARY
        )
