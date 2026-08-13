"""Linkes Panel: Auswahl eines Handbuch-Themas + PDF-Export."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel
from widgets.userguide.userguide_topic_card import UserguideTopicCard


class UserguideTopicPanel(RoundedPanel):
    """Zeigt alle Handbuch-Themen als auswählbare Liste.

    Unten sitzt der PDF-Export - bewusst hier und nicht neben der
    Anleitung rechts, weil er immer das KOMPLETTE Handbuch ausgibt
    und nicht nur das gerade gewählte Thema.
    """

    # Hochformat: Breite des Export-Knopfes in der Kopfzeile und
    # Anzahl der Themen nebeneinander.
    PORTRAIT_EXPORT_WIDTH = 210
    PORTRAIT_COLUMNS = 3

    def __init__(self, on_select_topic, on_export_pdf=None, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.on_select_topic = on_select_topic
        self.on_export_pdf = on_export_pdf
        self.selected_card = None

        # Im Hochformat liegt die Themenliste quer ÜBER der Anleitung
        # und ist entsprechend flach: Überschrift und Export teilen
        # sich dort eine Zeile, die Themen stehen nebeneinander statt
        # untereinander. Sonst bliebe für die Liste selbst nur noch
        # ein Streifen von wenigen Pixeln.
        self.hochformat = theme.is_portrait()

        title = KiGLabel(text="Themen")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(42)

        self.export_button = Button(
            text="Als PDF exportieren",
            size_hint_y=None, height=dp(theme.CATEGORY_TILE_HEIGHT),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="16sp", bold=True,
        )
        self.export_button.bind(on_release=lambda *_args: self._export_clicked())

        if self.hochformat:

            header = BoxLayout(
                orientation="horizontal",
                spacing=dp(theme.ROW_SPACING),
                size_hint_y=None,
                height=dp(theme.CATEGORY_TILE_HEIGHT)
            )

            title.size_hint_y = 1
            header.add_widget(title)

            self.export_button.size_hint_x = None
            self.export_button.width = dp(self.PORTRAIT_EXPORT_WIDTH)
            header.add_widget(self.export_button)

            self.add_widget(header)

        else:
            self.add_widget(title)

        self.scroll = ScrollView(bar_width=dp(12))

        if self.hochformat:
            self.list_layout = GridLayout(
                cols=self.PORTRAIT_COLUMNS,
                spacing=dp(theme.ROW_SPACING),
                size_hint_y=None
            )
        else:
            self.list_layout = BoxLayout(
                orientation="vertical",
                spacing=dp(theme.ROW_SPACING),
                size_hint_y=None
            )

        self.list_layout.bind(
            minimum_height=self.list_layout.setter("height")
        )
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        # -------------------------------------------------
        # PDF-Export
        # -------------------------------------------------

        if not self.hochformat:
            self.add_widget(self.export_button)

        self.status_label = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="12sp",
            size_hint_y=None, height=0, halign="left", valign="middle",
        )
        self.status_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.add_widget(self.status_label)

    def _export_clicked(self):

        if callable(self.on_export_pdf):
            self.on_export_pdf()

    def set_export_status(self, text):
        """Kurze Rückmeldung unter dem Export-Knopf (leerer Text
        blendet die Zeile wieder aus)."""

        self.status_label.text = text
        self.status_label.height = dp(34) if text else 0

    def set_export_available(self, verfuegbar):
        """Sperrt den Export, wenn er auf diesem Gerät nicht geht.

        Ein Knopf, der nur eine Fehlermeldung ausspuckt, ist ärgerlicher
        als einer, dem man ansieht, dass er gerade nichts kann.
        """

        self.export_button.disabled = not verfuegbar

        if not verfuegbar:
            self.export_button.text = "PDF-Export nicht verfügbar"

    def set_export_busy(self, busy):
        """Während des Exports den Knopf sperren - das Erzeugen des
        PDFs dauert je nach Anzahl der Screenshots einen Moment."""

        self.export_button.disabled = busy
        self.export_button.text = "Wird erstellt..." if busy else "Als PDF exportieren"

    def set_topics(self, topics):

        self.list_layout.clear_widgets()
        self.selected_card = None

        for topic in topics:
            card = UserguideTopicCard(
                topic=topic,
                callback=self._card_selected
            )
            self.list_layout.add_widget(card)

    def _card_selected(self, card, topic):

        if self.selected_card is not None:
            self.selected_card.unselect()

        self.selected_card = card
        card.select()

        self.on_select_topic(topic)

    def select_first(self):
        """Wählt das erste Thema aus (list_layout.children ist von
        unten nach oben sortiert, daher reversed())."""

        cards = [
            child for child in reversed(self.list_layout.children)
            if isinstance(child, UserguideTopicCard)
        ]

        if cards:
            self._card_selected(cards[0], cards[0].topic)
