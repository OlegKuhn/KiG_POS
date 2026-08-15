"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    payment_footer.py

Beschreibung:
    Footer des PaymentPanels.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.uix.boxlayout import BoxLayout

from kivy.metrics import dp

import theme

from widgets.common.kig_action_tile import KiGActionTile


class PaymentFooter(BoxLayout):
    """
    Footer des PaymentPanels.
    """

    HEIGHT = 70
    SPACING = theme.ROW_SPACING

    def __init__(
            self,
            cancel_callback=None,
            ok_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.cancel_callback = cancel_callback
        self.ok_callback = ok_callback

        self.orientation = "horizontal"

        self.size_hint = (1, None)
        self.height = dp(self.HEIGHT)

        self.spacing = dp(self.SPACING)

        # =====================================================
        # Abbrechen
        # =====================================================

        self.btn_cancel = KiGActionTile(
            text="Abbrechen",
            callback=self._cancel_clicked
        )

        self.add_widget(
            self.btn_cancel
        )

        # =====================================================
        # OK
        # =====================================================

        self.btn_ok = KiGActionTile(
            text="OK",
            callback=self._ok_clicked
        )

        self.add_widget(
            self.btn_ok
        )

    # =====================================================
    # Button-Callbacks
    # =====================================================

    def _cancel_clicked(self, tile, action):
        """
        Abbrechen wurde gedrückt.
        """

        if callable(self.cancel_callback):
            self.cancel_callback()

    # -----------------------------------------------------

    def _ok_clicked(self, tile, action):
        """
        OK wurde gedrückt.
        """

        if callable(self.ok_callback):
            self.ok_callback()