"""Wiederverwendbarer Kalender-Dropdown zur Datumsauswahl (statt Freitext)."""

import calendar
from datetime import date

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from widgets.common.kig_popup import KiGPopup
from kivy.uix.widget import Widget

import theme

from widgets.kig_label import KiGLabel

MONTH_NAMES = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
)
WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


class _DayButton(Button):
    """Einzelner Tag im Kalendergitter."""

    def __init__(self, day, selected, callback, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.callback = callback

        self.text = str(day.day)
        self.font_size = "16sp"
        self.bold = True
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = theme.TEXT_WHITE if selected else theme.TEXT_PRIMARY

        with self.canvas.before:
            Color(*(theme.PRIMARY_ORANGE if selected else theme.SURFACE))
            self.background = RoundedRectangle(radius=[dp(8)])

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self.bind(on_release=lambda *_args: self.callback(self.day))

    def _update_canvas(self, *_args):
        self.background.pos = self.pos
        self.background.size = self.size


class DatePickerPopup(KiGPopup):
    """Kalender-Popup zur Auswahl eines einzelnen Datums.

    Verwendung:
        DatePickerPopup(on_select=lambda iso_date: ..., initial_date=None).open()

    initial_date: ISO-Datumsstring ("JJJJ-MM-TT") oder None (dann wird
    der heutige Monat angezeigt, ohne Vorauswahl).
    """

    def __init__(self, on_select, initial_date=None, title="Datum wählen", **kwargs):
        super().__init__(**kwargs)

        self.on_select = on_select
        self.title = title
        self.size_hint = (None, None)
        self.size = (dp(420), dp(480))
        self.auto_dismiss = True

        if initial_date:
            try:
                parsed = date.fromisoformat(initial_date)
            except ValueError:
                parsed = date.today()
        else:
            parsed = date.today()

        self.selected_day = parsed if initial_date else None
        self.visible_year = parsed.year
        self.visible_month = parsed.month

        root = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        with root.canvas.before:
            Color(*theme.CARD)
            self._background = RoundedRectangle(pos=root.pos, size=root.size, radius=[0])
        root.bind(pos=self._update_background, size=self._update_background)

        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(theme.ROW_SPACING))
        header.add_widget(self._nav_button("‹", self._previous_month))

        self.month_label = KiGLabel(text=self._month_label())
        self.month_label.set_font_size(18)
        self.month_label.set_bold(True)
        self.month_label.set_color(theme.TEXT_PRIMARY)
        header.add_widget(self.month_label)

        header.add_widget(self._nav_button("›", self._next_month))
        root.add_widget(header)

        weekdays = GridLayout(cols=7, size_hint_y=None, height=dp(26))
        for weekday in WEEKDAYS:
            label = KiGLabel(text=weekday)
            label.set_font_size(12)
            label.set_bold(True)
            label.set_color(theme.TEXT_SECONDARY)
            weekdays.add_widget(label)
        root.add_widget(weekdays)

        self.day_grid = GridLayout(cols=7, spacing=dp(theme.LABEL_SPACING))
        root.add_widget(self.day_grid)

        today_button = Button(
            text="Heute", size_hint_y=None, height=dp(44),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="14sp", bold=True,
        )
        today_button.bind(on_release=lambda *_args: self._select_day(date.today()))
        root.add_widget(today_button)

        self.content = root
        self._refresh_grid()

    def _update_background(self, instance, _value):
        self._background.pos = instance.pos
        self._background.size = instance.size

    @staticmethod
    def _nav_button(text, callback):
        button = Button(
            text=text, size_hint_x=None, width=dp(48),
            background_normal="", background_down="",
            background_color=theme.SURFACE, color=theme.TEXT_PRIMARY,
            font_size="18sp", bold=True,
        )
        button.bind(on_release=lambda *_args: callback())
        return button

    def _month_label(self):
        return f"{MONTH_NAMES[self.visible_month - 1]} {self.visible_year}"

    def _previous_month(self):
        if self.visible_month == 1:
            self.visible_year -= 1
            self.visible_month = 12
        else:
            self.visible_month -= 1
        self._refresh_grid()

    def _next_month(self):
        if self.visible_month == 12:
            self.visible_year += 1
            self.visible_month = 1
        else:
            self.visible_month += 1
        self._refresh_grid()

    def _refresh_grid(self):
        self.month_label.text = self._month_label()
        self.day_grid.clear_widgets()

        first_weekday, days_in_month = calendar.monthrange(self.visible_year, self.visible_month)
        for _ in range(first_weekday):
            self.day_grid.add_widget(Widget())

        for day_number in range(1, days_in_month + 1):
            day = date(self.visible_year, self.visible_month, day_number)
            self.day_grid.add_widget(
                _DayButton(day, day == self.selected_day, self._select_day)
            )

    def _select_day(self, day):
        self.dismiss()
        if callable(self.on_select):
            self.on_select(day.isoformat())
