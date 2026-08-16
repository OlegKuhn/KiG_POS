from kivy.properties import (
    BooleanProperty,
    ObjectProperty
)

from kivy.graphics import (
    Color,
    RoundedRectangle,
    Line
)

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.metrics import dp

import theme
import config

from widgets.kig_label import KiGLabel


class CartItemWidget(ButtonBehavior, BoxLayout):
    """
    Darstellung einer Position im Warenkorb.
    """

    selected = BooleanProperty(False)

    callback = ObjectProperty(
        None,
        allownone=True
    )

    # Höhe einer Position. Bemessen nach den Mengentasten: Sie sollen
    # quadratisch sein (QUANTITY_BUTTON_WIDTH), und der Innenabstand
    # kommt oben und unten dazu.
    HEIGHT = 64

    PADDING = theme.TILE_PADDING
    SPACING = theme.SPACE_XS

    TITLE_SIZE = 18
    DETAIL_SIZE = 15

    # Mengentasten
    #
    # Sie gehen über die ganze Höhe der Position und sind fingerbreit:
    # 48 dp sind rund 8 mm und damit das Maß, unter dem Treffer auf
    # einem Tablet zur Glückssache werden. Vorher teilten sie sich die
    # untere Zeile mit den Beträgen und waren keine 3 mm hoch.
    QUANTITY_BUTTON_WIDTH = 48
    QUANTITY_BUTTON_FONT = 28

    RADIUS = 10

    def __init__(
            self,
            cart_item,
            callback=None,
            quantity_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.cart_item = cart_item
        self.callback = callback
        self.quantity_callback = quantity_callback

        # Waagerecht geteilt: links die Angaben zur Position, rechts
        # die beiden Mengentasten über die volle Höhe.
        self.orientation = "horizontal"

        self.size_hint = (1, None)
        self.height = dp(self.HEIGHT)

        self.padding = dp(self.PADDING)
        self.spacing = dp(self.SPACING)

        self.always_release = True

        # =====================================================
        # Hintergrund
        # =====================================================

        with self.canvas.before:

            self.bg_color = Color(
                *theme.CART_BACKGROUND
            )

            self.bg = RoundedRectangle(
                radius=[self.RADIUS]
            )

            self.border_color = Color(
                0, 0, 0, 0
            )

            self.border = Line(
                width=2
            )

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        # =====================================================
        # Angaben zur Position
        # =====================================================

        self.text_column = BoxLayout(
            orientation="vertical",
            spacing=dp(self.SPACING),
        )

        self.add_widget(self.text_column)

        # =====================================================
        # Titel
        # =====================================================

        self.lbl_title = KiGLabel()

        self.lbl_title.text = (
            cart_item.article.name
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

        # Sehr lange Artikelnamen sollen die feste Zeilenhöhe der
        # Warenkorb-Position nicht sprengen (der Text würde sonst über
        # die Zeile hinausgezeichnet) - ab der zweiten Zeile wird
        # deshalb mit "…" abgeschnitten statt umzubrechen.
        self.lbl_title.max_lines = 1
        self.lbl_title.shorten = True
        self.lbl_title.shorten_from = "right"

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.text_column.add_widget(
            self.lbl_title
        )

        # =====================================================
        # Untere Zeile
        # =====================================================

        self.bottom = BoxLayout()

        # =====================================================
        # Menge / Einzelpreis
        # =====================================================

        self.lbl_quantity = KiGLabel()

        self.lbl_quantity.text = (
            f"{cart_item.quantity} × "
            f"{cart_item.unit_price:.2f} "
            f"{config.CURRENCY}"
        )

        self.lbl_quantity.set_font_size(
            self.DETAIL_SIZE
        )

        self.lbl_quantity.set_color(
            theme.TEXT_SECONDARY
        )

        self.lbl_quantity.horizontal_alignment = "left"
        self.lbl_quantity.vertical_alignment = "middle"

        self.lbl_quantity.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.bottom.add_widget(
            self.lbl_quantity
        )

        # =====================================================
        # Gesamtpreis
        # =====================================================

        self.lbl_total = KiGLabel()

        self.lbl_total.text = (
            f"{cart_item.total_price:.2f} "
            f"{config.CURRENCY}"
        )

        self.lbl_total.set_bold(True)

        self.lbl_total.set_font_size(
            self.DETAIL_SIZE
        )

        self.lbl_total.set_color(
            theme.TEXT_PRIMARY
        )

        self.lbl_total.horizontal_alignment = "right"
        self.lbl_total.vertical_alignment = "middle"

        self.lbl_total.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.bottom.add_widget(
            self.lbl_total
        )

        self.text_column.add_widget(
            self.bottom
        )

        # =====================================================
        # Menge direkt ändern
        # =====================================================
        #
        # Ohne diese beiden Tasten muss man denselben Artikel mehrfach
        # antippen oder den Umweg über "Bearbeiten" gehen - bei Andrang
        # zu langsam.
        #
        # Sie stehen in einer eigenen Spalte am rechten Rand und
        # nehmen die volle Höhe der Position ein. Die Beträge bleiben
        # dabei untereinander bündig, weil diese Spalte in jeder Zeile
        # gleich breit ist.

        self.buttons = BoxLayout(
            orientation="horizontal",
            size_hint=(None, 1),
            width=2 * dp(self.QUANTITY_BUTTON_WIDTH) + dp(self.SPACING),
            spacing=dp(self.SPACING),
        )

        self.btn_minus = self._quantity_button("-", -1)
        self.buttons.add_widget(self.btn_minus)

        self.btn_plus = self._quantity_button("+", +1)
        self.buttons.add_widget(self.btn_plus)

        self.add_widget(
            self.buttons
        )

    # =====================================================
    # Mengentasten
    # =====================================================

    def _quantity_button(self, beschriftung, veraenderung):

        button = Button(
            text=beschriftung,
            size_hint=(1, 1),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size=f"{self.QUANTITY_BUTTON_FONT}sp", bold=True,
        )
        button.bind(
            on_release=lambda *_args: self._change_quantity(veraenderung)
        )
        return button

    def _change_quantity(self, veraenderung):

        if callable(self.quantity_callback):
            self.quantity_callback(self.cart_item, veraenderung)

    # =====================================================
    # Canvas
    # =====================================================

    def _update_canvas(self, *args):

        self.bg.pos = self.pos
        self.bg.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.RADIUS
        )

    # =====================================================
    # Auswahl
    # =====================================================

    def select(self):

        self.selected = True

        self.border_color.rgba = (
            theme.PRIMARY_ORANGE
        )

        self.lbl_title.set_color(
            theme.PRIMARY_ORANGE
        )

        self.lbl_quantity.set_color(
            theme.PRIMARY_ORANGE
        )

        self.lbl_total.set_color(
            theme.PRIMARY_ORANGE
        )

    # -----------------------------------------------------

    def unselect(self):

        self.selected = False

        self.border_color.rgba = (
            0, 0, 0, 0
        )

        self.lbl_title.set_color(
            theme.TEXT_PRIMARY
        )

        self.lbl_quantity.set_color(
            theme.TEXT_SECONDARY
        )

        self.lbl_total.set_color(
            theme.TEXT_PRIMARY
        )

    # =====================================================
    # Button
    # =====================================================

    def on_release(self):

        if callable(self.callback):

            self.callback(
                self,
                self.cart_item
            )