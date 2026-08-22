"""Dashboard-Karte: offene Bestellmenge + Wareneingang buchen (nur Einzelartikel)."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.common.feldausrichtung import links_ausrichten
from widgets.kig_label import KiGLabel


class BestellmengeCard(RoundedPanel):
    """Entspricht der bisherigen Einkaufsliste, nur pro Artikel statt
    für alle Artikel auf einmal."""

    def __init__(self, on_amount_button, on_receive, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.on_amount_button = on_amount_button
        self.on_receive = on_receive

        title = KiGLabel(text="Einkauf / Bestellmenge")
        title.set_font_size(20)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(30)
        self.add_widget(title)

        hint = KiGLabel(
            text="Menge für die nächste Einkaufsliste festlegen. Beim "
                 "Wareneingang wird die Menge direkt dem Bestand gutgeschrieben."
        )
        hint.set_font_size(13)
        hint.set_alignment("left")
        hint.set_color(theme.TEXT_SECONDARY)
        hint.size_hint_y = None
        hint.height = dp(36)
        hint.text_size = (None, None)
        self.add_widget(hint)

        row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(theme.CARD_SPACING))

        self.amount_button = Button(
            text="0", size_hint=(None, None), size=(dp(110), dp(56)),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="20sp", bold=True,
        )
        links_ausrichten(self.amount_button)

        self.amount_button.bind(on_release=lambda *_args: self.on_amount_button())
        row.add_widget(self.amount_button)

        receive_button = Button(
            text="Wareneingang jetzt buchen",
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="15sp", bold=True,
        )
        receive_button.bind(on_release=lambda *_args: self.on_receive())
        row.add_widget(receive_button)

        self.add_widget(row)

        # Restlicher Platz bleibt frei (Karte füllt bei Nebeneinander-
        # Anordnung die volle Höhe des Dashboards).
        self.add_widget(BoxLayout())

    def set_amount(self, amount):
        self.amount_button.text = str(amount)

    def get_amount(self):
        try:
            return int(self.amount_button.text)
        except ValueError:
            return 0
