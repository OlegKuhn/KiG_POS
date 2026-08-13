"""Auswählbares Thema in der Userguide-Themenliste, im Stil von CategoryCard."""

from kivy.metrics import dp
from kivy.uix.button import Button

import theme


class UserguideTopicCard(Button):

    def __init__(self, topic, callback=None, **kwargs):
        super().__init__(**kwargs)

        self.topic = topic
        self.callback = callback

        self.size_hint = (1, None)
        self.height = dp(56)

        self.text = topic["title"]
        self.font_size = "18sp"
        self.bold = True

        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(theme.CARD_PADDING), 0)

        self.background_normal = ""
        self.background_down = ""

        self.background_color = theme.CARD
        self.color = theme.TEXT_PRIMARY

        self.bind(size=self._update_text_size)

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
            self.callback(self, self.topic)
