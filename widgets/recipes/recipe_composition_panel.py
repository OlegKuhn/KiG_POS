"""Rechtes Panel: Zusammensetzung (Zutaten + Mengen) eines Rezepts."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

import theme
import units

from widgets.common.feldausrichtung import links_ausrichten
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_panel import RoundedPanel
from widgets.common.rounded_spinner import RoundedSpinner
from widgets.kig_label import KiGLabel
from widgets.recipes.recipe_ingredient_row import RecipeIngredientRow


class RecipeCompositionPanel(RoundedPanel):
    """Zeigt die Zutatenliste des gewählten Rezepts und erlaubt es,
    weitere Zutaten mit Menge hinzuzufügen bzw. zu entfernen."""

    NO_RECIPE_TEXT = "Kein Rezept ausgewählt"
    NO_INGREDIENTS_TEXT = "Bitte zuerst eine Zutat anlegen (Artikel-Screen)."

    def __init__(
            self,
            quantity_callback,
            unit_callback,
            remove_callback,
            add_amount_callback,
            add_confirm_callback,
            add_free_text_amount_callback=None,
            add_free_text_confirm_callback=None,
            **kwargs
    ):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.quantity_callback = quantity_callback
        self.unit_callback = unit_callback
        self.remove_callback = remove_callback
        self.add_amount_callback = add_amount_callback
        self.add_confirm_callback = add_confirm_callback
        self.add_free_text_amount_callback = add_free_text_amount_callback
        self.add_free_text_confirm_callback = add_free_text_confirm_callback

        self.ingredient_options = {}
        self.ingredient_units = {}
        self._add_amount = 0
        self._add_free_text_amount = 0

        #
        # Überschrift
        #

        self.title_label = KiGLabel(text=self.NO_RECIPE_TEXT)
        self.title_label.set_font_size(26)
        self.title_label.set_bold(True)
        self.title_label.set_alignment("left")
        self.title_label.set_color(theme.TEXT_PRIMARY)
        self.title_label.size_hint_y = None
        self.title_label.height = dp(42)
        self.add_widget(self.title_label)

        # Die Ueberschrift der Karte lautet beim Rezept selbst schon
        # "Zusammensetzung" (siehe products_screen). Auf dem Telefon
        # stand das Wort deshalb zweimal untereinander - dort bleibt
        # die Zweitzeile weg.
        self.subtitle = KiGLabel(text="Zusammensetzung")
        self.subtitle.set_font_size(15)
        self.subtitle.set_alignment("left")
        self.subtitle.set_color(theme.TEXT_SECONDARY)
        self.subtitle.size_hint_y = None
        self.subtitle.height = dp(24)
        self.add_widget(self.subtitle)

        # Berechnete Kennzahlen: wie oft reicht der aktuelle
        # Zutatenbestand noch für einen Verkauf (limitiert durch die
        # knappste Zutat) und was kostet eine Portion, umgerechnet aus
        # den Einkaufspreisen der Zutaten (siehe
        # database.py:get_recipe_available_quantity/get_recipe_cost).
        # Wie viele Zutaten das Rezept hat - entscheidet mit, ob ein
        # unbestimmter Einkaufspreis ein Hinweis wert ist (siehe
        # set_summary). Ein Rezept ganz ohne Zutaten ist einfach noch
        # nicht fertig.
        self.ingredient_count = 0

        self.summary_label = KiGLabel(text="")
        self.summary_label.set_font_size(15)
        self.summary_label.set_bold(True)
        self.summary_label.set_alignment("left")
        self.summary_label.set_color(theme.TEXT_PRIMARY)
        self.summary_label.size_hint_y = None
        self.summary_label.height = 0
        self.summary_label.opacity = 0
        self.add_widget(self.summary_label)

        #
        # Zutatenliste
        #

        self.scroll = ScrollView(bar_width=dp(12))

        self.list_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.ROW_SPACING),
            size_hint_y=None
        )
        self.list_layout.bind(
            minimum_height=self.list_layout.setter("height")
        )
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        #
        # Zutat hinzufügen
        #

        # Auf dem Telefon steht die Zutat ueber ihren Angaben statt
        # daneben: Menge (90), Einheit (90) und "Hinzufuegen" (150)
        # belegen 330 dp - mehr, als die ganze Karte dort breit ist.
        # Nachgemessen bekam das Zutatenfeld genau 0 Bildpunkte.
        self.schmal = theme.is_narrow()

        self.add_row, steuerzeile = self._zweizeilig()

        self.ingredient_spinner = RoundedSpinner(
            text=self.NO_INGREDIENTS_TEXT
        )
        self.ingredient_spinner.bind(text=self._ingredient_selected)

        self._oben(self.add_row, steuerzeile, self.ingredient_spinner)

        self.add_amount_button = Button(
            text="0", size_hint_x=None, width=dp(90),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="18sp", bold=True,
        )
        links_ausrichten(self.add_amount_button)

        self.add_amount_button.bind(
            on_release=lambda *_args: self.add_amount_callback()
        )
        self._unten(steuerzeile, self.add_amount_button, 0.28)

        self.unit_spinner = RoundedSpinner(
            text=units.ALL_UNITS[0],
            values=units.ALL_UNITS,
            size_hint_x=None,
            width=dp(90)
        )
        self._unten(steuerzeile, self.unit_spinner, 0.28)

        self.add_button = Button(
            text="Hinzufügen", size_hint_x=None, width=dp(150),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="16sp", bold=True,
        )
        self.add_button.bind(
            on_release=lambda *_args: self.add_confirm_callback()
        )
        self._unten(steuerzeile, self.add_button, 0.44)

        self.add_widget(self.add_row)

        #
        # Zutat OHNE eigenen Artikelstamm hinzufügen (z. B. Minze,
        # Limette, brauner Zucker) - rein zur Anzeige im Rezept, ohne
        # Bestandsführung. Bewusst eine eigene Zeile statt das
        # Dropdown oben zu erweitern: dort stehen ausschließlich
        # echte Zutaten-Artikel (siehe database.py:get_ingredient_articles).
        #

        # Schmal braucht der Satz zwei Zeilen - in einer 20 dp hohen
        # Zeile lief die zweite sonst in die Felder darunter.
        self.free_text_hint = KiGLabel(
            text="...oder eine Zutat ohne Artikel eintragen "
                 "(z. B. Minze, Limette)"
        )
        self.free_text_hint.set_font_size(13)
        self.free_text_hint.set_alignment("left")
        self.free_text_hint.set_color(theme.TEXT_SECONDARY)
        self.free_text_hint.size_hint_y = None
        self.free_text_hint.height = dp(36 if self.schmal else 20)
        self.add_widget(self.free_text_hint)

        self.free_text_row, freie_steuerzeile = self._zweizeilig()

        self.free_text_name_input = RoundedInput(
            hint_text="Name (z. B. Minze)", multiline=False,
        )
        self.free_text_name_input.foreground_color = theme.INPUT_TEXT
        self.free_text_name_input.hint_text_color = theme.INPUT_HINT
        self._oben(
            self.free_text_row, freie_steuerzeile,
            self.free_text_name_input,
        )

        self.free_text_amount_button = Button(
            text="0", size_hint_x=None, width=dp(90),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="18sp", bold=True,
        )
        links_ausrichten(self.free_text_amount_button)

        self.free_text_amount_button.bind(
            on_release=lambda *_args: self.add_free_text_amount_callback()
            if callable(self.add_free_text_amount_callback) else None
        )
        self._unten(freie_steuerzeile, self.free_text_amount_button, 0.26)

        self.free_text_unit_input = RoundedInput(
            hint_text="Einheit (z. B. TL)", multiline=False,
            size_hint_x=None, width=dp(120),
        )
        self.free_text_unit_input.foreground_color = theme.INPUT_TEXT
        self.free_text_unit_input.hint_text_color = theme.INPUT_HINT
        self._unten(freie_steuerzeile, self.free_text_unit_input, 0.30)

        self.free_text_add_button = Button(
            text="Hinzufügen", size_hint_x=None, width=dp(150),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="16sp", bold=True,
        )
        self.free_text_add_button.bind(
            on_release=lambda *_args: self._free_text_confirm_clicked()
        )
        self._unten(freie_steuerzeile, self.free_text_add_button, 0.44)

        self.add_widget(self.free_text_row)

        self.set_recipe(None)

    ########################################################
    # Eine Zeile - auf dem Telefon zwei
    ########################################################

    ZEILE_HOEHE = 58
    SCHMAL_ZEILE_HOEHE = 52

    def _zweizeilig(self):
        """Liefert die Zeile und die Stelle, an die ihre Angaben
        gehoeren.

        Breit ist beides dasselbe: eine Zeile. Schmal ist es ein Kasten
        aus zwei Zeilen - oben das Feld, unten Menge, Einheit und
        "Hinzufuegen".
        """

        if not self.schmal:

            zeile = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(self.ZEILE_HOEHE),
                spacing=dp(theme.ROW_SPACING),
            )

            return zeile, zeile

        kasten = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(2 * self.SCHMAL_ZEILE_HOEHE + theme.ROW_SPACING),
            spacing=dp(theme.ROW_SPACING),
        )

        steuerzeile = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(self.SCHMAL_ZEILE_HOEHE),
            spacing=dp(theme.ROW_SPACING),
        )

        return kasten, steuerzeile

    def _oben(self, kasten, steuerzeile, widget):
        """Haengt das Namensfeld ein - schmal in seine eigene Zeile,
        mit den Angaben darunter.

        Kivy stellt in einer senkrechten Reihe das zuerst Hinzugefuegte
        nach oben; das Feld muss also vor der Steuerzeile kommen.
        """

        if self.schmal:
            widget.size_hint_y = None
            widget.height = dp(self.SCHMAL_ZEILE_HOEHE)

        kasten.add_widget(widget)

        if self.schmal:
            kasten.add_widget(steuerzeile)

    def _unten(self, steuerzeile, widget, anteil):
        """Haengt eine Angabe ein - schmal mit Anteil statt fester
        Breite, damit die drei zusammen genau die Zeile fuellen."""

        if self.schmal:
            widget.size_hint_x = anteil
            widget.width = 0

        steuerzeile.add_widget(widget)

    def inhaltshoehe(self):
        """Wie hoch die Karte sein muss, damit beide Eingabezeilen und
        ein paar Zutaten sichtbar sind (siehe Stammdatenkarte)."""

        fest = (
            dp(42)                      # Ueberschrift
            + self.subtitle.height      # "Zusammensetzung"
            + self.summary_label.height
            + self.add_row.height
            + self.free_text_hint.height
            + self.free_text_row.height
            + dp(theme.CARD_SPACING) * 5
            + dp(theme.CARD_PADDING) * 2
        )

        return fest + max(dp(120), self.list_layout.minimum_height)

    ########################################################
    # Rezept
    ########################################################

    def set_recipe(self, recipe):

        self.selected_recipe = recipe

        if recipe is None:
            self.title_label.text = self.NO_RECIPE_TEXT
        else:
            self.title_label.text = recipe["name"]

        doppelt = self.title_label.text == self.subtitle.text

        self.subtitle.height = 0 if doppelt else dp(24)
        self.subtitle.opacity = 0 if doppelt else 1

        self.add_row.disabled = recipe is None
        self.add_row.opacity = 0.4 if recipe is None else 1

        self.free_text_row.disabled = recipe is None
        self.free_text_row.opacity = 0.4 if recipe is None else 1

        self.set_add_amount(0)
        self.set_add_free_text_amount(0)
        self.clear_free_text_inputs()

        if recipe is None:
            self.set_summary(None, None)

    def set_summary(self, available, cost):
        """available: wie oft der aktuelle Zutatenbestand noch reicht
        (None = unbestimmt, z. B. noch keine Zutaten hinterlegt).
        cost: berechneter Einkaufspreis je Portion (None = unbestimmt,
        z. B. Flasche ohne hinterlegte Flaschengröße)."""

        parts = []

        if available is not None:
            parts.append(f"Verfügbar: {available} Verkäufe")

        if cost is not None:
            parts.append(f"Berechneter Einkaufspreis: {cost:.2f} €".replace(".", ","))

        elif self.ingredient_count:

            # Ein unbestimmter Preis muss auffallen: Die Kasse bucht
            # solche Verkäufe mit 0,00 Einkauf, der Gewinn in der
            # Statistik ist dann zu hoch. Meist fehlt bei einer
            # Flaschen-Zutat der Wareneingang (und damit der Preis je
            # ml) oder es steht eine Freitext-Zutat im Rezept.
            parts.append(
                "Einkaufspreis unbestimmt - bitte bei den Zutaten den "
                "Wareneingang mit Preis buchen"
            )

        text = "   ·   ".join(parts)

        self.summary_label.text = text
        self.summary_label.height = dp(24) if text else 0
        self.summary_label.opacity = 1 if text else 0

        self.summary_label.set_color(
            theme.ERROR if (cost is None and self.ingredient_count)
            else theme.TEXT_PRIMARY
        )

    ########################################################
    # Zutatenliste
    ########################################################

    def set_ingredients(self, ingredients):

        self.ingredient_count = len(ingredients or [])

        self.list_layout.clear_widgets()

        if not ingredients:
            self.list_layout.add_widget(self._empty_label())
            return

        for ingredient in ingredients:
            row = RecipeIngredientRow(
                ingredient=ingredient,
                quantity_callback=self.quantity_callback,
                unit_callback=self.unit_callback,
                remove_callback=self.remove_callback
            )
            self.list_layout.add_widget(row)

    @staticmethod
    def _empty_label():

        label = KiGLabel(
            text="Noch keine Zutaten zugeordnet."
        )
        label.set_font_size(15)
        label.set_alignment("left")
        label.set_color(theme.TEXT_SECONDARY)
        label.size_hint_y = None
        label.height = dp(40)
        return label

    ########################################################
    # Verfügbare Zutaten (Spinner)
    ########################################################

    def set_ingredient_options(self, ingredients):

        self.ingredient_options = {
            row["name"]: row["id"] for row in ingredients
        }

        # Lagereinheit je Zutat, als Vorgabe für den Einheiten-Spinner.
        self.ingredient_units = {
            row["name"]: row["stock_unit"] for row in ingredients
        }

        if not ingredients:
            self.ingredient_spinner.values = []
            self.ingredient_spinner.text = self.NO_INGREDIENTS_TEXT
            return

        self.ingredient_spinner.values = list(self.ingredient_options)

        if self.ingredient_spinner.text not in self.ingredient_options:
            self.ingredient_spinner.text = next(iter(self.ingredient_options))
        else:
            # Auswahl unverändert - Einheit trotzdem synchron halten,
            # falls sich die Lagereinheit der Zutat zwischenzeitlich
            # geändert hat.
            self._sync_unit_default(self.ingredient_spinner.text)

    def _ingredient_selected(self, _instance, name):

        self._sync_unit_default(name)

    def _sync_unit_default(self, ingredient_name):
        """Beschränkt die wählbaren Einheiten auf solche, die sich
        verlustfrei in die Lagereinheit der Zutat umrechnen lassen
        (z. B. ml/cl/l für eine in ml geführte Zutat), und wählt die
        Lagereinheit selbst als Vorgabe.

        "Flasche" hat keinen festen ml-Wert und wird daher wie ml
        behandelt (siehe units.stock_dimension_unit) - ein Rezept
        braucht immer eine präzise Menge (z. B. "20 ml"), nie
        "0,03 Flaschen"."""

        stored_unit = self.ingredient_units.get(ingredient_name)

        if stored_unit is None:
            return

        default_unit = units.stock_dimension_unit(stored_unit)

        self.unit_spinner.values = units.compatible_units(default_unit)
        self.unit_spinner.text = default_unit

    def get_selected_ingredient_id(self):

        return self.ingredient_options.get(self.ingredient_spinner.text)

    def get_selected_unit(self):

        return self.unit_spinner.text

    ########################################################
    # Menge für neue Zutat
    ########################################################

    def set_add_amount(self, value):

        self._add_amount = max(0, int(value))
        self.add_amount_button.text = str(self._add_amount)

    def get_add_amount(self):

        return self._add_amount

    ########################################################
    # Menge für neue Zutat OHNE Artikel (Freitext)
    ########################################################

    def set_add_free_text_amount(self, value):

        self._add_free_text_amount = max(0, int(value))
        self.free_text_amount_button.text = str(self._add_free_text_amount)

    def get_add_free_text_amount(self):

        return self._add_free_text_amount

    def get_free_text_name(self):

        return self.free_text_name_input.text.strip()

    def get_free_text_unit(self):

        return self.free_text_unit_input.text.strip()

    def clear_free_text_inputs(self):

        self.free_text_name_input.text = ""
        self.free_text_unit_input.text = ""
        self.set_add_free_text_amount(0)

    def _free_text_confirm_clicked(self):

        if callable(self.add_free_text_confirm_callback):
            self.add_free_text_confirm_callback()
