"""Dashboard-Karte: aktueller Lagerbestand + Änderungshistorie (nur Einzelartikel)."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import config
import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.inventory.history_tile import HistoryTile
from widgets.kig_label import KiGLabel


class BestandCard(RoundedPanel):
    """Zeigt den aktuellen Bestand und erlaubt eine Korrektur
    über den bestehenden StockAdjustmentDialog.

    Steht bei Nebeneinander-Anordnung im Dashboard neben der
    Stammdaten-Karte und füllt daher die volle verfügbare Höhe - die
    Historie scrollt deshalb in ihrem eigenen, begrenzten Bereich statt
    die Karte unbegrenzt wachsen zu lassen.
    """

    def __init__(self, on_adjust, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.on_adjust = on_adjust

        header = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(theme.ROW_SPACING))

        title = KiGLabel(text="Bestand")
        title.set_font_size(20)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        header.add_widget(title)
        self.add_widget(header)

        stock_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(theme.CARD_SPACING))

        self.stock_label = KiGLabel(text="- Stück")
        self.stock_label.set_font_size(26)
        self.stock_label.set_bold(True)
        self.stock_label.set_alignment("left")
        self.stock_label.set_color(theme.TEXT_PRIMARY)
        stock_row.add_widget(self.stock_label)

        adjust_button = Button(
            text="Bestand anpassen", size_hint=(None, None), size=(dp(180), dp(50)),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="15sp", bold=True,
        )
        adjust_button.bind(on_release=lambda *_args: self.on_adjust())
        stock_row.add_widget(adjust_button)

        self.add_widget(stock_row)

        # Flaschenäquivalent (z. B. "≈ 0,9 Flaschen à 700ml") bewusst
        # als eigene, kleinere Zeile UNTER dem Hauptbestand statt in
        # dasselbe Label gequetscht - sonst würde der Text bei
        # längeren Werten die feste Zeilenhöhe von stock_row sprengen.
        self.stock_detail_label = KiGLabel(text="")
        self.stock_detail_label.set_font_size(14)
        self.stock_detail_label.set_alignment("left")
        self.stock_detail_label.set_color(theme.TEXT_SECONDARY)
        self.stock_detail_label.size_hint_y = None
        self.stock_detail_label.height = 0
        self.stock_detail_label.opacity = 0
        self.add_widget(self.stock_detail_label)

        # -------------------------------------------------
        # "Reicht für" - verkaufbare Portionen je Rezept, das
        # diese Zutat verwendet (mehrere Rezepte teilen sich
        # denselben Bestand).
        # -------------------------------------------------

        self.reicht_fuer_container = BoxLayout(
            orientation="vertical", spacing=dp(theme.LABEL_SPACING), size_hint_y=None, height=0
        )
        self.reicht_fuer_container.bind(
            minimum_height=self.reicht_fuer_container.setter("height")
        )
        self.add_widget(self.reicht_fuer_container)

        history_title = KiGLabel(text="Änderungshistorie")
        history_title.set_font_size(16)
        history_title.set_bold(True)
        history_title.set_alignment("left")
        history_title.set_color(theme.TEXT_SECONDARY)
        history_title.size_hint_y = None
        history_title.height = dp(26)
        self.add_widget(history_title)

        self.history_container = BoxLayout(
            orientation="vertical", spacing=dp(theme.ROW_SPACING), size_hint_y=None
        )
        self.history_container.bind(
            minimum_height=self.history_container.setter("height")
        )

        history_scroll = ScrollView(bar_width=dp(10))
        history_scroll.add_widget(self.history_container)
        self.add_widget(history_scroll)

    def set_stock(self, quantity, unit="Stück", bottle_size_ml=None):

        value = float(quantity or 0)
        text = str(int(value)) if value.is_integer() else f"{value:.2f}".replace(".", ",")

        detail_text = ""

        if unit == config.BOTTLE_UNIT:
            self.stock_label.text = f"{text} ml"
            if bottle_size_ml:
                bottles = value / bottle_size_ml
                bottles_text = (
                    str(int(bottles)) if bottles.is_integer() else f"{bottles:.1f}".replace(".", ",")
                )
                size_text = (
                    str(int(bottle_size_ml)) if float(bottle_size_ml).is_integer()
                    else f"{bottle_size_ml:.2f}".replace(".", ",")
                )
                detail_text = f"≈ {bottles_text} Flaschen à {size_text}ml"
        else:
            self.stock_label.text = f"{text} {unit}"

        self.stock_detail_label.text = detail_text
        self._set_detail_visible(bool(detail_text))

    def _set_detail_visible(self, visible):
        self.stock_detail_label.height = dp(20) if visible else 0
        self.stock_detail_label.opacity = 1 if visible else 0

    def set_reicht_fuer(self, entries):
        """entries: Liste von (Rezeptname, verkaufbare_Menge)-Tupeln."""

        self.reicht_fuer_container.clear_widgets()

        if not entries:
            return

        caption = KiGLabel(text="Reicht für:")
        caption.set_font_size(14)
        caption.set_bold(True)
        caption.set_alignment("left")
        caption.set_color(theme.TEXT_SECONDARY)
        caption.size_hint_y = None
        caption.height = dp(22)
        self.reicht_fuer_container.add_widget(caption)

        for recipe_name, count in entries:
            row = Label(
                text=f"{recipe_name}: {count} Verkäufe",
                color=theme.TEXT_PRIMARY, font_size="14sp", size_hint_y=None,
                height=dp(22), halign="left", valign="middle",
            )
            row.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            self.reicht_fuer_container.add_widget(row)

    def set_history(self, entries):

        self.history_container.clear_widgets()

        if not entries:
            label = KiGLabel(text="Noch keine Bestandsänderungen vorhanden.")
            label.set_font_size(14)
            label.set_alignment("left")
            label.set_color(theme.TEXT_SECONDARY)
            label.size_hint_y = None
            label.height = dp(36)
            self.history_container.add_widget(label)
            return

        for entry in entries:
            self.history_container.add_widget(HistoryTile(entry))
