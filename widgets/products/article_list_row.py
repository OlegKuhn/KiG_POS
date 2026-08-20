"""Eine Zeile der zusammengeführten Artikelliste (Artikel/Einkauf/Inventar/Rezepte)."""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import config
import theme

from widgets.common.kig_symbol import KiGSymbolButton, KREUZ


class ArticleListRow(BoxLayout):
    """Zeigt Name, Kategorie, Verkaufs-/Einkaufspreis und Bestand eines
    Artikels.

    Einzelartikel erhalten zusätzlich einen Schnellzugriff auf die
    Bestellmenge: Menge festlegen ("Menge"-Button) UND direkt als
    Wareneingang bestätigen ("Buchen"-Button) - ganz ohne den
    Bearbeiten-Dialog zu öffnen. Mix-/Rezeptartikel führen keinen
    eigenen Bestand, daher entfallen dort Bestand/Bestellmenge - ihre
    Zusammensetzung wird im Bearbeiten-Dashboard verwaltet.

    Im Hochformat steht dieselbe Zeile zweizeilig: oben Name und
    Kategorie, darunter Preise, Bestand und die Schaltflächen. Alle
    sieben Spalten nebeneinander bräuchten rund 790 Bildpunkte - mehr,
    als ein hochkantes Fenster hergibt; der Artikelname bliebe sonst
    ohne Platz. Die Spaltenüberschriften entfallen dort deshalb, die
    Werte tragen ihre Beschriftung selbst ("VK 2,50 €").
    """

    PORTRAIT_HEIGHT = 92

    def __init__(
            self,
            article,
            order_amount,
            amount_callback,
            confirm_callback,
            edit_callback,
            delete_callback,
            **kwargs
    ):
        super().__init__(
            orientation="horizontal",
            spacing=dp(theme.ROW_SPACING),
            padding=(dp(theme.CARD_SPACING), dp(theme.SPACE_XS)),
            size_hint_y=None,
            height=dp(68),
            **kwargs
        )

        self.article = article
        self.amount_callback = amount_callback
        self.confirm_callback = confirm_callback
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback

        is_mix = article["article_type"] == "MIX"

        with self.canvas.before:
            Color(*theme.CARD)
            self._background = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        if theme.is_portrait():
            self._build_portrait(article, order_amount, is_mix)
            return

        # -------------------------------------------------
        # Name + Kategorie
        # -------------------------------------------------

        name_column = BoxLayout(orientation="vertical", spacing=dp(theme.LABEL_SPACING))

        name_label = Label(
            text=article["name"], color=theme.TEXT_PRIMARY, bold=True,
            font_size="16sp", halign="left", valign="middle",
        )
        name_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        name_column.add_widget(name_label)

        category_text = article["category_name"] or "-"
        if is_mix:
            category_text += "  ·  Mix / Rezept"

        category_label = Label(
            text=category_text, color=theme.TEXT_SECONDARY, font_size="12sp",
            halign="left", valign="middle",
        )
        category_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        name_column.add_widget(category_label)

        self.add_widget(name_column)

        # -------------------------------------------------
        # Verkaufspreis / Einkaufspreis / Bestand
        # -------------------------------------------------

        self.add_widget(self._value_label(self._format_price(article["price"]), dp(78)))
        self.add_widget(self._value_label(self._format_price(article["purchase_price"]), dp(78)))

        if is_mix:
            stock_text = "–"
        elif article["stock_unit"] == config.BOTTLE_UNIT:
            stock_text = f"{self._format_stock(article.get('stock', 0))} ml"
        else:
            stock_text = self._format_stock(article.get("stock", 0))
        self.add_widget(self._value_label(stock_text, dp(78)))

        # -------------------------------------------------
        # Bestellmenge: Menge festlegen + direkt buchen
        # -------------------------------------------------

        self.amount_button = Button(
            text=str(order_amount) if not is_mix else "–",
            size_hint_x=None, width=dp(80),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="15sp", bold=True,
            disabled=is_mix,
        )
        if not is_mix:
            self.amount_button.bind(
                on_release=lambda *_args: self.amount_callback(self.article)
            )
        self.add_widget(self.amount_button)

        confirm_button = Button(
            text="Buchen", size_hint_x=None, width=dp(90),
            background_normal="", background_down="",
            background_color=theme.SUCCESS, color=theme.TEXT_WHITE,
            font_size="13sp", bold=True,
            disabled=is_mix,
        )
        if not is_mix:
            # on_press statt on_release: reagiert direkt beim Berühren,
            # zuverlässiger bei kleinsten Fingerbewegungen in ScrollViews.
            confirm_button.bind(
                on_press=lambda *_args: self.confirm_callback(self.article)
            )
        self.add_widget(confirm_button)

        # -------------------------------------------------
        # Bearbeiten / Löschen
        # -------------------------------------------------

        edit_button = Button(
            text="Bearbeiten", size_hint_x=None, width=dp(100),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="13sp", bold=True,
        )
        edit_button.bind(
            on_release=lambda *_args: self.edit_callback(self.article)
        )
        self.add_widget(edit_button)

        delete_button = KiGSymbolButton(
            symbol=KREUZ, symbol_color=theme.TEXT_WHITE,
            size_hint_x=None, width=dp(46),
            background_color=theme.ERROR, color=theme.TEXT_WHITE,
        )
        delete_button.bind(
            on_release=lambda *_args: self.delete_callback(self.article)
        )
        self.add_widget(delete_button)

    # =====================================================
    # Hochformat
    # =====================================================

    def _build_portrait(self, article, order_amount, is_mix):
        """Zweizeilige Fassung derselben Zeile für schmale Fenster."""

        self.orientation = "vertical"
        self.spacing = dp(theme.SPACE_XS)
        self.height = dp(self.PORTRAIT_HEIGHT)

        # -------------------------------------------------
        # Obere Zeile: Name, Kategorie, Löschen
        # -------------------------------------------------

        obere_zeile = BoxLayout(
            spacing=dp(theme.ROW_SPACING), size_hint_y=None, height=dp(46)
        )

        name_column = BoxLayout(
            orientation="vertical", spacing=dp(theme.LABEL_SPACING)
        )

        name_label = Label(
            text=article["name"], color=theme.TEXT_PRIMARY, bold=True,
            font_size="16sp", halign="left", valign="bottom",
            shorten=True, shorten_from="right",
        )
        name_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        name_column.add_widget(name_label)

        kategorie_text = article["category_name"] or "-"

        if is_mix:
            kategorie_text += "  ·  Mix / Rezept"

        category_label = Label(
            text=kategorie_text, color=theme.TEXT_SECONDARY, font_size="12sp",
            halign="left", valign="top", shorten=True, shorten_from="right",
        )
        category_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        name_column.add_widget(category_label)

        obere_zeile.add_widget(name_column)

        delete_button = KiGSymbolButton(
            symbol=KREUZ, symbol_color=theme.TEXT_WHITE,
            size_hint_x=None, width=dp(46),
            background_color=theme.ERROR, color=theme.TEXT_WHITE,
        )
        delete_button.bind(
            on_release=lambda *_args: self.delete_callback(self.article)
        )
        obere_zeile.add_widget(delete_button)

        self.add_widget(obere_zeile)

        # -------------------------------------------------
        # Untere Zeile: Werte und Schaltflächen
        # -------------------------------------------------

        untere_zeile = BoxLayout(
            spacing=dp(theme.ROW_SPACING), size_hint_y=None, height=dp(38)
        )

        untere_zeile.add_widget(self._caption_label(
            f"VK {self._format_price(article['price'])}"
        ))
        untere_zeile.add_widget(self._caption_label(
            f"EK {self._format_price(article['purchase_price'])}"
        ))

        if is_mix:
            bestand_text = "Bestand –"
        elif article["stock_unit"] == config.BOTTLE_UNIT:
            bestand_text = (
                f"Bestand {self._format_stock(article.get('stock', 0))} ml"
            )
        else:
            bestand_text = (
                f"Bestand {self._format_stock(article.get('stock', 0))}"
            )

        untere_zeile.add_widget(self._caption_label(bestand_text))

        self.amount_button = Button(
            text=str(order_amount) if not is_mix else "–",
            size_hint_x=None, width=dp(64),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="15sp", bold=True,
            disabled=is_mix,
        )
        if not is_mix:
            self.amount_button.bind(
                on_release=lambda *_args: self.amount_callback(self.article)
            )
        untere_zeile.add_widget(self.amount_button)

        confirm_button = Button(
            text="Buchen", size_hint_x=None, width=dp(80),
            background_normal="", background_down="",
            background_color=theme.SUCCESS, color=theme.TEXT_WHITE,
            font_size="13sp", bold=True,
            disabled=is_mix,
        )
        if not is_mix:
            # on_press statt on_release: siehe Querformat-Fassung oben.
            confirm_button.bind(
                on_press=lambda *_args: self.confirm_callback(self.article)
            )
        untere_zeile.add_widget(confirm_button)

        edit_button = Button(
            text="Bearbeiten", size_hint_x=None, width=dp(94),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="13sp", bold=True,
        )
        edit_button.bind(
            on_release=lambda *_args: self.edit_callback(self.article)
        )
        untere_zeile.add_widget(edit_button)

        self.add_widget(untere_zeile)

    @staticmethod
    def _caption_label(text):
        """Wert mit eigener Beschriftung, Breite vom Layout bestimmt."""

        label = Label(
            text=text, color=theme.TEXT_PRIMARY, font_size="13sp",
            halign="left", valign="middle", shorten=True, shorten_from="right",
        )
        label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        return label

    @staticmethod
    def _value_label(text, width):
        return Label(
            text=text, color=theme.TEXT_PRIMARY, font_size="14sp",
            size_hint_x=None, width=width, halign="right", valign="middle",
            text_size=(width, dp(68)),
        )

    def _update_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    def set_order_amount(self, amount):
        self.amount_button.text = str(amount)

    @staticmethod
    def _format_price(value):
        return f"{float(value or 0):.2f} €".replace(".", ",")

    @staticmethod
    def _format_stock(value):
        value = float(value or 0)
        return str(int(value)) if value.is_integer() else f"{value:.2f}".replace(".", ",")
