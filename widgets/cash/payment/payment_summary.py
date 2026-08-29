"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    payment_summary.py

Beschreibung:
    Anzeige und Schnellwahl beim Bezahlen.

    Oben die Scheine, die an der Bar tatsächlich über den
    Tresen gehen - ein Tipp darauf setzt den gegebenen
    Betrag. Das ist schneller als vier Tastendrücke und,
    wichtiger, es lässt sich nicht vertippen.

    Unten steht, was zählt: gegeben und Rückgeld.

    Der zu zahlende Betrag steht bewusst NICHT mehr hier -
    er steht schon groß im Warenkorb daneben. Zweimal
    dieselbe Zahl auf einem Bildschirm heißt, dass jemand
    sie vergleicht statt sie zu lesen.

Version:
    2.0.0

Build:
    0002
=========================================================
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout

import theme

from widgets.kig_label import KiGLabel


class PaymentSummary(BoxLayout):
    """
    Schnellwahl und Zahlungsinformationen.
    """

    SPACING = theme.CARD_SPACING

    # Die Scheine, die im Vereinsheim vorkommen. Kleiner als 5 EUR
    # lohnt die Abkürzung nicht - da ist der Nummernblock schneller.
    SCHNELLWAHL = (5, 10, 20, 50, 100)

    # Drei nebeneinander statt fünf: Bei 350 dp Panelbreite blieben
    # sonst 57 dp je Knopf - zu wenig für einen Daumen.
    SPALTEN = 3

    BUTTON_HEIGHT = 62
    CAPTION_HEIGHT = 26
    ROW_HEIGHT = 46

    def __init__(self, shortcut_callback=None, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.spacing = dp(self.SPACING)

        self.shortcut_callback = shortcut_callback

        self._paid = 0.0
        self._total = 0.0

        # =====================================================
        # Oben: Schnellwahl
        # =====================================================

        self.add_widget(
            self._caption("Schnellwahl")
        )

        zeilen = -(-len(self.SCHNELLWAHL) // self.SPALTEN)

        self.shortcut_grid = GridLayout(
            cols=self.SPALTEN,
            spacing=dp(theme.ROW_SPACING),
            size_hint=(1, None),
            height=(
                zeilen * dp(self.BUTTON_HEIGHT)
                + (zeilen - 1) * dp(theme.ROW_SPACING)
            ),
        )

        self.shortcut_buttons = []

        for betrag in self.SCHNELLWAHL:

            knopf = Button(
                text=f"{betrag} €",
                background_normal="", background_down="",
                background_color=theme.SURFACE,
                color=theme.TEXT_PRIMARY,
                font_size="20sp", bold=True,
            )

            knopf.bind(
                on_release=lambda _instanz, wert=betrag:
                self._shortcut_gewaehlt(wert)
            )

            self.shortcut_buttons.append(knopf)
            self.shortcut_grid.add_widget(knopf)

        self.add_widget(self.shortcut_grid)

        # =====================================================
        # Unten: gegeben und Rückgeld
        # =====================================================

        # Ein Abstandhalter dazwischen: Schnellwahl ist Bedienung,
        # das Darunter ist Ergebnis. Die Trennung soll man sehen.
        self.add_widget(BoxLayout())

        self.lbl_paid = self._value_label()

        self.add_widget(
            self._row("Gegeben", self.lbl_paid)
        )

        self.lbl_change = self._value_label()

        self.add_widget(
            self._row("Rückgeld", self.lbl_change)
        )

        self.update()

    # =====================================================
    # Bausteine
    # =====================================================

    @staticmethod
    def _caption(text):

        label = KiGLabel(text=text)
        label.set_font_size(16)
        label.set_bold(True)
        label.set_alignment("left")
        label.set_color(theme.TEXT_SECONDARY)
        label.size_hint_y = None
        label.height = dp(PaymentSummary.CAPTION_HEIGHT)

        return label

    @staticmethod
    def geld(betrag):
        """Betrag mit Komma - wie in der Warenkorbsumme, im
        Kassenbuch und in der Statistik.

        Hier stand bisher der Punkt aus Pythons Standardformat. Auf
        demselben Bildschirm "13,00 €" als Summe und "10.00 €"
        daneben zu lesen, ist genau die Art Kleinigkeit, die an der
        Bar fuer einen Wimpernschlag Unsicherheit sorgt.

        (Die einzelnen Warenkorbzeilen schreiben noch mit Punkt -
        eine alte Stelle, die hier nicht mit umgebaut wurde.)
        """

        return f"{float(betrag or 0):.2f} €".replace(".", ",")

    @staticmethod
    def _value_label():

        label = KiGLabel()
        label.set_font_size(28)
        label.set_bold(True)
        label.set_alignment("right")
        label.set_color(theme.TEXT_PRIMARY)

        return label

    def _row(self, text, wert_label):
        """Eine Zeile der Tabelle: links die Bezeichnung, rechts der
        Betrag."""

        zeile = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(self.ROW_HEIGHT),
            spacing=dp(theme.ROW_SPACING),
        )

        beschriftung = KiGLabel(text=text)
        beschriftung.set_font_size(17)
        beschriftung.set_alignment("left")
        beschriftung.set_color(theme.TEXT_SECONDARY)

        zeile.add_widget(beschriftung)
        zeile.add_widget(wert_label)

        return zeile

    # =====================================================
    # Schnellwahl
    # =====================================================

    def _shortcut_gewaehlt(self, betrag):

        if callable(self.shortcut_callback):
            self.shortcut_callback(betrag)

    def _schnellwahl_faerben(self):
        """Hebt hervor, welcher Schein gerade gedrückt wurde.

        Nur die Farbe - der Betrag steht ohnehin darunter. Wer
        zwischendurch am Nummernblock tippt, sieht die Hervorhebung
        wieder verschwinden und weiß, dass jetzt sein eigener Wert
        gilt.
        """

        for knopf, betrag in zip(self.shortcut_buttons, self.SCHNELLWAHL):

            gewaehlt = abs(self._paid - betrag) < 0.005

            knopf.background_color = (
                theme.PRIMARY_ORANGE if gewaehlt else theme.SURFACE
            )
            knopf.color = (
                theme.TEXT_WHITE if gewaehlt else theme.TEXT_PRIMARY
            )

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

        Angezeigt wird er hier nicht (er steht im Warenkorb) -
        gebraucht wird er für das Rückgeld.
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

        self.lbl_paid.text = self.geld(self.paid)

        self.lbl_change.text = self.geld(self.change)

        # Reicht das Gegebene noch nicht, ist das Rückgeld keine
        # Aussage - dann steht dort 0,00, und zwar zurückhaltend.
        self.lbl_change.set_color(
            theme.SUCCESS if self.paid >= self.total and self.paid
            else theme.TEXT_SECONDARY
        )

        self._schnellwahl_faerben()
