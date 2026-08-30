from kivy.metrics import dp
from kivy.uix.button import Button

import theme


class CategoryCard(Button):
    """Einfache auswählbare Kategorie."""

    def __init__(
            self,
            category,
            callback=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.category = category
        self.callback = callback

        self.size_hint = (1, None)
        self.height = dp(52) if theme.is_narrow() else dp(64)

        self.text = category["name"]

        # Auf dem Telefon stehen zwei Karten nebeneinander - mit 19 sp
        # brach "Alkoholfrei" dort dreizeilig um.
        self.font_size = "15sp" if theme.is_narrow() else "19sp"
        self.bold = True

        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(theme.CARD_PADDING), 0)

        self.background_normal = ""
        self.background_down = ""

        self.background_color = theme.CARD
        self.color = theme.TEXT_PRIMARY

        self.bind(
            size=self._update_text_size
        )

    def _update_text_size(self, *_args):

        self.text_size = (
            self.width - dp(32),
            self.height
        )

    def select(self):

        self.background_color = theme.PRIMARY_ORANGE
        self.color = theme.TEXT_WHITE

    def unselect(self):

        self.background_color = theme.CARD
        self.color = theme.TEXT_PRIMARY

    def on_release(self):

        if callable(self.callback):
            self.callback(
                self,
                self.category
            )

