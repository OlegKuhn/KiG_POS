from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.cash.category_panel import CashCategoryPanel
from widgets.cash.article_panel import CashArticlePanel


class CashLeftPanel(BoxLayout):

    # Feste Höhe der Kategorienkarte im Hochformat. Sie muss eine
    # ganze Kachelreihe fassen; weitere Reihen scrollen.
    PORTRAIT_CATEGORY_HEIGHT = 130

    def __init__(
            self,
            categories=None,
            article_callback=None,
            category_articles_callback=None,
            text_keyboard_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.article_callback = article_callback
        self.category_articles_callback = category_articles_callback

        self.orientation = "vertical"
        self.spacing = dp(theme.SCREEN_SPACING)

        # =====================================================
        # Kategorien (eigene weiße Karte, siehe category_panel.py)
        # =====================================================
        #
        # Im Hochformat teilt sich dieser Bereich die Höhe mit dem
        # Warenkorb darunter. Ein anteiliger Wert (0.24) ließe der
        # Kategorienkarte dann zu wenig für eine ganze Kachelreihe -
        # sie bekommt deshalb eine feste Höhe für genau eine Reihe;
        # weitere Reihen scrollen wie gewohnt.

        hochformat = theme.is_portrait()

        self.category_panel_widget = CashCategoryPanel(
            categories=categories or [],
            callback=self.category_selected,
            size_hint_y=None if hochformat else 0.24,
        )

        if hochformat:
            self.category_panel_widget.height = dp(self.PORTRAIT_CATEGORY_HEIGHT)

        # =====================================================
        # Artikel (eigene weiße Karte, siehe article_panel.py)
        # =====================================================

        self.article_panel_widget = CashArticlePanel(
            article_callback=self.article_callback,
            category_callback=self.category_articles_callback,
            text_keyboard_callback=text_keyboard_callback,
            size_hint_y=1 if hochformat else 0.76,
        )

        # =====================================================
        # Panels hinzufügen
        # =====================================================

        self.add_widget(
            self.category_panel_widget
        )

        self.add_widget(
            self.article_panel_widget
        )

    # =====================================================
    # Kategorie gewählt
    # =====================================================

    def category_selected(self, category):

        self.article_panel_widget.show_category(
            category
        )

    # =====================================================
    # Kategorien aktualisieren
    # =====================================================

    def set_categories(self, categories):

        self.category_panel_widget.set_categories(
            categories
        )