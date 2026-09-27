"""Mittleres/rechtes Panel: zusammengeführte Artikelliste."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import theme

from widgets.common.kig_bildknopf import neuknopf
from widgets.products.article_list_row import SPALTEN_INAKTIV, SPALTEN_QUER

from widgets.common.exporthinweis import hinweisfeld_vorbereiten
from widgets.common import schreibschutz

from widgets.common.kig_schalter import KiGSchalter
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel
from widgets.products.article_list_row import ArticleListRow, InaktiveArtikelZeile


class ArticleListPanel(RoundedPanel):
    """Zeigt alle Artikel (gefiltert nach Kategorie) als Liste."""

    HEADER_ROW_HEIGHT = 42

    # Breite, die Überschrift und Schaltflächen nebeneinander
    # brauchen. Darunter wandern die Schaltflächen in eine eigene
    # Zeile. Seit der Regler "Inaktive" dazugehört, sind es 720 dp
    # für die Zeile selbst - und daneben soll noch Platz bleiben.
    HEADER_MIN_WIDTH = 900

    # Darunter reicht selbst die eigene Zeile nicht mehr für die
    # ausgeschriebenen Beschriftungen.
    SHORT_LABEL_WIDTH = 440

    # Breite der Schaltflächen, solange sie neben der Überschrift
    # stehen. Ohne feste Breite teilten sie sich die Zeile hälftig mit
    # der Überschrift - und der längste Text ("Einkaufsliste
    # exportieren") liefe über seinen Knopf hinaus.
    BUTTON_WIDTHS = {
        "inaktiv_schalter": 170,
        "sort_button": 130,
        "export_button": 200,
        "teilen_button": 110,
        "new_button": 64,
    }

    LANGE_BESCHRIFTUNGEN = {
        "sort_button": "Sortierung",
        "export_button": "Einkaufsliste exportieren",
        "teilen_button": "Teilen",
        "new_button": "",
    }

    KURZE_BESCHRIFTUNGEN = {
        "sort_button": "Sortieren",
        "export_button": "Export",
        "teilen_button": "Teilen",
        "new_button": "",
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
            teilen_callback,
            ansicht_callback=None,
            aktivieren_callback=None,
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
        self.teilen_callback = teilen_callback
        self.ansicht_callback = ansicht_callback
        self.aktivieren_callback = aktivieren_callback

        # "aktiv" oder "inaktiv" - welcher Reiter gerade vorn liegt
        self.ansicht = "aktiv"

        self.rows = {}
        self.title_label = None

        # -------------------------------------------------
        # Kopfzeile
        # -------------------------------------------------

        # Die Kopfzeile passt sich der Breite an (siehe
        # _update_header): In einem schmalen Fenster brauchen Überschrift
        # und drei Schaltflächen nebeneinander mehr Platz, als da ist -
        # dort rücken die Schaltflächen unter die Überschrift und
        # tragen kürzere Beschriftungen.

        self.header = BoxLayout(
            size_hint_y=None, height=dp(self.HEADER_ROW_HEIGHT),
            spacing=dp(theme.ROW_SPACING),
        )

        # Die Überschrift bleibt als Beschriftung bestehen (sie sagt,
        # welche Kategorie gefiltert ist), steht aber nicht mehr in der
        # Karte: Dass man in der Artikelverwaltung ist, zeigt die
        # Kopfzeile.
        self.title_label = KiGLabel(text="Artikel")

        self.header.add_widget(Widget())

        self.header_buttons = BoxLayout(spacing=dp(theme.ROW_SPACING))

        # Aktiv oder inaktiv: ein Regler statt zweier Reiter.
        #
        # Geloescht wird ein Artikel nie, nur abgeschaltet - vorher
        # aber verschwand er damit spurlos aus der Liste. Die beiden
        # Reiter, die ihn zurueckholten, belegten dafuer eine eigene
        # Zeile ueber der Tabelle. Der Regler sagt dasselbe und passt
        # neben die Exportknoepfe.
        self.inaktiv_schalter = KiGSchalter(
            text="Inaktive",
            on_change=self._schalter_umgelegt,
        )
        self.header_buttons.add_widget(self.inaktiv_schalter)

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

        self.teilen_button = Button(
            text="Teilen",
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="14sp", bold=True,
        )
        self.teilen_button.bind(on_release=lambda *_args: self.teilen_callback())
        self.header_buttons.add_widget(self.teilen_button)

        # Nur das Plus - wofuer es steht, sagt die Ueberschrift
        # "Artikel" daneben.
        self.new_button = neuknopf(self.new_callback)
        self.header_buttons.add_widget(self.new_button)

        self.header.add_widget(self.header_buttons)

        self.add_widget(self.header)

        # Nebengeraet: Was die Datenbank ablehnt, wird hier gar nicht
        # erst angeboten (siehe widgets/common/schreibschutz.py).
        self.nur_ansicht = schreibschutz.nur_ansicht()

        if self.nur_ansicht:

            schreibschutz.sperren(self.new_button, self.sort_button)

            hinweis = Label(
                text=schreibschutz.HINWEIS,
                color=theme.WARNING, font_size="13sp", bold=True,
                halign="left", valign="middle",
                size_hint_y=None, height=dp(26),
            )
            hinweis.bind(
                size=lambda instanz, groesse: setattr(
                    instanz, "text_size", groesse
                )
            )
            self.add_widget(hinweis)

        self.bind(width=self._update_header)
        self._update_header()

        self.export_status = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="12sp",
            halign="right", valign="middle",
        )

        # Waechst mit: Nach einem Export steht hier zusaetzlich der
        # Ordner (siehe widgets/common/exporthinweis.py).
        hinweisfeld_vorbereiten(self.export_status, dp(18))
        self.add_widget(self.export_status)

        # -------------------------------------------------
        # Spaltenkopf
        # -------------------------------------------------

        # Im Hochformat entfällt der Spaltenkopf: Dort steht jede Zeile
        # zweizeilig und trägt ihre Beschriftungen selbst, es gibt also
        # keine durchgehenden Spalten mehr, über die er passen könnte
        # (siehe article_list_row.ArticleListRow._build_portrait).
        self.columns = None

        if not theme.is_portrait():

            self.columns = BoxLayout(
                size_hint_y=None, height=dp(24),
                spacing=dp(theme.ROW_SPACING), padding=(dp(theme.CARD_SPACING), 0),
            )

            self._spaltenkopf(SPALTEN_QUER)

            self.add_widget(self.columns)

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

    # =====================================================
    # Aktiv / inaktiv
    # =====================================================

    def _schalter_umgelegt(self, an):

        if callable(self.ansicht_callback):
            self.ansicht_callback("inaktiv" if an else "aktiv")

    def set_ansicht(self, ansicht, anzahl_inaktiv=None):
        """Zeigt die gewählte Liste; die Zahl am Regler sagt, ob sich
        ein Blick auf die inaktiven Artikel lohnt."""

        self.ansicht = ansicht

        if anzahl_inaktiv is not None:
            self.inaktiv_schalter.text = f"Inaktive ({anzahl_inaktiv})"

        self.inaktiv_schalter.setzen(ansicht == "inaktiv")

        if self.columns is not None:
            self._spaltenkopf(
                SPALTEN_INAKTIV if ansicht == "inaktiv" else SPALTEN_QUER
            )

    def _spaltenkopf(self, spalten):

        columns = self.columns
        columns.clear_widgets()

        # Dieselben Spalten wie die Zeilen darunter (siehe
        # SPALTEN_QUER) - und mit text_size: Ohne sie setzt Kivy den
        # Text mittig in seine Spalte, gleich welche Ausrichtung
        # eingestellt ist, und "Verkauf" stand neben statt ueber
        # "2,50 €".
        for text, breite, ausrichtung in spalten:

            kopf = Label(
                text=text, color=theme.TEXT_SECONDARY, font_size="11sp",
                bold=True, halign=ausrichtung, valign="middle",
                size_hint_x=None if breite else 1,
                width=dp(breite) if breite else 0,
            )

            # "Menge" steht ueber einem Feld, dessen Wert 12 dp vom
            # Rand beginnt - die Ueberschrift ruckt mit.
            if text == "Menge":
                kopf.padding = [dp(12), 0, 0, 0]

            kopf.bind(
                size=lambda instanz, groesse: setattr(
                    instanz, "text_size", groesse
                )
            )

            columns.add_widget(kopf)

    def set_title(self, text):
        self.title_label.text = text

    def _update_header(self, *_args):
        """Ordnet die Kopfzeile nach verfügbarer Breite.

        Vier Schaltflächen neben der Überschrift brauchen rund 740 dp.
        Gibt das Fenster die nicht her, rücken sie in eine eigene Zeile,
        und wird es noch enger, tragen sie kürzere Beschriftungen.
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


        # Neben der Überschrift behalten die Schaltflächen ihre Breite,
        # in der eigenen Zeile teilen sie sich den Platz.
        if eine_zeile:

            gesamt = 0

            for name, breite in self.BUTTON_WIDTHS.items():
                knopf = getattr(self, name)
                knopf.size_hint_x = None
                knopf.width = dp(breite)
                gesamt += dp(breite)

            self.header_buttons.size_hint_x = None
            self.header_buttons.width = (
                gesamt + dp(theme.ROW_SPACING) * (len(self.BUTTON_WIDTHS) - 1)
            )

        else:

            for name in self.BUTTON_WIDTHS:
                getattr(self, name).size_hint_x = 1

            self.header_buttons.size_hint_x = 1

    def set_export_status(self, text):
        self.export_status.text = text

    def set_articles(self, articles, order_amounts):

        self.list_layout.clear_widgets()
        self.rows.clear()

        if not articles:
            self.list_layout.add_widget(self._empty_label(
                "Keine inaktiven Artikel."
                if self.ansicht == "inaktiv"
                else "Keine Artikel in dieser Kategorie."
            ))
            return

        if self.ansicht == "inaktiv":

            for position, article in enumerate(articles):
                row = InaktiveArtikelZeile(
                    article=article,
                    aktivieren_callback=self.aktivieren_callback,
                    edit_callback=self.edit_callback,
                    zebra=position % 2 == 1,
                )
                self.rows[article["id"]] = row
                self.list_layout.add_widget(row)

            return

        # Abwechselnd weiß und leicht grau: Die Zeilen standen weiß auf
        # weißer Karte, und bei zwanzig Artikeln verrutschte das Auge
        # zwischen Name und Bestand in die Nachbarzeile.
        for position, article in enumerate(articles):
            row = ArticleListRow(
                article=article,
                order_amount=order_amounts.get(article["id"], 0),
                amount_callback=self.amount_callback,
                confirm_callback=self.confirm_callback,
                edit_callback=self.edit_callback,
                delete_callback=self.delete_callback,
                zebra=position % 2 == 1,
            )
            self.rows[article["id"]] = row
            self.list_layout.add_widget(row)

    def update_row_amount(self, article_id, amount):
        row = self.rows.get(article_id)
        if row is not None:
            row.set_order_amount(amount)

    @staticmethod
    def _empty_label(text="Keine Artikel in dieser Kategorie."):
        label = KiGLabel(text=text)
        label.set_font_size(15)
        label.set_alignment("left")
        label.set_color(theme.TEXT_SECONDARY)
        label.size_hint_y = None
        label.height = dp(40)
        return label
