from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView

import theme

from widgets.cash.category_tile import CashCategoryTile
from widgets.common.adaptive_grid import KiGAdaptiveGrid
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


class CashCategoryPanel(RoundedPanel):
    """
    Zeigt die Kategorien im CashScreen an.

    Aufgaben:
    - Kategorien darstellen
    - ausgewählte Kategorie markieren
    - ausgewählte Kategorie an CashLeftPanel weitergeben

    Optisch an widgets/products/category_panel.py angeglichen (weiße
    Karte mit orangem Titel) - die Kategorien bleiben aber bewusst
    antippbare Kacheln statt einer Liste, da das für den Kassenbetrieb
    die bessere Bedienbarkeit bietet.
    """

    def __init__(
            self,
            categories=None,
            callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.callback = callback
        self.active_tile = None

        self.orientation = "vertical"
        self.padding = dp(theme.CARD_PADDING)
        self.spacing = dp(theme.CARD_SPACING)

        # =====================================================
        # Überschrift
        # =====================================================

        title = KiGLabel(text="Kategorien")
        title.set_font_size(22)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(32)
        self.add_widget(title)

        # =====================================================
        # Scrollbereich
        # =====================================================

        self.scroll = ScrollView(bar_width=dp(10))

        # =====================================================
        # Kategorie-Grid
        # =====================================================

        self.grid = KiGAdaptiveGrid(
            tile_width=dp(theme.CATEGORY_TILE_WIDTH),
            tile_height=dp(theme.CATEGORY_TILE_HEIGHT)
        )

        self.scroll.add_widget(
            self.grid
        )

        self.add_widget(
            self.scroll
        )

        # =====================================================
        # Kategorien setzen
        # =====================================================

        self.set_categories(
            categories or []
        )

    # =====================================================
    # Kategorien setzen
    # =====================================================

    def set_categories(self, categories):
        """
        Ersetzt die aktuell angezeigten Kategorien.
        """

        # Alte Auswahl verwerfen
        self.active_tile = None

        # Kacheln neu erzeugen
        self.grid.set_tiles(
            categories,
            CashCategoryTile,
            self.category_selected
        )

    # =====================================================
    # Kategorie gewählt
    # =====================================================

    def category_selected(self, tile, category):
        """
        Wird aufgerufen, wenn eine Kategorie angeklickt wurde.
        """

        # Ein zweiter Klick auf dieselbe Kategorie hebt den
        # Filter auf und zeigt wieder alle Artikel.
        if self.active_tile is tile:
            tile.unselect()
            self.active_tile = None

            if callable(self.callback):
                self.callback(None)

            return

        # Alte Auswahl entfernen

        if self.active_tile is not None:
            self.active_tile.unselect()

        # -------------------------------------------------
        # Neue Auswahl markieren
        # -------------------------------------------------

        tile.select()

        self.active_tile = tile

        # -------------------------------------------------
        # Kategorie weitergeben
        # -------------------------------------------------

        if callable(self.callback):
            self.callback(category)

    # =====================================================
    # Auswahl zurücksetzen
    # =====================================================

    def clear_selection(self):
        """
        Entfernt die aktuelle Kategorieauswahl.
        """

        if self.active_tile is not None:
            self.active_tile.unselect()

        self.active_tile = None
