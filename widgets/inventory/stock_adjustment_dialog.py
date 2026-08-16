"""
=========================================================
KiG POS
=========================================================

Datei:
    stock_adjustment_dialog.py

Beschreibung:
    Dialog zur Bestandskorrektur.

    Bei Artikeln mit Einheit "Flasche" gibt es zusätzlich eine
    Flaschenrechner-Hilfe: Anzahl Flaschen × Flaschengröße (ml)
    ergibt automatisch den neuen Bestand in ml - der eigentliche
    Bestand wird für solche Artikel immer in ml geführt.

Version:
    2.0.0
=========================================================
"""

from datetime import datetime

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from widgets.common.kig_popup import KiGPopup
from kivy.uix.scrollview import ScrollView

import config
import theme

from widgets.kig_label import KiGLabel
from widgets.common.rounded_input import RoundedInput
from widgets.common.kig_action_tile import KiGActionTile


class StockAdjustmentDialog(KiGPopup):

    def __init__(
            self,
            article,
            current_stock,
            on_save=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.article = article
        self.current_stock = current_stock
        self.on_save = on_save

        self.title = "Bestandskorrektur"

        self.size_hint = (0.75, 0.85)

        self.auto_dismiss = False

        self.timestamp = datetime.now()

        self.is_bottle_article = self._article_stock_unit() == config.BOTTLE_UNIT
        self.bottle_size_used = None

        self.content = self.build_ui()

    def _article_stock_unit(self):

        if hasattr(self.article, "stock_unit"):
            return self.article.stock_unit

        if "stock_unit" in self.article.keys():
            return self.article["stock_unit"]

        return None

    def _article_bottle_size(self):

        if hasattr(self.article, "bottle_size_ml"):
            return self.article.bottle_size_ml

        if "bottle_size_ml" in self.article.keys():
            return self.article["bottle_size_ml"]

        return None

    # =====================================================
    # Oberfläche
    # =====================================================

    def build_ui(self):

        root = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING)
        )

        # Eigener, themefähiger Hintergrund statt des Kivy-eigenen
        # Popup-Standardskins - so ist der Kontrast zu den Labels in
        # jedem Modus garantiert (siehe create_label()).
        with root.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=self._update_background,
            size=self._update_background
        )

        # Alle Formularfelder stecken in einem scrollbaren Bereich,
        # damit sie bei vielen Feldern (z. B. Flaschenrechner) im
        # Rahmen des Dialogs bleiben statt über ihn hinauszuragen -
        # nur die Buttons bleiben unten fest sichtbar.
        fields = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            size_hint_y=None,
        )
        fields.bind(minimum_height=fields.setter("height"))

        fields_scroll = ScrollView(bar_width=dp(10), do_scroll_x=False)
        fields_scroll.add_widget(fields)
        root.add_widget(fields_scroll)

        # -------------------------------------------------
        # Artikelname
        # -------------------------------------------------

        if hasattr(self.article, "name"):

            article_name = self.article.name

        else:

            article_name = self.article["name"]

        fields.add_widget(

            self.create_label(
                f"Artikel: {article_name}",
                bold=True
            )

        )

        # -------------------------------------------------
        # Aktueller Bestand
        # -------------------------------------------------

        current_stock = self.format_quantity(
            self.current_stock
        )

        stock_caption = f"Aktueller Bestand: {current_stock}"
        if self.is_bottle_article:
            stock_caption += " ml"

        fields.add_widget(self.create_label(stock_caption))

        # -------------------------------------------------
        # Neuer Bestand
        # -------------------------------------------------

        fields.add_widget(

            self.create_label(
                "Neuer Bestand (ml)" if self.is_bottle_article else "Neuer Bestand",
                bold=True
            )

        )

        self.txt_stock = RoundedInput(
            text=current_stock,
            multiline=False,
            size_hint_y=None,
            height=dp(60)
        )

        fields.add_widget(
            self.txt_stock
        )

        # -------------------------------------------------
        # Flaschenrechner (nur Einheit "Flasche")
        # -------------------------------------------------

        if self.is_bottle_article:
            fields.add_widget(self._build_bottle_helper())

        # -------------------------------------------------
        # Grund
        # -------------------------------------------------

        fields.add_widget(

            self.create_label(
                "Grund",
                bold=True
            )

        )

        self.txt_reason = RoundedInput(
            multiline=False,
            size_hint_y=None,
            height=dp(60)
        )

        fields.add_widget(
            self.txt_reason
        )

        # -------------------------------------------------
        # Bearbeitet von
        # -------------------------------------------------

        fields.add_widget(

            self.create_label(
                "Bearbeitet von",
                bold=True
            )

        )

        self.txt_user = RoundedInput(
            multiline=False,
            size_hint_y=None,
            height=dp(60)
        )

        fields.add_widget(
            self.txt_user
        )

        # -------------------------------------------------
        # Zeitpunkt
        # -------------------------------------------------

        fields.add_widget(

            self.create_label(
                "Zeitpunkt",
                bold=True
            )

        )

        fields.add_widget(

            self.create_label(
                self.timestamp.strftime(
                    "%d.%m.%Y %H:%M:%S"
                )
            )

        )

        # -------------------------------------------------
        # Buttons (fest am unteren Rand, außerhalb des Scroll-Bereichs)
        # -------------------------------------------------

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(90),
            spacing=dp(theme.ROW_SPACING)
        )

        root.add_widget(
            buttons
        )

        buttons.add_widget(

            KiGActionTile(

                text="Abbrechen",

                callback=lambda *_:
                self.dismiss()

            )

        )

        buttons.add_widget(

            KiGActionTile(

                text="Speichern",

                callback=self.save

            )

        )

        return root

    def _build_bottle_helper(self):
        """Kleiner Rechner: Anzahl Flaschen × Flaschengröße -> ml.

        Übernimmt das Ergebnis per Knopfdruck in das Feld "Neuer
        Bestand" - der eigentliche Bestand bleibt so immer eindeutig
        in ml, die Flaschenangabe ist nur eine Eingabehilfe.
        """

        box = BoxLayout(
            orientation="vertical", spacing=dp(theme.ROW_SPACING),
            size_hint_y=None, height=dp(112),
        )

        box.add_widget(self.create_label("...oder in Flaschen umrechnen"))

        row = BoxLayout(spacing=dp(theme.ROW_SPACING), size_hint_y=None, height=dp(60))

        default_size = self._article_bottle_size()
        size_text = ""
        if default_size:
            size_text = (
                str(int(default_size)) if float(default_size).is_integer()
                else f"{default_size:.2f}".replace(".", ",")
            )

        self.txt_bottle_count = RoundedInput(
            hint_text="Anzahl Flaschen", multiline=False,
            size_hint_x=0.4,
        )
        row.add_widget(self.txt_bottle_count)

        self.txt_bottle_size = RoundedInput(
            hint_text="ml je Flasche", text=size_text, multiline=False,
            size_hint_x=0.4,
        )
        row.add_widget(self.txt_bottle_size)

        apply_button = Button(
            text="Übernehmen", size_hint_x=0.2,
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="14sp", bold=True,
        )
        apply_button.bind(on_release=lambda *_args: self._apply_bottle_helper())
        row.add_widget(apply_button)

        box.add_widget(row)

        return box

    def _apply_bottle_helper(self):

        try:
            count = float(self.txt_bottle_count.text.strip().replace(",", "."))
            size = float(self.txt_bottle_size.text.strip().replace(",", "."))
        except ValueError:
            return

        if count < 0 or size <= 0:
            return

        total_ml = count * size
        self.txt_stock.text = self.format_quantity(total_ml)
        self.bottle_size_used = size

    # =====================================================
    # Hintergrund
    # =====================================================

    def _update_background(self, instance, _value):

        self._background.pos = instance.pos
        self._background.size = instance.size

    # =====================================================
    # Labels
    # =====================================================

    def create_label(
            self,
            text,
            bold=False
    ):

        label = KiGLabel(
            text=text
        )

        label.set_color(
            theme.TEXT_PRIMARY
        )

        if bold:

            label.set_bold(True)

        # Feste Höhe: innerhalb des scrollbaren Formularbereichs
        # (size_hint_y=None, siehe build_ui()) würde ein flexibles
        # Label sonst auf Höhe 0 zusammenschrumpfen.
        label.size_hint_y = None
        label.height = dp(30)

        return label

    # =====================================================
    # Formatierung
    # =====================================================

    @staticmethod
    def format_quantity(quantity):

        try:

            if float(quantity).is_integer():

                return str(
                    int(quantity)
                )

        except Exception:

            pass

        return f"{float(quantity):.2f}"

    # =====================================================
    # Validierung
    # =====================================================

    def validate(self):

        stock = self.txt_stock.text.strip()

        reason = self.txt_reason.text.strip()

        user = self.txt_user.text.strip()

        if not stock:
            return False

        if not reason:
            return False

        if not user:
            return False

        try:

            float(
                stock.replace(",", ".")
            )

        except ValueError:

            return False

        return True

    # =====================================================
    # Speichern
    # =====================================================

    def save(self, *_):

        if not self.validate():
            return

        if callable(self.on_save):

            self.on_save(

                float(
                    self.txt_stock.text
                    .strip()
                    .replace(",", ".")
                ),

                self.txt_reason.text.strip(),

                self.txt_user.text.strip(),

                self.timestamp.strftime(
                    "%d.%m.%Y %H:%M:%S"
                ),

                self.bottle_size_used

            )

        self.dismiss()
