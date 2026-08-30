from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from kivy.metrics import dp

import geldformat
import theme

from widgets.kig_label import KiGLabel
from widgets.kig_tile import KiGTile


class CashArticleTile(KiGTile):
    """
    Kachel zur Darstellung eines Artikels im CashScreen.

    Erwartet ein Article-Objekt aus models.article.Article.

    Verwendete Eigenschaften:
        article.id
        article.category_id
        article.name
        article.price
    """

    title = StringProperty("")
    price = StringProperty("")
    stock = StringProperty("")

    PADDING = theme.TILE_PADDING
    SPACING = theme.SPACE_XS

    TITLE_SIZE = 24
    PRICE_SIZE = 18

    # Telefon: kleinere Kachel, kleinere Schrift. Mit 24 sp blieb von
    # "Apfelschorle" auf 168 dp Breite nur noch "Apfel…" übrig.
    NARROW_TITLE_SIZE = 16
    NARROW_PRICE_SIZE = 14
    NARROW_STOCK_SIZE = 11

    STOCK_SIZE = 13

    def __init__(
            self,
            article,
            callback=None,
            **kwargs
    ):

        if theme.is_narrow():
            self.TITLE_SIZE = self.NARROW_TITLE_SIZE
            self.PRICE_SIZE = self.NARROW_PRICE_SIZE
            self.STOCK_SIZE = self.NARROW_STOCK_SIZE
            self.PADDING = theme.SPACE_S

        super().__init__(**kwargs)

        # =====================================================
        # Daten
        # =====================================================

        self.article = article
        self.callback = callback

        # =====================================================
        # Größe
        # =====================================================

        self.size_hint = (None, None)

        self.size = tuple(
            dp(wert) for wert in theme.narrow_article_tile()
        ) if theme.is_narrow() else (
            dp(theme.ARTICLE_TILE_WIDTH),
            dp(theme.ARTICLE_TILE_HEIGHT)
        )

        # =====================================================
        # Layout
        # =====================================================

        self.layout = BoxLayout(
            orientation="vertical",
            padding=dp(self.PADDING),
            spacing=dp(self.SPACING)
        )

        self.add_widget(
            self.layout
        )

        # =====================================================
        # Artikelname
        # =====================================================

        self.lbl_title = KiGLabel(
            size_hint=(1, 0.52)
        )

        self.lbl_title.set_bold(True)

        self.lbl_title.set_font_size(
            self.TITLE_SIZE
        )

        self.lbl_title.set_color(
            theme.TEXT_PRIMARY
        )

        self.lbl_title.horizontal_alignment = "left"
        self.lbl_title.vertical_alignment = "middle"

        # Sehr lange Artikelnamen sollen die feste Kachelhöhe nicht
        # sprengen (der Text würde sonst oben/unten über die Kachel
        # hinausgezeichnet) - ab der dritten Zeile wird deshalb mit
        # "…" abgeschnitten statt weiter zu umbrechen.
        self.lbl_title.max_lines = 2
        self.lbl_title.shorten = True
        self.lbl_title.shorten_from = "right"

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        self.layout.add_widget(
            self.lbl_title
        )

        self.lbl_stock = KiGLabel(size_hint=(1, 0.18))
        self.lbl_stock.set_font_size(self.STOCK_SIZE)
        self.lbl_stock.set_color(theme.TEXT_SECONDARY)
        self.lbl_stock.horizontal_alignment = "left"
        self.lbl_stock.vertical_alignment = "middle"
        self.lbl_stock.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.layout.add_widget(self.lbl_stock)

        # =====================================================
        # Preis
        # =====================================================

        self.lbl_price = KiGLabel(
            size_hint=(1, 0.30)
        )

        self.lbl_price.set_bold(False)

        self.lbl_price.set_font_size(
            self.PRICE_SIZE
        )

        self.lbl_price.set_color(
            theme.TEXT_SECONDARY
        )

        self.lbl_price.horizontal_alignment = "right"
        self.lbl_price.vertical_alignment = "middle"

        self.lbl_price.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        self.layout.add_widget(
            self.lbl_price
        )

        # =====================================================
        # Bindings
        # =====================================================

        self.bind(
            pos=self._update_layout,
            size=self._update_layout,
            title=self._update_content,
            price=self._update_content,
            stock=self._update_content
        )

        # =====================================================
        # Unterstützt sqlite3.Row UND Article
        # =====================================================

        if hasattr(article, "name"):

            self.title = article.name

            price = article.price

            article_type = getattr(article, "article_type", "SINGLE")

        else:

            self.title = article["name"]

            price = article["price"]

            article_type = article["article_type"] if "article_type" in article.keys() else "SINGLE"

        # Mix-/Rezeptartikel führen keinen eigenen Bestand - hier
        # zeigt die Zahl, wie oft die knappste Zutat den Verkauf noch
        # hergibt (siehe database.py:get_recipe_available_quantity),
        # daher die abweichende Beschriftung "Verfügbar" statt "Bestand".
        self.stock_caption = "Verfügbar" if article_type == "MIX" else "Bestand"

        self.stock_quantity = self._stock_value(getattr(article, "stock", 0))

        self.stock = self._format_stock(getattr(article, "stock", 0))

        self.price = geldformat.geld(price)

        self._mark_sold_out()

        # =====================================================
        # Initial aktualisieren
        # =====================================================

        self._update_layout()
        self._update_content()

    # =========================================================
    # Layout
    # =========================================================

    def _update_layout(self, *args):

        self.layout.pos = self.pos
        self.layout.size = self.size

    # =========================================================
    # Inhalt
    # =========================================================

    def _update_content(self, *args):

        self.lbl_title.text = self.title

        self.lbl_title.text_size = (
            self.lbl_title.size
        )

        self.lbl_price.text = self.price

        self.lbl_price.text_size = (
            self.lbl_price.size
        )

        self.lbl_stock.text = f"{getattr(self, 'stock_caption', 'Bestand')}: {self.stock}"
        self.lbl_stock.text_size = self.lbl_stock.size

    # =========================================================
    # Ausverkauft
    # =========================================================

    def _mark_sold_out(self):
        """Färbt die Kachel leicht grau, wenn nichts mehr da ist.

        Antippen bleibt möglich: An der Bar wird gelegentlich
        nachgeschenkt, bevor jemand den Wareneingang bucht - ein
        gesperrter Artikel würde den Verkauf aufhalten. Die Kachel soll
        nur ins Auge fallen.
        """

        self.sold_out = (
            self.stock_quantity is not None and self.stock_quantity <= 0
        )

        if not self.sold_out:
            return

        self.background_color = theme.TILE_SOLD_OUT

        # Auch nach einem Tipp wieder grau werden (siehe
        # KiGTile.animate_press).
        self.normal_color = theme.TILE_SOLD_OUT

        self.lbl_title.set_color(theme.TEXT_SECONDARY)
        self.lbl_stock.set_color(theme.TEXT_LIGHT)
        self.lbl_price.set_color(theme.TEXT_LIGHT)

    @staticmethod
    def _stock_value(stock):
        """Bestand als Zahl - oder None, wenn er sich nicht bestimmen
        lässt (dann wird auch nichts eingegraut)."""

        try:
            return float(stock)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_stock(stock):
        try:
            stock = float(stock)
            if stock.is_integer():
                return str(int(stock))
            return f"{stock:.2f}".replace(".", ",")
        except (TypeError, ValueError):
            return "-"

    # =========================================================
    # Titel setzen
    # =========================================================

    def set_title(self, title: str):

        self.title = title

    # =========================================================
    # Preis setzen
    # =========================================================

    def set_price(self, price: str):

        self.price = price

    # =========================================================
    # Klick
    # =========================================================

    def on_release(self):

        if callable(self.callback):

            self.callback(
                self,
                self.article
            )

    # =========================================================
    # String
    # =========================================================

    def __repr__(self):

        return (
            f"CashArticleTile("
            f"title='{self.title}'"
            f")"
        )
