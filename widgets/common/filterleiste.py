"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/filterleiste.py

Beschreibung:
    Die Leiste am unteren Bildschirmrand, die hochklappt.

    An dieser Stelle stand früher die Fußzeile mit Version
    und "Programm beenden" - eine Zeile, die auf jedem
    Bildschirm Platz kostete und nichts zur Arbeit beitrug.
    Jetzt steht dort, wonach gerade gefiltert wird:

        Zeitraum                      August 2026   ^

    Ein Tipp klappt die Bedienelemente hoch, ein zweiter
    schickt sie wieder weg. Solange sie unten liegen,
    gehört der ganze Bildschirm dem Wesentlichen - der
    Tabelle, der Liste, den Zahlen.

Version:
    1.0.0
=========================================================
"""

from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.common.kig_symbol import KiGSymbol, PFEIL_OBEN, PFEIL_UNTEN
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


class _Filterzeile(ButtonBehavior, BoxLayout):
    """Die immer sichtbare Zeile: Was ist eingestellt, und wohin
    führt ein Tipp."""

    def __init__(self, titel, on_tipp, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.spacing = dp(theme.SPACE_S)
        self.size_hint_y = None
        self.height = dp(Filterleiste.ZEILE_HOEHE)

        self.beschriftung = KiGLabel()
        self.beschriftung.set_text(titel)
        self.beschriftung.set_font_size(15 if theme.is_narrow() else 17)
        self.beschriftung.set_bold(True)
        self.beschriftung.set_alignment("left")
        self.beschriftung.set_color(theme.TEXT_SECONDARY)
        self.beschriftung.max_lines = 1
        self.beschriftung.size_hint_x = None
        self.beschriftung.width = dp(78 if theme.is_narrow() else 100)
        self.beschriftung.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.beschriftung)

        # Was gerade eingestellt ist - der eigentliche Grund, warum die
        # Leiste zugeklappt trotzdem etwas sagt.
        self.stand = KiGLabel()
        self.stand.set_font_size(15 if theme.is_narrow() else 18)
        self.stand.set_bold(True)
        self.stand.set_alignment("right")
        self.stand.set_color(theme.PRIMARY_ORANGE)
        self.stand.max_lines = 1
        self.stand.shorten = True
        self.stand.shorten_from = "right"
        self.stand.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.stand)

        self.symbol = KiGSymbol(
            symbol=PFEIL_OBEN,
            color=theme.PRIMARY_ORANGE,
            size_hint=(None, 1),
            width=dp(22),
        )
        self.add_widget(self.symbol)

        self.bind(
            on_release=lambda *_args: on_tipp() if callable(on_tipp) else None
        )

    def setzen(self, text, offen):

        self.stand.set_text(text or "")

        self.symbol.set_symbol(PFEIL_UNTEN if offen else PFEIL_OBEN)


class Filterleiste(RoundedPanel):
    """Die Filterleiste eines Bildschirms.

    `inhalt` sind die Bedienelemente, die beim Aufklappen erscheinen -
    also genau die, die vorher oben oder links Platz belegt haben.
    `zusammenfassung` liefert den Text für die zugeklappte Zeile.
    """

    ZEILE_HOEHE = 44

    def __init__(
            self,
            inhalt,
            titel="Filter",
            zusammenfassung=None,
            inhalt_hoehe=220,
            **kwargs
    ):

        super().__init__(
            orientation="vertical",
            padding=dp(theme.SPACE_S),
            spacing=dp(theme.SPACE_XS),
            **kwargs
        )

        self.size_hint_y = None

        self.inhalt = inhalt
        self.zusammenfassung = zusammenfassung
        self.inhalt_hoehe = inhalt_hoehe

        self.offen = False

        self.zeile = _Filterzeile(titel, self.umschalten)

        self._nur_zeile()

    # =====================================================
    # Auf und zu
    # =====================================================

    @property
    def _zeilenhoehe(self):

        return (
            dp(self.ZEILE_HOEHE)
            + dp(theme.SPACE_S) * 2
        )

    def _nur_zeile(self):

        self.clear_widgets()
        self.add_widget(self.zeile)

        self.height = self._zeilenhoehe

        self.offen = False

        self.aktualisieren()

    def aufklappen(self):

        if self.offen:
            return

        self.clear_widgets()

        # Kivy stellt in einer senkrechten Reihe das zuerst
        # Hinzugefuegte nach oben: erst der Inhalt, dann die Zeile.
        self.inhalt.size_hint_y = None
        self.inhalt.height = dp(self.inhalt_hoehe)

        self.add_widget(self.inhalt)
        self.add_widget(self.zeile)

        self.height = (
            self._zeilenhoehe
            + dp(self.inhalt_hoehe)
            + dp(theme.SPACE_XS)
        )

        self.offen = True

        self.aktualisieren()

    def zuklappen(self):

        if not self.offen:
            return

        self._nur_zeile()

    def umschalten(self):

        if self.offen:
            self.zuklappen()
        else:
            self.aufklappen()

    # =====================================================
    # Stand
    # =====================================================

    def aktualisieren(self):
        """Schreibt neu, was gerade eingestellt ist."""

        text = ""

        if callable(self.zusammenfassung):
            text = self.zusammenfassung()

        self.zeile.setzen(text, self.offen)
