"""Dialog zum Festlegen der Reihenfolge von Kategorien und Artikeln."""

from kivy.graphics import Color, Rectangle, RoundedRectangle, Triangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from widgets.common.kig_popup import KiGPopup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import theme

from database import DatabaseManager
from widgets.cash.article_tile import CashArticleTile
from widgets.cash.category_tile import CashCategoryTile
from widgets.common.kig_action_tile import KiGActionTile
from widgets.kig_label import KiGLabel


class ArrowButton(ButtonBehavior, Widget):
    """Touch-Schaltfläche mit gezeichnetem Pfeil, unabhängig von Schriftarten."""

    def __init__(self, direction, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.callback = callback

        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.background = RoundedRectangle(radius=[dp(12)])
            Color(1, 1, 1, 1)
            self.arrow = Triangle()

        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *_args):
        self.background.pos = self.pos
        self.background.size = self.size

        center_x = self.center_x
        center_y = self.center_y
        size = min(self.width, self.height) * 0.24

        if self.direction == "up":
            self.arrow.points = (
                center_x, center_y + size,
                center_x - size, center_y - size,
                center_x + size, center_y - size
            )
        else:
            self.arrow.points = (
                center_x, center_y - size,
                center_x - size, center_y + size,
                center_x + size, center_y + size
            )

    def on_release(self):
        if callable(self.callback):
            self.callback()


class ProductSortDialog(KiGPopup):
    """Touchfreundliche Reihenfolgeverwaltung mit Auf-/Ab-Pfeilen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db = DatabaseManager()
        self.title = "Produkt-Sortierung"
        self.size_hint = (0.95, 0.90)
        self.auto_dismiss = False

        self.categories = []
        self.category_tiles = []
        self.article_tiles_by_category = {}
        self.selected_category = None
        self.selected_category_tile = None
        self.selected_article_tile = None

        self.content = self._build_ui()
        self._load_categories()

    def _build_ui(self):
        root = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
        )

        # Eigener, themefähiger Hintergrund statt des Kivy-eigenen
        # Popup-Standardskins - so ist der Kontrast zu den Labels in
        # jedem Modus garantiert (siehe _title()).
        with root.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_background, size=self._update_background)

        body = BoxLayout(orientation="horizontal", spacing=dp(theme.SCREEN_SPACING))
        body.add_widget(self._build_category_column())
        body.add_widget(self._build_article_column())
        root.add_widget(body)

        buttons = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(theme.ROW_SPACING))
        buttons.add_widget(KiGActionTile(text="Abbrechen", callback=lambda *_: self.dismiss()))
        buttons.add_widget(KiGActionTile(text="Speichern", callback=self.save))
        root.add_widget(buttons)
        return root

    def _build_category_column(self):
        column = BoxLayout(orientation="vertical", spacing=dp(theme.CARD_SPACING))
        column.add_widget(self._title("Kategorien"))
        self.category_layout = self._make_list(column)

        controls = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(theme.ROW_SPACING))
        controls.add_widget(ArrowButton("up", callback=lambda: self.move_category(-1)))
        controls.add_widget(ArrowButton("down", callback=lambda: self.move_category(1)))
        column.add_widget(controls)
        return column

    def _build_article_column(self):
        column = BoxLayout(orientation="vertical", spacing=dp(theme.CARD_SPACING))
        column.add_widget(self._title("Artikel der Kategorie"))
        self.article_layout = self._make_list(column)

        controls = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(theme.ROW_SPACING))
        controls.add_widget(ArrowButton("up", callback=lambda: self.move_article(-1)))
        controls.add_widget(ArrowButton("down", callback=lambda: self.move_article(1)))
        column.add_widget(controls)
        return column

    def _update_background(self, instance, _value):
        self._background.pos = instance.pos
        self._background.size = instance.size

    @staticmethod
    def _title(text):
        label = KiGLabel(text=text)
        label.set_font_size(24)
        label.set_bold(True)
        label.set_alignment("left")
        label.set_color(theme.TEXT_PRIMARY)
        label.size_hint_y = None
        label.height = dp(40)
        return label

    @staticmethod
    def _make_list(parent):
        scroll = ScrollView(bar_width=dp(12))
        layout = BoxLayout(orientation="vertical", spacing=dp(theme.ROW_SPACING), size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))
        scroll.add_widget(layout)
        parent.add_widget(scroll)
        return layout

    def _load_categories(self):
        self.categories = list(self.db.get_categories())
        self.category_tiles = [self._make_category_tile(category) for category in self.categories]
        self._refresh_category_view()

        if self.category_tiles:
            self.select_category(self.category_tiles[0], self.categories[0])

    def _make_category_tile(self, category):
        tile = CashCategoryTile(category=category, callback=self.select_category)
        tile.size_hint = (1, None)
        tile.height = dp(70)
        return tile

    def _make_article_tile(self, article):
        tile = CashArticleTile(article=article, callback=self.select_article)
        tile.size_hint = (1, None)
        tile.height = dp(100)
        return tile

    def select_category(self, tile, category):
        if self.selected_category_tile is not None:
            self.selected_category_tile.unselect()

        self.selected_category = category
        self.selected_category_tile = tile
        tile.select()
        self.selected_article_tile = None
        self._load_articles(category["id"])

    def _load_articles(self, category_id):
        if category_id not in self.article_tiles_by_category:
            rows = self.db.get_articles_by_category(category_id, active_only=False)
            self.article_tiles_by_category[category_id] = [
                self._make_article_tile(article) for article in rows
            ]

        self._refresh_article_view()

    def select_article(self, tile, _article):
        if self.selected_article_tile is not None:
            self.selected_article_tile.unselect()

        self.selected_article_tile = tile
        tile.select()

    def move_category(self, offset):
        if self.selected_category_tile is None:
            return

        index = self.category_tiles.index(self.selected_category_tile)
        target = index + offset
        if not 0 <= target < len(self.category_tiles):
            return

        self.category_tiles[index], self.category_tiles[target] = (
            self.category_tiles[target], self.category_tiles[index]
        )
        self._refresh_category_view()

    def move_article(self, offset):
        if self.selected_category is None or self.selected_article_tile is None:
            return

        tiles = self.article_tiles_by_category[self.selected_category["id"]]
        index = tiles.index(self.selected_article_tile)
        target = index + offset
        if not 0 <= target < len(tiles):
            return

        tiles[index], tiles[target] = tiles[target], tiles[index]
        self._refresh_article_view()

    def _refresh_category_view(self):
        self.category_layout.clear_widgets()
        for tile in self.category_tiles:
            self.category_layout.add_widget(tile)

    def _refresh_article_view(self):
        self.article_layout.clear_widgets()
        if self.selected_category is None:
            return

        for tile in self.article_tiles_by_category[self.selected_category["id"]]:
            self.article_layout.add_widget(tile)

    def save(self, *_args):
        self.db.set_category_order([tile.data["id"] for tile in self.category_tiles])

        for article_tiles in self.article_tiles_by_category.values():
            self.db.set_article_order([tile.article["id"] for tile in article_tiles])

        self.dismiss()
