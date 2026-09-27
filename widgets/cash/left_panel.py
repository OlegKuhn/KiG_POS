"""Kassenauswahl mit Suchfeld und horizontalen Kategorie-Tasten."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from widgets.cash.article_panel import CashArticlePanel
from widgets.cash.design import CashButton, category_color


class CategoryButton(CashButton):
    def __init__(self, category, **kwargs):
        self.category = category
        super().__init__(text=category['name'], soft=True, size_hint_x=None, width=dp(154),
                         font_size='15sp', **kwargs)
        self.text_size = (dp(140), None)
        self.halign = 'center'
        with self.canvas.after:
            Color(*category_color(category['id']))
            self.marker = RoundedRectangle(radius=[dp(2)])
        self.bind(pos=self._marker, size=self._marker)
        self._marker()

    def _marker(self, *_):
        self.marker.pos = (self.x + dp(10), self.y + dp(5))
        self.marker.size = (max(0, self.width - dp(20)), dp(3))

    def unselect(self):
        self.select(False)

    def select(self, active=True):
        super().select(active)


class CashLeftPanel(BoxLayout):
    def __init__(self, categories=None, article_callback=None,
                 category_articles_callback=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.article_callback = article_callback
        self.category_articles_callback = category_articles_callback
        self._selected_card = None
        self.category_panel_widget = None
        self.article_panel_widget = CashArticlePanel(
            article_callback=article_callback, category_callback=category_articles_callback)
        self.category_row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        self.all_button = CashButton(text='Alle Kategorien', active=True, soft=True, size_hint_x=None,
                                     width=dp(150), font_size='16sp', bold=True)
        self.all_button.bind(on_release=lambda *_: self.show_all())
        self.category_row.add_widget(self.all_button)
        scroll = ScrollView(do_scroll_y=False, bar_width=dp(3))
        self.category_grid = BoxLayout(size_hint_x=None, spacing=dp(8))
        self.category_grid.bind(minimum_width=self.category_grid.setter('width'))
        scroll.add_widget(self.category_grid)
        self.category_row.add_widget(scroll)
        self.article_panel_widget.add_widget(self.category_row, index=1)
        self.add_widget(self.article_panel_widget)
        self.set_categories(categories or [])

    def show_all(self):
        self.clear_selection()
        self.article_panel_widget.show_category(None)

    def category_selected(self, card, category):
        if self._selected_card is card:
            self.show_all()
            return
        self.clear_selection()
        self._selected_card = card
        card.select()
        self.all_button.select(False)
        self.article_panel_widget.show_category(category)

    @property
    def selected_category(self):
        return self._selected_card.category if self._selected_card else None

    def clear_selection(self):
        if self._selected_card:
            self._selected_card.unselect()
        self._selected_card = None
        self.all_button.select(True)

    def set_categories(self, categories):
        self.article_panel_widget.category_names = {c['id']: c['name'] for c in categories}
        self.clear_selection()
        self.category_grid.clear_widgets()
        for category in categories:
            button = CategoryButton(category)
            button.bind(on_release=lambda card, value=category: self.category_selected(card, value))
            self.category_grid.add_widget(button)
