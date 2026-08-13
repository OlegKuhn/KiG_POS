from kivy.graphics import Color
from kivy.graphics import RoundedRectangle
from kivy.uix.boxlayout import BoxLayout

import config
import theme

from widgets.kig_label import KiGLabel


class AmountDisplay(BoxLayout):

    HEIGHT = 70
    RADIUS = 8

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.size_hint = (1, None)
        self.height = self.HEIGHT

        self._value = 0
        self._mode = "price"

        # =====================================================
        # Hintergrund
        # =====================================================

        with self.canvas.before:

            Color(1, 1, 1, 1)

            self.background = RoundedRectangle(
                radius=[self.RADIUS]
            )

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        # =====================================================
        # Anzeige
        # =====================================================

        self.lbl_amount = KiGLabel()

        self.lbl_amount.set_bold(True)
        self.lbl_amount.set_font_size(32)
        self.lbl_amount.set_color(theme.PRIMARY_ORANGE)

        self.lbl_amount.horizontal_alignment = "center"
        self.lbl_amount.vertical_alignment = "middle"

        self.lbl_amount.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(self.lbl_amount)

        self._update()

    # =====================================================
    # Canvas
    # =====================================================

    def _update_canvas(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

    # =====================================================
    # Eigenschaften
    # =====================================================

    @property
    def value(self):

        return self._value

    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def set_value(self, value, mode="price"):

        self._value = max(0, int(value))
        self._mode = mode

        self._update()

    # -----------------------------------------------------

    def clear(self):

        self.set_value(0, self._mode)

    # =====================================================
    # Intern
    # =====================================================

    def _update(self):

        if self._mode == "price":

            euro = self._value // 100
            cent = self._value % 100

            self.lbl_amount.text = (
                f"{euro},{cent:02d} {config.CURRENCY}"
            )

        else:

            self.lbl_amount.text = str(self._value)