from functools import partial

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

import theme

from widgets.common.kig_action_tile import KiGActionTile
from widgets.common.numpad.amount_display import AmountDisplay
from widgets.common.numpad.numpad_button import NumpadButton
from widgets.common.slide_panel import SlidePanel


class NumpadPanel(SlidePanel, BoxLayout):

    DISPLAY_WIDTH = 290
    DISPLAY_HEIGHT = 90

    GRID_SPACING = theme.ROW_SPACING

    BUTTON_BAR_HEIGHT = 80

    def __init__(
            self,
            confirm_callback=None,
            cancel_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback

        self._value = 0

        self.orientation = "vertical"

        self.init_slide(theme.NUMPAD_PANEL_WIDTH)

        self.padding = theme.CARD_PADDING
        self.spacing = theme.CARD_SPACING

        self.mode = "price"

        #
        # Hintergrund
        #

        self.canvas.before.clear()

        with self.canvas.before:

            from kivy.graphics import Color
            from kivy.graphics import Rectangle

            Color(*theme.CART_BACKGROUND)

            self.background = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        #
        # Display
        #

        self.display_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, None),
            height=self.DISPLAY_HEIGHT
        )

        self.display = AmountDisplay()

        self.display.size_hint = (None, None)
        self.display.width = self.DISPLAY_WIDTH
        self.display.height = self.DISPLAY_HEIGHT

        self.display_container.add_widget(
            self.display
        )

        self.add_widget(
            self.display_container
        )

        #
        # Nummernblock
        #

        self.grid_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 1)
        )

        self.grid = GridLayout(
            cols=3,
            spacing=self.GRID_SPACING,
            size_hint=(None, None)
        )

        self.grid.bind(
            minimum_width=self.grid.setter("width"),
            minimum_height=self.grid.setter("height")
        )

        self.grid_container.add_widget(
            self.grid
        )

        self.add_widget(
            self.grid_container
        )

        #
        # Erste Reihe
        #

        self.grid.add_widget(
            NumpadButton(
                "7",
                callback=partial(
                    self._digit_pressed,
                    7
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "8",
                callback=partial(
                    self._digit_pressed,
                    8
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "9",
                callback=partial(
                    self._digit_pressed,
                    9
                )
            )
        )

        #
        # Zweite Reihe
        #

        self.grid.add_widget(
            NumpadButton(
                "4",
                callback=partial(
                    self._digit_pressed,
                    4
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "5",
                callback=partial(
                    self._digit_pressed,
                    5
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "6",
                callback=partial(
                    self._digit_pressed,
                    6
                )
            )
        )

        #
        # Dritte Reihe
        #

        self.grid.add_widget(
            NumpadButton(
                "1",
                callback=partial(
                    self._digit_pressed,
                    1
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "2",
                callback=partial(
                    self._digit_pressed,
                    2
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "3",
                callback=partial(
                    self._digit_pressed,
                    3
                )
            )
        )

        #
        # Vierte Reihe
        #

        self.grid.add_widget(
            NumpadButton(
                "C",
                callback=self._clear
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "0",
                callback=partial(
                    self._digit_pressed,
                    0
                )
            )
        )

        self.grid.add_widget(
            NumpadButton(
                "←",
                callback=self._backspace
            )
        )

        #
        # Buttons unten
        #

        self.button_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=self.BUTTON_BAR_HEIGHT,
            spacing=theme.ROW_SPACING
        )

        # Zwei Kacheln zu je 160 px (theme.CATEGORY_TILE_WIDTH) plus
        # Abstand ergeben 328 px und passen damit NICHT in die 318 px
        # zwischen den Innenrändern des Panels - sie ragten bisher
        # beidseitig heraus. Die Breite bestimmt deshalb die Reihe,
        # nicht die Kachel. WICHTIG: erst NACH der Konstruktion setzen,
        # KiGActionTile überschreibt übergebene Werte im Konstruktor.
        def schaltflaeche(text, callback):

            kachel = KiGActionTile(text=text, callback=callback)

            kachel.size_hint = (1, None)
            kachel.height = theme.CATEGORY_TILE_HEIGHT

            return kachel

        self.btn_cancel = schaltflaeche("Abbrechen", self._cancel)

        self.btn_confirm = schaltflaeche("Bestätigen", self._confirm)

        self.button_layout.add_widget(
            self.btn_cancel
        )

        self.button_layout.add_widget(
            self.btn_confirm
        )

        self.add_widget(
            self.button_layout
        )

        #
        # Anfangswert
        #

        self.display.set_value(0)

    # =====================================================
    # Zeichenfläche
    # =====================================================

    def _update_canvas(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

    # =====================================================
    # Eingabe
    # =====================================================

    def _digit_pressed(self, digit, *args):

        self._value = self._value * 10 + digit

        self.display.set_value(
            self._value,
            self.mode
        )

        if callable(self.change_callback):
            self.change_callback(self._value)

    # -----------------------------------------------------

    def _clear(self, *args):

        self._value = 0

        self.display.set_value(
            self._value,
            self.mode
        )

        if callable(self.change_callback):
            self.change_callback(self._value)

    # -----------------------------------------------------

    def _backspace(self, *args):

        self._value //= 10

        self.display.set_value(
            self._value,
            self.mode
        )

        if callable(self.change_callback):
            self.change_callback(self._value)

    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def set_value(self, value):

        self._value = max(
            0,
            int(value)
        )

        self.display.set_value(
            self._value,
            self.mode
        )

        if callable(self.change_callback):
            self.change_callback(self._value)

    # -----------------------------------------------------

    def get_value(self):

        return self._value

    # -----------------------------------------------------

    def clear(self):

        self.set_value(0)

    # =====================================================
    # Buttons
    # =====================================================

    def _confirm(self, *args):

        self.close()

        if callable(self.confirm_callback):

            self.confirm_callback(
                self.get_value()
            )

    # -----------------------------------------------------

    def _cancel(self, *args):

        self.close()

        if callable(self.cancel_callback):

            self.cancel_callback()

    # =====================================================
    # Öffnen
    # =====================================================

    def open(
            self,
            value=0,
            mode="price",
            confirm_callback=None,
            cancel_callback=None,
            change_callback=None
    ):

        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        self.change_callback = change_callback
        self.mode = mode

        # Startwert setzen
        self.set_value(value)

        self.slide_open()

    # =====================================================
    # Schließen
    # =====================================================

    def close(self):

        self.slide_close(on_closed=self._closed)

    # =====================================================

    def _closed(self, *args):

        self.confirm_callback = None
        self.cancel_callback = None
        self.change_callback = None