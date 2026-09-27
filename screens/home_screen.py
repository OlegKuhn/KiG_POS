"""Dashboard: aktuelle Umsätze, Planung und Kassenbuch auf einen Blick."""
from datetime import datetime
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
import config
import theme
import geldformat
from database import DatabaseManager
from dashboard_data import dashboard_snapshot
from widgets.dashboard import DashboardCard, AccentPanel, ProgressTrack, icon_badge, accent, detail_row


MONTHS = ('Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
          'August', 'September', 'Oktober', 'November', 'Dezember')


def text_label(text='', size=16, bold=False, color=None, height=None, align='left'):
    label = Label(text=text, font_size=f'{size}sp', bold=bold,
                  color=color or theme.TEXT_PRIMARY, halign=align, valign='middle',
                  size_hint_y=None, height=dp(height or size * 1.5))
    label.bind(size=lambda obj, value: setattr(obj, 'text_size', (value[0], None)))
    if height is None:
        label.bind(texture_size=lambda obj, value: setattr(obj, 'height', max(dp(size * 1.5), value[1] + dp(4))))
    return label


def date_text(value):
    if not value:
        return 'Ohne Frist'
    try:
        return datetime.fromisoformat(value).strftime('%d.%m.%Y')
    except ValueError:
        return value


class HomeScreen(Screen):
    def __init__(self, database=None, **kwargs):
        super().__init__(**kwargs)
        self.db = database or DatabaseManager()
        self._clock_event = None
        self._minute = None
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        self.body = BoxLayout(orientation='vertical', size_hint_y=None,
                              padding=dp(24), spacing=dp(18))
        self.body.bind(minimum_height=self.body.setter('height'))
        self.hero = BoxLayout(size_hint_y=None, height=dp(78), spacing=dp(12))
        self.branding = BoxLayout(orientation='vertical')
        self.heading = text_label('KiG POS', size=32, bold=True, height=46)
        self.branding.add_widget(self.heading)
        self.branding.add_widget(text_label('Gemeinsam feiern. Gemeinsam stark.', color=theme.TEXT_SECONDARY, height=26))
        self.datetime_label = text_label(size=15, color=theme.TEXT_SECONDARY, height=24)
        self.hero.add_widget(self.branding)
        self.body.add_widget(self.hero)
        self.metrics = GridLayout(cols=3, spacing=dp(10), size_hint_y=None)
        self.metrics.bind(minimum_height=self.metrics.setter('height'))
        self.metric_values = {}
        for key, caption in (
                ('revenue', 'Tagesumsatz'),
                ('shifts', 'Offene Schichten'),
                ('tasks', 'Offene Punkte')):
            tone = {'revenue': 'orange', 'shifts': 'teal', 'tasks': 'lavender'}[key]
            card = AccentPanel(tone=tone, orientation='horizontal', padding=dp(10), spacing=dp(8), size_hint_y=None, height=dp(84))
            card.add_widget(icon_badge({'revenue': 'statistics', 'shifts': 'time-management', 'tasks': 'checklist'}[key], tone, 36))
            stack = BoxLayout(orientation='vertical')
            card.add_widget(stack)
            stack.add_widget(text_label(caption, size=12, color=theme.TEXT_SECONDARY, height=24))
            value = text_label('–', size=26, bold=True, color=accent(tone), height=36)
            self.metric_values[key] = value
            stack.add_widget(value)
            self.metrics.add_widget(card)
        self.hero.add_widget(self.metrics)
        self.hero.add_widget(self.datetime_label)
        self.grid = GridLayout(cols=2, spacing=dp(18), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.event_card = DashboardCard('Nächste 3 Veranstaltungen', config.SCREEN_EVENTS, self._open, 'teal', 'events', 'Die nächsten Veranstaltungen im Überblick')
        self.shift_card = DashboardCard('Offene Schichten', config.SCREEN_SHIFTPLAN, self._open, 'amber', 'time-management', 'Noch zu besetzende Schichten')
        self.task_card = DashboardCard('Offene Checklistenpunkte', config.SCREEN_CHECKLIST, self._open, 'lavender', 'checklist', 'Noch zu erledigende Aufgaben')
        self.month_card = DashboardCard('Kassenbuch · Monat', config.SCREEN_CASHBOOK, self._open, 'sage', 'statistics', 'Einnahmen und Ausgaben im Überblick')
        for card in (self.event_card, self.shift_card, self.task_card, self.month_card):
            self.grid.add_widget(card)
        self.body.add_widget(self.grid)
        self.scroll.add_widget(self.body)
        self.add_widget(self.scroll)
        self.bind(width=self._update_columns)
        self._update_columns()

    def _update_columns(self, *_):
        wide = self.width >= dp(1180)
        self.metrics.cols = 3 if self.width >= dp(600) else 1
        self.grid.cols = 2 if self.width >= dp(940) else 1
        self.body.padding = dp(14 if self.width < dp(600) else 24)
        self.hero.orientation = 'horizontal' if wide else 'vertical'
        self.hero.height = dp(84 if wide else (224 if self.metrics.cols == 3 else 412))
        self.branding.size_hint = (1, 1) if wide else (1, None)
        if not wide:
            self.branding.height = dp(72)
        self.metrics.size_hint_x = None if wide else 1
        self.metrics.pos_hint = {'center_y': .5}
        if wide:
            self.metrics.width = dp(620)
        # Gleich breite Außenbereiche zentrieren die Kennzahlen exakt
        # zwischen Markenblock und Datum, unabhängig von der Fensterbreite.
        self.datetime_label.size_hint_x = 1
        self.datetime_label.halign = 'right' if wide else 'left'
        self.datetime_label.pos_hint = {'center_y': .5}
        for card in (self.event_card, self.shift_card, self.task_card, self.month_card):
            card.title.font_size = '16sp' if self.width < dp(600) else '20sp'
            card.height = dp(330 if self.grid.cols == 2 else 370)
            card.compact(self.width < dp(600))

    def refresh(self):
        data = dashboard_snapshot(self.db)
        self.snapshot = data
        self.metric_values['revenue'].text = geldformat.geld(data['daily_revenue'])
        self.metric_values['shifts'].text = str(len(data['shifts']))
        self.metric_values['tasks'].text = str(len(data['tasks']))
        for card in (self.event_card, self.shift_card, self.task_card, self.month_card):
            card.rows.clear_widgets()
        for event in data['events']:
            details = date_text(event['start_date'])
            if event['end_date'] and event['end_date'] != event['start_date']:
                details += ' – ' + date_text(event['end_date'])
            if event['location']:
                details += ' · ' + event['location']
            self._event_row(event, details)
        if not data['events']:
            self.event_card.line('Keine anstehenden Veranstaltungen')
        for shift in data['shifts']:
            time = ' – '.join(t for t in (shift['start_time'], shift['end_time']) if t)
            self._shift_row(shift, time)
        if not data['shifts']:
            self.shift_card.line('Keine offenen Schichten', 'In den angelegten Plänen anstehender Veranstaltungen.')
        for task in data['tasks']:
            overdue = bool(task['deadline'] and task['deadline'] < data['today'].isoformat())
            self.task_card.line(task['task'],
                task['checklist_name'] + ' · ' + date_text(task['deadline']) +
                (f" · {task['responsible']}" if task['responsible'] else '') +
                (' · überfällig' if overdue else ''), warning=overdue,
                callback=lambda item=task: self._open_task(item))
        if not data['tasks']:
            self.task_card.line('Keine offenen Checklistenpunkte')
        self.month_card.title.text = f"Kassenbuch · {MONTHS[data['today'].month - 1]} {data['today'].year}"
        self._money_comparison(data)
        self._money_row('Datum', 'Einnahmen', 'Ausgaben', bold=True)
        for row in data['monthly']:
            self._money_row(date_text(row['date']), geldformat.geld(row['income']), geldformat.geld(row['expenses']))
        if not data['monthly']:
            self.month_card.rows.add_widget(text_label('Noch keine Buchungen in diesem Monat.', size=14, color=theme.TEXT_SECONDARY))
        self._money_row('Gesamt', geldformat.geld(data['income']), geldformat.geld(data['expenses']), bold=True)
        self.month_card.rows.add_widget(text_label('Saldo: ' + geldformat.geld(data['income'] - data['expenses']), bold=True))
        if data['invalid_entries']:
            self.month_card.rows.add_widget(text_label(
                f"{data['invalid_entries']} Buchungen mit Prüfhinweisen im Kassenbuch.", size=13, color=theme.ERROR))
        self._update_time()

    def _event_row(self, event, details):
        row = detail_row(callback=lambda: self._open_event(event))
        row.padding = dp(8)
        badge = AccentPanel(tone='teal', orientation='vertical', padding=dp(6),
                            size_hint=(None, None), size=(dp(54), dp(52)), pos_hint={'center_y': .5})
        day = datetime.fromisoformat(event['start_date'])
        badge.add_widget(text_label(str(day.day), size=22, bold=True, height=24, align='center'))
        badge.add_widget(text_label(MONTHS[day.month - 1][:3].upper(), size=11, color=accent('teal'), height=16, align='center'))
        row.add_widget(badge)
        words = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(3))
        words.bind(minimum_height=words.setter('height'))
        words.add_widget(text_label(event['name'], size=16, bold=True))
        words.add_widget(text_label(details, size=13, color=theme.TEXT_SECONDARY))
        row.add_widget(words)
        self.event_card.rows.add_widget(row)

    def _shift_row(self, shift, time):
        row = detail_row(orientation='vertical', callback=lambda: self._open_shift(shift))
        row.spacing = dp(4)
        row.add_widget(text_label(shift['event_name'], size=16, bold=True))
        row.add_widget(text_label((shift['task'] or 'Schicht') + ' · ' + date_text(shift['event_date']) +
                                 (f' · {time}' if time else ''), size=13, color=theme.TEXT_SECONDARY))
        status = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        status.add_widget(text_label(f"{shift['besetzt']} / {shift['needed']} besetzt", size=14, height=26))
        status.add_widget(text_label(f"{shift['missing']} " + ('fehlt' if shift['missing'] == 1 else 'fehlen'), size=14, bold=True,
                                     color=theme.ERROR, height=26, align='right'))
        row.add_widget(status)
        row.add_widget(ProgressTrack(shift['besetzt'] / max(1, shift['needed']), 'teal'))
        self.shift_card.rows.add_widget(row)

    def _money_comparison(self, data):
        comparison = BoxLayout(size_hint_y=None, height=dp(78), spacing=dp(20))
        maximum = max(abs(data['income']), abs(data['expenses']), 1)
        for caption, key, tone in (('Einnahmen', 'income', 'sage'), ('Ausgaben', 'expenses', 'terracotta')):
            column = BoxLayout(orientation='vertical', spacing=dp(4))
            column.add_widget(text_label(caption, size=13, color=theme.TEXT_SECONDARY, height=22))
            column.add_widget(text_label(geldformat.geld(data[key]), size=23, bold=True, color=accent(tone), height=34))
            column.add_widget(ProgressTrack(float(abs(data[key]) / maximum), tone))
            comparison.add_widget(column)
        self.month_card.rows.add_widget(comparison)

    def _money_row(self, caption, income, expenses, bold=False):
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(6))
        for index, text in enumerate((caption, income, expenses)):
            row.add_widget(text_label(text, size=14, bold=bold, height=32,
                                      align='left' if index == 0 else 'right'))
        self.month_card.rows.add_widget(row)

    def _update_time(self):
        now = datetime.now()
        self.datetime_label.text = now.strftime('%d.%m.%Y  ·  %H:%M:%S')
        self._minute = now.strftime('%Y-%m-%d %H:%M')

    def _tick(self, *_):
        if datetime.now().strftime('%Y-%m-%d %H:%M') != self._minute:
            self.refresh()
        else:
            self._update_time()

    def on_pre_enter(self, *_):
        self.refresh()
        if self._clock_event is None:
            self._clock_event = Clock.schedule_interval(self._tick, 1)

    def on_pre_leave(self, *_):
        self.stop()

    def stop(self):
        if self._clock_event is not None:
            self._clock_event.cancel()
            self._clock_event = None

    def on_parent(self, instance, parent):
        if parent is None:
            self.stop()

    def _planner_target(self, name):
        if self.manager is None or not self.manager.has_screen(config.SCREEN_PLANNER):
            return None
        self._open(name)
        return self.manager.get_screen(config.SCREEN_PLANNER).tab_manager.get_screen(name)

    def _open_event(self, event):
        current = next((dict(row) for row in self.db.get_events() if row['id'] == event['id']), None)
        if current is None:
            self.refresh()
            return
        screen = self._planner_target(config.SCREEN_EVENTS)
        if screen:
            screen.select_entry(current)

    def _open_task(self, task):
        if self.db.get_checklist(task['checklist_id']) is None:
            self.refresh()
            return
        screen = self._planner_target(config.SCREEN_CHECKLIST)
        if screen:
            screen.select_checklist(task['checklist_id'])
            self._reveal_row(screen, screen.items_box,
                             lambda row: getattr(row, 'item', {'id': None})['id'] == task['id'])

    def _open_shift(self, shift):
        if self.db.get_shift_plan(shift['plan_id']) is None:
            self.refresh()
            return
        screen = self._planner_target(config.SCREEN_SHIFTPLAN)
        if screen:
            screen.suche_input.text = ''
            screen.select_plan(shift['plan_id'])
            self._reveal_row(screen, screen.shifts_box,
                             lambda row: screen.shift_rows.get(shift['id']) is row)

    @staticmethod
    def _reveal_row(screen, container, matches):
        # Erst nach dem Layout zur Aufgabe scrollen; die Auswahl bleibt
        # bestehen, auch wenn ein Plan weiter unten in der Liste steht.
        def reveal(_):
            if screen.manager is None or screen.manager.current_screen is not screen:
                return
            row = next((row for row in container.children if matches(row)), None)
            if row is not None and isinstance(container.parent, ScrollView):
                container.parent.scroll_to(row, padding=dp(12), animate=False)
        Clock.schedule_once(reveal, .1)

    def _open(self, target):
        if self.manager is not None:
            if (target in (config.SCREEN_CASHBOOK, config.SCREEN_STATISTICS)
                    and self.manager.has_screen(config.SCREEN_EARNINGS)):
                self.manager.get_screen(config.SCREEN_EARNINGS).select_tab(target)
                target = config.SCREEN_EARNINGS
            if (target in (config.SCREEN_EVENTS, config.SCREEN_SHIFTPLAN, config.SCREEN_CHECKLIST)
                    and self.manager.has_screen(config.SCREEN_PLANNER)):
                self.manager.get_screen(config.SCREEN_PLANNER).select_tab(target)
                target = config.SCREEN_PLANNER
            self.manager.current = target

    def open_cash(self): self._open(config.SCREEN_CASH)
    def open_statistics(self): self._open(config.SCREEN_STATISTICS)
    def open_events(self): self._open(config.SCREEN_EVENTS)
    def open_cashbook(self): self._open(config.SCREEN_CASHBOOK)
    def open_checklist(self): self._open(config.SCREEN_CHECKLIST)
    def open_shiftplan(self): self._open(config.SCREEN_SHIFTPLAN)
    def open_articles(self): self._open(config.SCREEN_PRODUCTS)
    def open_settings(self): self._open(config.SCREEN_SETTINGS)
    def open_userguide(self): self._open(config.SCREEN_USE)
