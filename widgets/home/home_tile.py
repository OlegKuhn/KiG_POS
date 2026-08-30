from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty

from kivy.metrics import dp

import theme

from widgets.kig_label import KiGLabel
from widgets.kig_tile import KiGTile


class HomeTile(KiGTile):

    title = StringProperty("")
    subtitle = StringProperty("")
    icon = StringProperty("")

    # Kleiner als die allgemeine Kachel (KiGTile: 260 x 180): Auf der
    # Startseite zählt, wie viele Bereiche auf einen Blick zu sehen
    # sind - im Hochformat passt so eine Kachel mehr in die Reihe.
    WIDTH = 210
    HEIGHT = 140

    # Auf dem Telefon: zwei nebeneinander statt einer. Bei 210 dp
    # Breite passte nur eine Kachel in die Zeile, und von neun waren
    # fünf zu sehen - der Rest lag unter dem Falz.
    NARROW_WIDTH = 172
    NARROW_HEIGHT = 104

    PADDING = theme.SPACE_M
    SPACING = theme.LABEL_SPACING

    ICON_SIZE = 56
    NARROW_ICON_SIZE = 38

    TITLE_SIZE = 17
    SUBTITLE_SIZE = 12

    NARROW_TITLE_SIZE = 14
    NARROW_SUBTITLE_SIZE = 10

    # Zwei Kacheln je Reihe - aber wie breit, entscheidet der
    # Bildschirm. Ein festes Mass ging schief: Gebaut fuer 412 dp,
    # gemessen auf einem S24 dann 339 dp - und schon passte nur noch
    # eine Kachel in die Reihe, mit viel Luft daneben.
    NARROW_SPALTEN = 2

    # Unter dieser Breite lohnt keine zweite Spalte mehr.
    NARROW_MIN_WIDTH = 130

    # Hoehe im Verhaeltnis zur Breite: Symbol, Titel und Untertitel
    # brauchen etwa zwei Drittel der Breite an Hoehe.
    NARROW_SEITENVERHAELTNIS = 0.64

    @classmethod
    def masse(cls):
        """Breite und Höhe der Kachel auf diesem Bildschirm."""

        if not theme.is_narrow():
            return cls.WIDTH, cls.HEIGHT

        verfuegbar = (
            (theme.CURRENT_WIDTH or cls.NARROW_WIDTH * 2)
            - 2 * theme.SCREEN_PADDING
            - (cls.NARROW_SPALTEN - 1) * theme.TILE_SPACING
        )

        breite = max(
            cls.NARROW_MIN_WIDTH, verfuegbar / cls.NARROW_SPALTEN
        )

        return breite, round(breite * cls.NARROW_SEITENVERHAELTNIS)

    def __init__(self, **kwargs):

        schmal = theme.is_narrow()

        if schmal:
            # Vor super(): KiGTile nimmt die Maße aus diesen Feldern.
            self.WIDTH, self.HEIGHT = self.masse()
            self.ICON_SIZE = self.NARROW_ICON_SIZE
            self.TITLE_SIZE = self.NARROW_TITLE_SIZE
            self.SUBTITLE_SIZE = self.NARROW_SUBTITLE_SIZE
            self.PADDING = theme.SPACE_S

        super().__init__(**kwargs)

        self.layout = BoxLayout(
            orientation="vertical",
            padding=dp(self.PADDING),
            spacing=dp(self.SPACING)
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
            size=(dp(self.ICON_SIZE), dp(self.ICON_SIZE)),
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

        # Auf dem Telefon ist die Kachel schmal: Ein langer Untertitel
        # ("Artikel, Bestand, Einkauf & Rezepte") braucht dort mehr
        # Zeilen, als die Kachel hoch ist - ab der dritten wird
        # abgeschnitten statt hinauszuwachsen.
        if theme.is_narrow():
            self.lbl_subtitle.max_lines = 2
            self.lbl_subtitle.shorten = True
            self.lbl_subtitle.shorten_from = "right"

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