"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/hinweis_popup.py

Beschreibung:
    Ein Hinweis, den man wegtippen kann.

    Klingt selbstverständlich, war es nicht: Hinweise wurden
    bisher als Popup ohne Schaltfläche gezeigt, das sich nur
    durch einen Tipp DANEBEN schließen ließ. Auf einem
    Tablet, das den halben Bildschirm mit dem Popup füllt,
    ist "daneben" nicht offensichtlich - der Hinweis wirkte
    wie ein hängendes Programm.

    Deshalb hier immer eine sichtbare Schaltfläche.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import theme

from widgets.common.kig_popup import KiGPopup


class HinweisPopup(KiGPopup):

    def __init__(
            self,
            message,
            title="Hinweis",
            button_text="Verstanden",
            **kwargs
    ):
        super().__init__(**kwargs)

        self.title = title

        self.size_hint = (0.7, None)
        self.height = dp(260)

        inhalt = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        with inhalt.canvas.before:
            Color(*theme.CARD)
            self._hintergrund = Rectangle(pos=inhalt.pos, size=inhalt.size)

        inhalt.bind(pos=self._hintergrund_setzen, size=self._hintergrund_setzen)

        text = Label(
            text=message, color=theme.TEXT_PRIMARY, font_size="15sp",
            halign="left", valign="middle",
        )
        text.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        inhalt.add_widget(text)

        knopf = Button(
            text=button_text, size_hint_y=None, height=dp(52),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="16sp", bold=True,
        )
        knopf.bind(on_release=lambda *_args: self.dismiss())

        inhalt.add_widget(knopf)

        self.content = inhalt

    def _hintergrund_setzen(self, instanz, _wert):

        self._hintergrund.pos = instanz.pos
        self._hintergrund.size = instanz.size
