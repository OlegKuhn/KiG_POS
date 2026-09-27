"""Auswertung der über die Kasse abgeschlossenen Verkäufe."""

from datetime import datetime

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

import config
import geldformat
import storage
import teilen
import theme
from database import DatabaseManager
from widgets.common.kig_popup import KiGPopup
from widgets.common.kig_symbol import KiGSymbolButton, KREUZ
from widgets.common.date_picker_popup import DatePickerPopup
from widgets.common.exporthinweis import (
    export_hinweis, hinweisfeld_vorbereiten,
)
from widgets.common.feld import Feldknopf
from widgets.common.kig_bildknopf import loeschknopf
from widgets.common.filterleiste import Filterleiste
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_divider import KiGDividerVertical
from widgets.common.rounded_spinner import RoundedSpinner
from widgets.kig_label import KiGLabel
from widgets.statistics.verkaufsauswertung import Verkaufsauswertung


class SaleRow(RecycleDataViewBehavior, ButtonBehavior, BoxLayout):
    """Eine auswählbare Zeile der Verkaufstabelle.

    Die Zeilen stehen in einer RecycleView: Gebaut werden nur so viele,
    wie auf den Bildschirm passen, und beim Rollen bekommen dieselben
    Zeilen neue Werte (refresh_view_attrs). Vorher entstand je
    verkaufter Einheit ein eigenes Widget mit acht Beschriftungen - bei
    18.000 Einheiten dauerte der Wechsel in die Statistik am Rechner
    fast vier Minuten, obwohl die Datenbank in 0,4 Sekunden fertig war.

    Ob eine Zeile ausgewählt ist, steht deshalb nicht in der Zeile,
    sondern in ihren Daten (data["selected"]) - die Zeile selbst zeigt
    gleich eine andere Einheit.
    """

    def __init__(self, **kwargs):
        # Flacher als frueher: Die Tabelle steht jetzt in der schmalen
        # rechten Spalte, dort zaehlt jede Zeile.
        self.zeilenhoehe = StatisticsScreen.zeilenhoehe()

        super().__init__(
            orientation="horizontal", size_hint_y=None,
            height=dp(self.zeilenhoehe), **kwargs
        )

        self.sale = None
        self.index = None
        self.selected = False
        self.ist_storno = False
        self.grundfarbe = theme.CARD

        with self.canvas.before:
            self._color = Color(*self.grundfarbe)
            self._background = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        self.bind(pos=self._refresh_canvas, size=self._refresh_canvas)

        # Dieselbe Aufteilung wie die Kopfzeile - beide kommen aus
        # StatisticsScreen.spalten().
        self.labels = []

        for width in StatisticsScreen.spalten()[1]:
            label = Label(
                text="", color=theme.TEXT_PRIMARY, font_size="12sp",
                halign="left", valign="middle",
                text_size=(None, dp(self.zeilenhoehe)),
                size_hint_x=width,
                shorten=True, shorten_from="right",
            )
            self.labels.append(label)
            self.add_widget(label)

    def refresh_view_attrs(self, rv, index, data):
        """Übernimmt die Werte einer anderen Einheit."""

        self.rv = rv
        self.index = index

        sale = self.sale = data["sale"]
        self.selected = data.get("selected", False)

        # Stornos stehen mit negativer Menge in denselben Tabellen. Die
        # Menge selbst wird in dieser Tabelle nicht angezeigt - ohne
        # eigene Kennzeichnung wäre eine Stornozeile also nicht von
        # einem Verkauf zu unterscheiden.
        self.ist_storno = (sale["quantity"] or 0) < 0

        # Grundfarbe merken: Beim Abwählen muss die Storno-Einfärbung
        # zurückkommen und nicht das normale Weiß.
        self.grundfarbe = theme.STORNO_ROW if self.ist_storno else theme.CARD

        artikel = sale["article_name"]
        if self.ist_storno:
            artikel = f"Storno: {artikel}"

        if StatisticsScreen.kompakt():

            values = (
                StatisticsScreen.format_date(sale["business_date"]),
                artikel,
                StatisticsScreen.money(sale["unit_price"]),
                StatisticsScreen.money(sale["profit"]),
            )

        else:

            values = (
                sale["event_name"],
                StatisticsScreen.format_date(sale["business_date"]),
                sale["category_name"],
                artikel,
                StatisticsScreen.money(sale["unit_price"]),
                StatisticsScreen.money(sale["purchase_price"]),
                StatisticsScreen.money(sale["profit"]),
            )

        for spalte, (label, value) in enumerate(zip(self.labels, values)):
            label.text = str(value)
            # Nur der Gewinn wird rot - der Betrag selbst bleibt lesbar,
            # das Vorzeichen macht die Richtung deutlich.
            label.color = (
                theme.ERROR
                if self.ist_storno and spalte == len(values) - 1
                else theme.TEXT_PRIMARY
            )

        self._faerben()

        return super().refresh_view_attrs(rv, index, data)

    def _faerben(self):

        self._color.rgba = (
            theme.PRIMARY_ORANGE_LIGHT if self.selected else self.grundfarbe
        )

    def _refresh_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    def on_release(self):

        if self.sale is None:
            return

        self.selected = not self.selected
        self._faerben()

        # In die Daten schreiben - sonst stünde die Auswahl nach dem
        # Rollen an einer anderen Einheit.
        if getattr(self, "rv", None) is not None and self.index is not None:
            self.rv.data[self.index]["selected"] = self.selected

        bildschirm = getattr(self.rv, "bildschirm", None)

        if bildschirm is not None:
            bildschirm._row_selected(self, self.selected)


class StatisticsScreen(Screen):
    """Tabellarische Umsatz- und Gewinnübersicht je Verkaufsposition."""

    ALLE_KATEGORIEN = "Alle Kategorien"

    # Höhe einer Kennzahlenzeile (Einnahmen, Ausgaben, Gewinn)
    TOTAL_ROW_HEIGHT = 34

    # Anteil der Breite, den im Querformat das Bild bekommt - der Rest
    # gehört den Einzelverkäufen.
    BILD_ANTEIL = 0.66

    def __init__(self, revenue_changed_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.revenue_changed_callback = revenue_changed_callback
        self.selected_rows = {}

        # Zuletzt ausgegebene Datei - sie haengt am Teilen-Knopf.
        self.letzte_ausgabe = None
        self.event_options = {"Alle Events": None}
        self.category_options = {self.ALLE_KATEGORIEN: None}

        # Im Hochformat steht die Auswertung unter der Verkaufstabelle
        # statt daneben (siehe theme.set_orientation).
        self.hochformat = theme.is_portrait()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(theme.SCREEN_PADDING),
            spacing=dp(theme.SCREEN_SPACING),
        )

        chart = self._build_auswertung_panel()
        sales = self._build_sales_panel()

        self.eigene_filter = False

        from widgets.common.title_actions import TitleActions
        self.title_actions = TitleActions(self._title('Statistik'), self.design_actions)

        root.add_widget(self.title_actions)
        root.add_widget(self.design_metrics)

        if self.hochformat:

            # Hochkant ist fuer zwei Spalten keine Breite da: Bild und
            # Tabelle stehen untereinander, die Seite rollt.
            root.size_hint_y = None
            root.bind(minimum_height=root.setter('height'))

            chart.size_hint = (1, None)
            chart.height = dp(350)
            sales.size_hint = (1, None)
            sales.height = dp(520)

            root.add_widget(chart)
            root.add_widget(sales)

            scroll = ScrollView(do_scroll_x=False, bar_width=dp(8))
            scroll.add_widget(root)
            self.add_widget(scroll)

            return

        # Quer: links das Bild ueber zwei Drittel, rechts die Belege
        # im letzten Drittel. Die Auswertung beantwortet die Frage
        # ("Was ging weg?"), die Einzelverkaeufe belegen sie - sie
        # braucht deshalb den Platz, die Tabelle die Spalte daneben.
        #
        # Beide fuellen die Hoehe, statt untereinander zu rollen: Wer
        # die Statistik oeffnet, will das Bild sehen, nicht erst
        # dorthin scrollen.
        self.inhalt = BoxLayout(
            orientation="horizontal",
            spacing=dp(theme.SCREEN_SPACING),
        )

        chart.size_hint = (self.BILD_ANTEIL, 1)
        sales.size_hint = (1 - self.BILD_ANTEIL, 1)

        self.inhalt.add_widget(chart)
        self.inhalt.add_widget(sales)

        root.add_widget(self.inhalt)

        self.add_widget(root)

    def _build_sales_panel(self):
        panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
            size_hint=(1, 0.42) if self.hochformat else (0.36, 1),
        )

        title = KiGLabel(text="Einzelverkäufe")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.section_color('sage'))
        title.size_hint_y = None
        title.height = dp(38)
        panel.add_widget(title)

        # Die Felder stehen untereinander, jedes ueber die ganze
        # Breite der Filterkarte. Nebeneinander gezogen blieben fuer
        # Ereignis, Von, Bis und "Aktualisieren" je rund ein Viertel
        # Bildschirm - vier flache Kaesten in einer Reihe.
        filters = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.ROW_SPACING),
        )

        def zeile(beschriftung, feld):
            """Ein Feld mit seiner Ueberschrift darueber."""

            kasten = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(24) + dp(theme.FELD_HOEHE),
                spacing=dp(2),
            )

            titel = KiGLabel(text=beschriftung)
            titel.set_font_size(13)
            titel.set_alignment("left")
            titel.set_color(theme.TEXT_SECONDARY)
            titel.size_hint_y = None
            titel.height = dp(24)
            kasten.add_widget(titel)

            feld.size_hint_y = None
            feld.height = dp(theme.FELD_HOEHE)
            kasten.add_widget(feld)

            return kasten

        # Ein blanker Kivy-Spinner stand hier als dunkler Kasten mit
        # weisser Schrift zwischen lauter hellen Feldern.
        self.event_filter = RoundedSpinner(
            text="Alle Events", values=("Alle Events",),
        )
        self.event_filter.bind(text=lambda *_args: self._filter_geaendert())

        filters.add_widget(zeile("Veranstaltung", self.event_filter))

        # Nur die Artikel einer Kategorie - Balken, Kreis, Kennzahlen,
        # Tabelle und Ausgabe folgen alle demselben Filter.
        self.category_filter = RoundedSpinner(
            text=self.ALLE_KATEGORIEN, values=(self.ALLE_KATEGORIEN,),
        )
        self.category_filter.bind(text=lambda *_args: self._filter_geaendert())

        filters.add_widget(zeile("Kategorie", self.category_filter))

        self.date_from_value = None
        self.date_to_value = None

        filters.add_widget(zeile("Von", self._build_date_filter(
            "Von", lambda: self.open_date_picker("from"),
            lambda: self.clear_date_filter("from"),
        )))
        filters.add_widget(zeile("Bis", self._build_date_filter(
            "Bis", lambda: self.open_date_picker("to"),
            lambda: self.clear_date_filter("to"),
        )))

        aktualisieren = self._button("Übernehmen", self._filter_bestaetigen)
        self.filter_confirm_button = aktualisieren
        aktualisieren.size_hint_y = None
        aktualisieren.height = dp(theme.FELD_HOEHE)

        filters.add_widget(aktualisieren)

        # Ereignis und Zeitraum sind der Filter dieses Bildschirms -
        # sie stehen jetzt unten in der Leiste. Die Karte darueber
        # gehoert damit ganz der Tabelle.
        self.filterleiste = Filterleiste(
            inhalt=filters,
            titel="Auswahl",
            zusammenfassung=self._filter_text,
            inhalt_hoehe=(
                4 * (24 + theme.FELD_HOEHE)
                + theme.FELD_HOEHE
                + 4 * theme.ROW_SPACING
                + 2 * theme.CARD_PADDING
            ),
        )

        actions_top = BoxLayout(
            size_hint_y=None, height=dp(40),
            spacing=dp(theme.ROW_SPACING),
        )

        actions_top.add_widget(self._button("Excel", self.export_excel, width=dp(100)))
        actions_top.add_widget(self._button("PDF", self.export_pdf, width=dp(90)))
        actions_top.add_widget(self._button("Teilen", self.teilen_clicked, width=dp(100)))

        self.design_actions = actions_top

        # Eigene Zeile unter den Knoepfen: Der Hinweis nennt den Ordner
        # mit, und ein vollstaendiger Pfad braucht die ganze Breite
        # (siehe widgets/common/exporthinweis.py).
        self.export_status = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="13sp",
            halign="left", valign="middle",
        )

        hinweisfeld_vorbereiten(self.export_status, 0)

        panel.add_widget(self.export_status)

        panel.add_widget(self._build_repair_hint())

        # Bewusst OHNE Abstand zwischen den Spalten: die Kopfzeile muss
        # exakt dieselbe Spaltenaufteilung haben wie SaleRow (dort
        # ebenfalls kein spacing), sonst stehen Überschrift und Wert
        # nicht mehr übereinander. Beide Stellen also nur gemeinsam ändern.
        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=0)
        for title_text, width in zip(*self.spalten()):
            label = Label(
                text=title_text, bold=True, color=theme.TEXT_PRIMARY,
                font_size="13sp", halign="left", valign="middle",
                text_size=(None, dp(34)), size_hint_x=width,
            )
            header.add_widget(label)
        panel.add_widget(header)

        # RecycleView statt einer Zeile je Einheit - siehe SaleRow.
        self.sales_view = RecycleView(do_scroll_x=False, bar_width=dp(8))
        self.sales_view.bildschirm = self

        self.sales_rows = RecycleBoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            default_size=(None, dp(self.zeilenhoehe())),
            default_size_hint=(1, None),
            size_hint_y=None,
        )
        self.sales_rows.bind(minimum_height=self.sales_rows.setter("height"))

        self.sales_view.add_widget(self.sales_rows)

        # Erst NACH add_widget: Die RecycleView reicht die Zeilenart an
        # ihr Layout weiter - vorher hat sie keins, und die Tabelle
        # blieb ohne jede Zeile.
        self.sales_view.viewclass = SaleRow

        # Hinweis bei leerer Auswahl - eine RecycleView kann nur Zeilen
        # ihrer eigenen Art zeigen, der Hinweis liegt deshalb darüber.
        self.leer_label = self._empty_label("Keine Verkäufe im gewählten Zeitraum.")

        tabelle = FloatLayout()
        self.sales_view.pos_hint = {"x": 0, "y": 0}
        self.sales_view.size_hint = (1, 1)
        self.leer_label.pos_hint = {"x": 0, "top": 1}
        self.leer_label.size_hint = (1, None)
        tabelle.add_widget(self.sales_view)
        tabelle.add_widget(self.leer_label)

        panel.add_widget(tabelle)

        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.ROW_SPACING))
        actions.add_widget(loeschknopf(
            self.delete_selected, text="Ausgewählte",
            font_size="15sp", bold=True,
        ))
        actions.add_widget(loeschknopf(
            self.delete_period, text="Zeitraum",
            font_size="15sp", bold=True,
        ))
        panel.add_widget(actions)
        manual_button = self._button('Manuelle Buchungen', self.open_manual_entries, width=dp(200))
        manual_button.size_hint_y = None
        manual_button.height = dp(44)
        actions_top.add_widget(manual_button)
        return panel

    def open_manual_entries(self):
        from widgets.statistics.manual_entries import ManualEntriesPopup
        if self._auswahl()[3] is not None:
            self.category_filter.text = self.ALLE_KATEGORIEN
        ManualEntriesPopup(self.db, self._auswahl(), self.refresh).open()

    @staticmethod
    def spalten():
        """Ueberschriften und Breiten der Verkaufstabelle.

        In der schmalen rechten Spalte vier statt sieben: Sieben
        Ueberschriften ergaben dort einen einzigen Streifen, in dem
        "VerkaufEinkaufGewinn" uebereinanderlag. Event, Kategorie und
        Einkauf entfallen dann - wer sie braucht, sieht sie in der
        Ausgabe nach Excel.
        """

        if StatisticsScreen.kompakt():
            return (
                ("Datum", "Artikel", "Verkauf", "Gewinn"),
                (0.22, 0.40, 0.19, 0.19),
            )

        return (
            ("Event", "Datum", "Kategorie", "Artikel",
             "Verkauf", "Einkauf", "Gewinn"),
            (0.20, 0.12, 0.15, 0.20, 0.11, 0.11, 0.11),
        )

    @staticmethod
    def zeilenhoehe():
        """Höhe einer Verkaufszeile in dp."""

        return 34 if StatisticsScreen.kompakt() else 46

    @staticmethod
    def kompakt():
        """Ob die Verkaufstabelle in ihrer kurzen Fassung steht.

        Sie sitzt jetzt in der schmalen rechten Spalte - dort ist fuer
        sieben Spalten kein Platz. Im Hochformat steht sie dagegen
        ueber die ganze Breite und darf alles zeigen.
        """

        return not theme.is_portrait()

    # =====================================================
    # Fehlende Einkaufspreise nachtragen
    # =====================================================

    def _build_repair_hint(self):
        """Zeile, die auf Rezeptverkäufe ohne Einkaufspreis hinweist.

        Solche Positionen entstehen, wenn beim Verkauf die Kosten der
        Zutaten nicht bestimmbar waren (z. B. Flasche ohne
        Wareneingang): Gebucht wurde dann 0,00, der Gewinn steht damit
        zu hoch. Die Zeile bleibt unsichtbar, solange alles stimmt.
        """

        self.repair_row = BoxLayout(
            size_hint_y=None, height=0, opacity=0,
            spacing=dp(theme.ROW_SPACING),
        )

        self.repair_label = Label(
            text="", color=theme.ERROR, font_size="13sp",
            halign="left", valign="middle",
        )
        self.repair_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        self.repair_row.add_widget(self.repair_label)
        self.repair_row.add_widget(
            self._button("Einkaufspreise nachtragen", self.repair_costs, width=dp(220))
        )

        return self.repair_row

    def _refresh_repair_hint(self, date_from, date_to, event_id, category_id=None):

        offen = self.db.count_missing_recipe_costs(
            date_from, date_to, event_id, category_id
        )

        if not offen:
            self.repair_row.height = 0
            self.repair_row.opacity = 0
            self.repair_row.disabled = True
            return

        self.repair_label.text = (
            f"{offen} {'Verkauf' if offen == 1 else 'Verkäufe'} von "
            "Rezeptartikeln ohne Einkaufspreis - der Gewinn steht zu hoch."
        )

        self.repair_row.height = dp(40)
        self.repair_row.opacity = 1
        self.repair_row.disabled = False

    def repair_costs(self):

        auswahl = self._auswahl()

        offen = self.db.count_missing_recipe_costs(*auswahl)

        if not offen:
            return

        self._confirm(
            f"Bei {offen} Verkaufsposition(en) den heute gültigen "
            "Rezeptpreis als Einkaufspreis nachtragen?",
            lambda: self._repair_costs_confirmed(*auswahl),
            confirm_text="Nachtragen",
        )

    def _repair_costs_confirmed(self, date_from, date_to, event_id, category_id=None):

        nachgetragen = self.db.repair_recipe_costs(
            date_from, date_to, event_id, category_id
        )

        self.refresh()

        self.export_status.text = (
            f"{nachgetragen} Einkaufspreis(e) nachgetragen."
            if nachgetragen else
            "Kein Preis nachtragbar - bitte zuerst den Wareneingang "
            "der Zutaten mit Preis buchen."
        )

    def _build_auswertung_panel(self):
        """Die grosse linke Karte: das Bild der Verkäufe.

        Oben die summierten Verkäufe als Balken, absteigend nach
        Umsatz, daneben derselbe Zeitraum als Kreis je Kategorie.
        Darunter die Kennzahlen.

        Alles bezieht sich auf den unten eingestellten Zeitraum und
        das gewählte Event; ohne Filter auf sämtliche Verkäufe.
        """

        panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
            size_hint=(1, 0.58) if self.hochformat else (0.64, 1),
        )

        panel.add_widget(self._title("Auswertung"))

        self.auswertung = Verkaufsauswertung()

        panel.add_widget(self.auswertung)

        self.design_metrics = self._kennzahlen_block()

        # Was davon mit KiG Karte oder Gutschein beglichen wurde. Der
        # Umsatz darüber enthält diese Beträge: Verkauft wurde die Ware
        # ja - sie ging nur nicht bar in die Kasse.
        self.entwertet_label = Label(
            text="", color=theme.TEXT_PRIMARY, font_size="13sp",
            markup=True,
            size_hint_y=None, height=dp(22),
            halign="left", valign="middle",
        )
        self.entwertet_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        panel.add_widget(self.entwertet_label)

        self.period_label = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="13sp",
            size_hint_y=None, height=dp(22),
            halign="left", valign="middle",
        )
        self.period_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        panel.add_widget(self.period_label)

        return panel

    def _kennzahlen_block(self):
        """Einnahmen, Ausgaben und Gewinn - eine Leiste aus drei
        Abschnitten.

        Hier standen drei einzelne Karten mit Luecken dazwischen. Drei
        Zahlen, die sich zueinander verhalten (Einnahmen minus
        Ausgaben ergibt den Gewinn), gehoeren aber zusammen: Die
        Leiste ist EINE Karte, in die zwei Striche die drei gleich
        breiten Abschnitte teilen.
        """

        hoehe = dp(92)

        leiste = RoundedPanel(
            orientation="horizontal",
            size_hint_y=None,
            height=hoehe,
            padding=(0, dp(4)),
            spacing=0,
        )

        self.total_labels = {}

        for schluessel, beschriftung, farbe in (
            ("revenue", "Einnahmen", theme.TEXT_PRIMARY),
            ("expenses", "Ausgaben", theme.TEXT_PRIMARY),
            ("profit", "Gewinn", theme.PRIMARY_ORANGE),
        ):

            # Zwischen den Abschnitten ein Strich, aussen keiner - der
            # Rand der Karte ist dort schon.
            if leiste.children:
                leiste.add_widget(KiGDividerVertical(
                    color=theme.CARD_BORDER, padding=dp(14),
                ))

            abschnitt = BoxLayout(
                orientation="vertical",
                padding=(dp(18), dp(10)),
                spacing=dp(4),
            )

            titel = Label(
                text=beschriftung, color=theme.TEXT_SECONDARY,
                font_size="13sp", halign="left", valign="middle",
                size_hint_y=None, height=dp(24),
            )
            titel.bind(size=lambda obj, value: setattr(obj, 'text_size', value))
            abschnitt.add_widget(titel)

            wert = Label(
                text=self.money(0), color=farbe,
                font_size="22sp",
                bold=True, halign="left", valign="middle",
                size_hint_y=None, height=dp(40),
            )
            wert.bind(size=lambda obj, value: setattr(obj, 'text_size', value))

            self.total_labels[schluessel] = wert

            abschnitt.add_widget(wert)

            leiste.add_widget(abschnitt)

        return leiste

    @staticmethod
    def _button(text, callback, width=None):
        button = Button(
            text=text, background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="15sp", bold=True, size_hint_x=None if width else 1,
        )
        if width:
            button.width = width
        button.bind(on_release=lambda *_args: callback())
        return button

    @staticmethod
    def _title(text):
        label = KiGLabel(text=text)
        label.set_font_size(22)
        label.set_bold(True)
        label.set_alignment("left")
        label.set_color(theme.section_color('sage'))
        label.size_hint_y = None
        label.height = dp(34)
        return label


    def teilen_clicked(self):
        """Gibt die zuletzt ausgegebene Datei weiter (siehe teilen.py)."""

        erfolg, meldung = teilen.teilen(self.letzte_ausgabe)

        self.export_status.text = meldung

    @staticmethod
    def money(value):
        return geldformat.geld(value)

    @staticmethod
    def format_date(iso_date):
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            return str(iso_date or "-")

    def on_pre_enter(self, *_args):

        self._filter_wird_gefuellt = True

        try:
            self._populate_event_filter()
            self._populate_category_filter()
        finally:
            self._filter_wird_gefuellt = False

        self.refresh()

    def _populate_category_filter(self):
        """Bietet die Kategorien der Artikelverwaltung als Filter an."""

        current_selection = self.category_filter.text
        self.category_options = {self.ALLE_KATEGORIEN: None}

        for kategorie in self.db.get_categories():
            self.category_options[kategorie["name"]] = kategorie["id"]

        self.category_filter.values = tuple(self.category_options)
        self.category_filter.text = (
            current_selection if current_selection in self.category_options
            else self.ALLE_KATEGORIEN
        )

    def _populate_event_filter(self):
        """Bietet alle im Kalender gepflegten Events als optionalen Filter an."""

        current_selection = self.event_filter.text
        self.event_options = {"Alle Events": None}

        for event in self.db.get_events():
            if event["entry_type"] != "EVENT":
                continue
            label = f"{event['name']} ({self.format_date(event['start_date'])})"
            self.event_options[label] = event["id"]

        self.event_filter.values = tuple(self.event_options)
        self.event_filter.text = (
            current_selection if current_selection in self.event_options
            else "Alle Events"
        )

    def _period(self):
        return self.date_from_value, self.date_to_value

    def _auswahl(self):
        """Zeitraum, Event und Kategorie - so, wie die Datenbank sie
        erwartet: (date_from, date_to, event_id, category_id)."""

        date_from, date_to = self._period()

        return (
            date_from,
            date_to,
            self.event_options.get(self.event_filter.text),
            self.category_options.get(self.category_filter.text),
        )

    def _filter_geaendert(self):

        self.refresh()

        if getattr(self, "filterleiste", None) is not None:
            self.filterleiste.aktualisieren()

    def _filter_bestaetigen(self):
        self.refresh()
        self.filterleiste.zuklappen()

    def _filter_text(self):
        """Was in der zugeklappten Filterleiste steht."""

        teile = [self.event_filter.text]

        if self.category_filter.text != self.ALLE_KATEGORIEN:
            teile.append(self.category_filter.text)

        von = self.date_from_value
        bis = self.date_to_value

        if von and bis:
            teile.append(f"{self.format_date(von)} - {self.format_date(bis)}")
        elif von:
            teile.append(f"ab {self.format_date(von)}")
        elif bis:
            teile.append(f"bis {self.format_date(bis)}")
        else:
            teile.append("ganzer Zeitraum")

        return "   ·   ".join(teile)

    # =====================================================
    # Zeitraum-Auswahl (Kalender-Dropdown)
    # =====================================================

    def _build_date_filter(self, label_prefix, on_pick, on_clear):
        """Ein Datumsfeld als Button (öffnet den Kalender) + Löschen-Knopf,
        anstatt das Datum von Hand eintippen zu müssen."""

        box = BoxLayout(spacing=dp(theme.LABEL_SPACING))

        # Datumsfeld, kein Aktionsknopf - es sieht deshalb aus wie
        # ein Feld (siehe widgets/common/feld.py).
        button = Feldknopf(
            text=f"{label_prefix}: alle",
            on_tipp=on_pick,
        )

        box.add_widget(button)

        clear_button = KiGSymbolButton(
            symbol=KREUZ, symbol_color=theme.TEXT_SECONDARY,
            size_hint_x=None, width=dp(36),
            background_color=theme.SURFACE,
        )
        clear_button.bind(on_release=lambda *_args: on_clear())
        box.add_widget(clear_button)

        if label_prefix == "Von":
            self.date_from_button = button
        else:
            self.date_to_button = button

        return box

    def open_date_picker(self, which):

        current = self.date_from_value if which == "from" else self.date_to_value

        DatePickerPopup(
            title="Von: Startdatum" if which == "from" else "Bis: Enddatum",
            initial_date=current,
            on_select=lambda iso_date: self.date_picked(which, iso_date),
        ).open()

    def date_picked(self, which, iso_date):

        label_prefix = "Von" if which == "from" else "Bis"
        button = self.date_from_button if which == "from" else self.date_to_button

        if which == "from":
            self.date_from_value = iso_date
        else:
            self.date_to_value = iso_date

        button.text = f"{label_prefix}: {self.format_date(iso_date)}"
        self.refresh()

        self.filterleiste.aktualisieren()

    def clear_date_filter(self, which):

        label_prefix = "Von" if which == "from" else "Bis"
        button = self.date_from_button if which == "from" else self.date_to_button

        if which == "from":
            self.date_from_value = None
        else:
            self.date_to_value = None

        button.text = f"{label_prefix}: alle"
        self.refresh()

        self.filterleiste.aktualisieren()

    def refresh(self):

        # Während die Auswahlfelder beim Öffnen gefüllt werden, meldet
        # jedes seine Änderung - die Statistik lud dabei dreimal
        # hintereinander (siehe on_pre_enter).
        if getattr(self, "_filter_wird_gefuellt", False):
            return

        auswahl = self._auswahl()
        self.selected_rows.clear()

        # Einmal laden - Tabelle, Kennzahlen, Balken und Kreis rechnen
        # alle aus denselben Zeilen. Früher holte jede ihre eigenen.
        rows = self.db.get_statistic_sale_items(*auswahl)

        self.sales_view.data = [{"sale": row, "selected": False} for row in rows]
        self.sales_view.scroll_y = 1

        self.leer_label.opacity = 0 if rows else 1

        self._refresh_totals(*auswahl, zeilen=rows)
        self._refresh_auswertung(*auswahl, zeilen=rows)
        self._refresh_repair_hint(*auswahl)

    def _row_selected(self, row, selected):
        row_key = row.sale["row_key"]
        if selected:
            self.selected_rows[row_key] = row.sale["sale_item_id"]
        else:
            self.selected_rows.pop(row_key, None)

    def _refresh_totals(self, date_from, date_to, event_id, category_id=None,
                        zeilen=None):
        """Kennzahlen und Kreisdiagramm - beide für denselben Zeitraum
        wie die Tabelle links."""

        kennzahlen = self.db.get_period_totals(
            date_from, date_to, event_id, category_id, zeilen=zeilen
        )

        for schluessel, label in self.total_labels.items():
            label.text = self.money(kennzahlen[schluessel])

        self.period_label.text = self._period_text(kennzahlen)
        if kennzahlen.get('manual_income') or kennzahlen.get('manual_expenses'):
            self.period_label.text += (' | manuell: +' + self.money(kennzahlen['manual_income'])
                                       + ' / -' + self.money(kennzahlen['manual_expenses']))

        self.entwertet_label.text = self._entwertet_text(kennzahlen)

        # Das Bild oben zeigt denselben Zeitraum - es wird gleich
        # danach mit denselben Grenzen gefuellt
        # (siehe _refresh_auswertung).

    def _entwertet_text(self, kennzahlen):
        """"Entwertet: KiG Karte 12,00 € | Gutschein 5,00 € | bar
        83,00 €" - leer, solange nichts entwertet wurde."""

        karte = kennzahlen.get("kig_karte") or 0
        gutschein = kennzahlen.get("gutschein") or 0

        if not karte and not gutschein:
            return ""

        return (
            f"[b]Entwertet:[/b] KiG Karte {self.money(karte)} | "
            f"Gutschein {self.money(gutschein)} | "
            f"bar {self.money(kennzahlen['bar'])}"
        )

    def _period_text(self, kennzahlen):
        """Eine Zeile, die sagt, worauf sich die Zahlen beziehen.

        Ohne sie ließe sich am Diagramm nicht ablesen, ob gerade ein
        Zeitraum eingegrenzt ist oder alles gezeigt wird.
        """

        date_from, date_to = self._period()

        if date_from and date_to:
            zeitraum = f"{self.format_date(date_from)} - {self.format_date(date_to)}"
        elif date_from:
            zeitraum = f"ab {self.format_date(date_from)}"
        elif date_to:
            zeitraum = f"bis {self.format_date(date_to)}"
        else:
            zeitraum = "gesamter Zeitraum"

        if self.event_filter.text != "Alle Events":
            zeitraum = f"{self.event_filter.text} | {zeitraum}"

        if self.category_filter.text != self.ALLE_KATEGORIEN:
            zeitraum = f"{self.category_filter.text} | {zeitraum}"

        bons = kennzahlen["receipts"]

        return (
            f"{zeitraum} | {kennzahlen['quantity']} Einheiten auf "
            f"{bons} {'Bon' if bons == 1 else 'Bons'}"
        )

    def _refresh_auswertung(self, date_from, date_to, event_id, category_id=None,
                            zeilen=None):
        """Fuellt Balken und Kreis - beide aus demselben Zeitraum."""

        self.auswertung.set_data(
            self.db.get_article_sales(
                date_from, date_to, event_id, category_id, zeilen=zeilen
            ),
            self.db.get_category_revenues(
                date_from, date_to, event_id, category_id, zeilen=zeilen
            ),
        )

    @staticmethod
    def _empty_label(text):
        return Label(
            text=text, color=theme.TEXT_SECONDARY, font_size="14sp", size_hint_y=None,
            height=dp(42), halign="left", valign="middle", text_size=(None, dp(42)),
        )

    # =====================================================
    # Ausgabe: Excel und PDF
    # =====================================================

    def _beschreibung(self):
        """Wofür die Zahlen gelten - in Worten, für den Kopf der
        Ausgabe."""

        date_from, date_to = self._period()

        if date_from and date_to:
            zeitraum = f"{self.format_date(date_from)} - {self.format_date(date_to)}"
        elif date_from:
            zeitraum = f"ab {self.format_date(date_from)}"
        elif date_to:
            zeitraum = f"bis {self.format_date(date_to)}"
        else:
            zeitraum = "gesamter Zeitraum"

        teile = []

        if self.event_filter.text != "Alle Events":
            teile.append(self.event_filter.text)

        if self.category_filter.text != self.ALLE_KATEGORIEN:
            teile.append(f"Kategorie {self.category_filter.text}")

        teile.append(zeitraum)

        return " | ".join(teile)

    def export_excel(self):
        """Die Statistik der aktuellen Auswahl als Excel-Mappe:
        Zusammenfassung mit Diagrammen und die Einzelverkäufe (siehe
        berichte/statistik_bericht.py)."""

        self._ausgeben("excel")

    def export_pdf(self):
        """Dieselbe Auswahl als PDF-Bericht - Kennzahlen, Kreis, Balken
        und die Tabelle je Artikel."""

        self._ausgeben("pdf")

    def _ausgeben(self, art):

        from berichte import statistik_bericht

        auswahl = self._auswahl()

        daten = statistik_bericht.sammeln(self.db, auswahl, self._beschreibung())

        if not daten["einzeln"] and not daten.get('manual'):
            self.export_status.text = "Keine Verkäufe in der gewählten Auswahl zum Exportieren."
            return

        stempel = datetime.now().strftime("%Y-%m-%d_%H-%M")

        try:
            if art == "pdf":
                pfad = storage.export_dir("pdf") / f"statistik_{stempel}.pdf"
                statistik_bericht.pdf(daten, pfad)
            else:
                pfad = storage.export_dir("excel") / f"statistik_{stempel}.xlsx"
                statistik_bericht.excel(daten, pfad)

        except OSError as fehler:
            # Meist ist die Datei gerade in Excel geöffnet.
            self.export_status.text = f"Ausgabe fehlgeschlagen: {fehler}"
            return

        self.letzte_ausgabe = pfad

        self.export_status.text = export_hinweis(pfad)

    def delete_selected(self):
        if not self.selected_rows:
            return
        self._confirm(
            f"{len(self.selected_rows)} ausgewählte Verkaufsposition(en) löschen?",
            lambda: self._delete_selected_confirmed(),
        )

    def _delete_selected_confirmed(self):
        units_per_sale_item = {}
        for sale_item_id in self.selected_rows.values():
            units_per_sale_item[sale_item_id] = (
                units_per_sale_item.get(sale_item_id, 0) + 1
            )
        for sale_item_id, quantity in units_per_sale_item.items():
            self.db.delete_sale_units(sale_item_id, quantity)
        self.refresh()
        self._notify_revenue_changed()

    def delete_period(self):
        date_from, date_to = self._period()
        if not date_from or not date_to or date_from > date_to:
            self._confirm("Bitte zuerst einen gültigen Zeitraum eingeben.", None)
            return
        # Gelöscht wird der ganze Zeitraum - Event und Kategorie
        # grenzen hier nichts ein. Das muss in der Frage stehen.
        self._confirm(
            "Alle Verkäufe im gewählten Zeitraum löschen?\n"
            "(unabhängig von Event und Kategorie)",
            lambda: self._delete_period_confirmed(date_from, date_to),
        )

    def _delete_period_confirmed(self, date_from, date_to):
        self.db.delete_sales_in_period(date_from, date_to)
        self.refresh()
        self._notify_revenue_changed()

    def _notify_revenue_changed(self):
        """Meldet Änderungen an den Verkaufsdaten, damit der Header-Tagesumsatz

        (der nur die heutigen Verkäufe zeigt) unmittelbar aktualisiert wird,
        falls gelöschte Positionen den heutigen Geschäftstag betreffen.
        """
        if callable(self.revenue_changed_callback):
            self.revenue_changed_callback()

    def _confirm(self, message, callback, confirm_text="Löschen"):
        content = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )
        content.add_widget(Label(text=message, color=theme.TEXT_PRIMARY, font_size="16sp"))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.ROW_SPACING))
        popup = KiGPopup(title="Verkaufsdaten", content=content, size_hint=(0.45, None), height=dp(190), auto_dismiss=False)
        cancel = self._button("Abbrechen", popup.dismiss)
        buttons.add_widget(cancel)
        if callback:
            confirm = self._button(confirm_text, lambda: (popup.dismiss(), callback()))
            buttons.add_widget(confirm)
        content.add_widget(buttons)
        popup.open()
