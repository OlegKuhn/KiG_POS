"""Darstellung der Kasse mit vorhandenen Theme- und Demo-Farben."""
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.button import Button
import theme


def category_color(category_id):
    # Kräftig statt gedeckt: Der Streifen unter dem Namen ist das
    # einzige Merkmal der Kategorie - im Zelt, bei wenig Licht und aus
    # einem Meter Entfernung müssen sich die Farben unterscheiden.
    palette = ((0.00, 0.64, 0.73, 1), (0.96, 0.45, 0.09, 1),
               (0.35, 0.74, 0.18, 1), (0.66, 0.33, 0.83, 1),
               (0.13, 0.50, 0.95, 1), (0.97, 0.76, 0.10, 1))
    value = sum((index + 1) * ord(char) for index, char in enumerate(str(category_id)))
    return palette[value % len(palette)]


class CashButton(Button):
    """Umrandete Taste mit sichtbarem Druck- und Auswahlzustand."""
    def __init__(self, active=False, soft=False, **kwargs):
        self.active = active
        self.soft = soft
        super().__init__(background_normal='', background_down='',
                         background_color=(0, 0, 0, 0), **kwargs)
        with self.canvas.before:
            self.fill = Color()
            self.shape = RoundedRectangle(radius=[dp(7)])
            self.edge_color = Color(*theme.CARD_BORDER)
            self.edge = Line(width=1)
        self.bind(pos=self._draw, size=self._draw, state=self._draw, disabled=self._draw)
        self._draw()

    def select(self, active):
        self.active = active
        self._draw()

    def _draw(self, *_):
        self.fill.rgba = (theme.BUTTON_DISABLED if self.disabled else
                          theme.TILE_PRESS_COLOR if self.state == 'down' else
                          theme.PRIMARY_ORANGE if self.active else theme.SURFACE)
        self.color = theme.TEXT_ON_ACCENT if self.active else theme.TEXT_PRIMARY
        if self.active and self.soft and self.state != 'down':
            self.fill.rgba = tuple(a * .12 + b * .88 for a, b in zip(theme.PRIMARY_ORANGE, theme.CARD))
            self.color = theme.PRIMARY_ORANGE_DARK if theme.get_mode() == 'light' else theme.PRIMARY_ORANGE
        self.shape.pos, self.shape.size = self.pos, self.size
        self.edge.rounded_rectangle = (*self.pos, *self.size, dp(7))


class SectionButton(CashButton):
    """Bereichsfarben für Register; Hauptaktionen behalten Vereinsorange."""
    def __init__(self, tone, **kwargs):
        self.tone = tone
        super().__init__(**kwargs)

    def _draw(self, *_):
        super()._draw()
        color = theme.section_color(self.tone)
        self.fill.rgba = color if self.active else theme.tinted(color, .07)
        self.color = theme.TEXT_ON_ACCENT if self.active else theme.TEXT_PRIMARY
        self.edge_color.rgba = color if self.active else theme.tinted(color, .25)
        if self.state == 'down':
            self.fill.rgba = theme.tinted(color, .65)
