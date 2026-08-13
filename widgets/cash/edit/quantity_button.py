from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.kig_label import KiGLabel


class QuantityButton(ButtonBehavior, BoxLayout):

    SIZE = 60
    RADIUS = 6

    def __init__(self, text, callback=None, **kwargs):

        super().__init__(**kwargs)

        self.callback = callback

        self.size_hint = (None, None)
        self.size = (self.SIZE, self.SIZE)

        with self.canvas.before:

            self.bg_color = Color(*theme.PRIMARY_ORANGE)

            self.background = RoundedRectangle(
                radius=[self.RADIUS]
            )

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        self.label = KiGLabel()

        self.label.text = text
        self.label.set_bold(True)
        self.label.set_font_size(28)
        self.label.set_color(theme.TEXT_WHITE)

        self.label.horizontal_alignment = "center"
        self.label.vertical_alignment = "middle"

        self.label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(self.label)

    # =====================================================
    # Canvas
    # =====================================================

    def _update_canvas(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

    # =====================================================
    # Hover / Press
    # =====================================================

    def on_press(self):

        self.bg_color.rgba = theme.PRIMARY_ORANGE_DARK

    def on_release(self):

        self.bg_color.rgba = theme.PRIMARY_ORANGE

        if callable(self.callback):
            self.callback(self)