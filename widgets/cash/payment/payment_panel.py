"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    payment_panel.py

Beschreibung:
    Panel für den Zahlungsvorgang.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.graphics import (
    Color,
    Rectangle
)
from kivy.uix.boxlayout import BoxLayout

from kivy.metrics import dp

import theme

from widgets.kig_label import KiGLabel
from widgets.cash.payment.payment_summary import PaymentSummary
from widgets.cash.payment.payment_footer import PaymentFooter
from widgets.common.slide_panel import SlidePanel


class PaymentPanel(SlidePanel, BoxLayout):
    """
    Panel für den Zahlungsvorgang.
    """

    PANEL_WIDTH = 350

    HEADER_HEIGHT = 60

    PADDING = theme.CARD_PADDING
    SPACING = theme.CARD_SPACING

    def __init__(
            self,
            cancel_callback=None,
            ok_callback=None,
            shortcut_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.padding = dp(self.PADDING)
        self.spacing = dp(self.SPACING)

        #
        # Standardmäßig geschlossen
        #

        self.init_slide(dp(self.PANEL_WIDTH))

        with self.canvas.before:

            self.bg_color = Color(
                *theme.CARD
            )

            self.bg = Rectangle()

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        # =====================================================
        # Header
        # =====================================================

        self.header = BoxLayout(
            size_hint=(1, None),
            height=dp(self.HEADER_HEIGHT)
        )

        self.lbl_title = KiGLabel()

        self.lbl_title.text = "Bezahlen"

        self.lbl_title.set_font_size(24)
        self.lbl_title.set_bold(True)
        self.lbl_title.set_color(theme.PRIMARY_ORANGE)

        self.lbl_title.horizontal_alignment = "center"
        self.lbl_title.vertical_alignment = "middle"

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.header.add_widget(
            self.lbl_title
        )

        self.add_widget(
            self.header
        )

        # =====================================================
        # Summary
        # =====================================================

        self.summary = PaymentSummary(
            shortcut_callback=shortcut_callback
        )

        self.add_widget(
            self.summary
        )

        # =====================================================
        # Footer
        # =====================================================

        self.footer = PaymentFooter(
            cancel_callback=cancel_callback,
            ok_callback=ok_callback
        )

        self.add_widget(
            self.footer
        )

    # =====================================================
    # Hintergrund
    # =====================================================

    def _update_canvas(self, *args):

        self.bg.pos = self.pos
        self.bg.size = self.size

    # =====================================================
    # Panel
    # =====================================================

    def open(self, total):

        self.summary.set_total(total)

        self.summary.set_paid(0.0)

        # Jeder Zahlvorgang faengt bei null an - auch die gelegten
        # Scheine.
        self.summary.scheine_zuruecksetzen()

        self.slide_open()

    # -----------------------------------------------------

    def close(self):

        self.slide_close()

    # =====================================================
    # Schnittstelle
    # =====================================================

    def set_paid_amount(self, amount):

        self.summary.set_paid(amount)

    # -----------------------------------------------------

    def schein_gelegt(self, betrag):

        self.summary.schein_gelegt(betrag)

    # -----------------------------------------------------

    def scheine_zuruecksetzen(self):

        self.summary.scheine_zuruecksetzen()

    # -----------------------------------------------------

    @property
    def paid(self):

        return self.summary.paid

    # -----------------------------------------------------

    @property
    def total(self):

        return self.summary.total

    # -----------------------------------------------------

    @property
    def change(self):

        return self.summary.change