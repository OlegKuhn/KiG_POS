from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

import theme

from widgets.cash.article_tile import CashArticleTile
from widgets.common.adaptive_grid import KiGAdaptiveGrid
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


class CashArticlePanel(RoundedPanel):
    """Optisch an widgets/products/article_list_panel.py angeglichen
    (weiße Karte mit orangem Titel "Artikel") - die Artikel bleiben
    aber bewusst große, antippbare Kacheln statt einer Zeilenliste,
    da das für das schnelle Kassieren die bessere Bedienbarkeit
    bietet."""

    def __init__(
            self,
            article_callback=None,
            category_callback=None,
            text_keyboard_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.article_callback = article_callback
        self.category_callback = category_callback

        # Die zuletzt gesetzten Artikel im Original - die Suche filtert
        # nur die Anzeige, ohne die Kategorieauswahl zu verlieren.
        self._alle_artikel = []

        self.orientation = "vertical"
        self.padding = dp(theme.CARD_PADDING)
        self.spacing = dp(theme.CARD_SPACING)

        # =====================================================
        # Überschrift und Suche
        # =====================================================

        kopf = BoxLayout(
            size_hint_y=None, height=dp(44), spacing=dp(theme.ROW_SPACING)
        )

        title = KiGLabel(text="Artikel")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        kopf.add_widget(title)

        self.search_input = RoundedInput(
            hint_text="Artikel suchen...", multiline=False,
            kig_keyboard_mode="text",
            size_hint_x=None, width=dp(240),
        )
        self.search_input.text_keyboard_callback = text_keyboard_callback
        self.search_input.bind(text=lambda *_args: self._apply_filter())
        kopf.add_widget(self.search_input)

        self.clear_search_button = Button(
            text="X", size_hint=(None, None), size=(dp(44), dp(44)),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="16sp", bold=True, opacity=0, disabled=True,
        )
        self.clear_search_button.bind(on_release=lambda *_args: self.clear_search())
        kopf.add_widget(self.clear_search_button)

        self.add_widget(kopf)

        # =====================================================
        # ScrollView
        # =====================================================

        scroll = ScrollView(bar_width=dp(10))

        # =====================================================
        # Artikel-Grid
        # =====================================================

        # Das Raster bestimmt die Kachelgröße (siehe
        # KiGAdaptiveGrid.add_tile) - im Hochformat kleiner, damit eine
        # ganze Reihe sichtbar bleibt.
        if theme.is_portrait():
            kachel_breite = theme.PORTRAIT_ARTICLE_TILE_WIDTH
            kachel_hoehe = theme.PORTRAIT_ARTICLE_TILE_HEIGHT
        else:
            kachel_breite = theme.ARTICLE_TILE_WIDTH
            kachel_hoehe = theme.ARTICLE_TILE_HEIGHT

        self.grid = KiGAdaptiveGrid(
            tile_width=kachel_breite,
            tile_height=kachel_hoehe
        )

        scroll.add_widget(
            self.grid
        )

        self.add_widget(
            scroll
        )

    # =====================================================
    # Kategorie anzeigen
    # =====================================================

    def show_category(self, category):

        if callable(self.category_callback):

            articles = self.category_callback(
                category
            )

        else:

            articles = []

        # Suchbegriff zuruecksetzen, bevor die neue Auswahl kommt -
        # sonst blendet ein vergessener Suchtext stillschweigend
        # Artikel der frisch gewaehlten Kategorie aus.
        self.search_input.text = ""

        self.set_articles(
            articles
        )

    # =====================================================
    # Artikel anzeigen
    # =====================================================

    def set_articles(self, articles):

        self._alle_artikel = list(articles)
        self._apply_filter()

    # =====================================================
    # Suche
    # =====================================================

    def _apply_filter(self, *_args):
        """Zeigt nur Artikel, deren Name den Suchtext enthält.

        Bewusst "enthält" statt "beginnt mit": An der Bar tippt man
        eher "cola" als "jacky", um Jacky Cola zu finden.
        """

        suchtext = self.search_input.text.strip().lower()

        # Das kleine Kreuz erscheint nur, wenn es auch etwas
        # zurückzusetzen gibt.
        hat_suchtext = bool(suchtext)
        self.clear_search_button.opacity = 1 if hat_suchtext else 0
        self.clear_search_button.disabled = not hat_suchtext

        if suchtext:
            sichtbar = [
                artikel for artikel in self._alle_artikel
                if suchtext in self._artikelname(artikel).lower()
            ]
        else:
            sichtbar = self._alle_artikel

        self.grid.set_tiles(
            sichtbar,
            CashArticleTile,
            callback=self.article_callback
        )

    @staticmethod
    def _artikelname(artikel):
        """Unterstützt Article-Objekte ebenso wie sqlite3.Row."""

        if hasattr(artikel, "name"):
            return artikel.name

        return artikel["name"]

    def clear_search(self):
        """Setzt die Suche zurück - auch beim Betreten des Screens und
        beim Wechsel der Kategorie, damit nicht unbemerkt ein alter
        Suchbegriff Artikel ausblendet."""

        if self.search_input.text:
            self.search_input.text = ""
        else:
            self._apply_filter()

    # =====================================================
    # Leeren
    # =====================================================

    def clear(self):

        self._alle_artikel = []
        self.grid.clear_widgets()
