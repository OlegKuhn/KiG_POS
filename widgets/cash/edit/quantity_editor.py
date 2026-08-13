from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.common.clickable_label import ClickableLabel
from widgets.cash.edit.quantity_button import QuantityButton


class QuantityEditor(BoxLayout):

    LABEL_WIDTH = 120
    HEIGHT = 60
    SPACING = theme.ROW_SPACING

    def __init__(
            self,
            quantity=1,
            callback=None,
            edit_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.callback = callback
        self.edit_callback = edit_callback

        self._quantity = max(1, int(quantity))

        self.orientation = "horizontal"

        self.size_hint = (None, None)
        self.height = self.HEIGHT

        self.spacing = self.SPACING

        # =====================================================
        # Minus
        # =====================================================

        self.btn_minus = QuantityButton(
            text="-",
            callback=self._minus_clicked
        )

        self.add_widget(self.btn_minus)

        # =====================================================
        # Menge
        # =====================================================

        self.lbl_quantity = ClickableLabel(
            callback=self._quantity_clicked
        )

        self.lbl_quantity.set_bold(True)
        self.lbl_quantity.set_font_size(28)
        self.lbl_quantity.set_color(theme.TEXT_PRIMARY)

        self.lbl_quantity.horizontal_alignment = "center"
        self.lbl_quantity.vertical_alignment = "middle"

        self.lbl_quantity.size_hint = (None, None)
        self.lbl_quantity.width = self.LABEL_WIDTH
        self.lbl_quantity.height = self.HEIGHT

        self.lbl_quantity.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(self.lbl_quantity)

        # =====================================================
        # Plus
        # =====================================================

        self.btn_plus = QuantityButton(
            text="+",
            callback=self._plus_clicked
        )

        self.add_widget(self.btn_plus)

        # Gesamtbreite berechnen
        self.width = (
            self.btn_minus.width +
            self.SPACING +
            self.LABEL_WIDTH +
            self.SPACING +
            self.btn_plus.width
        )

        self._update()

    # =====================================================
    # Eigenschaften
    # =====================================================

    @property
    def quantity(self):

        return self._quantity

    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def set_quantity(self, quantity):

        self._quantity = max(1, int(quantity))
        self._update()

    # =====================================================
    # Buttons
    # =====================================================

    def _minus_clicked(self, button):

        if self._quantity > 1:

            self._quantity -= 1

            self._update()
            self._dispatch()

    # -----------------------------------------------------

    def _plus_clicked(self, button):

        self._quantity += 1

        self._update()
        self._dispatch()

    # -----------------------------------------------------

    def _quantity_clicked(self, label):

        if callable(self.edit_callback):
            self.edit_callback(self.quantity)

    # =====================================================
    # Intern
    # =====================================================

    def _update(self):

        self.lbl_quantity.text = str(self._quantity)

    # -----------------------------------------------------

    def _dispatch(self):

        if callable(self.callback):
            self.callback(self._quantity)