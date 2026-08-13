"""Anzeige eines einzelnen Eintrags der Bestandsänderungshistorie."""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

import theme


class HistoryTile(BoxLayout):
    """Ein bewusst einfaches Layout, damit Historientexte stets sichtbar sind."""

    def __init__(self, history_entry, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.LABEL_SPACING),
            padding=dp(theme.CARD_SPACING),
            size_hint_y=None,
            height=dp(142),
            **kwargs
        )

        with self.canvas.before:
            Color(*theme.CARD)
            self._background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )

        self.bind(pos=self._update_background, size=self._update_background)

        old_quantity = self.format_quantity(history_entry["old_quantity"])
        new_quantity = self.format_quantity(history_entry["new_quantity"])

        self.add_widget(self._create_label(history_entry["reason"], bold=True))
        self.add_widget(
            self._create_label(f"Bestand: {old_quantity} -> {new_quantity}")
        )
        self.add_widget(
            self._create_label(
                f"Bearbeitet von: {history_entry['changed_by']}"
            )
        )
        self.add_widget(self._create_label(history_entry["changed_at"]))

    def _update_background(self, *_):
        self._background.pos = self.pos
        self._background.size = self.size

    @staticmethod
    def _create_label(text, bold=False):
        """Standard-Label statt KiGLabel, mit fest schwarzer Schriftfarbe."""

        return Label(
            text=str(text or "-"),
            color=theme.TEXT_PRIMARY,
            bold=bold,
            font_size="16sp",
            halign="left",
            valign="middle",
            text_size=(None, dp(25)),
            size_hint_y=None,
            height=dp(25)
        )

    @staticmethod
    def format_quantity(value):
        try:
            numeric_value = float(value)
            if numeric_value.is_integer():
                return str(int(numeric_value))
            return f"{numeric_value:.2f}"
        except (TypeError, ValueError):
            return "-"
