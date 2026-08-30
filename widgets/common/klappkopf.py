"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/klappkopf.py

Beschreibung:
    Anklickbare Überschrift, die ihren Inhalt auf- und
    zuklappt.

    Gebaut für schmale Bildschirme: Auf einem Telefon ist
    Höhe das knappe Gut. Neun Startkacheln oder acht
    Kategorien untereinander passen dort nicht mehr auf
    einen Schirm - zugeklappt bleibt je eine Zeile stehen,
    und was gerade gebraucht wird, ist ohne Scrollen zu
    sehen.

    Der Kopf trägt links einen gezeichneten Winkel (nach
    unten = offen, nach rechts = zu; siehe kig_symbol.py -
    Kivys Schrift kennt keine Pfeile) und rechts optional
    eine Anzahl.

    Er klappt nichts selbst: Er meldet den Tipp, und wer
    ihn benutzt, entscheidet, was mit dem Inhalt geschieht.
    So kann derselbe Kopf eine Kachelgruppe tragen wie eine
    Artikelliste.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

import theme

from widgets.common.kig_symbol import KiGSymbol, PFEIL_RECHTS, PFEIL_UNTEN


class Klappkopf(ButtonBehavior, BoxLayout):

    HOEHE = 38
    SYMBOL_GROESSE = 20

    def __init__(
            self,
            text,
            offen=True,
            zusatz="",
            on_klapp=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.padding = (dp(theme.SPACE_S), 0)
        self.spacing = dp(theme.SPACE_S)

        self.size_hint_y = None
        self.height = dp(self.HOEHE)

        self.offen = offen
        self.on_klapp = on_klapp

        with self.canvas.before:
            self._farbe = Color(*theme.SURFACE)
            self._hintergrund = RoundedRectangle(
                radius=[dp(theme.BUTTON_RADIUS)]
            )

        self.bind(pos=self._verschoben, size=self._verschoben)

        self.symbol = KiGSymbol(
            symbol=PFEIL_UNTEN if offen else PFEIL_RECHTS,
            color=theme.TEXT_SECONDARY,
            size_hint=(None, 1),
            width=dp(self.SYMBOL_GROESSE),
        )
        self.add_widget(self.symbol)

        self.beschriftung = Label(
            text=text, color=theme.TEXT_PRIMARY,
            font_size="15sp", bold=True,
            halign="left", valign="middle",
        )
        self.beschriftung.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.beschriftung)

        self.zusatz = Label(
            text=zusatz, color=theme.TEXT_SECONDARY,
            font_size="13sp",
            halign="right", valign="middle",
            size_hint_x=None, width=dp(64),
        )
        self.zusatz.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.zusatz)

        self.bind(on_release=self._getippt)

    # =====================================================

    def _verschoben(self, *_args):

        self._hintergrund.pos = self.pos
        self._hintergrund.size = self.size

        # Der gezeichnete Winkel haengt nicht am Layout, sondern an
        # seinen eigenen Koordinaten - er muss mit.
        self.symbol.neu_zeichnen()

    def _getippt(self, *_args):

        self.set_offen(not self.offen)

        if callable(self.on_klapp):
            self.on_klapp(self.offen)

    def set_offen(self, offen):
        """Setzt den Zustand, ohne jemanden zu benachrichtigen."""

        self.offen = offen

        self.symbol.set_symbol(PFEIL_UNTEN if offen else PFEIL_RECHTS)

    def set_text(self, text):

        self.beschriftung.text = text

    def set_zusatz(self, text):
        """Kleine Angabe rechts - etwa die Anzahl der Einträge."""

        self.zusatz.text = text

    def hervorheben(self, aktiv):
        """Färbt den Kopf ein, solange seine Gruppe die gewählte ist."""

        self._farbe.rgba = theme.PRIMARY_ORANGE if aktiv else theme.SURFACE

        self.beschriftung.color = (
            theme.TEXT_WHITE if aktiv else theme.TEXT_PRIMARY
        )
        self.zusatz.color = (
            theme.TEXT_WHITE if aktiv else theme.TEXT_SECONDARY
        )
        self.symbol.set_color(
            theme.TEXT_WHITE if aktiv else theme.TEXT_SECONDARY
        )
