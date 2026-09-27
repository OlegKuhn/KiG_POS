from kivy.graphics import Color, Line, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout

from kivy.metrics import dp

import geldformat
import theme

from widgets.common.kig_bildknopf import bearbeitenknopf

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
        self.padding = 0
        self.spacing = dp(theme.CARD_SPACING)
        self.size_hint_y = None
        self.height = dp(138)

        with self.canvas.before:
            Color(*theme.CARD)
            self._background = RoundedRectangle(radius=[dp(8)])
            Color(0, 0, 0, 0)
            self._separator = Line(width=1)

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        total_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(46)
        )

        caption = KiGLabel(text="Gesamt")
        caption.set_color(theme.TEXT_PRIMARY)
        caption.set_bold(True)
        caption.set_font_size(theme.FONT_SUBTITLE)
        caption.horizontal_alignment = "left"

        self.lbl_total = KiGLabel(text="0,00 €")
        self.lbl_total.set_bold(True)
        self.lbl_total.set_font_size(34)
        self.lbl_total.set_color(theme.TEXT_PRIMARY)
        self.lbl_total.horizontal_alignment = "right"
        self.lbl_total.size_hint_x = None
        self.lbl_total.width = dp(142)

        total_row.add_widget(caption)
        total_row.add_widget(self.lbl_total)
        self.add_widget(total_row)

        self.buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(theme.ROW_SPACING),
            size_hint_y=None,
            height=dp(theme.CART_ACTION_TILE_HEIGHT)
        )
        self.add_widget(self.buttons)

        def tile(text, callback):
            schaltflaeche = KiGActionTile(
                text=text,
                callback=callback,
                height=dp(theme.CART_ACTION_TILE_HEIGHT)
            )

            # KiGActionTile setzt sich intern auf eine feste Breite
            # (theme.CATEGORY_TILE_WIDTH). Zwei davon passen knapp
            # nebeneinander, drei ragen über den Panelrand hinaus -
            # deshalb bestimmt hier das Layout die Breite.
            schaltflaeche.size_hint_x = 1
            schaltflaeche.size_hint_y = None
            schaltflaeche.height = dp(theme.CART_ACTION_TILE_HEIGHT)

            return schaltflaeche

        # Zwei Sätze von Schaltflächen: Im Storno-Modus wären
        # "Bearbeiten" und "Bezahlen" sinnlos bis gefährlich, deshalb
        # werden sie dort komplett ausgetauscht (siehe set_storno_mode).
        # Der Einstieg in den Storno sitzt oben in der Kopfzeile des
        # Warenkorbs neben "Leeren" (siehe cart_panel.py).
        # Breit genug fuer beides: Das Sinnbild sagt, was passiert,
        # das Wort bleibt daneben stehen.
        self.edit_button = bearbeitenknopf(
            lambda: edit_callback(None, None) if callable(edit_callback)
            else None,
            text="Bearbeiten",
            size_hint=(1, None),
            height=dp(theme.CART_ACTION_TILE_HEIGHT),
            font_size="16sp", bold=True,
        )
        self.pay_button = tile("Bezahlen", pay_callback)
        self.pay_button.background_color = theme.PRIMARY_ORANGE
        self.pay_button.normal_color = theme.PRIMARY_ORANGE
        self.pay_button.lbl_title.set_color(theme.TEXT_ON_ACCENT)
        self.storno_color = theme.ERROR

        self.storno_cancel_button = tile("Abbrechen", storno_cancel_callback)
        self.storno_confirm_button = tile("Storno buchen", storno_confirm_callback)

        self.storno_confirm_button.background_color = theme.ERROR
        self.storno_confirm_button.normal_color = theme.ERROR
        self.storno_confirm_button.lbl_title.set_color(theme.TEXT_ON_ACCENT)
        self.set_storno_mode(False)

    # =====================================================
    # Modus
    # =====================================================

    def set_storno_mode(self, aktiv):

        self.storno_active = aktiv
        self.buttons.clear_widgets()

        if aktiv:
            self.buttons.add_widget(self.storno_cancel_button)
            self.buttons.add_widget(self.storno_confirm_button)
        else:
            if getattr(self, "has_items", False):
                self.buttons.add_widget(self.edit_button)
            self.buttons.add_widget(self.pay_button)

    def _update_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size
        y = self.top - 12
        self._separator.points = [self.x, y, self.right, y]

    def set_total(self, value: float):
        self.lbl_total.text = geldformat.geld(value)

    def update(self, total: float, has_items=True):
        self.has_items = has_items
        self.pay_button.disabled = not has_items
        self.pay_button.opacity = 1
        self.pay_button.lbl_title.disabled_color = theme.TEXT_ON_ACCENT
        self.pay_button.background_color = (theme.PRIMARY_ORANGE if has_items else
            tuple(a * .5 + b * .5 for a, b in zip(theme.PRIMARY_ORANGE, theme.CARD)))
        self.set_storno_mode(self.storno_active)
        self.set_total(total)
