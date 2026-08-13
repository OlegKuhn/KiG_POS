"""
=========================================================
KiG POS
=========================================================

Datei:
    kig_divider.py

Beschreibung:
    Wiederverwendbare Trennlinien für KiG POS.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.graphics import Color, Line
from kivy.properties import (
    ListProperty,
    NumericProperty
)
from kivy.uix.widget import Widget

import theme


class KiGDivider(Widget):
    """
    Basisklasse für alle Divider.
    """

    thickness = NumericProperty(1)

    color = ListProperty(theme.HEADER_SEPARATOR)

    padding = NumericProperty(10)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        with self.canvas:

            self._color = Color(*self.color)

            self._line = Line(
                width=self.thickness
            )

        self.bind(
            pos=self._update_graphics,
            size=self._update_graphics,
            color=self._update_graphics,
            thickness=self._update_graphics,
            padding=self._update_graphics
        )

    def _update_graphics(self, *args):
        pass

class KiGDividerVertical(KiGDivider):
    """
    Vertikale Trennlinie.
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.size_hint = (None, 1)

        self.width = self.thickness

    def _update_graphics(self, *args):

        self._color.rgba = self.color

        self._line.width = self.thickness

        self._line.points = (

            self.center_x,
            self.y + self.padding,

            self.center_x,
            self.top - self.padding

        )

class KiGDividerHorizontal(KiGDivider):
    """
    Horizontale Trennlinie.
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.size_hint = (1, None)

        self.height = self.thickness

    def _update_graphics(self, *args):

        self._color.rgba = self.color

        self._line.width = self.thickness

        self._line.points = (

            self.x + self.padding,
            self.center_y,

            self.right - self.padding,
            self.center_y

        )