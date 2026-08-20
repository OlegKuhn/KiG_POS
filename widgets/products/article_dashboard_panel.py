"""Vollflächiges Dashboard eines einzelnen Artikels (ersetzt die Liste).

Fasst zusammen, was vorher auf vier getrennten Screens verteilt war:
Stammdaten (Artikel), Bestand (Inventar), Bestellmenge (Einkauf) und
bei Mix-Artikeln die Zusammensetzung (Rezepte). Die Karten stehen
nebeneinander statt untereinander - jede Karte füllt die volle
verfügbare Höhe und scrollt bei Bedarf intern (z. B. die
Bestandshistorie).
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import theme

from widgets.common.kig_symbol import KiGSymbolButton, PFEIL_LINKS

from widgets.kig_label import KiGLabel
from widgets.products.dashboard_stammdaten_card import StammdatenCard
from widgets.products.dashboard_bestand_card import BestandCard
from widgets.products.dashboard_bestellmenge_card import BestellmengeCard
from widgets.recipes.recipe_composition_panel import RecipeCompositionPanel


class ArticleDashboardPanel(BoxLayout):

    def __init__(
            self,
            on_back,
            on_save,
            on_numpad,
            on_adjust_stock,
            on_order_amount_button,
            on_receive_order,
            on_recipe_quantity,
            on_recipe_unit,
            on_recipe_remove,
            on_recipe_add_amount,
            on_recipe_add_confirm,
            on_recipe_add_free_text_amount=None,
            on_recipe_add_free_text_confirm=None,
            **kwargs
    ):
        super().__init__(orientation="vertical", spacing=dp(theme.CARD_SPACING), **kwargs)

        # -------------------------------------------------
        # Kopfzeile
        # -------------------------------------------------

        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.CARD_SPACING))

        # Der Pfeil wird gezeichnet: Kivys Schrift kennt "←" nicht
        # und setzte an seine Stelle ein leeres Kaestchen.
        back_button = KiGSymbolButton(
            symbol=PFEIL_LINKS,
            text="Zurück", size_hint_x=None, width=dp(130),
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="15sp", bold=True,
        )
        back_button.bind(on_release=lambda *_args: on_back())
        header.add_widget(back_button)

        self.title_label = KiGLabel(text="Artikel")
        self.title_label.set_font_size(26)
        self.title_label.set_bold(True)
        self.title_label.set_alignment("left")
        self.title_label.set_color(theme.TEXT_PRIMARY)
        header.add_widget(self.title_label)

        self.add_widget(header)

        # -------------------------------------------------
        # Karten - nebeneinander, jede füllt die volle Höhe
        # -------------------------------------------------

        self.cards_layout = BoxLayout(orientation="horizontal", spacing=dp(theme.SCREEN_SPACING))
        self.add_widget(self.cards_layout)

        self.stammdaten_card = StammdatenCard(
            on_save=on_save, on_numpad=on_numpad,         )

        self.bestand_card = BestandCard(on_adjust=on_adjust_stock)

        self.bestellmenge_card = BestellmengeCard(
            on_amount_button=on_order_amount_button, on_receive=on_receive_order,
        )

        self.rezept_card = RecipeCompositionPanel(
            quantity_callback=on_recipe_quantity,
            unit_callback=on_recipe_unit,
            remove_callback=on_recipe_remove,
            add_amount_callback=on_recipe_add_amount,
            add_confirm_callback=on_recipe_add_confirm,
            add_free_text_amount_callback=on_recipe_add_free_text_amount,
            add_free_text_confirm_callback=on_recipe_add_free_text_confirm,
                    )

    # =====================================================
    # Anzeige
    # =====================================================

    def show_for_new_article(self, category_id=None):
        """Leerer Artikel-Dialog. Bestand/Bestellmenge/Rezept ergeben
        erst nach dem ersten Speichern einen Sinn."""

        self.title_label.text = "Neuer Artikel"
        self.stammdaten_card.clear(category_id=category_id)

        self.cards_layout.clear_widgets()
        self.stammdaten_card.size_hint_x = 0.5
        self.cards_layout.add_widget(self.stammdaten_card)
        self.cards_layout.add_widget(BoxLayout(size_hint_x=0.5))

    def show_for_article(self, article):

        self.title_label.text = article["name"]
        self.stammdaten_card.load_article(article)

        self.cards_layout.clear_widgets()

        if article["article_type"] == "MIX":
            self.stammdaten_card.size_hint_x = 0.35
            self.rezept_card.size_hint_x = 0.65
            self.cards_layout.add_widget(self.stammdaten_card)
            self.cards_layout.add_widget(self.rezept_card)
        else:
            self.stammdaten_card.size_hint_x = 0.30
            self.bestand_card.size_hint_x = 0.38
            self.bestellmenge_card.size_hint_x = 0.32
            self.cards_layout.add_widget(self.stammdaten_card)
            self.cards_layout.add_widget(self.bestand_card)
            self.cards_layout.add_widget(self.bestellmenge_card)
