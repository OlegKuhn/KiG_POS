from kivy.properties import StringProperty
from kivy.graphics import Color, RoundedRectangle
from widgets.cash.design import category_color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

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

    PADDING = 14
    SPACING = theme.SPACE_XS

    TITLE_SIZE = 20
    PRICE_SIZE = 28

    STOCK_SIZE = 17

    # Kleiner als das wird ein Name nicht - lieber bricht die zweite
    # Zeile ab, als dass er unlesbar wird.
    MIN_TITLE_SIZE = 11

    def __init__(
            self,
            article,
            callback=None,
            category_name="",
            **kwargs
    ):

        super().__init__(**kwargs)

        # =====================================================
        # Daten
        # =====================================================

        self.category_name = category_name
        self.article = article
        self.callback = callback
        category_id = article.category_id if hasattr(article, 'category_id') else article['category_id']
        self.normal_color = theme.tinted(category_color(category_id), .11)
        self.background_color = self.normal_color
        self.border_color.rgba = (0, 0, 0, 0)

        # =====================================================
        # Größe
        # =====================================================

        self.size_hint = (None, None)

        self.size = (
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

        # Mehr Höhe als früher: Passt ein Name nicht in eine Zeile,
        # steht er in zweien (siehe _titel_einpassen). Bestand und
        # Preis rücken dafür nach unten.
        self.lbl_title = KiGLabel(
            size_hint=(1, 0.58)
        )

        self.lbl_title.set_bold(True)

        self.lbl_title.set_font_size(
            self.TITLE_SIZE
        )

        self.lbl_title.set_color(
            theme.TEXT_PRIMARY
        )

        self.lbl_title.horizontal_alignment = "left"
        self.lbl_title.vertical_alignment = "top"

        # Höchstens zwei Zeilen. "shorten" bleibt aus: Damit setzt Kivy
        # jeden Text in eine einzige Zeile und kürzt ihn - aus
        # "Apfelschorle naturtrüb" wurde "Apfelschorle na…", obwohl
        # darunter Platz für eine zweite Zeile war.
        self.lbl_title.max_lines = 2
        self.lbl_title.shorten = False

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        self.lbl_title.bind(size=lambda *_a: self._titel_einpassen())

        self.layout.add_widget(
            self.lbl_title
        )

        self.lbl_stock = KiGLabel(size_hint=(1, 0.14))
        self.lbl_stock.set_font_size(self.STOCK_SIZE)
        self.lbl_stock.set_color(theme.TEXT_SECONDARY)
        self.lbl_stock.horizontal_alignment = "left"
        self.lbl_stock.vertical_alignment = "middle"
        self.lbl_stock.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.layout.add_widget(Widget(size_hint_y=None, height=dp(12)))
        self.layout.add_widget(self.lbl_stock)
        self.lbl_title.size_hint_y = None
        self.lbl_title.height = dp(50)
        self.lbl_stock.size_hint_y = None
        self.lbl_stock.height = dp(28)
        self.layout.add_widget(Widget())

        # =====================================================
        # Preis
        # =====================================================

        self.lbl_price = KiGLabel(
            size_hint=(1, 0.28)
        )

        self.lbl_price.set_bold(True)
        self.lbl_price.size_hint_y = None
        self.lbl_price.height = dp(38)

        self.lbl_price.set_font_size(
            self.PRICE_SIZE
        )

        self.lbl_price.set_color(
            theme.PRIMARY_ORANGE
        )

        self.lbl_price.horizontal_alignment = "left"
        self.lbl_price.vertical_alignment = "bottom"

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

        with self.canvas.after:
            Color(*category_color(article.category_id if hasattr(article, 'category_id') else article['category_id']))
            self.category_marker = RoundedRectangle(radius=[dp(2)])
        self.bind(pos=self._marker_layout, size=self._marker_layout)

        # Der Streifen hängt am Namen, nicht am Kachelrand.
        self.lbl_title.bind(pos=self._marker_layout, size=self._marker_layout)

        self._marker_layout()
        self._mark_sold_out()

        # =====================================================
        # Initial aktualisieren
        # =====================================================

        self._update_layout()
        self._update_content()

    # =========================================================
    # Layout
    # =========================================================

    # Höhe des Farbstreifens unter dem Artikelnamen
    MARKER_HOEHE = 7

    def _marker_layout(self, *_):
        """Der Farbstreifen der Kategorie - unter dem Namen.

        Über dem Namen lag er am oberen Kachelrand und ging neben dem
        Rahmen unter; unter dem Namen gehört er sichtbar zum Artikel.
        """

        innen = dp(self.PADDING)

        self.category_marker.pos = (
            self.x + innen,
            self.lbl_title.y - dp(self.MARKER_HOEHE) - dp(2),
        )
        self.category_marker.size = (
            max(0, self.width - 2 * innen), dp(self.MARKER_HOEHE)
        )

    def _update_layout(self, *args):

        self.layout.pos = self.pos
        self.layout.size = self.size

    # =========================================================
    # Inhalt
    # =========================================================

    def _titel_einpassen(self, *_args):
        """Wählt die Schriftgröße des Namens.

        Passt er in voller Größe in eine Zeile, bleibt es dabei. Sonst
        wird er auf zwei Zeilen umbrochen - und so weit verkleinert,
        dass beide Zeilen in die Kachel passen und kein einzelnes Wort
        über den Rand ragt.
        """

        breite, hoehe = self.lbl_title.size
        titel = self.title or ""

        if breite <= 1 or hoehe <= 1 or not titel:
            return

        schluessel = (titel, round(breite), round(hoehe))

        if getattr(self, "_titel_masse", None) == schluessel:
            return

        self._titel_masse = schluessel

        from kivy.core.text import Label as CoreLabel
        from kivy.metrics import sp

        def ausmass(text, groesse):
            return CoreLabel(font_size=sp(groesse), bold=True).get_extents(text)

        def zeilen(groesse):
            """Wie viele Zeilen braucht der Name - None, wenn ein Wort
            allein breiter ist als die Kachel."""

            anzahl = 1
            zeile = ""

            for wort in titel.split():

                if ausmass(wort, groesse)[0] > breite:
                    return None

                probe = f"{zeile} {wort}".strip()

                if ausmass(probe, groesse)[0] <= breite:
                    zeile = probe
                else:
                    anzahl += 1
                    zeile = wort

            return anzahl

        gewaehlt = self.MIN_TITLE_SIZE

        for groesse in range(self.TITLE_SIZE, self.MIN_TITLE_SIZE - 1, -1):

            benoetigt = zeilen(groesse)

            if benoetigt is None or benoetigt > 2:
                continue

            zeilenhoehe = ausmass(titel, groesse)[1]

            if benoetigt * zeilenhoehe <= hoehe:
                gewaehlt = groesse
                break

        if self.lbl_title.text_size_sp != gewaehlt:
            self.lbl_title.set_font_size(gewaehlt)

    def _update_content(self, *args):

        self.lbl_title.text = self.title

        self._titel_einpassen()

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
