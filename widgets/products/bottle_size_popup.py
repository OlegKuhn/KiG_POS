"""Popup: fragt beim Wareneingang eines "Flasche"-Artikels die Flaschengröße ab.

Der Bestand wird für solche Artikel immer intern in ml geführt - dieses
Popup rechnet "N Flaschen" in die tatsächlich zu bucherende ml-Menge um.
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.common.numpad.numpad_panel import NumpadPanel
from widgets.kig_label import KiGLabel
from kivy.uix.popup import Popup


class BottleSizePopup(Popup):

    def __init__(self, article_name, bottle_count, default_size_ml, on_confirm, **kwargs):
        super().__init__(**kwargs)

        self.on_confirm = on_confirm
        self.bottle_count = bottle_count

        self.title = "Flaschengröße"
        self.size_hint = (None, None)
        self.size = (theme.NUMPAD_PANEL_WIDTH + dp(50), dp(580))
        self.auto_dismiss = False

        root = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        with root.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_background, size=self._update_background)

        info = KiGLabel(
            text=(
                f"{bottle_count} × \"{article_name}\"\n"
                "Wie viel ml hat eine Flasche?"
            )
        )
        info.set_font_size(17)
        info.set_bold(True)
        info.set_alignment("left")
        info.set_color(theme.TEXT_PRIMARY)
        info.size_hint_y = None
        info.height = dp(64)
        root.add_widget(info)

        self.numpad = NumpadPanel()
        root.add_widget(self.numpad)

        self.content = root

        self.numpad.open(
            value=int(default_size_ml or 0),
            mode="integer",
            confirm_callback=self._confirmed,
            cancel_callback=self.dismiss,
        )

    def _update_background(self, instance, _value):
        self._background.pos = instance.pos
        self._background.size = instance.size

    def _confirmed(self, bottle_size_ml):

        self.dismiss()

        if bottle_size_ml <= 0:
            return

        if callable(self.on_confirm):
            self.on_confirm(bottle_size_ml)
