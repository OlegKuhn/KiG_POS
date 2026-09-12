"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/kig_symbol.py

Beschreibung:
    Gezeichnete Symbole für Schaltflächen.

    Kivys Schrift (Roboto) kennt weder Haken noch Kreuz
    noch Pfeile - an ihrer Stelle erscheint ein leeres
    Kästchen. Statt auf Zeichen auszuweichen, die zufällig
    vorhanden sind, werden die drei gebrauchten Symbole
    hier mit ein paar Linien gezeichnet: Das sieht auf
    jedem Gerät gleich aus, auch auf dem E-Ink-Tablet, und
    hängt von keiner Schriftart ab.

    Mülleimer, Stift und Plus sind KEINE gezeichneten
    Symbole: Für sie liegen Bilder in assets/icons
    (siehe widgets/common/kig_bildknopf.py).

    Verfügbar sind:

        haken         Erledigt-Häkchen
        kreuz         Löschen / Entfernen
        pfeil_links   Zurück
        pfeil_unten   Aufgeklappt (siehe Klappkopf)
        pfeil_rechts  Zugeklappt
        pfeil_oben    Zuklappen (siehe Warenkorb)

Version:
    1.0.0
=========================================================
"""

from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.widget import Widget

import theme


HAKEN = "haken"
KREUZ = "kreuz"
PFEIL_LINKS = "pfeil_links"
PFEIL_UNTEN = "pfeil_unten"
PFEIL_RECHTS = "pfeil_rechts"
PFEIL_OBEN = "pfeil_oben"


def _linienzuege(symbol, x, y, groesse):
    """Die Linienzüge eines Symbols.

    Ein Quadrat der Kantenlänge `groesse`, dessen linke untere Ecke
    bei (x, y) liegt. Zurück kommt eine Liste von Linienzügen - die
    einfachen Symbole bestehen aus einem, Mülleimer und Stift aus
    mehreren.

    Die Zahlen sind Anteile der Kantenlänge: So sieht jedes Symbol in
    jeder Größe gleich aus.
    """

    def punkte(*anteile):
        """Rechnet Anteilspaare in Bildpunkte um."""

        werte = []

        for spalte, zeile in anteile:
            werte += [x + groesse * spalte, y + groesse * zeile]

        return werte

    if symbol == HAKEN:
        # Kurzer Schenkel nach unten links, langer nach oben rechts.
        return [punkte((0.16, 0.52), (0.42, 0.24), (0.86, 0.76))]

    if symbol == KREUZ:
        # Zwei Striche - als ein Linienzug ginge nur ein "V".
        return [
            punkte((0.24, 0.24), (0.76, 0.76)),
            punkte((0.24, 0.76), (0.76, 0.24)),
        ]

    if symbol == PFEIL_LINKS:
        # Strich und Spitze
        return [
            punkte((0.80, 0.50), (0.20, 0.50)),
            punkte((0.42, 0.28), (0.20, 0.50), (0.42, 0.72)),
        ]

    if symbol == PFEIL_UNTEN:
        # Winkel nach unten: aufgeklappt, der Inhalt steht darunter.
        return [punkte((0.24, 0.62), (0.50, 0.36), (0.76, 0.62))]

    if symbol == PFEIL_OBEN:
        # Winkel nach oben: zuklappen.
        return [punkte((0.24, 0.38), (0.50, 0.64), (0.76, 0.38))]

    if symbol == PFEIL_RECHTS:
        # Winkel nach rechts: zugeklappt.
        return [punkte((0.38, 0.24), (0.64, 0.50), (0.38, 0.76))]

    return []


def zeichnen(symbol, x, y, groesse, linienbreite):
    """Zeichnet ein Symbol in die gerade offene Zeichenfläche.

    Farbe setzt der Aufrufer - so gilt dieselbe Rechnung für das
    Symbol allein wie für das auf einer Schaltfläche.
    """

    for zug in _linienzuege(symbol, x, y, groesse):

        if not zug:
            continue

        Line(
            points=zug, width=dp(linienbreite),
            cap="round", joint="round",
        )


class KiGSymbol(Widget):
    """Zeichnet ein Symbol - ohne eigenes Verhalten."""

    def __init__(self, symbol=HAKEN, color=None, line_width=2.2, **kwargs):

        super().__init__(**kwargs)

        self.symbol = symbol
        self.symbol_color = color or theme.TEXT_PRIMARY
        self.line_width = line_width

        # Erst im nächsten Frame zeichnen, nicht sofort beim
        # Verschieben: Ein Symbol in einer Liste, die gerade umgebaut
        # wird, wandert während eines Layoutdurchgangs mehrmals.
        # Zeichnete es bei jedem Zwischenschritt, bliebe am Ende die
        # Fassung von einer Zwischenstellung stehen - nachgemessen an
        # den Klappköpfen der Kasse, deren Winkel 26 Bildpunkte über
        # ihrer Zeile hingen.
        self._nachzeichnen = Clock.create_trigger(self._zeichnen, -1)

        self.bind(pos=self._nachzeichnen, size=self._nachzeichnen)

        self._zeichnen()

    def neu_zeichnen(self):
        """Zeichnet im nächsten Frame neu.

        Für Fälle, in denen sich nicht das Symbol selbst bewegt,
        sondern das, worin es sitzt.
        """

        self._nachzeichnen()

    def set_color(self, color):

        self.symbol_color = color
        self._zeichnen()

    def set_symbol(self, symbol):

        self.symbol = symbol
        self._zeichnen()

    def _zeichnen(self, *_args):

        self.canvas.clear()

        if not self.symbol or self.width <= 0 or self.height <= 0:
            return

        groesse = min(self.width, self.height)

        x = self.center_x - groesse / 2
        y = self.center_y - groesse / 2

        with self.canvas:

            Color(*self.symbol_color)

            zeichnen(self.symbol, x, y, groesse, self.line_width)


class KiGSymbolButton(Button):
    """Schaltfläche mit gezeichnetem Symbol.

    Ohne Text sitzt das Symbol in der Mitte. Mit Text steht es links
    daneben - so bleibt "Zurück" lesbar und trägt trotzdem seinen
    Pfeil.
    """

    SYMBOL_BOX = 26

    def __init__(
            self,
            symbol=HAKEN,
            symbol_color=None,
            line_width=2.2,
            **kwargs
    ):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", theme.SURFACE)
        kwargs.setdefault("color", theme.TEXT_PRIMARY)

        super().__init__(**kwargs)

        self.symbol = symbol
        self.symbol_color = symbol_color or kwargs["color"]
        self.line_width = line_width

        self.bind(pos=self._zeichnen, size=self._zeichnen, text=self._zeichnen)

        self._zeichnen()

    def set_symbol_color(self, color):

        self.symbol_color = color
        self._zeichnen()

    def set_symbol(self, symbol):

        self.symbol = symbol
        self._zeichnen()

    def _zeichnen(self, *_args):

        self.canvas.after.clear()

        if not self.symbol or self.width <= 0 or self.height <= 0:
            return

        kante = min(dp(self.SYMBOL_BOX), self.height * 0.6, self.width * 0.6)

        if self.text:
            # Links neben der Beschriftung, mit etwas Luft zum Rand.
            x = self.x + dp(12)
        else:
            x = self.center_x - kante / 2

        y = self.center_y - kante / 2

        with self.canvas.after:

            Color(*self.symbol_color)

            zeichnen(self.symbol, x, y, kante, self.line_width)
