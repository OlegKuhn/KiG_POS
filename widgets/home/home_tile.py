from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty

import theme

from widgets.kig_label import KiGLabel
from widgets.kig_tile import KiGTile


class HomeTile(KiGTile):

    title = StringProperty("")
    subtitle = StringProperty("")
    icon = StringProperty("")

    PADDING = theme.CARD_PADDING
    SPACING = theme.LABEL_SPACING

    ICON_SIZE = 72

    TITLE_SIZE = 20
    SUBTITLE_SIZE = 14

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.layout = BoxLayout(
            orientation="vertical",
            padding=self.PADDING,
            spacing=self.SPACING
        )

        self.add_widget(self.layout)

        self.icon_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 0.42)
        )

        self.img_icon = Image(
            source="",
            size_hint=(None, None),
            size=(self.ICON_SIZE, self.ICON_SIZE),
            fit_mode="contain",
            mipmap=True
        )

        self.icon_container.add_widget(
            self.img_icon
        )

        self.layout.add_widget(
            self.icon_container
        )

        self.lbl_title = KiGLabel()

        self.lbl_title.set_bold(True)
        self.lbl_title.set_font_size(self.TITLE_SIZE)
        self.lbl_title.set_color(theme.PRIMARY_ORANGE)

        self.lbl_title.horizontal_alignment = "center"
        self.lbl_title.vertical_alignment = "middle"

        self.lbl_title.size_hint = (1, 0.16)

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.layout.add_widget(
            self.lbl_title
        )

        self.lbl_subtitle = KiGLabel()

        self.lbl_subtitle.set_bold(False)
        self.lbl_subtitle.set_font_size(self.SUBTITLE_SIZE)
        self.lbl_subtitle.set_color(theme.TEXT_SECONDARY)

        self.lbl_subtitle.horizontal_alignment = "center"
        self.lbl_subtitle.vertical_alignment = "middle"

        # Etwas mehr Höhe als der Titel: manche Kacheln (z. B. "ARTIKEL")
        # haben einen längeren Untertitel, der auf zwei Zeilen umbricht -
        # sonst würde er über den unteren Rand der Kachel hinausragen.
        self.lbl_subtitle.size_hint = (1, 0.30)

        self.lbl_subtitle.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.layout.add_widget(
            self.lbl_subtitle
        )

        self.bind(
            pos=self._update_layout,
            size=self._update_layout,
            title=self._update_content,
            subtitle=self._update_content,
            icon=self._update_content
        )

        self._update_layout()
        self._update_content()

    def _update_layout(self, *args):

        self.layout.pos = self.pos
        self.layout.size = self.size

    # =====================================================
    # Inhalt aktualisieren
    # =====================================================

    def _update_content(self, *args):

        self.img_icon.source = self.icon
        self.img_icon.reload()

        self.lbl_title.text = self.title
        self.lbl_title.text_size = self.lbl_title.size

        self.lbl_subtitle.text = self.subtitle
        self.lbl_subtitle.text_size = self.lbl_subtitle.size

    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def set_title(self, title: str):

        self.title = title

    # -----------------------------------------------------

    def set_subtitle(self, subtitle: str):

        self.subtitle = subtitle

    # -----------------------------------------------------

    def set_icon(self, icon: str):

        self.icon = icon

    # =====================================================
    # String
    # =====================================================

    def __repr__(self):

        return (
            f"HomeTile(title='{self.title}')"
        )

    def on_release(self):
        super().on_release()

        if callable(self.callback):
            self.callback()