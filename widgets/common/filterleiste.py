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

    Aufgeklappt ist der Teil mit den Bedienelementen
    bewusst NICHT so breit wie der Bildschirm, sondern eine
    hohe, schmale Karte über der Zeile - so, wie ein Menü
    aus seiner Schaltfläche herauswächst. Über die ganze
    Breite gezogen standen die Felder sonst als flacher
    Streifen nebeneinander und wirkten gequetscht; in der
    schmalen Karte stehen sie untereinander und haben ihre
    volle Höhe.

Version:
    1.1.0
=========================================================
"""

from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

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


class Filterleiste(FloatLayout):
    """Die Filterleiste eines Bildschirms.

    `inhalt` sind die Bedienelemente, die beim Aufklappen erscheinen -
    also genau die, die vorher oben oder links Platz belegt haben.
    `zusammenfassung` liefert den Text für die zugeklappte Zeile.
    """

    ZEILE_HOEHE = 44

    # Höchstbreite der aufgeklappten Karte. Breiter braucht sie nicht
    # zu sein: Darin stehen Felder untereinander, und ein Feld ist
    # rund 300 dp breit gut zu lesen.
    INHALT_BREITE = 420

    def __init__(
            self,
            inhalt,
            titel="Filter",
            zusammenfassung=None,
            inhalt_hoehe=280,
            **kwargs
    ):

        super().__init__(**kwargs)

        # Die Leiste selbst ist immer nur die Zeile hoch. Die Karte
        # mit den Bedienelementen LEGT sich beim Aufklappen darueber,
        # statt den Bildschirm zusammenzuschieben: Sonst wurde die
        # Tabelle darueber auf einen Streifen gequetscht, waehrend man
        # den Filter einstellt.
        self.size_hint_y = None

        self.inhalt = inhalt
        self.zusammenfassung = zusammenfassung
        self.inhalt_hoehe = inhalt_hoehe

        self.offen = False

        # --------------------------------------------------
        # Die immer sichtbare Zeile, in ihrer eigenen Karte
        # --------------------------------------------------

        self.zeile = _Filterzeile(titel, self.umschalten)

        self.zeilen_karte = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.SPACE_S),
            size_hint=(1, None),
            height=self._zeilenhoehe,
            pos_hint={"x": 0, "y": 0},
        )
        self.zeilen_karte.add_widget(self.zeile)

        # --------------------------------------------------
        # Die Karte mit den Bedienelementen
        # --------------------------------------------------

        self.inhalt_karte = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
            size_hint=(None, None),
        )

        self.bind(pos=self._karte_setzen, size=self._karte_setzen)

        self._nur_zeile()

    # =====================================================
    # Auf und zu
    # =====================================================

    @property
    def _zeilenhoehe(self):

        return dp(self.ZEILE_HOEHE) + dp(theme.SPACE_S) * 2

    def _karte_setzen(self, *_args):
        """Legt die Karte über die Leiste - rechtsbündig, von unten
        nach oben.

        Auf einem schmalen Gerät darf sie alles nehmen, was da ist;
        sonst bleibt sie bei ihrer Höchstbreite.
        """

        if not self.offen:
            return

        self.inhalt_karte.width = min(
            dp(self.INHALT_BREITE), max(dp(200), self.width)
        )

        self.inhalt_karte.height = dp(self.inhalt_hoehe)

        self.inhalt_karte.right = self.right

        self.inhalt_karte.y = self.top + dp(theme.SPACE_XS)

    def _nur_zeile(self):

        if self.inhalt_karte.parent is self:
            self.remove_widget(self.inhalt_karte)

        if self.zeilen_karte.parent is not self:
            self.add_widget(self.zeilen_karte)

        self.height = self._zeilenhoehe

        self.offen = False

        self.aktualisieren()

    def aufklappen(self):

        if self.offen:
            return

        if self.inhalt.parent is not self.inhalt_karte:

            if self.inhalt.parent is not None:
                self.inhalt.parent.remove_widget(self.inhalt)

            self.inhalt_karte.add_widget(self.inhalt)

        self.inhalt.size_hint_y = 1

        self.add_widget(self.inhalt_karte)

        self.offen = True

        self._karte_setzen()

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

    def on_touch_down(self, touch):
        """Ein Tipp neben die offene Karte schließt sie.

        Wie bei einem Menü: Man kommt wieder heraus, ohne den Winkel
        zu suchen. Der Tipp wird dabei geschluckt - sonst löst
        derselbe Fingerdruck noch etwas auf dem Bildschirm darunter
        aus.
        """

        if self.offen:

            auf_karte = self.inhalt_karte.collide_point(*touch.pos)
            auf_zeile = self.zeilen_karte.collide_point(*touch.pos)

            if not auf_karte and not auf_zeile:
                self.zuklappen()
                return True

        return super().on_touch_down(touch)

    # =====================================================
    # Stand
    # =====================================================

    def aktualisieren(self):
        """Schreibt neu, was gerade eingestellt ist."""

        text = ""

        if callable(self.zusammenfassung):
            text = self.zusammenfassung()

        self.zeile.setzen(text, self.offen)
