"""Rustikale Kalenderübersicht mit Details und verknüpften Schichten."""
from datetime import date, datetime

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import config
import theme
from widgets.cash.design import CashButton
from widgets.common.rounded_panel import RoundedPanel
from widgets.common.rounded_spinner import RoundedSpinner


def label(text, size=16, bold=False, height=32):
    item = Label(text=text, font_size=f'{size}sp', bold=bold,
                 color=theme.TEXT_PRIMARY, halign='left', valign='middle',
                 size_hint_y=None, height=dp(height), shorten=True,
                 shorten_from='right')
    item.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
    return item


class PlannerAction(CashButton):
    def __init__(self, warning=False, **kwargs):
        self.warning = warning
        super().__init__(**kwargs)

    def _draw(self, *_):
        super()._draw()
        if self.warning:
            self.color = theme.ERROR
            self.edge_color.rgba = theme.ERROR
            self.fill.rgba = theme.ERROR_LIGHT


def action(text, callback, active=False, height=48, warning=False):
    item = PlannerAction(text=text, active=active, warning=warning, font_size='15sp', bold=True,
                      size_hint_y=None, height=dp(height), valign='middle', halign='center', shorten=True)
    item.bind(size=lambda w, _: setattr(w, 'text_size', (w.width - dp(16), w.height)))
    item.bind(on_release=lambda *_: callback())
    return item


def date_text(value):
    try:
        return date.fromisoformat(value).strftime('%d.%m.%Y')
    except (TypeError, ValueError):
        return value or '–'


def scroll_list(parent):
    scroll = ScrollView(bar_width=dp(5), do_scroll_x=False)
    body = BoxLayout(orientation='vertical', spacing=dp(7), size_hint_y=None)
    body.bind(minimum_height=body.setter('height'))
    scroll.add_widget(body)
    parent.add_widget(scroll)
    return body


def shift_problems(shift):
    problems = []
    if shift['besetzt'] < shift['needed']:
        problems.append('Unterbesetzt')
    if shift['needed'] < 1 or not (shift['task'] or '').strip():
        problems.append('Angaben prüfen')
    for key in ('start_time', 'end_time'):
        value = shift[key]
        if value:
            try:
                datetime.strptime(value, '%H:%M')
            except ValueError:
                problems.append('Uhrzeit prüfen')
                break
    return problems


def checklist_problems(db):
    overdue = invalid = 0
    for checklist in db.get_checklists():
        for item in db.get_checklist_items(checklist['id']):
            if item['done']:
                continue
            if not (item['task'] or '').strip():
                invalid += 1
            if item['deadline']:
                try:
                    overdue += date.fromisoformat(item['deadline']) < date.today()
                except ValueError:
                    invalid += 1
    return overdue, invalid


class PlannerOverview:
    """Ansichtsaufbau; die bestehenden Editor- und Speicherwege bleiben im Screen."""

    def build_overview(self, weekdays):
        self.selected_entry_id = None
        self.entries = []
        outer = ScrollView(do_scroll_x=False, bar_width=dp(6))
        self.overview = BoxLayout(orientation='vertical', size_hint_y=None,
                                 padding=dp(16), spacing=dp(14))
        self.overview.bind(minimum_height=self.overview.setter('height'))
        outer.add_widget(self.overview)
        self.add_widget(outer)
        self.toolbar = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(16))
        self.toolbar.add_widget(label('Veranstaltungen & Termine', 26, True, 50))
        self.month_controls = self._build_header()
        self.toolbar.add_widget(self.month_controls)
        self.overview.add_widget(self.toolbar)

        self.main_row = BoxLayout(spacing=dp(14), size_hint_y=None, height=dp(460))
        self.calendar_panel = RoundedPanel(orientation='vertical', padding=dp(12), spacing=dp(5))
        headings = GridLayout(cols=7, size_hint_y=None, height=dp(28))
        for weekday in weekdays:
            heading = label(weekday, 14, True, 28)
            heading.halign = 'center'
            headings.add_widget(heading)
        self.calendar_panel.add_widget(headings)
        self.calendar_grid = GridLayout(cols=7, spacing=dp(4))
        self.calendar_panel.add_widget(self.calendar_grid)
        self.main_row.add_widget(self.calendar_panel)
        self.detail_panel = RoundedPanel(orientation='vertical', padding=dp(16), spacing=dp(8))
        self.detail_body = scroll_list(self.detail_panel)
        self.detail_actions = BoxLayout(orientation='vertical', size_hint_y=None,
                                       height=dp(104), spacing=dp(8))
        self.detail_panel.add_widget(self.detail_actions)
        self.main_row.add_widget(self.detail_panel)
        self.overview.add_widget(self.main_row)

        self.summaries = GridLayout(cols=3, spacing=dp(14), size_hint_y=None, height=dp(240))
        self.summary_bodies = []
        for title in ('Veranstaltungen · kommend', 'Termine · kommend', 'Schichten zur Auswahl'):
            panel = RoundedPanel(orientation='vertical', padding=dp(14), spacing=dp(8))
            panel.add_widget(label(title, 17, True, 30))
            self.summary_bodies.append(scroll_list(panel))
            self.summaries.add_widget(panel)
        self.overview.add_widget(self.summaries)
        self.main_row.bind(width=self._align_columns)
        self.bind(width=self._overview_resize)
        self._overview_resize()

    def _overview_resize(self, *_):
        narrow = self.width < dp(1000)
        self.main_row.orientation = 'vertical' if narrow else 'horizontal'
        self.main_row.height = dp(870 if narrow else 460)
        self.calendar_panel.size_hint = (1, .55) if narrow else (1, 1)
        self.detail_panel.size_hint = (1, .45) if narrow else (None, 1)
        self.summaries.cols = 1 if narrow else 3
        self.summaries.height = dp(740 if narrow else 240)
        self.toolbar.orientation = 'vertical' if narrow else 'horizontal'
        self.toolbar.height = dp(110 if narrow else 50)
        self.month_controls.size_hint_x = 1 if narrow else None
        if not narrow:
            self.month_controls.width = dp(430)
        self._align_columns()

    def _align_columns(self, *_):
        if self.main_row.orientation == 'horizontal':
            self.detail_panel.width = (self.main_row.width - 2 * dp(14)) / 3

    def select_day(self, day):
        self.selected_day = day
        self.selected_entry_id = None
        self.refresh_calendar()

    def select_entry(self, entry):
        self.selected_entry_id = entry['id']
        self.selected_day = date.fromisoformat(entry['start_date'])
        self.visible_year, self.visible_month = self.selected_day.year, self.selected_day.month
        self._sync_month_picker()
        self.refresh_calendar()

    def show_today(self):
        today = date.today()
        self.visible_year, self.visible_month = today.year, today.month
        self.selected_day, self.selected_entry_id = today, None
        self._sync_month_picker()
        self.refresh_calendar()

    def entries_on(self, day):
        value = day.isoformat()
        return [entry for entry in self.entries
                if entry['start_date'] <= value <= (entry['end_date'] or entry['start_date'])]

    def refresh_overview(self):
        from screens.events_screen import TYPE_LABELS, CalendarDayButton
        daily = self.entries_on(self.selected_day)
        selected = next((e for e in daily if e['id'] == self.selected_entry_id), None)
        selected = selected or (daily[0] if daily else None)
        self.selected_entry_id = selected['id'] if selected else None
        body = self.detail_body
        body.clear_widgets()
        self.detail_actions.clear_widgets()
        overdue, invalid = checklist_problems(self.db)
        checklist_warning = bool(overdue or invalid)
        body.add_widget(label(date_text(self.selected_day.isoformat()), 15, height=26))
        if not selected:
            body.add_widget(label('Keine Einträge an diesem Tag.', 18, True, 60))
            self.detail_actions.add_widget(action('Eintrag anlegen', lambda: self.open_entry_editor(self.selected_day), True))
        else:
            if len(daily) > 1:
                options = {f'{i + 1} · {CalendarDayButton._display_name(e)}': e
                           for i, e in enumerate(daily)}
                picker = RoundedSpinner(values=list(options), size_hint_y=None, height=dp(44),
                                        text=next(k for k, e in options.items() if e['id'] == selected['id']))
                picker.bind(text=lambda _, value: self._select_detail(options[value]))
                body.add_widget(picker)
            body.add_widget(label(CalendarDayButton._display_name(selected), 23, True, 46))
            fields = [('Art', TYPE_LABELS.get(selected['entry_type'], 'Eintrag')),
                      ('Datum', date_text(selected['start_date']))]
            if selected['end_date'] and selected['end_date'] != selected['start_date']:
                fields[-1] = ('Datum', date_text(selected['start_date']) + ' – ' + date_text(selected['end_date']))
            fields.extend((key, selected[field]) for key, field in
                          [('Ort', 'location'), ('Veranstalter', 'organizer')] if selected[field])
            for key, value in fields:
                body.add_widget(label(f'{key}: {value}', 15, height=32))
            editing = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
            editing.add_widget(action('Bearbeiten', lambda: self.open_entry_editor(
                date.fromisoformat(selected['start_date']), selected)))
            editing.add_widget(action('+ Neuer Eintrag',
                                      lambda: self.open_entry_editor(self.selected_day), True))
            self.detail_actions.add_widget(editing)
            links = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
            if selected['entry_type'] == 'EVENT':
                plan_exists = self.db.get_shift_plan_for_event(selected['id']) is not None
                selected_plan = self.db.get_shift_plan_for_event(selected['id'])
                needs_help = selected_plan and any(shift_problems(s) for s in self.db.get_shifts(selected_plan['id']))
                shift_button = action('Schichtplan öffnen' if plan_exists else 'Kein Schichtplan',
                                      lambda: self.open_selected_shifts(selected), warning=bool(needs_help))
                shift_button.disabled = not plan_exists
                links.add_widget(shift_button)
            links.add_widget(action('Checklisten öffnen', self.open_checklists, warning=checklist_warning))
            self.detail_actions.add_widget(links)
        if checklist_warning:
            notes = []
            if overdue:
                notes.append(f'{overdue} überfällig')
            if invalid:
                notes.append(f'{invalid} Angaben prüfen')
            notice = label('Alle Checklisten: ' + ' · '.join(notes), 14, height=44)
            notice.color = theme.ERROR
            body.add_widget(notice)

        for entry_type, target in zip(('EVENT', 'APPOINTMENT'), self.summary_bodies[:2]):
            target.clear_widgets()
            upcoming = sorted((e for e in self.entries if e['entry_type'] == entry_type
                               and (e['end_date'] or e['start_date']) >= date.today().isoformat()),
                              key=lambda e: (e['start_date'], e['id']))
            if not upcoming:
                target.add_widget(label('Keine kommenden Einträge.', 15, height=54))
            for entry in upcoming:
                button = action(f"{date_text(entry['start_date'])}  ·  {entry['name']}",
                                lambda e=entry: self.select_entry(e), height=48)
                button.halign = 'left'
                button.shorten = True
                button.bind(size=lambda w, _: setattr(w, 'text_size', (w.width - dp(16), w.height)))
                target.add_widget(button)

        target = self.summary_bodies[2]
        target.clear_widgets()
        plan = self.db.get_shift_plan_for_event(selected['id']) if selected and selected['entry_type'] == 'EVENT' else None
        shifts = self.db.get_shifts(plan['id']) if plan else []
        if not plan:
            target.add_widget(label('Kein Schichtplan zur Auswahl.' if selected else
                                    'Bitte eine Veranstaltung auswählen.', 15, height=54))
        else:
            target.add_widget(label(selected['name'], 15, True))
            if not shifts:
                target.add_widget(label('Noch keine Schichten angelegt.', 15, height=48))
            for shift in shifts:
                problems = shift_problems(shift)
                times = ' – '.join(t for t in (shift['start_time'], shift['end_time']) if t)
                text = f"{shift['task']} · {shift['besetzt']} / {shift['needed']} besetzt"
                text += (f'\n{times}' if times else '')
                if problems:
                    text += '\n' + ' · '.join(problems)
                button = action(text, lambda: self.open_selected_shifts(selected),
                                height=82 if problems else 62, warning=bool(problems))
                button.shorten = False
                target.add_widget(button)

    def _select_detail(self, entry):
        self.selected_entry_id = entry['id']
        self.refresh_overview()

    def open_selected_shifts(self, entry):
        if self.manager is None:
            return
        plan = self.db.get_shift_plan_for_event(entry['id'])
        if plan:
            self.manager.current = config.SCREEN_SHIFTPLAN
            self.manager.get_screen(config.SCREEN_SHIFTPLAN).select_plan(plan['id'])

    def open_checklists(self):
        if self.manager is not None:
            self.manager.current = config.SCREEN_CHECKLIST
