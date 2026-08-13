"""
=========================================================
KiG POS

KiGWidget
=========================================================

Basisklasse aller KiG-Widgets.

Alle eigenen Widgets der Anwendung erben von
dieser Klasse.

Version : 0.1.0
Build   : 0001
=========================================================
"""

from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty
)

from kivy.uix.floatlayout import FloatLayout


class KiGWidget(FloatLayout):
    """
    Basisklasse aller Widgets.
    """

    enabled = BooleanProperty(True)

    visible = BooleanProperty(True)

    background_color = ColorProperty(
        (1, 1, 1, 1)
    )

    radius = NumericProperty(15)

    opacity_enabled = NumericProperty(1.0)

    opacity_disabled = NumericProperty(0.45)

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.opacity = self.opacity_enabled

    # -------------------------------------------------

    def enable(self):

        self.enabled = True

        self.disabled = False

        self.opacity = self.opacity_enabled

    # -------------------------------------------------

    def disable(self):

        self.enabled = False

        self.disabled = True

        self.opacity = self.opacity_disabled

    # -------------------------------------------------

    def show(self):

        self.visible = True

        self.opacity = 1

    # -------------------------------------------------

    def hide(self):

        self.visible = False

        self.opacity = 0