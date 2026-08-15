from kivy.animation import Animation

from kivy.metrics import dp

import theme

from widgets.common.kig_action_tile import KiGActionTile


class NumpadButton(KiGActionTile):

    WIDTH = 90
    HEIGHT = 90

    def __init__(
            self,
            text,
            callback=None,
            **kwargs
    ):

        super().__init__(
            text=text,
            callback=callback,
            **kwargs
        )

        self.size_hint = (None, None)

        self.size = (
            dp(self.WIDTH),
            dp(self.HEIGHT)
        )

        self.background_color = theme.PRIMARY_ORANGE

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