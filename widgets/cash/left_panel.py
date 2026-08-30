from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.cash.article_panel import CashArticlePanel
from widgets.cash.schmales_artikelpanel import SchmalesArtikelpanel
from widgets.products.category_panel import CategoryPanel


class CashLeftPanel(BoxLayout):
    """Kategorien und Artikel der Kasse.

    Aufgebaut wie die Artikelübersicht: links die Kategorien als
    Liste, rechts daneben die Artikel - und zwar in beiden
    Ausrichtungen. Eine Liste zeigt bei vielen Kategorien mehr auf
    einen Blick als eine Kachelreihe, und nebeneinander nimmt sie den
    Artikeln keine Höhe weg. Gerade im Hochformat zählt das: Dort
    teilt sich der Artikelbereich die Höhe ohnehin schon mit dem
    Warenkorb.

    Die Kategorienliste ist dieselbe wie in der Artikelverwaltung
    (widgets/products/category_panel.py), nur ohne deren
    Schaltflächen "Neu" und "Bearbeiten": An der Kasse wird
    ausgewählt, nicht verwaltet.
    """

    # Anteil der Kategorienliste an der Breite ...
    CATEGORY_WIDTH_SHARE = 0.24

    # ... aber nie schmaler als das: Auf einem Telefon wären 24 % rund
    # 90 dp, und darin ist "Alkoholfrei" nicht mehr zu lesen.
    CATEGORY_MIN_WIDTH = 150

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

        self.orientation = "horizontal"
        self.spacing = dp(theme.SCREEN_SPACING)

        # Auf dem Telefon ist für zwei Spalten kein Platz - dort stehen
        # die Kategorien als Klappköpfe über ihren Artikeln (siehe
        # widgets/cash/schmales_artikelpanel.py). Nach außen sieht
        # dieses Panel gleich aus, deshalb merkt der Kassenbildschirm
        # nichts davon.
        self.schmal = theme.is_narrow()

        if self.schmal:

            self.category_panel_widget = None

            self.article_panel_widget = SchmalesArtikelpanel(
                article_callback=self.article_callback,
                category_callback=self.category_articles_callback,
            )

            self.add_widget(self.article_panel_widget)

            self.set_categories(categories or [])

            return

        # =====================================================
        # Kategorien
        # =====================================================

        self.category_panel_widget = CategoryPanel(
            on_new=None,
            on_edit=None,
            show_actions=False,

            # Auch im Hochformat eine Liste: Die Karte steht hier in
            # beiden Ausrichtungen als schmale Spalte neben den
            # Artikeln, nicht als flaches Band darüber.
            als_liste=True,
        )

        # Feste Breite statt Anteil, damit die Untergrenze greifen
        # kann (siehe _update_category_width).
        self.category_panel_widget.size_hint_x = None

        # =====================================================
        # Artikel
        # =====================================================

        self.article_panel_widget = CashArticlePanel(
            article_callback=self.article_callback,
            category_callback=self.category_articles_callback,
        )

        # Nimmt, was die Kategorienliste übrig lässt.
        self.article_panel_widget.size_hint_x = 1

        self.add_widget(self.category_panel_widget)
        self.add_widget(self.article_panel_widget)

        self.bind(width=self._update_category_width)
        self._update_category_width()

        self.set_categories(categories or [])

    # =====================================================
    # Breite der Kategorienliste
    # =====================================================

    def _update_category_width(self, *_args):

        if self.category_panel_widget is None:
            return

        self.category_panel_widget.width = max(
            dp(self.CATEGORY_MIN_WIDTH),
            self.width * self.CATEGORY_WIDTH_SHARE,
        )

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

        if self.schmal:
            return self.article_panel_widget.selected_category

        if self._selected_card is None:
            return None

        return self._selected_card.category

    def clear_selection(self):

        if self.schmal:
            # Zugeklappt zeigte die Kasse gar keine Artikel mehr -
            # deshalb rueckt hier die erste Kategorie nach.
            self.article_panel_widget.erste_oeffnen()
            return

        if self._selected_card is not None:
            self._selected_card.unselect()

        self._selected_card = None

    # =====================================================
    # Kategorien aktualisieren
    # =====================================================

    def set_categories(self, categories):

        if self.schmal:
            self.article_panel_widget.set_categories(categories)
            return

        self.clear_selection()

        self.category_panel_widget.set_categories(
            categories,
            self.category_selected
        )
