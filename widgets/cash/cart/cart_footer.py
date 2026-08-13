from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.kig_label import KiGLabel
from widgets.common.kig_action_tile import KiGActionTile


class CartFooter(BoxLayout):
    """Summen- und Aktionsbereich des Warenkorbs ohne Pfandanzeige."""

    def __init__(
            self,
            edit_callback=None,
            pay_callback=None,
            storno_confirm_callback=None,
            storno_cancel_callback=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.padding = (theme.CARD_PADDING,) * 4
        self.spacing = theme.CARD_SPACING
        self.size_hint_y = None
        self.height = 135

        with self.canvas.before:
            Color(*theme.CART_FOOTER_BACKGROUND)
            self._background = Rectangle()
            Color(*theme.CART_SEPARATOR)
            self._separator = Line(width=1)

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        total_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=46
        )

        caption = KiGLabel(text="Summe")
        caption.set_bold(True)
        caption.set_font_size(theme.FONT_SUBTITLE)
        caption.horizontal_alignment = "left"

        self.lbl_total = KiGLabel(text="0,00 €")
        self.lbl_total.set_bold(True)
        self.lbl_total.set_font_size(32)
        self.lbl_total.horizontal_alignment = "right"
        self.lbl_total.size_hint_x = None
        self.lbl_total.width = 170

        total_row.add_widget(caption)
        total_row.add_widget(self.lbl_total)
        self.add_widget(total_row)

        self.buttons = BoxLayout(
            orientation="horizontal",
            spacing=theme.ROW_SPACING,
            size_hint_y=None,
            height=theme.CART_ACTION_TILE_HEIGHT
        )
        self.add_widget(self.buttons)

        def tile(text, callback):
            schaltflaeche = KiGActionTile(
                text=text,
                callback=callback,
                height=theme.CART_ACTION_TILE_HEIGHT
            )

            # KiGActionTile setzt sich intern auf eine feste Breite
            # (theme.CATEGORY_TILE_WIDTH). Zwei davon passen knapp
            # nebeneinander, drei ragen über den Panelrand hinaus -
            # deshalb bestimmt hier das Layout die Breite.
            schaltflaeche.size_hint_x = 1
            schaltflaeche.size_hint_y = None
            schaltflaeche.height = theme.CART_ACTION_TILE_HEIGHT

            return schaltflaeche

        # Zwei Sätze von Schaltflächen: Im Storno-Modus wären
        # "Bearbeiten" und "Bezahlen" sinnlos bis gefährlich, deshalb
        # werden sie dort komplett ausgetauscht (siehe set_storno_mode).
        # Der Einstieg in den Storno sitzt oben in der Kopfzeile des
        # Warenkorbs neben "Leeren" (siehe cart_panel.py).
        self.edit_button = tile("Bearbeiten", edit_callback)
        self.pay_button = tile("Bezahlen", pay_callback)

        self.storno_cancel_button = tile("Abbrechen", storno_cancel_callback)
        self.storno_confirm_button = tile("Storno buchen", storno_confirm_callback)

        self.set_storno_mode(False)

    # =====================================================
    # Modus
    # =====================================================

    def set_storno_mode(self, aktiv):

        self.buttons.clear_widgets()

        if aktiv:
            self.buttons.add_widget(self.storno_cancel_button)
            self.buttons.add_widget(self.storno_confirm_button)
        else:
            self.buttons.add_widget(self.edit_button)
            self.buttons.add_widget(self.pay_button)

    def _update_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size
        y = self.top - 12
        self._separator.points = [self.x, y, self.right, y]

    def set_total(self, value: float):
        self.lbl_total.text = f"{value:.2f} €".replace(".", ",")

    def update(self, total: float):
        self.set_total(total)
