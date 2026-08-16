from math import ceil

from kivy.uix.gridlayout import GridLayout

from kivy.metrics import dp

import theme


class KiGAdaptiveGrid(GridLayout):
    """Kachelraster, das die Spaltenzahl an die verfügbare Breite anpasst.

    padding ist bewusst 0: Das Raster sitzt immer in einer Karte, die
    bereits ihren eigenen Innenabstand (theme.CARD_PADDING) mitbringt -
    ein zusätzlicher Rand hier würde die Kacheln doppelt so weit vom
    Kartenrand wegrücken wie überall sonst.
    """

    def __init__(
            self,
            tile_width,
            tile_height,
            spacing=None,
            padding=0,
            fixed_cols=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        # -------------------------------------------------
        # Einstellungen
        # -------------------------------------------------

        # dp() erst hier, nicht im Standardargument: Dort wuerde es
        # beim Import einmalig ausgerechnet - und damit die
        # Bildschirmdichte einfrieren, die zu diesem Zeitpunkt gilt.
        if spacing is None:
            spacing = dp(theme.TILE_SPACING)

        self.tile_width = tile_width
        self.tile_height = tile_height

        # None = Spalten automatisch berechnen
        # Zahl = feste Anzahl an Spalten
        self.fixed_cols = fixed_cols

        # -------------------------------------------------
        # Grid
        # -------------------------------------------------

        self.cols = (
            self.fixed_cols
            if self.fixed_cols is not None
            else 1
        )

        self.col_default_width = self.tile_width
        self.row_default_height = self.tile_height

        self.col_force_default = True
        self.row_force_default = True

        self.spacing = (
            spacing,
            spacing
        )

        self.padding = (
            padding,
            padding
        )

        # -------------------------------------------------
        # Höhe
        # -------------------------------------------------

        self.size_hint_y = None

        self.bind(
            minimum_height=self.setter("height")
        )

        # -------------------------------------------------
        # Breitenänderungen beobachten
        # -------------------------------------------------

        self.bind(
            width=self._update_columns
        )

    # =====================================================
    # Spalten / Höhe aktualisieren
    # =====================================================

    def _update_columns(self, *args):

        if self.width <= 0:
            return

        horizontal_spacing = self.spacing[0]

        available_width = (
            self.width
            - self.padding[0]
            - self.padding[2]
        )

        # -------------------------------------------------
        # Spalten bestimmen
        # -------------------------------------------------

        if self.fixed_cols is not None:

            cols = max(
                1,
                int(self.fixed_cols)
            )

        else:

            cols = max(
                1,
                int(
                    (
                        available_width
                        + horizontal_spacing
                    )
                    //
                    (
                        self.tile_width
                        + horizontal_spacing
                    )
                )
            )

        if cols != self.cols:
            self.cols = cols

        # -------------------------------------------------
        # Zeilen berechnen
        # -------------------------------------------------

        child_count = len(
            self.children
        )

        if child_count == 0:
            rows = 0
        else:
            rows = ceil(
                child_count / self.cols
            )

        # -------------------------------------------------
        # Höhe berechnen
        # -------------------------------------------------

        vertical_spacing = self.spacing[1]

        self.height = (
            self.padding[1]
            + self.padding[3]
            + rows * self.tile_height
            + max(
                0,
                rows - 1
            ) * vertical_spacing
        )

    # =====================================================
    # Kachel hinzufügen
    # =====================================================

    def add_tile(self, tile):

        # Das Grid bestimmt die Größe der Kachel.
        tile.size_hint = (
            None,
            None
        )

        tile.width = self.tile_width
        tile.height = self.tile_height

        super().add_widget(
            tile
        )

        self._update_columns()

    # =====================================================
    # Kacheln löschen
    # =====================================================

    def clear_tiles(self):

        super().clear_widgets()

        self._update_columns()

    # =====================================================
    # Kacheln setzen
    # =====================================================

    def set_tiles(
            self,
            items,
            tile_class,
            callback=None
    ):

        self.clear_tiles()

        for item in items:

            if callback is None:

                tile = tile_class(
                    item
                )

            else:

                tile = tile_class(
                    item,
                    callback=callback
                )

            self.add_tile(
                tile
            )