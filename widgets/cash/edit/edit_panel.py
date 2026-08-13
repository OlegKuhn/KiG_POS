from kivy.graphics import (
    Color,
    Rectangle,
    Line
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

import theme

from widgets.kig_label import KiGLabel
from widgets.common.kig_action_tile import KiGActionTile
from widgets.cash.edit.quantity_editor import QuantityEditor
from widgets.common.slide_panel import SlidePanel


class EditPanel(SlidePanel, BoxLayout):

    WIDTH = 350

    PADDING = theme.CARD_PADDING
    SPACING = theme.CARD_SPACING

    HEADER_HEIGHT = 60

    BUTTON_SPACING = theme.ROW_SPACING
    BUTTON_WIDTH = 160
    BUTTON_HEIGHT = theme.CATEGORY_TILE_HEIGHT

    def __init__(
            self,
            price_callback=None,
            quantity_callback=None,
            apply_callback=None,
            delete_callback=None,
            duplicate_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.price_callback = price_callback

        self.quantity_callback = quantity_callback

        self.apply_callback = apply_callback

        self.delete_callback = delete_callback

        self.duplicate_callback = duplicate_callback

        self.orientation = "vertical"

        self.init_slide(self.WIDTH)

        self.padding = self.PADDING
        self.spacing = self.SPACING

        self.cart_item = None

        # =====================================================
        # Hintergrund
        # =====================================================

        with self.canvas.before:

            Color(*theme.CARD)

            self.background = Rectangle()

        with self.canvas.after:

            Color(*theme.CART_SEPARATOR)

            self.separator = Line(width=1)

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        # =====================================================
        # Header
        # =====================================================

        self.lbl_title = KiGLabel()

        self.lbl_title.text = "Artikel bearbeiten"

        self.lbl_title.set_bold(True)
        self.lbl_title.set_font_size(24)
        self.lbl_title.set_color(theme.PRIMARY_ORANGE)

        self.lbl_title.horizontal_alignment = "left"
        self.lbl_title.vertical_alignment = "middle"

        self.lbl_title.size_hint = (1, None)
        self.lbl_title.height = self.HEADER_HEIGHT

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(
            self.lbl_title
        )

        # =====================================================
        # Artikelname
        # =====================================================

        self.lbl_article = KiGLabel()

        self.lbl_article.text = ""

        self.lbl_article.set_bold(True)
        self.lbl_article.set_font_size(18)
        self.lbl_article.set_color(theme.TEXT_PRIMARY)

        self.lbl_article.horizontal_alignment = "left"
        self.lbl_article.vertical_alignment = "middle"

        self.lbl_article.size_hint = (1, None)
        self.lbl_article.height = 40

        self.lbl_article.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(
            self.lbl_article
        )

        # =====================================================
        # Menge
        # =====================================================

        self.lbl_quantity = KiGLabel()

        self.lbl_quantity.text = "Menge"

        self.lbl_quantity.set_bold(True)
        self.lbl_quantity.set_font_size(16)
        self.lbl_quantity.set_color(theme.TEXT_PRIMARY)

        self.lbl_quantity.horizontal_alignment = "left"

        self.lbl_quantity.size_hint = (1, None)
        self.lbl_quantity.height = 28

        self.lbl_quantity.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(
            self.lbl_quantity
        )

        # =====================================================
        # Quantity Editor
        # =====================================================

        self.quantity_container = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=70
        )

        self.quantity_editor = QuantityEditor(
            edit_callback=self.quantity_clicked
        )

        self.quantity_container.add_widget(
            Widget()
        )

        self.quantity_container.add_widget(
            self.quantity_editor
        )

        self.quantity_container.add_widget(
            Widget()
        )

        self.add_widget(
            self.quantity_container
        )

        # =====================================================
        # Preis
        # =====================================================

        self.lbl_price = KiGLabel()

        self.lbl_price.text = "Preis"

        self.lbl_price.set_bold(True)
        self.lbl_price.set_font_size(16)
        self.lbl_price.set_color(theme.TEXT_PRIMARY)

        self.lbl_price.horizontal_alignment = "left"

        self.lbl_price.size_hint = (1, None)
        self.lbl_price.height = 28

        self.lbl_price.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(
            self.lbl_price
        )

        # =====================================================
        # Preis Button
        # =====================================================

        self.btn_price = KiGActionTile(
            text="0,00 €",
            callback=self._price_clicked
        )

        self.btn_price.size_hint = (1, None)

        self.btn_price.height = theme.CATEGORY_TILE_HEIGHT

        self.add_widget(
            self.btn_price
        )

        # =====================================================
        # Spacer
        # =====================================================

        self.add_widget(
            Widget()
        )

        # =====================================================
        # Buttons
        # =====================================================

        self.button_area = BoxLayout(
            orientation="vertical",
            spacing=self.BUTTON_SPACING,
            size_hint=(1, None),
            height=self.BUTTON_HEIGHT * 2 + self.BUTTON_SPACING
        )

        # -----------------------------------------------------
        # Erste Reihe
        # -----------------------------------------------------

        self.row1 = BoxLayout(
            spacing=self.BUTTON_SPACING,
            size_hint=(1, None),
            height=self.BUTTON_HEIGHT
        )

        # -----------------------------------------------------
        # Zweite Reihe
        # -----------------------------------------------------

        self.row2 = BoxLayout(
            spacing=self.BUTTON_SPACING,
            size_hint=(1, None),
            height=self.BUTTON_HEIGHT
        )

        # -----------------------------------------------------
        # Buttons
        # -----------------------------------------------------

        # Zwei Kacheln zu je 160 px plus Abstand ergeben 328 px und
        # passen damit NICHT in die 318 px zwischen den Innenrändern
        # des Panels - sie ragten bisher beidseitig heraus. Die Breite
        # bestimmt deshalb die Reihe, nicht die Kachel (wie in
        # cart_footer.py). size_hint erst NACH der Konstruktion setzen:
        # KiGActionTile überschreibt im Konstruktor übergebene Werte.
        def schaltflaeche(text, callback):

            kachel = KiGActionTile(
                text=text,
                height=self.BUTTON_HEIGHT,
                callback=callback
            )

            kachel.size_hint = (1, None)
            kachel.height = self.BUTTON_HEIGHT

            return kachel

        self.btn_duplicate = schaltflaeche("Duplizieren", self._duplicate_clicked)

        self.btn_delete = schaltflaeche("Löschen", self._delete_clicked)

        self.btn_cancel = schaltflaeche("Abbrechen", self._cancel_clicked)

        self.btn_apply = schaltflaeche("Übernehmen", self._apply_clicked)

        # -----------------------------------------------------
        # Zusammenbauen
        # -----------------------------------------------------

        self.row1.add_widget(
            self.btn_duplicate
        )

        self.row1.add_widget(
            self.btn_delete
        )

        self.row2.add_widget(
            self.btn_cancel
        )

        self.row2.add_widget(
            self.btn_apply
        )

        self.button_area.add_widget(
            self.row1
        )

        self.button_area.add_widget(
            self.row2
        )

        self.add_widget(
            self.button_area
        )
        pass

    # =====================================================
    # Canvas
    # =====================================================

    def _update_canvas(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

        y = self.top - self.HEADER_HEIGHT

        self.separator.points = [
            self.x,
            y,
            self.right,
            y
        ]

    # =====================================================
    # Öffnen
    # =====================================================

    def open(self, cart_item):

        self.cart_item = cart_item
        print("EditPanel.open:", cart_item.unit_price)

        self.lbl_article.text = cart_item.article.name

        self.quantity_editor.set_quantity(
            cart_item.quantity
        )

        price = int(cart_item.unit_price * 100)

        euro = price // 100
        cent = price % 100

        self.btn_price.set_title(
            f"{price // 100},{price % 100:02d} €"
        )

        self.slide_open()

    # =====================================================
    # Schließen
    # =====================================================

    def close(self):

        self.cart_item = None

        self.slide_close(on_closed=self._closed)

    # =====================================================

    def _closed(self, *args):

        self.lbl_article.text = ""

        self.btn_price.set_title("0,00 €")

    # =====================================================
    # Preis
    # =====================================================

    def _price_clicked(self, tile, action):

        if callable(self.price_callback):

            self.price_callback(
                self.cart_item
            )

    # =====================================================
    # Buttons
    # =====================================================

    def _duplicate_clicked(self, tile, action):

        if callable(self.duplicate_callback):
            self.duplicate_callback(self.cart_item)

    # -----------------------------------------------------

    def _delete_clicked(self, tile, action):

        if callable(self.delete_callback):
            self.delete_callback(self.cart_item)

    # -----------------------------------------------------

    def _cancel_clicked(self, tile, action):

        self.close()

    # -----------------------------------------------------

    def _apply_clicked(self, tile, action):

        if callable(self.apply_callback):
            self.apply_callback(
                self.cart_item,
                self.quantity_editor.quantity
            )

    def quantity_clicked(self, quantity):

        if callable(self.quantity_callback):
            self.quantity_callback(self.cart_item)