from kivy.uix.behaviors import ButtonBehavior

from widgets.kig_label import KiGLabel


class ClickableLabel(ButtonBehavior, KiGLabel):

    def __init__(self, callback=None, **kwargs):

        super().__init__(**kwargs)

        self.callback = callback

    # -----------------------------------------------------

    def on_release(self):

        if callable(self.callback):
            self.callback(self)