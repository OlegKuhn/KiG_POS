"""Dashboard-Karte: aktueller Lagerbestand und seine Korrektur (nur Einzelartikel).

Der Verlauf steht seit der Aufteilung der Artikelmaske in einer
eigenen Karte rechts (siehe dashboard_verlauf_card.py).
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import config
import theme

from widgets.common.rounded_panel import RoundedPanel
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
        # Knapper Rand: Die Leiste steht unter den Stammdaten, und jede
        # Zeile, die sie weniger braucht, bekommen dort die Felder.
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            padding=(dp(theme.CARD_PADDING), dp(theme.SPACE_S)),
            **kwargs
        )

        # Die Karte ist so hoch wie ihr Inhalt - sie steht als Leiste
        # unter den Stammdaten, nicht mehr als volle Spalte.
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        self.on_adjust = on_adjust

        schmal = theme.is_narrow()

        stock_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(theme.CARD_SPACING))

        title = KiGLabel(text="Bestand")
        title.set_font_size(20)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_x = None
        title.width = dp(90 if schmal else 110)
        stock_row.add_widget(title)

        self.stock_label = KiGLabel(text="- Stück")

        # Auf dem Telefon kleiner: Neben "Bestand anpassen" blieben
        # der Zahl sonst keine 100 dp, und "55 Stück" brach um.
        self.stock_label.set_font_size(18 if schmal else 26)
        self.stock_label.set_bold(True)
        self.stock_label.set_alignment("left")
        self.stock_label.set_color(theme.TEXT_PRIMARY)
        stock_row.add_widget(self.stock_label)

        adjust_button = Button(
            text="Bestand anpassen",
            size_hint=(None, None),
            size=(dp(150 if schmal else 180), dp(50)),
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
