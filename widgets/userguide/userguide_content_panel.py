"""Rechtes Panel: Anzeige der Schritt-für-Schritt-Anleitung eines Themas."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel
from widgets.userguide.userguide_step_card import UserguideStepCard


class UserguideContentPanel(RoundedPanel):

    NO_TOPIC_TEXT = "Bitte links ein Thema auswählen"
    NO_STEPS_TEXT = "Für dieses Thema wird die Anleitung noch ergänzt."

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.title_label = KiGLabel(text=self.NO_TOPIC_TEXT)
        self.title_label.set_font_size(26)
        self.title_label.set_bold(True)
        self.title_label.set_alignment("left")
        self.title_label.set_color(theme.TEXT_PRIMARY)
        self.title_label.size_hint_y = None
        self.title_label.height = dp(42)
        self.add_widget(self.title_label)

        self.scroll = ScrollView(bar_width=dp(12))

        self.list_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            size_hint_y=None
        )
        self.list_layout.bind(
            minimum_height=self.list_layout.setter("height")
        )
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

    def set_topic(self, topic):

        self.list_layout.clear_widgets()

        if topic is None:
            self.title_label.text = self.NO_TOPIC_TEXT
            return

        self.title_label.text = topic["title"]

        steps = topic.get("steps") or []

        if not steps:
            self.list_layout.add_widget(self._empty_label())
            return

        for index, step in enumerate(steps, start=1):
            self.list_layout.add_widget(
                UserguideStepCard(number=index, step=step)
            )

    def _empty_label(self):

        label = KiGLabel(text=self.NO_STEPS_TEXT)
        label.set_font_size(16)
        label.set_alignment("left")
        label.set_color(theme.TEXT_SECONDARY)
        label.size_hint_y = None
        label.height = dp(60)
        return label
