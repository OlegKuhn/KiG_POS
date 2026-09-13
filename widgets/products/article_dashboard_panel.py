"""Vollflächiges Dashboard eines einzelnen Artikels (ersetzt die Liste).

Aufbau eines Einzelartikels im Querformat:

    +--------------------------------------+------------------+
    | Stammdaten                           | Bestandsverlauf  |
    |   Angaben            Schalter        |   Datum  Grund   |
    |   Name   ...         Aktiv    [x]    |   ...             |
    |   Preis  ...         An Kasse [x]    |                  |
    +--------------------------------------+                  |
    | Bestand  45 Stück   [Bestand anpassen]                  |
    +--------------------------------------+------------------+

Die Bestellmenge steht hier nicht mehr: Sie wird direkt in der
Artikelliste gebucht, und doppelt gefuehrt nahm sie den Stammdaten
eine ganze Spalte.

Mix-Artikel haben keinen eigenen Bestand; neben ihren Stammdaten steht
die Zusammensetzung.
"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

import theme

from widgets.common.kig_symbol import KiGSymbolButton, PFEIL_LINKS

from widgets.kig_label import KiGLabel
from widgets.products.dashboard_stammdaten_card import StammdatenCard
from widgets.products.dashboard_bestand_card import BestandCard
from widgets.products.dashboard_verlauf_card import VerlaufCard
from widgets.recipes.recipe_composition_panel import RecipeCompositionPanel


class ArticleDashboardPanel(BoxLayout):

    def __init__(
            self,
            on_back,
            on_save,
            on_numpad,
            on_adjust_stock,
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
        # Karten
        # -------------------------------------------------
        #
        # Am Rechner und auf dem Tablet nebeneinander, jede fuellt die
        # volle Hoehe.
        #
        # Auf dem Telefon untereinander in einem Rollbereich: Drei
        # Karten nebeneinander liessen der Stammdatenkarte dort 103
        # von 384 Punkten - die Eingabefelder waren 32 Punkte breit
        # und damit unbenutzbar. Untereinander bekommt jede die ganze
        # Breite.
        self.schmal = theme.is_narrow()

        self.cards_layout = BoxLayout(
            orientation="vertical" if self.schmal else "horizontal",
            spacing=dp(theme.SCREEN_SPACING),
        )

        if self.schmal:

            self.cards_layout.size_hint_y = None
            self.cards_layout.bind(
                minimum_height=self.cards_layout.setter("height")
            )

            self.karten_rollbereich = ScrollView(
                do_scroll_x=False, bar_width=dp(8)
            )
            self.karten_rollbereich.add_widget(self.cards_layout)

            self.add_widget(self.karten_rollbereich)

        else:
            self.add_widget(self.cards_layout)

        self.stammdaten_card = StammdatenCard(
            on_save=on_save, on_numpad=on_numpad,         )

        self.bestand_card = BestandCard(on_adjust=on_adjust_stock)

        self.verlauf_card = VerlaufCard()

        # Links stehen Stammdaten und Bestand uebereinander - als eine
        # Spalte neben dem Verlauf.
        self.links = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SCREEN_SPACING),
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

    def _leeren(self):
        """Nimmt alle Karten heraus - auch aus der linken Spalte, sonst
        haengen sie beim naechsten Artikel noch dort."""

        self.cards_layout.clear_widgets()
        self.links.clear_widgets()

        self.stammdaten_card.size_hint = (1, 1)

    def show_for_new_article(self, category_id=None):
        """Leerer Artikel-Dialog. Bestand und Rezept ergeben erst nach
        dem ersten Speichern einen Sinn."""

        self.title_label.text = "Neuer Artikel"
        self.stammdaten_card.clear(category_id=category_id)

        self._leeren()

        if self.schmal:
            self.stammdaten_card.set_zweispaltig(False)
            self._untereinander([(self.stammdaten_card, 430)])
            return

        self.cards_layout.orientation = "horizontal"

        self.stammdaten_card.set_zweispaltig(True)
        self.stammdaten_card.size_hint_x = 0.62

        self.cards_layout.add_widget(self.stammdaten_card)
        self.cards_layout.add_widget(BoxLayout(size_hint_x=0.38))

    def show_for_article(self, article):

        self.title_label.text = article["name"]
        self.stammdaten_card.load_article(article)

        self._leeren()

        ist_mix = article["article_type"] == "MIX"

        if self.schmal:

            self.stammdaten_card.set_zweispaltig(False)

            if ist_mix:
                self._untereinander([
                    (self.stammdaten_card, 430),
                    (self.rezept_card, 380),
                ])

            else:
                self._untereinander([
                    (self.stammdaten_card, 430),
                    (self.bestand_card, 90),
                    (self.verlauf_card, 300),
                ])

            return

        if ist_mix:

            # Neben dem Rezept ist fuer zwei Spalten kein Platz.
            self.cards_layout.orientation = "horizontal"

            self.stammdaten_card.set_zweispaltig(False)
            self.stammdaten_card.size_hint_x = 0.35
            self.rezept_card.size_hint_x = 0.65

            self.cards_layout.add_widget(self.stammdaten_card)
            self.cards_layout.add_widget(self.rezept_card)

            return

        self.stammdaten_card.set_zweispaltig(True)

        self.links.add_widget(self.stammdaten_card)
        self.links.add_widget(self.bestand_card)

        if theme.is_portrait():

            # Hochkant: Stammdaten und Bestand oben, der Verlauf
            # darunter ueber die volle Breite.
            self.cards_layout.orientation = "vertical"

            self.links.size_hint = (1, 0.62)
            self.verlauf_card.size_hint = (1, 0.38)

        else:

            self.cards_layout.orientation = "horizontal"

            self.links.size_hint = (0.62, 1)
            self.verlauf_card.size_hint = (0.38, 1)

        self.cards_layout.add_widget(self.links)
        self.cards_layout.add_widget(self.verlauf_card)

    def _untereinander(self, karten):
        """Stellt die Karten auf dem Telefon untereinander.

        Jede bekommt die ganze Breite und eine eigene Hoehe - sonst
        teilten sie sich die Hoehe des Rollbereichs und waeren alle
        drei zu flach.
        """

        self._karten_hoehen = karten

        for karte, hoehe in karten:

            karte.size_hint_x = 1
            karte.size_hint_y = None
            karte.height = dp(hoehe)

            self.cards_layout.add_widget(karte)

        # Nach oben rollen - sonst steht der Bereich dort, wo er beim
        # letzten Mal stand, und beim ersten Oeffnen ganz unten: Die
        # erste Karte lag dann oberhalb des Sichtfensters, der
        # Bildschirm wirkte leer.
        Clock.schedule_once(self._nach_oben, 0)

    def _nach_oben(self, *_args):

        # Erst die Hoehen: Eine Karte, die ihre Zeilen selbst zaehlen
        # kann, bekommt so viel, wie sie braucht - der feste Wert ist
        # nur die Untergrenze. (Die Zeilen stehen erst im naechsten
        # Bild, deshalb geschieht das hier und nicht in
        # _untereinander.)
        for karte, hoehe in getattr(self, "_karten_hoehen", ()):

            gebraucht = getattr(karte, "inhaltshoehe", None)

            if callable(gebraucht):
                karte.height = max(dp(hoehe), gebraucht())

        if getattr(self, "karten_rollbereich", None) is not None:
            self.karten_rollbereich.scroll_y = 1
