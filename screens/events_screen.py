"""Vollflächiger Monatskalender für Events, Barschichten und Termine."""

import calendar
from datetime import date

from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

import theme
from database import DatabaseManager
from widgets.common.feldausrichtung import links_ausrichten
from widgets.common.confirm_popup import ConfirmPopup
from widgets.common.kig_popup import KiGPopup
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


MONTH_NAMES = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
)
WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
TYPE_LABELS = {"EVENT": "Event", "SHIFT": "Barschicht", "APPOINTMENT": "Termin"}
LABEL_TYPES = {label: entry_type for entry_type, label in TYPE_LABELS.items()}


class CalendarDayButton(Button):
    """Tageskachel mit Datum oben links und den Einträgen des Tages."""

    def __init__(self, day, entries, selected, callback, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.callback = callback

        visible_entries = [self._display_name(entry) for entry in entries[:4]]
        if len(entries) > 4:
            visible_entries.append(f"+ {len(entries) - 4} weitere")

        self.text = "\n".join([str(day.day), *visible_entries])
        self.font_size = "15sp"
        self.bold = True
        self.halign = "left"
        self.valign = "top"
        self.padding = (dp(theme.TILE_PADDING), dp(theme.SPACE_XS))
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = theme.TEXT_PRIMARY

        with self.canvas.before:
            Color(*(theme.PRIMARY_ORANGE if selected else theme.CARD))
            self.background = RoundedRectangle(radius=[dp(8)])
        with self.canvas.after:
            Color(*theme.CARD_BORDER)
            self.calendar_border = Line(width=theme.BORDER_WIDTH)

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self.bind(on_release=lambda *_args: self.callback(self.day))

    @staticmethod
    def _display_name(entry):
        if entry["entry_type"] == "SHIFT" and entry["staff_names"]:
            return entry["staff_names"]
        return entry["name"]

    def _update_canvas(self, *_args):
        self.background.pos = self.pos
        self.background.size = self.size
        self.calendar_border.rounded_rectangle = (*self.pos, *self.size, dp(8))
        self.text_size = (self.width - dp(16), self.height - dp(12))


class EventsScreen(Screen):
    """Kalenderansicht; Detail- und Bearbeitungsfunktionen liegen in Popups."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db = DatabaseManager()
        today = date.today()
        self.visible_year = today.year
        self.visible_month = today.month
        self.selected_day = today
        self.month_options = {}
        self.day_popup = None

        root = BoxLayout(padding=dp(theme.SCREEN_PADDING))

        panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        title = KiGLabel(text="Kalender")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(42)
        panel.add_widget(title)

        panel.add_widget(self._build_header())

        weekdays = GridLayout(cols=7, size_hint_y=None, height=dp(34))
        for weekday in WEEKDAYS:
            label = KiGLabel(text=weekday)
            label.set_bold(True)
            label.set_color(theme.TEXT_SECONDARY)
            weekdays.add_widget(label)
        panel.add_widget(weekdays)

        self.calendar_grid = GridLayout(cols=7, spacing=dp(theme.ROW_SPACING))
        panel.add_widget(self.calendar_grid)
        root.add_widget(panel)
        self.add_widget(root)

        self._populate_month_picker()
        self.refresh_calendar()

    def _build_header(self):
        header = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(theme.ROW_SPACING))
        header.add_widget(self._button("‹", self.previous_month, width=dp(68)))

        self.month_spinner = Spinner(font_size="21sp")
        links_ausrichten(self.month_spinner)
        self.month_spinner.bind(text=self._month_selected)
        header.add_widget(self.month_spinner)
        header.add_widget(self._button("›", self.next_month, width=dp(68)))
        return header

    @staticmethod
    def _button(text, callback, width=None, height=None):
        button = Button(
            text=text,
            font_size="18sp",
            bold=True,
            background_normal="",
            background_down="",
            background_color=theme.SURFACE,
            color=theme.TEXT_PRIMARY,
            size_hint=(None, None) if width else (1, None),
            height=height or dp(54)
        )
        if width:
            button.width = width
        button.bind(on_release=lambda *_args: callback())
        return button

    def on_pre_enter(self, *_args):
        self.refresh_calendar()

    def previous_month(self):
        if self.visible_month == 1:
            self.visible_year -= 1
            self.visible_month = 12
        else:
            self.visible_month -= 1
        self._sync_month_picker()
        self.refresh_calendar()

    def next_month(self):
        if self.visible_month == 12:
            self.visible_year += 1
            self.visible_month = 1
        else:
            self.visible_month += 1
        self._sync_month_picker()
        self.refresh_calendar()

    def _populate_month_picker(self):
        for offset in range(-18, 19):
            year = self.visible_year + (self.visible_month - 1 + offset) // 12
            month = (self.visible_month - 1 + offset) % 12 + 1
            self.month_options[f"{MONTH_NAMES[month - 1]} {year}"] = (year, month)
        self.month_spinner.values = list(self.month_options)
        self._sync_month_picker()

    def _sync_month_picker(self):
        label = f"{MONTH_NAMES[self.visible_month - 1]} {self.visible_year}"
        if label not in self.month_options:
            self._populate_month_picker()
            return
        self.month_spinner.text = label

    def _month_selected(self, _spinner, label):
        if label in self.month_options:
            self.visible_year, self.visible_month = self.month_options[label]
            self.refresh_calendar()

    def refresh_calendar(self):
        entries_by_date = {}
        for entry in self.db.get_entries_for_month(self.visible_year, self.visible_month):
            entries_by_date.setdefault(entry["start_date"], []).append(entry)

        self.calendar_grid.clear_widgets()
        first_weekday, days_in_month = calendar.monthrange(self.visible_year, self.visible_month)
        for _ in range(first_weekday):
            self.calendar_grid.add_widget(Widget())

        for day_number in range(1, days_in_month + 1):
            day = date(self.visible_year, self.visible_month, day_number)
            self.calendar_grid.add_widget(
                CalendarDayButton(
                    day,
                    entries_by_date.get(day.isoformat(), []),
                    day == self.selected_day,
                    self.open_day_popup
                )
            )

    def open_day_popup(self, selected_day):
        self.selected_day = selected_day
        self.refresh_calendar()

        content = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )
        entries = self.db.get_entries_for_date(selected_day.isoformat())

        scroll = ScrollView(bar_width=dp(10))
        entry_list = BoxLayout(orientation="vertical", spacing=dp(theme.ROW_SPACING), size_hint_y=None)
        entry_list.bind(minimum_height=entry_list.setter("height"))
        scroll.add_widget(entry_list)
        content.add_widget(scroll)

        for entry in entries:
            display = CalendarDayButton._display_name(entry)
            button = self._button(
                f"{TYPE_LABELS.get(entry['entry_type'], 'Eintrag')}: {display}",
                lambda entry=entry: self.open_entry_editor(selected_day, entry),
                height=dp(54)
            )
            entry_list.add_widget(button)

        controls = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(theme.ROW_SPACING))
        controls.add_widget(self._button("Neu", lambda: self.open_entry_editor(selected_day), height=dp(54)))
        controls.add_widget(self._button("Schließen", lambda: self.day_popup.dismiss(), height=dp(54)))
        content.add_widget(controls)

        self.day_popup = KiGPopup(
            title=f"{selected_day.day}. {MONTH_NAMES[selected_day.month - 1]} {selected_day.year}",
            content=content,
            size_hint=(0.72, 0.72),
            auto_dismiss=False
        )
        self.day_popup.open()

    def open_entry_editor(self, selected_day, entry=None):
        if self.day_popup is not None:
            self.day_popup.dismiss()

        content = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )
        type_spinner = Spinner(values=list(LABEL_TYPES), size_hint_y=None, height=dp(54))
        links_ausrichten(type_spinner)
        name_input = RoundedInput(multiline=False, size_hint_y=None, height=dp(54))
        content.add_widget(type_spinner)
        content.add_widget(name_input)

        if entry is None:
            type_spinner.text = "Event"
            name_input.hint_text = "Name des Events oder Termins"
        else:
            type_spinner.text = TYPE_LABELS.get(entry["entry_type"], "Event")
            name_input.text = CalendarDayButton._display_name(entry)

        def update_hint(_spinner, label):
            name_input.hint_text = (
                "Namen der arbeitenden Personen" if label == "Barschicht"
                else "Name des Events oder Termins"
            )

        type_spinner.bind(text=update_hint)
        update_hint(type_spinner, type_spinner.text)

        buttons = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(theme.ROW_SPACING))
        editor_popup = KiGPopup(
            title="Eintrag bearbeiten" if entry else "Neuen Eintrag anlegen",
            content=content,
            size_hint=(0.62, None),
            height=min(dp(340), Window.height - dp(20)),
            pos_hint={"center_x": 0.5, "top": 0.98},
            auto_dismiss=False
        )

        buttons.add_widget(self._button("Speichern", lambda: self.save_entry(
            editor_popup, selected_day, entry, type_spinner.text, name_input.text
        ), height=dp(54)))

        if entry is not None:
            buttons.add_widget(self._button("Löschen", lambda: self.delete_entry(editor_popup, entry["id"]), height=dp(54)))

        buttons.add_widget(self._button("Abbrechen", editor_popup.dismiss, height=dp(54)))
        content.add_widget(buttons)
        editor_popup.open()

    def save_entry(self, popup, selected_day, entry, type_label, text):
        text = text.strip()
        if not text:
            return

        entry_type = LABEL_TYPES[type_label]
        name = "Barschicht" if entry_type == "SHIFT" else text
        staff_names = text if entry_type == "SHIFT" else ""

        if entry is None:
            self.db.add_event(
                name=name,
                location="",
                organizer="",
                start_date=selected_day.isoformat(),
                end_date=selected_day.isoformat(),
                entry_type=entry_type,
                staff_names=staff_names
            )
        else:
            self.db.update_event(entry["id"], name, entry_type, staff_names)

        popup.dismiss()
        self.refresh_calendar()

    def delete_entry(self, popup, entry_id):
        """Löscht einen Kalender-Eintrag.

        Hängen bereits Verkäufe am Eintrag, weigert sich die Datenbank
        (ein Verkauf darf nicht auf ein Event zeigen, das es nicht mehr
        gibt). Bisher geschah in diesem Fall gar nichts - der Knopf
        sah kaputt aus, obwohl er funktionierte. Jetzt wird der Grund
        genannt und nachgefragt, ob die Verkäufe vom Event gelöst
        werden sollen: Sie bleiben dann mit allen Beträgen in der
        Statistik, nur die Zuordnung entfällt.
        """

        verkaeufe = self.db.count_sales_for_event(entry_id)

        if verkaeufe == 0:

            if self.db.delete_event(entry_id):
                popup.dismiss()
                self.refresh_calendar()
            else:
                self.hinweis(
                    "Der Eintrag konnte nicht gelöscht werden. "
                    "Bitte die Anwendung neu starten und es erneut "
                    "versuchen."
                )

            return

        popup.dismiss()

        ConfirmPopup(
            title="Eintrag löschen",
            message=(
                f"Zu diesem Eintrag sind bereits {verkaeufe} "
                f"{'Verkauf' if verkaeufe == 1 else 'Verkäufe'} erfasst.\n\n"
                "Die Umsätze bleiben in der Statistik erhalten, verlieren "
                "aber die Zuordnung zu diesem Eintrag.\n\n"
                "Trotzdem löschen?"
            ),
            confirm_text="Trotzdem löschen",
            on_confirm=lambda: self._delete_entry_confirmed(entry_id),
        ).open()

    def _delete_entry_confirmed(self, entry_id):

        if self.db.delete_event(entry_id, detach_sales=True):
            self.refresh_calendar()
        else:
            self.hinweis("Der Eintrag konnte nicht gelöscht werden.")

    def hinweis(self, text):
        """Kurze Meldung, wenn etwas nicht geklappt hat - besser als
        eine Schaltfläche, die stumm bleibt."""

        content = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        label = KiGLabel(text=text)
        label.set_font_size(16)
        label.set_alignment("center")
        content.add_widget(label)

        popup = KiGPopup(
            title="Kalender", content=content,
            size_hint=(0.55, None), height=dp(220),
        )

        content.add_widget(self._button(
            "Schließen", popup.dismiss, height=dp(52)
        ))

        popup.open()
