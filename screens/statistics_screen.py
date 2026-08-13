"""Auswertung der über die Kasse abgeschlossenen Verkäufe."""

from datetime import datetime

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

import config
import storage
import theme
from database import DatabaseManager
from widgets.common.date_picker_popup import DatePickerPopup
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


class SaleRow(ButtonBehavior, BoxLayout):
    """Eine auswählbare Zeile der Verkaufstabelle."""

    def __init__(self, sale, selected_callback, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(46), **kwargs)
        self.sale = sale
        self.selected_callback = selected_callback
        self.selected = False

        # Stornos stehen mit negativer Menge in denselben Tabellen. Die
        # Menge selbst wird in dieser Tabelle nicht angezeigt - ohne
        # eigene Kennzeichnung wäre eine Stornozeile also nicht von
        # einem Verkauf zu unterscheiden.
        self.ist_storno = (sale["quantity"] or 0) < 0

        # Grundfarbe der Zeile merken: Beim Abwählen muss die
        # Storno-Einfärbung zurückkommen und nicht das normale Weiß.
        self.grundfarbe = theme.STORNO_ROW if self.ist_storno else theme.CARD

        with self.canvas.before:
            self._color = Color(*self.grundfarbe)
            self._background = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        self.bind(pos=self._refresh_canvas, size=self._refresh_canvas)

        artikel = sale["article_name"]
        if self.ist_storno:
            artikel = f"Storno: {artikel}"

        values = (
            sale["event_name"],
            StatisticsScreen.format_date(sale["business_date"]),
            sale["category_name"],
            artikel,
            StatisticsScreen.money(sale["unit_price"]),
            StatisticsScreen.money(sale["purchase_price"]),
            StatisticsScreen.money(sale["profit"]),
        )
        widths = (0.20, 0.12, 0.15, 0.20, 0.11, 0.11, 0.11)

        for spalte, (value, width) in enumerate(zip(values, widths)):
            # Nur der Gewinn wird rot - der Betrag selbst bleibt lesbar,
            # das Vorzeichen macht die Richtung deutlich.
            farbe = (
                theme.ERROR
                if self.ist_storno and spalte == len(values) - 1
                else theme.TEXT_PRIMARY
            )
            label = Label(
                text=str(value), color=farbe, font_size="13sp",
                halign="left", valign="middle", text_size=(None, dp(46)),
                size_hint_x=width,
            )
            self.add_widget(label)

    def _refresh_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    def on_release(self):
        self.selected = not self.selected
        self._color.rgba = (
            theme.PRIMARY_ORANGE_LIGHT if self.selected else self.grundfarbe
        )
        self.selected_callback(self, self.selected)


class BarGraphic(Widget):
    """Schlichtes horizontales Balkendiagramm ohne externe Bibliothek."""

    def __init__(self, ratio=0, **kwargs):
        super().__init__(**kwargs)
        self.ratio = ratio
        with self.canvas:
            Color(*theme.PRIMARY_ORANGE)
            self._bar = RoundedRectangle(radius=[dp(5)])
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_args):
        self._bar.pos = self.pos
        self._bar.size = (max(0, self.width * self.ratio), self.height)


class StatisticsScreen(Screen):
    """Tabellarische Umsatz- und Gewinnübersicht je Verkaufsposition."""

    def __init__(self, revenue_changed_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.revenue_changed_callback = revenue_changed_callback
        self.selected_rows = {}
        self.event_options = {"Alle Events": None}

        # Im Hochformat steht die Auswertung unter der Verkaufstabelle
        # statt daneben (siehe theme.set_orientation).
        self.hochformat = theme.is_portrait()

        root = BoxLayout(
            orientation="vertical" if self.hochformat else "horizontal",
            padding=dp(theme.SCREEN_PADDING),
            spacing=dp(theme.SCREEN_SPACING),
        )
        root.add_widget(self._build_sales_panel())
        root.add_widget(self._build_summary_panel())
        self.add_widget(root)

    def _build_sales_panel(self):
        panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
            size_hint=(1, 0.62) if self.hochformat else (0.64, 1),
        )

        title = KiGLabel(text="Verkäufe")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(38)
        panel.add_widget(title)

        filters = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.ROW_SPACING))
        self.event_filter = Spinner(
            text="Alle Events", values=("Alle Events",),
            font_size="15sp", size_hint_x=1.15,
        )
        self.event_filter.bind(text=lambda *_args: self.refresh())
        filters.add_widget(self.event_filter)

        self.date_from_value = None
        self.date_to_value = None

        filters.add_widget(self._build_date_filter(
            "Von", lambda: self.open_date_picker("from"), lambda: self.clear_date_filter("from"),
        ))
        filters.add_widget(self._build_date_filter(
            "Bis", lambda: self.open_date_picker("to"), lambda: self.clear_date_filter("to"),
        ))

        filters.add_widget(self._button("Aktualisieren", self.refresh, width=dp(130)))
        panel.add_widget(filters)

        actions_top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(theme.ROW_SPACING))
        self.export_status = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="13sp",
            halign="left", valign="middle",
        )
        self.export_status.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        actions_top.add_widget(self.export_status)
        actions_top.add_widget(self._button("Excel exportieren", self.export_excel, width=dp(170)))
        panel.add_widget(actions_top)

        # Bewusst OHNE Abstand zwischen den Spalten: die Kopfzeile muss
        # exakt dieselbe Spaltenaufteilung haben wie SaleRow (dort
        # ebenfalls kein spacing), sonst stehen Überschrift und Wert
        # nicht mehr übereinander. Beide Stellen also nur gemeinsam ändern.
        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=0)
        for title_text, width in zip(
            ("Event", "Datum", "Kategorie", "Artikel", "Verkauf", "Einkauf", "Gewinn"),
            (0.20, 0.12, 0.15, 0.20, 0.11, 0.11, 0.11),
        ):
            label = Label(
                text=title_text, bold=True, color=theme.TEXT_PRIMARY,
                font_size="13sp", halign="left", valign="middle",
                text_size=(None, dp(34)), size_hint_x=width,
            )
            header.add_widget(label)
        panel.add_widget(header)

        self.sales_rows = BoxLayout(orientation="vertical", spacing=dp(theme.SPACE_XS), size_hint_y=None)
        self.sales_rows.bind(minimum_height=self.sales_rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self.sales_rows)
        panel.add_widget(scroll)

        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.ROW_SPACING))
        actions.add_widget(self._button("Ausgewählte löschen", self.delete_selected))
        actions.add_widget(self._button("Zeitraum löschen", self.delete_period))
        panel.add_widget(actions)
        return panel

    def _build_summary_panel(self):
        # Hochformat: Die beiden Auswertungskarten stehen unter der
        # Tabelle nebeneinander - untereinander bliebe von beiden nur
        # noch ein Streifen übrig.
        panel = BoxLayout(
            orientation="horizontal" if self.hochformat else "vertical",
            spacing=dp(theme.SCREEN_SPACING),
            size_hint=(1, 0.38) if self.hochformat else (0.36, 1),
        )

        chart_panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
            size_hint=(0.5, 1) if self.hochformat else (1, 0.43),
        )
        chart_panel.add_widget(self._title("Top 5 Positionen"))

        # Fünf Zeilen zu 34 dp plus Abstand brauchen mehr Platz, als die
        # Karte je nach Fenstergröße hergibt - ohne ScrollView zeichneten
        # die untersten Zeilen bisher über den Kartenrand hinaus
        # (dieselbe Lösung wie bei der Tabelle darunter).
        self.top_rows = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            size_hint_y=None,
        )
        self.top_rows.bind(minimum_height=self.top_rows.setter("height"))

        top_scroll = ScrollView(do_scroll_x=False)
        top_scroll.add_widget(self.top_rows)
        chart_panel.add_widget(top_scroll)
        panel.add_widget(chart_panel)

        revenue_panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
            size_hint=(0.5, 1) if self.hochformat else (1, 0.57),
        )
        revenue_panel.add_widget(self._title("Gesamtverkaufszahlen"))
        table_header = BoxLayout(size_hint_y=None, height=dp(30))
        for text, width in (("Artikel", 0.62), ("Einnahmen", 0.38)):
            table_header.add_widget(Label(
                text=text, bold=True, color=theme.TEXT_PRIMARY, font_size="14sp",
                halign="left", valign="middle", text_size=(None, dp(30)), size_hint_x=width,
            ))
        revenue_panel.add_widget(table_header)
        self.revenue_rows = BoxLayout(orientation="vertical", spacing=dp(theme.SPACE_XS), size_hint_y=None)
        self.revenue_rows.bind(minimum_height=self.revenue_rows.setter("height"))
        revenue_scroll = ScrollView(do_scroll_x=False)
        revenue_scroll.add_widget(self.revenue_rows)
        revenue_panel.add_widget(revenue_scroll)
        panel.add_widget(revenue_panel)
        return panel

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
        label.set_color(theme.PRIMARY_ORANGE)
        label.size_hint_y = None
        label.height = dp(34)
        return label

    @staticmethod
    def money(value):
        return f"{float(value or 0):.2f} €".replace(".", ",")

    @staticmethod
    def format_date(iso_date):
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        except (TypeError, ValueError):
            return str(iso_date or "-")

    def on_pre_enter(self, *_args):
        self._populate_event_filter()
        self.refresh()

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

    # =====================================================
    # Zeitraum-Auswahl (Kalender-Dropdown)
    # =====================================================

    def _build_date_filter(self, label_prefix, on_pick, on_clear):
        """Ein Datumsfeld als Button (öffnet den Kalender) + Löschen-Knopf,
        anstatt das Datum von Hand eintippen zu müssen."""

        box = BoxLayout(spacing=dp(theme.LABEL_SPACING))

        button = self._button(f"{label_prefix}: alle", on_pick)
        box.add_widget(button)

        clear_button = Button(
            text="✕", size_hint_x=None, width=dp(36),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_SECONDARY,
            font_size="14sp", bold=True,
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

    def clear_date_filter(self, which):

        label_prefix = "Von" if which == "from" else "Bis"
        button = self.date_from_button if which == "from" else self.date_to_button

        if which == "from":
            self.date_from_value = None
        else:
            self.date_to_value = None

        button.text = f"{label_prefix}: alle"
        self.refresh()

    def refresh(self):
        date_from, date_to = self._period()
        event_id = self.event_options.get(self.event_filter.text)
        self.selected_rows.clear()
        self.sales_rows.clear_widgets()

        rows = self.db.get_statistic_sale_items(date_from, date_to, event_id)
        if not rows:
            self.sales_rows.add_widget(self._empty_label("Keine Verkäufe im gewählten Zeitraum."))
        else:
            for row in rows:
                self.sales_rows.add_widget(SaleRow(row, self._row_selected))

        self._refresh_top_three(date_from, date_to, event_id)
        self._refresh_revenue_table(date_from, date_to, event_id)

    def _row_selected(self, row, selected):
        row_key = row.sale["row_key"]
        if selected:
            self.selected_rows[row_key] = row.sale["sale_item_id"]
        else:
            self.selected_rows.pop(row_key, None)

    def _refresh_top_three(self, date_from, date_to, event_id):
        self.top_rows.clear_widgets()
        top_articles = self.db.get_top_selling_articles(date_from, date_to, event_id)
        if not top_articles:
            self.top_rows.add_widget(self._empty_label("Noch keine Verkaufsdaten."))
            return

        maximum = top_articles[0][1]
        for index, (name, quantity) in enumerate(top_articles, start=1):
            row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(theme.ROW_SPACING))
            row.add_widget(Label(
                text=f"{index}. {name}", color=theme.TEXT_PRIMARY, font_size="14sp",
                halign="left", valign="middle", text_size=(dp(105), dp(34)), size_hint_x=None, width=dp(105),
            ))
            row.add_widget(BarGraphic(ratio=quantity / maximum if maximum else 0))
            row.add_widget(Label(
                text=str(quantity), color=theme.TEXT_PRIMARY, font_size="14sp",
                size_hint_x=None, width=dp(30), halign="right", valign="middle", text_size=(dp(30), dp(34)),
            ))
            self.top_rows.add_widget(row)

    def _refresh_revenue_table(self, date_from, date_to, event_id):
        self.revenue_rows.clear_widgets()
        revenues = self.db.get_article_revenues(date_from, date_to, event_id)
        if not revenues:
            self.revenue_rows.add_widget(self._empty_label("Noch keine Einnahmen."))
            return

        for name, revenue in revenues:
            row = BoxLayout(size_hint_y=None, height=dp(34))
            row.add_widget(Label(
                text=name, color=theme.TEXT_PRIMARY, font_size="14sp", size_hint_x=0.62,
                halign="left", valign="middle", text_size=(None, dp(34)),
            ))
            row.add_widget(Label(
                text=self.money(revenue), color=theme.TEXT_PRIMARY, font_size="14sp", size_hint_x=0.38,
                halign="right", valign="middle", text_size=(None, dp(34)),
            ))
            self.revenue_rows.add_widget(row)

    @staticmethod
    def _empty_label(text):
        return Label(
            text=text, color=theme.TEXT_SECONDARY, font_size="14sp", size_hint_y=None,
            height=dp(42), halign="left", valign="middle", text_size=(None, dp(42)),
        )

    # =====================================================
    # Excel-Export
    # =====================================================

    def export_excel(self):
        """Exportiert die aktuell gefilterten Verkaufszahlen inklusive
        Diagrammen als Excel-Arbeitsmappe (zwei Blätter: Rohdaten und
        Auswertung mit Balkendiagrammen)."""

        from openpyxl import Workbook
        from openpyxl.chart import BarChart, Reference
        from openpyxl.styles import Font

        date_from, date_to = self._period()
        event_id = self.event_options.get(self.event_filter.text)

        sale_items = self.db.get_statistic_sale_items(date_from, date_to, event_id)
        top_articles = self.db.get_top_selling_articles(date_from, date_to, event_id, limit=5)
        revenues = self.db.get_article_revenues(date_from, date_to, event_id)

        if not sale_items:
            self.export_status.text = "Keine Verkäufe im gewählten Zeitraum zum Exportieren."
            return

        workbook = Workbook()
        bold = Font(bold=True)

        # -------------------------------------------------
        # Blatt 1: Verkäufe (Rohdaten)
        # -------------------------------------------------

        sales_sheet = workbook.active
        sales_sheet.title = "Verkäufe"

        headers = ("Event", "Datum", "Kategorie", "Artikel", "Menge", "Verkauf", "Einkauf", "Gewinn")
        sales_sheet.append(headers)
        for cell in sales_sheet[1]:
            cell.font = bold

        for row in sale_items:
            sales_sheet.append((
                row["event_name"], self.format_date(row["business_date"]), row["category_name"],
                row["article_name"], row["quantity"], row["unit_price"], row["purchase_price"],
                row["profit"],
            ))

        for column_cells in sales_sheet.columns:
            width = max(len(str(cell.value or "")) for cell in column_cells)
            sales_sheet.column_dimensions[column_cells[0].column_letter].width = max(10, width + 2)

        # -------------------------------------------------
        # Blatt 2: Auswertung (Top 5 + Gesamtverkaufszahlen)
        # -------------------------------------------------

        summary_sheet = workbook.create_sheet("Auswertung")

        summary_sheet.append(("Top 5 Positionen (Menge)",))
        summary_sheet["A1"].font = bold
        summary_sheet.append(("Artikel", "Menge"))
        for cell in summary_sheet[2]:
            cell.font = bold
        top_start_row = 3
        for name, quantity in top_articles:
            summary_sheet.append((name, quantity))
        top_end_row = top_start_row + len(top_articles) - 1

        if top_articles:
            top_chart = BarChart()
            top_chart.title = "Top 5 Positionen"
            top_chart.y_axis.title = "Menge"
            data = Reference(summary_sheet, min_col=2, min_row=2, max_row=top_end_row)
            categories = Reference(summary_sheet, min_col=1, min_row=top_start_row, max_row=top_end_row)
            top_chart.add_data(data, titles_from_data=True)
            top_chart.set_categories(categories)
            top_chart.width, top_chart.height = 16, 9
            summary_sheet.add_chart(top_chart, "D2")

        revenue_start_row = top_end_row + 3
        summary_sheet.cell(row=revenue_start_row, column=1, value="Gesamtverkaufszahlen (Einnahmen)").font = bold
        header_row = revenue_start_row + 1
        summary_sheet.cell(row=header_row, column=1, value="Artikel").font = bold
        summary_sheet.cell(row=header_row, column=2, value="Einnahmen").font = bold

        revenue_data_start = header_row + 1
        for offset, (name, revenue) in enumerate(revenues):
            summary_sheet.cell(row=revenue_data_start + offset, column=1, value=name)
            summary_sheet.cell(row=revenue_data_start + offset, column=2, value=round(revenue, 2))
        revenue_data_end = revenue_data_start + len(revenues) - 1

        if revenues:
            revenue_chart = BarChart()
            revenue_chart.title = "Gesamtverkaufszahlen"
            revenue_chart.y_axis.title = "Einnahmen (€)"
            data = Reference(summary_sheet, min_col=2, min_row=header_row, max_row=revenue_data_end)
            categories = Reference(summary_sheet, min_col=1, min_row=revenue_data_start, max_row=revenue_data_end)
            revenue_chart.add_data(data, titles_from_data=True)
            revenue_chart.set_categories(categories)
            revenue_chart.width, revenue_chart.height = 16, 9
            summary_sheet.add_chart(revenue_chart, f"D{revenue_start_row}")

        summary_sheet.column_dimensions["A"].width = 28
        summary_sheet.column_dimensions["B"].width = 14

        # -------------------------------------------------
        # Speichern
        # -------------------------------------------------

        filename = datetime.now().strftime("statistik_%Y-%m-%d_%H-%M.xlsx")
        export_path = storage.export_dir("excel") / filename
        workbook.save(export_path)

        self.export_status.text = f"Export erstellt: {export_path.name}"

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
        self._confirm(
            "Alle Verkäufe im gewählten Zeitraum löschen?",
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

    def _confirm(self, message, callback):
        content = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )
        content.add_widget(Label(text=message, color=theme.TEXT_PRIMARY, font_size="16sp"))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.ROW_SPACING))
        popup = Popup(title="Verkaufsdaten", content=content, size_hint=(0.45, None), height=dp(190), auto_dismiss=False)
        cancel = self._button("Abbrechen", popup.dismiss)
        buttons.add_widget(cancel)
        if callback:
            confirm = self._button("Löschen", lambda: (popup.dismiss(), callback()))
            buttons.add_widget(confirm)
        content.add_widget(buttons)
        popup.open()
