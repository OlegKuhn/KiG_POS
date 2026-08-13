from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.kig_label import KiGLabel
from widgets.kig_tile import KiGTile


class KiGTextTile(KiGTile):

    title = StringProperty("")
    data = ObjectProperty(None)

    PADDING = theme.TILE_PADDING
    TITLE_SIZE = 18

    def __init__(
            self,
            text="",
            data=None,
            callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.data = data
        self.callback = callback

        self.size_hint = (None, None)
        self.size = (
            theme.CATEGORY_TILE_WIDTH,
            theme.CATEGORY_TILE_HEIGHT
        )

        self.layout = BoxLayout(
            orientation="vertical",
            padding=self.PADDING
        )

        self.add_widget(self.layout)

        self.lbl_title = KiGLabel(
            text=text
        )

        self.lbl_title.set_bold(True)
        self.lbl_title.set_font_size(self.TITLE_SIZE)
        self.lbl_title.set_color(theme.TEXT_PRIMARY)

        self.lbl_title.horizontal_alignment = "center"
        self.lbl_title.vertical_alignment = "middle"

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.layout.add_widget(self.lbl_title)

        self.bind(
            pos=self._update_layout,
            size=self._update_layout,
            title=self._update_content
        )

        self.title = text

        self._update_layout()
        self._update_content()

    # =====================================================
    # Layout
    # =====================================================

    def _update_layout(self, *args):

        self.layout.pos = self.pos
        self.layout.size = self.size

    # =====================================================
    # Inhalt
    # =====================================================

    def _update_content(self, *args):

        self.lbl_title.text = self.title
        self.lbl_title.text_size = self.lbl_title.size

    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def set_title(self, title: str):

        self.title = title

    # =====================================================
    # Callback
    # =====================================================

    def _dispatch_callback(self):

        if callable(self.callback):
            self.callback(self, self.data)

    # =====================================================
    # Auswahl
    # =====================================================

    def select(self):
        super().select()

        self.lbl_title.set_color(theme.TEXT_PRIMARY)

    def unselect(self):

        super().unselect()

        self.lbl_title.set_color(theme.TEXT_PRIMARY)

    # =====================================================
    # String
    # =====================================================

    def __repr__(self):

        return f"KiGTextTile(title='{self.title}')"

    # =====================================================
    # Button
    # =====================================================

    def on_release(self):
        self._dispatch_callback()