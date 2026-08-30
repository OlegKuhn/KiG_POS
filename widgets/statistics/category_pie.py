"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/statistics/category_pie.py

Beschreibung:
    Kreisdiagramm der Einnahmen je Kategorie - ohne
    zusätzliche Bibliothek, allein mit Kivys Zeichenbefehlen.

    Kivy kann Kreisausschnitte von Haus aus: Eine Ellipse mit
    angle_start und angle_end ist genau ein Tortenstück. Mehr
    braucht es dafür nicht, und die Anwendung bleibt ohne
    weitere Abhängigkeit (wichtig für den Android-Bau).

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

import theme


# Ersatzfarben für Kategorien ohne eigene Farbe - bewusst gut
# unterscheidbar und in der Reihenfolge, in der sie vergeben werden.
FALLBACK_FARBEN = (
    "#1976D2", "#F57C00", "#43A047", "#7B1FA2",
    "#00838F", "#C62828", "#5D4037", "#616161",
)


def _farbe(wert, position):
    """Wandelt die hinterlegte Kategoriefarbe in Kivys Format.

    Fehlt sie oder ist sie unbrauchbar, kommt eine Ersatzfarbe zum
    Zug - ein farbloses Tortenstück wäre nicht zuzuordnen.
    """

    for kandidat in (wert, FALLBACK_FARBEN[position % len(FALLBACK_FARBEN)]):

        if not kandidat:
            continue

        try:
            return get_color_from_hex(kandidat)
        except (ValueError, IndexError):
            continue

    return theme.TEXT_SECONDARY


class CategoryPie(Widget):
    """Die Kreisfläche selbst (ohne Beschriftung)."""

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.anteile = []

        self.bind(pos=self._zeichnen, size=self._zeichnen)

    def set_data(self, anteile):
        """anteile: Liste aus (Name, Betrag, Farbe)."""

        # Nur positive Beträge ergeben ein Tortenstück. Ein durch
        # Stornos negativ gewordener Posten würde den Kreis sonst
        # rückwärts füllen.
        self.anteile = [
            (name, betrag, farbe)
            for name, betrag, farbe in anteile
            if betrag > 0
        ]

        self._zeichnen()

    def _zeichnen(self, *_args):

        self.canvas.clear()

        gesamt = sum(betrag for _name, betrag, _farbe in self.anteile)

        if gesamt <= 0:
            return

        # Quadratisch und mittig: Ein in die Breite gezogener Kreis
        # verzerrt die Anteile für das Auge.
        durchmesser = min(self.width, self.height)

        pos = (
            self.center_x - durchmesser / 2,
            self.center_y - durchmesser / 2,
        )

        winkel = 0

        with self.canvas:

            for position, (_name, betrag, farbe) in enumerate(self.anteile):

                anteil = betrag / gesamt
                ende = winkel + anteil * 360

                Color(*_farbe(farbe, position))

                Ellipse(
                    pos=pos,
                    size=(durchmesser, durchmesser),
                    angle_start=winkel,
                    angle_end=ende,
                )

                winkel = ende


class CategoryPiePanel(BoxLayout):
    """Kreisdiagramm mit Legende daneben.

    Die Legende trägt Namen, Betrag und Anteil - ohne sie wären die
    Tortenstücke nur bunte Flächen.
    """

    LEGENDE_ZEILE = 26
    PUNKT = 14

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.spacing = dp(theme.CARD_SPACING)

        self.pie = CategoryPie(size_hint_x=0.42)
        self.add_widget(self.pie)

        self.legende = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            size_hint_x=0.58,
        )
        self.add_widget(self.legende)

    def set_data(self, anteile):

        self.pie.set_data(anteile)
        self.legende.clear_widgets()

        gesamt = sum(betrag for _name, betrag, _farbe in anteile if betrag > 0)

        if gesamt <= 0:

            hinweis = Label(
                text="Keine Einnahmen im gewählten Zeitraum.",
                color=theme.TEXT_SECONDARY, font_size="13sp",
                halign="left", valign="middle",
            )

            # Umbruch an der eigenen Breite - auf einem Telefon lief
            # der Satz sonst rechts aus der Karte heraus.
            hinweis.bind(
                size=lambda instanz, groesse: setattr(
                    instanz, "text_size", groesse
                )
            )

            self.legende.add_widget(hinweis)

            return

        for position, (name, betrag, farbe) in enumerate(anteile):

            if betrag <= 0:
                continue

            self.legende.add_widget(
                self._zeile(name, betrag, farbe, position, gesamt)
            )

        # Der Rest der Legende bleibt leer, damit die Einträge oben
        # stehen und nicht über die Höhe verteilt werden.
        self.legende.add_widget(Widget())

    def _zeile(self, name, betrag, farbe, position, gesamt):

        zeile = BoxLayout(
            size_hint_y=None,
            height=dp(self.LEGENDE_ZEILE),
            spacing=dp(theme.SPACE_XS),
        )

        punkt = Widget(size_hint=(None, None),
                       size=(dp(self.PUNKT), dp(self.PUNKT)))

        with punkt.canvas:
            Color(*_farbe(farbe, position))
            kreis = Ellipse(size=punkt.size)

        def punkt_setzen(instanz, _wert):
            kreis.pos = (
                instanz.x,
                instanz.center_y - dp(self.PUNKT) / 2,
            )

        punkt.bind(pos=punkt_setzen, size=punkt_setzen)

        # Der Punkt sitzt in einer Zeile fester Höhe - ohne diese
        # Ausrichtung klebte er am unteren Rand.
        halter = BoxLayout(size_hint_x=None, width=dp(self.PUNKT))
        halter.add_widget(punkt)
        zeile.add_widget(halter)

        zeile.add_widget(Label(
            text=name, color=theme.TEXT_PRIMARY, font_size="13sp",
            halign="left", valign="middle",
            text_size=(None, dp(self.LEGENDE_ZEILE)), size_hint_x=0.52,
            shorten=True, shorten_from="right",
        ))

        anteil = betrag / gesamt * 100

        zeile.add_widget(Label(
            text=f"{anteil:.0f} %", color=theme.TEXT_SECONDARY,
            font_size="13sp", halign="right", valign="middle",
            text_size=(None, dp(self.LEGENDE_ZEILE)), size_hint_x=0.20,
        ))

        zeile.add_widget(Label(
            text=f"{betrag:.2f} €".replace(".", ","),
            color=theme.TEXT_PRIMARY, font_size="13sp", bold=True,
            halign="right", valign="middle",
            text_size=(None, dp(self.LEGENDE_ZEILE)), size_hint_x=0.28,
        ))

        return zeile
