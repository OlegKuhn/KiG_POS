"""Popup: fragt beim Wareneingang eines "Flasche"-Artikels Größe und Preis ab.

Zwei Schritte, beide über den Nummernblock:

    1. Wie viel ml hat eine Flasche?
    2. Was hat eine Flasche gekostet?

Der Bestand wird für solche Artikel immer intern in ml geführt - der
erste Wert rechnet "N Flaschen" in die zu buchende ml-Menge um.

Der zweite Wert ist der Grund, warum dieses Popup überhaupt zweistufig
ist: Aus Preis und Inhalt ergeben sich die Kosten je ml, und nur die
kann ein Rezept anteilig verrechnen. Wird beim nächsten Mal eine
andere Größe zu einem anderen Preis gekauft, mischt die Datenbank
beides zum gewichteten Durchschnitt (siehe
database.py:book_goods_receipt) - die Flaschengröße muss also nicht
über die Zeit gleich bleiben.
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.common.numpad.numpad_panel import NumpadPanel
from widgets.kig_label import KiGLabel
from widgets.common.kig_popup import KiGPopup


class BottleSizePopup(KiGPopup):

    def __init__(
            self,
            article_name,
            bottle_count,
            default_size_ml,
            on_confirm,
            default_price=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.on_confirm = on_confirm
        self.article_name = article_name
        self.bottle_count = bottle_count
        self.default_price = default_price

        self.bottle_size_ml = None

        self.title = "Wareneingang"
        self.size_hint = (None, None)
        self.size = (dp(theme.NUMPAD_PANEL_WIDTH + 50), dp(580))
        self.auto_dismiss = False

        root = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        with root.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_background, size=self._update_background)

        self.info = KiGLabel(text="")
        self.info.set_font_size(17)
        self.info.set_bold(True)
        self.info.set_alignment("left")
        self.info.set_color(theme.TEXT_PRIMARY)
        self.info.size_hint_y = None
        self.info.height = dp(64)
        root.add_widget(self.info)

        self.numpad = NumpadPanel()
        root.add_widget(self.numpad)

        self.content = root

        self._frage_groesse(default_size_ml)

    # =====================================================
    # Schritt 1: Flaschengröße
    # =====================================================

    def _frage_groesse(self, default_size_ml):

        self.info.text = (
            f"{self.bottle_count} × \"{self.article_name}\"\n"
            "Schritt 1 von 2: Wie viel ml hat eine Flasche?"
        )

        self.numpad.open(
            value=int(default_size_ml or 0),
            mode="integer",
            confirm_callback=self._groesse_bestaetigt,
            cancel_callback=self.dismiss,
        )

    def _groesse_bestaetigt(self, bottle_size_ml):

        if bottle_size_ml <= 0:
            self.dismiss()
            return

        self.bottle_size_ml = bottle_size_ml

        self._frage_preis()

    # =====================================================
    # Schritt 2: Preis je Flasche
    # =====================================================

    def _frage_preis(self):

        self.info.text = (
            f"{self.bottle_count} × \"{self.article_name}\" "
            f"à {self.bottle_size_ml:g} ml\n"
            "Schritt 2 von 2: Was kostet eine Flasche im Einkauf?"
        )

        # Der Nummernblock rechnet im Preismodus in Cent.
        self.numpad.open(
            value=int(round((self.default_price or 0) * 100)),
            mode="price",
            confirm_callback=self._preis_bestaetigt,
            cancel_callback=self.dismiss,
        )

    def _preis_bestaetigt(self, cent):

        self.dismiss()

        if not callable(self.on_confirm):
            return

        # Ohne Preisangabe bleibt es beim zuletzt bekannten Preis -
        # besser als eine 0, die sich später als Gewinn ausgibt.
        preis = (cent / 100) if cent > 0 else None

        self.on_confirm(self.bottle_size_ml, preis)

    # =====================================================

    def _update_background(self, instance, _value):
        self._background.pos = instance.pos
        self._background.size = instance.size
