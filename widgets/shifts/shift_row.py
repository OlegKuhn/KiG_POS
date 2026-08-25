"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/shifts/shift_row.py

Beschreibung:
    Eine Zeile des Schichtplans.

        Tätigkeit   von   bis   Ist/Soll  [Balken]  Helfer  [x]

    Der Balken beantwortet die Frage, um die es geht:
    Reicht es schon?

        grün      besetzt, niemand fehlt
        orange    teilweise besetzt
        rot       noch niemand eingetragen

    Geändert wird direkt in der Zeile; gespeichert wird,
    sobald ein Feld verlassen wird - genau wie in den
    Checklisten.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

import theme

from widgets.common.feldausrichtung import links_ausrichten
from widgets.common.kig_symbol import KREUZ, KiGSymbolButton
from widgets.common.rounded_input import RoundedInput


class Besetzungsbalken(Widget):
    """Zeigt als Balken, wie weit eine Schicht besetzt ist."""

    HOEHE = 16

    def __init__(self, besetzt=0, benoetigt=0, **kwargs):

        super().__init__(**kwargs)

        self.besetzt = besetzt
        self.benoetigt = benoetigt

        with self.canvas:

            self.grund_farbe = Color(*theme.BORDER_COLOR)
            self.grund = RoundedRectangle(radius=[dp(4)])

            self.balken_farbe = Color(*theme.SUCCESS)
            self.balken = RoundedRectangle(radius=[dp(4)])

        self.bind(pos=self._zeichnen, size=self._zeichnen)

        self._zeichnen()

    def setzen(self, besetzt, benoetigt):

        self.besetzt = besetzt
        self.benoetigt = benoetigt

        self._zeichnen()

    def _zeichnen(self, *_args):

        hoehe = min(dp(self.HOEHE), self.height)

        y = self.center_y - hoehe / 2

        self.grund.pos = (self.x, y)
        self.grund.size = (self.width, hoehe)

        anteil = (
            min(1.0, self.besetzt / self.benoetigt)
            if self.benoetigt > 0 else (1.0 if self.besetzt else 0.0)
        )

        self.balken.pos = (self.x, y)
        self.balken.size = (self.width * anteil, hoehe)

        self.balken_farbe.rgba = farbe_fuer(self.besetzt, self.benoetigt)


def farbe_fuer(besetzt, benoetigt):
    """Die Ampel des Schichtplans - an einer Stelle festgelegt."""

    if benoetigt <= 0:
        return theme.TEXT_SECONDARY

    if besetzt >= benoetigt:
        return theme.SUCCESS

    if besetzt <= 0:
        return theme.ERROR

    return theme.WARNING


class ShiftRow(BoxLayout):

    HEIGHT = 56

    # Spaltenaufteilung. Die Zahlen sind Anteile und wirken nur
    # zueinander - der Balken bekommt deshalb ausdruecklich einen
    # eigenen Anteil und nicht "den Rest", sonst draengt er die
    # Zeitfelder auf zwei Ziffern zusammen.
    TASK_WIDTH = 0.24
    TIME_WIDTH = 0.17
    COUNT_WIDTH = 90
    BAR_WIDTH = 0.22
    HELPER_WIDTH = 0.28
    REMOVE_WIDTH = 52

    def __init__(
            self,
            shift,
            on_change,
            on_needed,
            on_helpers,
            on_remove,
            **kwargs
    ):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(self.HEIGHT),
            spacing=dp(theme.ROW_SPACING),
            **kwargs
        )

        self.shift = shift
        self.on_change = on_change
        self.on_needed = on_needed
        self.on_helpers = on_helpers
        self.on_remove = on_remove

        # ---- Tätigkeit ----
        self.task_input = self._input(
            shift["task"], "Tätigkeit", self.TASK_WIDTH, "task"
        )
        self.add_widget(self.task_input)

        # ---- Zeit ----
        self.start_input = self._input(
            shift["start_time"], "18:00", self.TIME_WIDTH, "start_time"
        )
        self.add_widget(self.start_input)

        self.end_input = self._input(
            shift["end_time"], "21:00", self.TIME_WIDTH, "end_time"
        )
        self.add_widget(self.end_input)

        # ---- Ist / Soll ----
        self.needed_button = Button(
            text=self._count_text(),
            size_hint_x=None, width=dp(self.COUNT_WIDTH),
            background_normal="", background_down="",
            background_color=theme.SURFACE,
            font_size="15sp", bold=True,
        )
        links_ausrichten(self.needed_button)
        self.needed_button.bind(
            on_release=lambda *_a: self.on_needed(self)
        )
        self.add_widget(self.needed_button)

        # ---- Balken ----
        self.balken = Besetzungsbalken(
            besetzt=shift["besetzt"], benoetigt=shift["needed"],
            size_hint_x=self.BAR_WIDTH,
        )
        self.add_widget(self.balken)

        # ---- Helfer ----
        self.helper_button = Button(
            text=self._helper_text(),
            size_hint_x=self.HELPER_WIDTH,
            background_normal="", background_down="",
            background_color=theme.SURFACE,
            font_size="14sp",
        )
        links_ausrichten(self.helper_button)
        self.helper_button.bind(
            on_release=lambda *_a: self.on_helpers(self)
        )
        self.add_widget(self.helper_button)

        # ---- Entfernen ----
        entfernen = KiGSymbolButton(
            symbol=KREUZ,
            size_hint_x=None, width=dp(self.REMOVE_WIDTH),
            symbol_color=theme.ERROR,
        )
        entfernen.bind(on_release=lambda *_a: self.on_remove(self))
        self.add_widget(entfernen)

        self._faerben()

    # =====================================================

    def _input(self, wert, hinweis, breite, feld):

        feld_widget = RoundedInput(
            text=wert or "", hint_text=hinweis, multiline=False,
            size_hint_x=breite,
        )

        feld_widget.foreground_color = theme.INPUT_TEXT
        feld_widget.hint_text_color = theme.INPUT_HINT

        # Beim Verlassen speichern statt bei jedem Tastendruck.
        feld_widget.bind(
            focus=lambda instanz, hat_fokus: (
                None if hat_fokus
                else self.on_change(self, feld, instanz.text)
            )
        )

        return feld_widget

    def _count_text(self):

        return f"{self.shift['besetzt']} / {self.shift['needed']}"

    def _helper_text(self):

        namen = self.shift.get("helfer_namen") or ""

        if namen:
            return namen

        return "niemand" if self.shift["needed"] else "-"

    def _faerben(self):

        farbe = farbe_fuer(self.shift["besetzt"], self.shift["needed"])

        self.needed_button.color = farbe

        self.helper_button.color = (
            theme.ERROR
            if self.shift["besetzt"] == 0 and self.shift["needed"] > 0
            else theme.TEXT_PRIMARY
        )

    # =====================================================

    def aktualisieren(self, shift):
        """Übernimmt frische Zahlen, ohne die Zeile neu zu bauen."""

        self.shift = shift

        self.needed_button.text = self._count_text()
        self.helper_button.text = self._helper_text()

        self.balken.setzen(shift["besetzt"], shift["needed"])

        self._faerben()
