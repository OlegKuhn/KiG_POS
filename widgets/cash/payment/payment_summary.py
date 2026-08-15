"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    payment_summary.py

Beschreibung:
    Anzeige der Zahlungsinformationen.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.uix.boxlayout import BoxLayout

from kivy.metrics import dp

import theme

from widgets.kig_label import KiGLabel


class PaymentSummary(BoxLayout):
    """
    Anzeige der Zahlungsinformationen.
    """

    SPACING = theme.CARD_SPACING

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.spacing = dp(self.SPACING)

        self._paid = 0.0
        self._total = 0.0

        # =====================================================
        # Gegeben
        # =====================================================

        self.lbl_paid_caption = KiGLabel()

        self.lbl_paid_caption.text = "Gegeben"
        self.lbl_paid_caption.set_font_size(16)
        self.lbl_paid_caption.set_color(theme.TEXT_PRIMARY)

        self.add_widget(self.lbl_paid_caption)

        self.lbl_paid = KiGLabel()

        self.lbl_paid.set_font_size(32)
        self.lbl_paid.set_bold(True)
        self.lbl_paid.set_color(theme.TEXT_PRIMARY)

        self.add_widget(self.lbl_paid)

        # =====================================================
        # Zu zahlen
        # =====================================================

        self.lbl_total_caption = KiGLabel()

        self.lbl_total_caption.text = "Zu zahlen"
        self.lbl_total_caption.set_font_size(16)
        self.lbl_total_caption.set_color(theme.TEXT_PRIMARY)

        self.add_widget(self.lbl_total_caption)

        self.lbl_total = KiGLabel()

        self.lbl_total.set_font_size(32)
        self.lbl_total.set_bold(True)
        self.lbl_total.set_color(theme.TEXT_PRIMARY)

        self.add_widget(self.lbl_total)

        # =====================================================
        # Rückgeld
        # =====================================================

        self.lbl_change_caption = KiGLabel()

        self.lbl_change_caption.text = "Rückgeld"
        self.lbl_change_caption.set_font_size(16)
        self.lbl_change_caption.set_color(theme.TEXT_PRIMARY)

        self.add_widget(self.lbl_change_caption)

        self.lbl_change = KiGLabel()

        self.lbl_change.set_font_size(32)
        self.lbl_change.set_bold(True)
        self.lbl_change.set_color(theme.TEXT_PRIMARY)

        self.add_widget(self.lbl_change)

        self.update()

    # =====================================================
    # Setter
    # =====================================================

    def set_paid(self, amount):
        """
        Setzt den gegebenen Betrag.
        """

        self._paid = amount

        self.update()

    # -----------------------------------------------------

    def set_total(self, amount):
        """
        Setzt den zu zahlenden Betrag.
        """

        self._total = amount

        self.update()

    # =====================================================
    # Eigenschaften
    # =====================================================

    @property
    def paid(self):

        return self._paid

    @property
    def total(self):

        return self._total

    @property
    def change(self):

        if self._paid >= self._total:
            return self._paid - self._total

        return 0.0

    # =====================================================
    # Anzeige aktualisieren
    # =====================================================

    def update(self):
        """
        Aktualisiert die Anzeige.
        """

        self.lbl_paid.text = f"{self.paid:.2f} €"

        self.lbl_total.text = f"{self.total:.2f} €"

        self.lbl_change.text = f"{self.change:.2f} €"