from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.cash.article_panel import CashArticlePanel
from widgets.products.category_panel import CategoryPanel


class CashLeftPanel(BoxLayout):
    """Kategorien und Artikel der Kasse.

    Aufgebaut wie die Artikelübersicht: links die Kategorien als
    Liste, rechts daneben die Artikel. Die frühere Kachelreihe über
    den Artikeln ist damit verschwunden - eine Liste zeigt bei vielen
    Kategorien mehr auf einen Blick und braucht weniger Höhe, die den
    Artikeln zugutekommt.

    Die Kategorienliste ist dieselbe wie in der Artikelverwaltung
    (widgets/products/category_panel.py), nur ohne deren
    Schaltflächen "Neu" und "Bearbeiten": An der Kasse wird
    ausgewählt, nicht verwaltet.
    """

    # Anteil der Kategorienliste an der Breite (Querformat).
    CATEGORY_WIDTH_SHARE = 0.28

    # Im Hochformat eine feste Höhe statt eines Anteils: Der
    # Artikelbereich teilt sich die Höhe mit dem Warenkorb, ein Anteil
    # davon ließe der Liste nicht einmal genug für ihre eigene
    # Überschrift. Gerechnet: Innenabstand (2x16) + Überschrift (60) +
    # Abstand (12) + eine Kategorienzeile (64) = 168.
    PORTRAIT_CATEGORY_HEIGHT = 175

    def __init__(
            self,
            categories=None,
            article_callback=None,
            category_articles_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.article_callback = article_callback
        self.category_articles_callback = category_articles_callback

        self._selected_card = None

        hochformat = theme.is_portrait()

        # Querformat: Kategorien links neben den Artikeln.
        # Hochformat: darüber - nebeneinander bliebe für die
        # Artikelkacheln zu wenig Breite.
        self.orientation = "vertical" if hochformat else "horizontal"
        self.spacing = dp(theme.SCREEN_SPACING)

        # =====================================================
        # Kategorien
        # =====================================================

        self.category_panel_widget = CategoryPanel(
            on_new=None,
            on_edit=None,
            show_actions=False,
        )

        if hochformat:
            self.category_panel_widget.size_hint = (1, None)
            self.category_panel_widget.height = dp(self.PORTRAIT_CATEGORY_HEIGHT)
        else:
            self.category_panel_widget.size_hint = (self.CATEGORY_WIDTH_SHARE, 1)

        # =====================================================
        # Artikel
        # =====================================================

        self.article_panel_widget = CashArticlePanel(
            article_callback=self.article_callback,
            category_callback=self.category_articles_callback,
        )

        if hochformat:
            self.article_panel_widget.size_hint = (1, 1)
        else:
            self.article_panel_widget.size_hint = (1 - self.CATEGORY_WIDTH_SHARE, 1)

        self.add_widget(self.category_panel_widget)
        self.add_widget(self.article_panel_widget)

        self.set_categories(categories or [])

    # =====================================================
    # Kategorie gewählt
    # =====================================================

    def category_selected(self, card, category):
        """Ein zweiter Tipp auf dieselbe Kategorie hebt den Filter
        wieder auf und zeigt alle Artikel."""

        if self._selected_card is card:
            card.unselect()
            self._selected_card = None
            self.article_panel_widget.show_category(None)
            return

        if self._selected_card is not None:
            self._selected_card.unselect()

        self._selected_card = card
        card.select()

        self.article_panel_widget.show_category(category)

    # =====================================================
    # Auswahl
    # =====================================================

    @property
    def selected_category(self):
        """Die gewählte Kategorie - oder None für "alle"."""

        if self._selected_card is None:
            return None

        return self._selected_card.category

    def clear_selection(self):

        if self._selected_card is not None:
            self._selected_card.unselect()

        self._selected_card = None

    # =====================================================
    # Kategorien aktualisieren
    # =====================================================

    def set_categories(self, categories):

        self.clear_selection()

        self.category_panel_widget.set_categories(
            categories,
            self.category_selected
        )
