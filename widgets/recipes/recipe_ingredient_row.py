"""Zeile einer bereits zugeordneten Rezeptzutat mit Menge und Einheit."""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import theme
import units

from widgets.common.feldausrichtung import links_ausrichten
from widgets.common.rounded_spinner import RoundedSpinner


class RecipeIngredientRow(BoxLayout):
    """Zutat + Menge + Einheit, mit Menge-Button (zum Ändern),
    Einheiten-Auswahl und Entfernen-Button.

    Das Einheiten-Dropdown zeigt ausschließlich Einheiten, die sich
    verlustfrei in die aktuelle Lagereinheit der Zutat umrechnen
    lassen (siehe units.compatible_units) - eine Auswahl, die zu
    falschen Lagerabzügen führen könnte, ist so gar nicht erst wählbar.
    """

    def __init__(
            self,
            ingredient,
            quantity_callback,
            unit_callback,
            remove_callback,
            **kwargs
    ):
        # Auf dem Telefon steht der Name ueber Menge, Einheit und
        # "Entfernen" statt daneben: Die drei belegen 290 dp, die
        # Rezeptkarte ist dort keine 290 dp breit.
        self.schmal = theme.is_narrow()

        super().__init__(
            orientation="vertical" if self.schmal else "horizontal",
            spacing=dp(theme.SPACE_XS if self.schmal else theme.ROW_SPACING),
            padding=(dp(theme.CARD_SPACING), dp(theme.SPACE_XS)),
            size_hint_y=None,
            height=dp(96 if self.schmal else 58),
            **kwargs
        )

        self.ingredient = dict(ingredient)
        self.quantity_callback = quantity_callback
        self.unit_callback = unit_callback
        self.remove_callback = remove_callback

        with self.canvas.before:
            Color(*theme.CARD)
            self._background = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        name_text = self.ingredient["name"]
        if self.ingredient.get("ingredient_article_id") is None:
            # Kennzeichnet Freitext-Zutaten ohne eigenen Artikelstamm
            # (siehe RecipeCompositionPanel._add_free_text_row) - ohne
            # Bestandsführung, rein zur Anzeige im Rezept.
            name_text += "  (ohne Artikel)"

        self.name_label = Label(
            text=name_text, color=theme.TEXT_PRIMARY, bold=True,
            font_size="16sp", halign="left", valign="middle",
        )
        self.name_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        if self.schmal:
            self.name_label.size_hint_y = None
            self.name_label.height = dp(26)
            self.name_label.font_size = "15sp"

        self.add_widget(self.name_label)

        # Kivy stellt in einer senkrechten Reihe das zuerst
        # Hinzugefuegte nach oben - die Angabenzeile also nach dem
        # Namen.
        if self.schmal:

            self.angaben = BoxLayout(
                orientation="horizontal",
                spacing=dp(theme.ROW_SPACING),
                size_hint_y=None,
                height=dp(48),
            )

            self.add_widget(self.angaben)

        else:
            self.angaben = self

        self.amount_button = Button(
            text=self._format_quantity(), size_hint_x=None, width=dp(90),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="16sp", bold=True,
        )
        links_ausrichten(self.amount_button)

        self.amount_button.bind(
            on_release=lambda *_args: self.quantity_callback(self.ingredient)
        )
        self._einhaengen(self.amount_button, 0.28)

        # Freitext-Zutaten (ohne eigenen Artikelstamm, z. B. "Minze")
        # haben keine Lagereinheit, gegen die sich eine Umrechnung
        # prüfen ließe - ihre Einheit wird deshalb nur als Text
        # angezeigt statt als einschränkendes Dropdown.
        is_free_text = self.ingredient.get("ingredient_article_id") is None

        if is_free_text:
            unit_label = Label(
                text=self.ingredient.get("unit") or "-", color=theme.TEXT_SECONDARY,
                font_size="15sp", size_hint_x=None, width=dp(90),
                halign="center", valign="middle",
            )
            unit_label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            self._einhaengen(unit_label, 0.28)
        else:
            # "Flasche" hat keinen festen ml-Wert und wird für die
            # Einheiten-Kompatibilität daher wie ml behandelt (siehe
            # units.stock_dimension_unit) - der tatsächliche Bestand
            # einer Flasche-Zutat wird ja ohnehin immer in ml geführt.
            article_stock_unit = units.stock_dimension_unit(
                self.ingredient.get("article_stock_unit")
            )
            current_unit = self.ingredient.get("unit") or article_stock_unit

            self.unit_spinner = RoundedSpinner(
                text=current_unit,
                values=units.compatible_units(article_stock_unit or current_unit),
                size_hint_x=None,
                width=dp(90)
            )
            self.unit_spinner.bind(text=self._unit_changed)
            self._einhaengen(self.unit_spinner, 0.28)

        remove_button = Button(
            text="Entfernen", size_hint_x=None, width=dp(110),
            background_normal="", background_down="",
            background_color=theme.ERROR, color=theme.TEXT_WHITE,
            font_size="14sp", bold=True,
        )
        remove_button.bind(
            on_release=lambda *_args: self.remove_callback(self.ingredient)
        )
        self._einhaengen(remove_button, 0.44)

    def _einhaengen(self, widget, anteil):
        """Haengt eine Angabe ein - schmal anteilig statt fest breit."""

        if self.schmal:
            widget.size_hint_x = anteil
            widget.width = 0

        self.angaben.add_widget(widget)

    def _update_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    def _format_quantity(self):

        value = self.ingredient.get("quantity", 0)

        try:
            numeric = float(value)
            return str(int(numeric)) if numeric.is_integer() else f"{numeric:.2f}"
        except (TypeError, ValueError):
            return str(value)

    def _unit_changed(self, _instance, unit):

        if unit == self.ingredient.get("unit"):
            return

        self.ingredient["unit"] = unit

        if callable(self.unit_callback):
            self.unit_callback(self.ingredient, unit)
