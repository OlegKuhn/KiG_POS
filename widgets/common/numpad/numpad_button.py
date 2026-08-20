from kivy.animation import Animation

from kivy.metrics import dp

import theme

from widgets.common.kig_action_tile import KiGActionTile
from widgets.common.kig_symbol import KiGSymbol


class NumpadButton(KiGActionTile):

    WIDTH = 90
    HEIGHT = 90

    def __init__(
            self,
            text,
            callback=None,
            symbol=None,
            **kwargs
    ):
        """symbol zeichnet statt einer Beschriftung ein Zeichen -
        gebraucht fuer die Ruecktaste, deren Pfeil in Kivys Schrift
        fehlt (siehe widgets/common/kig_symbol.py)."""

        super().__init__(
            text="" if symbol else text,
            callback=callback,
            **kwargs
        )

        self.size_hint = (None, None)

        self.size = (
            dp(self.WIDTH),
            dp(self.HEIGHT)
        )

        self.background_color = theme.PRIMARY_ORANGE

        if symbol:
            self.layout.remove_widget(self.lbl_title)
            self.layout.add_widget(KiGSymbol(
                symbol=symbol, color=theme.TEXT_WHITE, line_width=3.0,
            ))

    # =====================================================
    # Animation
    # =====================================================

    def animate_press(self):

        Animation.cancel_all(self, "background_color")

        (
            Animation(
                background_color=theme.TILE_PRESS_COLOR,
                duration=0.06
            )
            +
            Animation(
                background_color=theme.PRIMARY_ORANGE,
                duration=0.08
            )
        ).start(self)