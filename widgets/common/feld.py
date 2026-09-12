"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/feld.py

Beschreibung:
    Wie ein Feld aussieht - an einer Stelle festgelegt.

    Ein Formular hatte bis hierher zweierlei Felder: Wo
    getippt wird, stand ein abgerundeter Rahmen mit ruhiger
    Schrift; wo ein Kalender oder der Nummernblock dahinter
    steckt, ein kantiger grauer Kasten mit fetter Schrift.
    Im Kassenbuch standen beide Sorten untereinander in
    derselben Spalte - nachgemessen: fuenf kantige, zwei
    runde.

    Hier stehen deshalb Flaeche, Rahmen und Schrift eines
    Feldes einmal. Wer ein Feld baut, nimmt sie:

        RoundedInput    Text tippen
        RoundedSpinner  aus einer Liste waehlen
        Feldknopf       antippen, dahinter oeffnet sich
                        Nummernblock oder Kalender

    Nicht gemeint sind Schaltflaechen, die etwas tun
    ("Speichern", "Export") und Kacheln: Die sehen anders
    aus, weil sie etwas anderes sind.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.button import Button

import theme

from widgets.common.feldausrichtung import links_ausrichten


class Feldflaeche:
    """Hintergrund und Rahmen eines Feldes.

    Zeichnet in `canvas.before` und haelt beides an Ort und Stelle.
    Was danach in `canvas.before` kommt, liegt darueber - das nutzt
    RoundedInput fuer seine Textfarbe.
    """

    def __init__(self, widget):

        self.widget = widget

        with widget.canvas.before:

            self.flaechenfarbe = Color(*theme.SURFACE)

            self.flaeche = RoundedRectangle(
                radius=[theme.INPUT_RADIUS]
            )

            self.rahmenfarbe = Color(*theme.BORDER_COLOR)

            self.rahmen = Line(width=theme.BORDER_WIDTH)

        widget.bind(pos=self.nachziehen, size=self.nachziehen)

        self.nachziehen()

    def nachziehen(self, *_args):

        self.flaeche.pos = self.widget.pos
        self.flaeche.size = self.widget.size

        self.rahmen.rounded_rectangle = (
            *self.widget.pos,
            *self.widget.size,
            theme.INPUT_RADIUS,
        )

    def hervorheben(self, an):
        """Oranger Rahmen, solange das Feld an der Reihe ist."""

        self.rahmenfarbe.rgba = (
            theme.PRIMARY_ORANGE if an else theme.BORDER_COLOR
        )

    def einfaerben(self, farbe, rahmen=None):
        """Fuer Felder, die zugleich eine Auswahl anzeigen (siehe
        Kassenbuch: der gewaehlte Monat).

        Der Rahmen geht mit: Ein grauer Strich um eine volle Flaeche
        sieht aus wie ein Rest vom vorigen Zustand.
        """

        self.flaechenfarbe.rgba = farbe

        self.rahmenfarbe.rgba = rahmen or farbe


def schrift_setzen(widget, groesse=None):
    """Gibt einem Feld die Schrift aller Felder.

    Ruhig und schwarz, nicht fett: Ein Formular voller fetter Werte
    liest sich wie eine Ueberschriftenliste. Die Groesse ist die der
    Eingabefelder - kleiner darf es nur werden, wo nachgemessen kein
    Platz ist.
    """

    widget.font_size = f"{groesse or theme.INPUT_FONT_SIZE}sp"

    if hasattr(widget, "bold"):
        widget.bold = False

    if hasattr(widget, "color"):
        widget.color = theme.INPUT_TEXT


class Feldknopf(Button):
    """Ein Feld, hinter dem sich etwas oeffnet.

    Sieht aus wie ein Eingabefeld und verhaelt sich wie eine
    Schaltflaeche: Ein Tipp oeffnet den Nummernblock, den Kalender
    oder einen Dialog. Genau dafuer standen ueberall im Programm
    einzeln zusammengesetzte Buttons.
    """

    def __init__(self, text="", groesse=None, on_tipp=None, **kwargs):

        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")

        # Der eigene Hintergrund wird gezeichnet, nicht gefuellt.
        kwargs.setdefault("background_color", (0, 0, 0, 0))

        super().__init__(text=text, **kwargs)

        schrift_setzen(self, groesse)

        # Kivy schreibt gesperrte Schaltflaechen in einem hellen Grau,
        # das auf der hellen Feldflaeche verschwindet - nachgemessen
        # am Mengenfeld eines Rezeptartikels, wo der Strich "-" gar
        # nicht mehr zu sehen war.
        self.disabled_color = theme.TEXT_SECONDARY

        self.flaeche = Feldflaeche(self)

        # Der Wert steht links, wie in jedem anderen Feld auch
        # (siehe widgets/common/feldausrichtung.py).
        links_ausrichten(self)

        # Waehrend des Tippens der orange Rahmen - dieselbe Rueckmeldung
        # wie bei einem Eingabefeld, das den Fokus bekommt.
        self.bind(state=self._gedrueckt)

        if callable(on_tipp):
            self.bind(on_release=lambda *_args: on_tipp())

    def _gedrueckt(self, _instanz, zustand):

        self.flaeche.hervorheben(zustand == "down")

    # =====================================================
    # Sperren
    # =====================================================

    def on_disabled(self, _instanz, gesperrt):
        """Gesperrt bleibt der Rahmen, die Schrift tritt zurueck."""

        self.color = (
            theme.TEXT_SECONDARY if gesperrt else theme.INPUT_TEXT
        )


def feldhoehe(schmal=None):
    """Die Hoehe, in der ein Feld ueberall gleich hoch ist."""

    if schmal is None:
        schmal = theme.is_narrow()

    return dp(46 if schmal else 52)
