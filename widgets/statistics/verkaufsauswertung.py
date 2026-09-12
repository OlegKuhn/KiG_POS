"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/statistics/verkaufsauswertung.py

Beschreibung:
    Ein Bild aus zwei Hälften: Was wurde verkauft, und wie
    verteilt es sich.

    Links die summierten Verkäufe, absteigend nach Umsatz -
    ein Balken je Artikel, in der Farbe seiner Kategorie.
    Rechts dieselben Farben als Kreis: wie viel jede
    Kategorie beigetragen hat.

    Beides gehört zusammen und steht deshalb in derselben
    Karte. Wer einen langen Balken sieht, findet seine Farbe
    im Kreis wieder, ohne den Blick über den halben
    Bildschirm zu tragen.

    Die Zahlen beziehen sich immer auf den eingestellten
    Zeitraum; ohne Filter auf alles (siehe
    screens/statistics_screen.py).

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import geldformat
import theme

from widgets.statistics.category_pie import CategoryPiePanel, _farbe


class Farbbalken(Widget):
    """Ein waagerechter Balken in der Farbe seiner Kategorie."""

    def __init__(self, anteil=0, farbe=None, **kwargs):

        super().__init__(**kwargs)

        self.anteil = anteil

        with self.canvas:

            # Die Spur, in der der Balken liegt - sie zeigt, wie weit
            # es bis zum groessten Wert noch waere.
            Color(*theme.PROGRESS_BACKGROUND)
            self._spur = RoundedRectangle(radius=[dp(5)])

            Color(*(farbe or theme.PRIMARY_ORANGE))
            self._balken = RoundedRectangle(radius=[dp(5)])

        self.bind(pos=self._zeichnen, size=self._zeichnen)

    def _zeichnen(self, *_args):

        hoehe = min(self.height, dp(18))

        y = self.center_y - hoehe / 2

        self._spur.pos = (self.x, y)
        self._spur.size = (self.width, hoehe)

        self._balken.pos = (self.x, y)
        self._balken.size = (max(0, self.width * self.anteil), hoehe)


class Verkaufsauswertung(BoxLayout):
    """Balken je Artikel und Kreis je Kategorie - ein Bild."""

    ZEILE = 34
    NAME_BREITE = 150
    WERT_BREITE = 96

    # Auf dem Telefon schmaler: Bei 339 dp Breite blieben dem Balken
    # zwischen Name (150) und Wert (96) sonst keine 50 Bildpunkte.
    NARROW_NAME_BREITE = 92
    NARROW_WERT_BREITE = 84

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.schmal = theme.is_narrow()

        if self.schmal:
            self.NAME_BREITE = self.NARROW_NAME_BREITE
            self.WERT_BREITE = self.NARROW_WERT_BREITE

        self.orientation = "vertical" if self.schmal else "horizontal"
        self.spacing = dp(theme.CARD_SPACING)

        # --------------------------------------------------
        # Links: die Balken
        # --------------------------------------------------

        self.balkenliste = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            size_hint_y=None,
        )
        self.balkenliste.bind(
            minimum_height=self.balkenliste.setter("height")
        )

        self.kreis = CategoryPiePanel()

        if self.schmal:

            # Auf dem Telefon ist fuer zwei nebeneinander kein Platz -
            # und auch untereinander reicht die Hoehe nicht fuer beide
            # zugleich: Balken UND Kreis in einer 400 Bildpunkte hohen
            # Karte liessen von den Balken eine einzige Zeile uebrig.
            # Deshalb rollt hier das ganze Bild, statt nur die Liste.
            self.kreis.size_hint_y = None
            self.kreis.height = dp(190)

            inhalt = BoxLayout(
                orientation="vertical",
                spacing=dp(theme.CARD_SPACING),
                size_hint_y=None,
            )
            inhalt.bind(minimum_height=inhalt.setter("height"))

            inhalt.add_widget(self.balkenliste)
            inhalt.add_widget(self.kreis)

            rollbereich = ScrollView(do_scroll_x=False, bar_width=dp(8))
            rollbereich.add_widget(inhalt)

            self.add_widget(rollbereich)

            return

        # Breit: links rollt die Liste, rechts steht der Kreis.
        rollbereich = ScrollView(do_scroll_x=False, bar_width=dp(8))
        rollbereich.add_widget(self.balkenliste)

        self.add_widget(rollbereich)

        self.kreis.size_hint_x = 0.42

        self.add_widget(self.kreis)

    # =====================================================
    # Daten
    # =====================================================

    def set_data(self, artikel, kategorien):
        """artikel: Liste aus get_article_sales (absteigend sortiert).
        kategorien: Liste aus get_category_revenues."""

        self.balkenliste.clear_widgets()

        self.kreis.set_data(kategorien)

        if not artikel:

            self.balkenliste.add_widget(Label(
                text="Noch keine Verkäufe im gewählten Zeitraum.",
                color=theme.TEXT_SECONDARY, font_size="14sp",
                size_hint_y=None, height=dp(42),
                halign="left", valign="middle",
                text_size=(None, dp(42)),
            ))

            return

        # Der groesste Umsatz gibt den Massstab - so ist der laengste
        # Balken immer ganz ausgefahren und die uebrigen sind daran zu
        # messen.
        groesster = max(
            (eintrag["umsatz"] for eintrag in artikel), default=0
        )

        # Die Farben stimmen mit dem Kreis ueberein: Dort bestimmt die
        # Reihenfolge der Kategorien die Ersatzfarbe, hier wird sie
        # deshalb aus derselben Reihenfolge geholt.
        reihenfolge = {
            name: position
            for position, (name, _betrag, _farbe)
            in enumerate(kategorien)
        }

        for eintrag in artikel:

            self.balkenliste.add_widget(
                self._zeile(eintrag, groesster, reihenfolge)
            )

    def _zeile(self, eintrag, groesster, reihenfolge):

        zeile = BoxLayout(
            size_hint_y=None,
            height=dp(self.ZEILE),
            spacing=dp(theme.ROW_SPACING),
        )

        name = Label(
            text=eintrag["name"], color=theme.TEXT_PRIMARY,
            font_size="14sp", halign="left", valign="middle",
            size_hint_x=None, width=dp(self.NAME_BREITE),
            text_size=(dp(self.NAME_BREITE), dp(self.ZEILE)),
            shorten=True, shorten_from="right",
        )
        zeile.add_widget(name)

        zeile.add_widget(Farbbalken(
            anteil=(
                eintrag["umsatz"] / groesster if groesster else 0
            ),
            farbe=_farbe(
                eintrag.get("farbe"),
                reihenfolge.get(eintrag["kategorie"], 0),
            ),
        ))

        # Menge und Umsatz - die Menge klein davor, damit die Spalte
        # der Betraege buendig bleibt.
        menge = eintrag["menge"]

        wert = Label(
            text=(
                f"{menge:g} x  {geldformat.geld(eintrag['umsatz'])}"
                if not self.schmal
                else f"{menge:g}x {geldformat.geld(eintrag['umsatz'])}"
            ),
            color=theme.TEXT_PRIMARY, font_size="14sp", bold=True,
            halign="right", valign="middle",
            size_hint_x=None, width=dp(self.WERT_BREITE),
            text_size=(dp(self.WERT_BREITE), dp(self.ZEILE)),
        )
        zeile.add_widget(wert)

        return zeile
