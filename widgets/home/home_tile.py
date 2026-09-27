"""Grosse, ruhige Navigationskarten ohne erfundene Inhalte."""
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

import theme
from widgets.kig_tile import KiGTile


class HomeTile(KiGTile):
    title = StringProperty("")
    subtitle = StringProperty("")
    index = StringProperty("")
    icon = StringProperty("")

    def __init__(self, primary=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(156)
        self.normal_color = (
            theme.SELECTION_BACKGROUND if theme.get_mode() == "dark"
            else (0.965, 0.875, 0.785, 1)
        ) if primary else theme.CARD
        self.background_color = self.normal_color
        self.border_color.rgba = theme.PRIMARY_ORANGE if primary else theme.CARD_BORDER
        self.layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(6))
        self.add_widget(self.layout)
        self.lbl_index = self._label(self.index, "12sp", theme.PRIMARY_ORANGE, True, 0.20)
        self.lbl_title = self._label(self.title, "23sp", theme.TEXT_PRIMARY, True, 0.42)
        self.lbl_subtitle = self._label(self.subtitle, "14sp", theme.TEXT_SECONDARY, False, 0.38)
        self.bind(pos=self._update_layout, size=self._update_layout,
                  title=self._update_content, subtitle=self._update_content,
                  index=self._update_content)
        self._update_layout()

    def _label(self, text, size, color, bold, height):
        label = Label(text=text, font_size=size, color=color, bold=bold,
                      halign="left", valign="middle", size_hint_y=height)
        label.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        self.layout.add_widget(label)
        return label

    def _update_layout(self, *_):
        self.layout.pos, self.layout.size = self.pos, self.size

    def _update_content(self, *_):
        self.lbl_index.text = self.index
        self.lbl_title.text = self.title
        self.lbl_subtitle.text = self.subtitle

    def set_title(self, title): self.title = title
    def set_subtitle(self, subtitle): self.subtitle = subtitle
    def set_icon(self, icon): self.icon = icon

    def on_release(self):
        if callable(self.callback):
            self.callback()
