from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Line

import theme


class RoundedPanel(BoxLayout):
    """Weiße Karte im Stil der Kassenbereiche."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*theme.CARD)
            self.background = RoundedRectangle(radius=[theme.CARD_RADIUS])

            Color(*theme.CARD_BORDER)
            self.border = Line(width=theme.BORDER_WIDTH)

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

    def _update_canvas(self, *_args):
        self.background.pos = self.pos
        self.background.size = self.size

        self.border.rounded_rectangle = (
            *self.pos,
            *self.size,
            theme.CARD_RADIUS
        )