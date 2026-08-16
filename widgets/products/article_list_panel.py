"""Mittleres/rechtes Panel: zusammengeführte Artikelliste."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel
from widgets.products.article_list_row import ArticleListRow


class ArticleListPanel(RoundedPanel):
    """Zeigt alle Artikel (gefiltert nach Kategorie) als Liste."""

    HEADER_ROW_HEIGHT = 42

    # Breite, die Überschrift und Schaltflächen nebeneinander
    # brauchen. Darunter wandern die Schaltflächen in eine eigene
    # Zeile.
    HEADER_MIN_WIDTH = 620

    # Darunter reicht selbst die eigene Zeile nicht mehr für die
    # ausgeschriebenen Beschriftungen.
    SHORT_LABEL_WIDTH = 380

    LANGE_BESCHRIFTUNGEN = {
        "sort_button": "Sortierung",
        "export_button": "Einkaufsliste exportieren",
        "new_button": "+ Neuer Artikel",
    }

    KURZE_BESCHRIFTUNGEN = {
        "sort_button": "Sortieren",
        "export_button": "Export",
        "new_button": "+ Neu",
    }

    def __init__(
            self,
            new_callback,
            amount_callback,
            confirm_callback,
            edit_callback,
            delete_callback,
            sort_callback,
            export_callback,
            **kwargs
    ):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.new_callback = new_callback
        self.amount_callback = amount_callback
        self.confirm_callback = confirm_callback
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback
        self.sort_callback = sort_callback
        self.export_callback = export_callback

        self.rows = {}
        self.title_label = None

        # -------------------------------------------------
        # Kopfzeile
        # -------------------------------------------------

        # Die Kopfzeile passt sich der Breite an (siehe
        # _update_header): Auf einem Telefon brauchen Überschrift und
        # drei Schaltflächen nebeneinander mehr Platz, als überhaupt da
        # ist - dort rücken die Schaltflächen unter die Überschrift und
        # tragen kürzere Beschriftungen.

        self.header = BoxLayout(
            size_hint_y=None, height=dp(self.HEADER_ROW_HEIGHT),
            spacing=dp(theme.ROW_SPACING),
        )

        self.title_label = KiGLabel(text="Artikel")
        self.title_label.set_font_size(26)
        self.title_label.set_bold(True)
        self.title_label.set_alignment("left")
        self.title_label.set_color(theme.PRIMARY_ORANGE)
        self.header.add_widget(self.title_label)

        self.header_buttons = BoxLayout(spacing=dp(theme.ROW_SPACING))

        self.sort_button = Button(
            text="Sortierung",
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="14sp", bold=True,
        )
        self.sort_button.bind(on_release=lambda *_args: self.sort_callback())
        self.header_buttons.add_widget(self.sort_button)

        self.export_button = Button(
            text="Einkaufsliste exportieren",
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="14sp", bold=True,
        )
        self.export_button.bind(on_release=lambda *_args: self.export_callback())
        self.header_buttons.add_widget(self.export_button)

        self.new_button = Button(
            text="+ Neuer Artikel",
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="14sp", bold=True,
        )
        self.new_button.bind(on_release=lambda *_args: self.new_callback())
        self.header_buttons.add_widget(self.new_button)

        self.header.add_widget(self.header_buttons)

        self.add_widget(self.header)

        self.bind(width=self._update_header)
        self._update_header()

        self.export_status = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="12sp", size_hint_y=None,
            height=dp(18), halign="right", valign="middle",
        )
        self.export_status.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.add_widget(self.export_status)

        # -------------------------------------------------
        # Spaltenkopf
        # -------------------------------------------------

        # Im Hochformat entfällt der Spaltenkopf: Dort steht jede Zeile
        # zweizeilig und trägt ihre Beschriftungen selbst, es gibt also
        # keine durchgehenden Spalten mehr, über die er passen könnte
        # (siehe article_list_row.ArticleListRow._build_portrait).
        if not theme.is_portrait():

            columns = BoxLayout(
                size_hint_y=None, height=dp(24),
                spacing=dp(theme.ROW_SPACING), padding=(dp(theme.CARD_SPACING), 0),
            )
            for text, width in (("Artikel", None), ("Verkauf", dp(78)), ("Einkauf", dp(78)),
                                ("Bestand", dp(78)), ("Menge", dp(80)), ("", dp(90)),
                                ("", dp(100)), ("", dp(46))):
                columns.add_widget(Label(
                    text=text, color=theme.TEXT_SECONDARY, font_size="11sp", bold=True,
                    halign="left" if width is None else "right", valign="middle",
                    size_hint_x=None if width else 1, width=width or 0,
                ))
            self.add_widget(columns)

        # -------------------------------------------------
        # Liste
        # -------------------------------------------------

        self.scroll = ScrollView(bar_width=dp(12))

        self.list_layout = BoxLayout(
            orientation="vertical", spacing=dp(theme.ROW_SPACING), size_hint_y=None
        )
        self.list_layout.bind(
            minimum_height=self.list_layout.setter("height")
        )
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

    def set_title(self, text):
        self.title_label.text = text

    def _update_header(self, *_args):
        """Ordnet die Kopfzeile nach verfügbarer Breite.

        Drei Schaltflächen neben der Überschrift brauchen rund 620 dp.
        Auf einem Telefon sind das mehr Bildpunkte, als der Bildschirm
        breit ist - dort rücken sie in eine eigene Zeile, und wird es
        noch enger, tragen sie kürzere Beschriftungen.
        """

        innen = self.width - dp(theme.CARD_PADDING) * 2

        eine_zeile = innen >= dp(self.HEADER_MIN_WIDTH)

        self.header.orientation = "horizontal" if eine_zeile else "vertical"

        zeilenhoehe = dp(self.HEADER_ROW_HEIGHT)

        self.header.height = (
            zeilenhoehe if eine_zeile
            else zeilenhoehe * 2 + dp(theme.ROW_SPACING)
        )

        beschriftungen = (
            self.LANGE_BESCHRIFTUNGEN
            if innen >= dp(self.SHORT_LABEL_WIDTH)
            else self.KURZE_BESCHRIFTUNGEN
        )

        for name, text in beschriftungen.items():
            getattr(self, name).text = text

    def set_export_status(self, text):
        self.export_status.text = text

    def set_articles(self, articles, order_amounts):

        self.list_layout.clear_widgets()
        self.rows.clear()

        if not articles:
            self.list_layout.add_widget(self._empty_label())
            return

        for article in articles:
            row = ArticleListRow(
                article=article,
                order_amount=order_amounts.get(article["id"], 0),
                amount_callback=self.amount_callback,
                confirm_callback=self.confirm_callback,
                edit_callback=self.edit_callback,
                delete_callback=self.delete_callback,
            )
            self.rows[article["id"]] = row
            self.list_layout.add_widget(row)

    def update_row_amount(self, article_id, amount):
        row = self.rows.get(article_id)
        if row is not None:
            row.set_order_amount(amount)

    @staticmethod
    def _empty_label():
        label = KiGLabel(text="Keine Artikel in dieser Kategorie.")
        label.set_font_size(15)
        label.set_alignment("left")
        label.set_color(theme.TEXT_SECONDARY)
        label.size_hint_y = None
        label.height = dp(40)
        return label
