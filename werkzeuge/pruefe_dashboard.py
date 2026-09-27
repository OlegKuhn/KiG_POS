"""Dashboard mit isolierter Datenbank: Filtergrenzen, Summen, Navigation und Layout."""
from pathlib import Path
import sys
import tempfile
from datetime import date, timedelta
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.config import Config
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '900')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import NoTransition
from kivy.metrics import dp
import storage, theme, config
from database import DatabaseManager
from dashboard_data import dashboard_snapshot


class DashboardCheck(App):
    def build(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix='kig-dashboard-')
        storage.data_dir = lambda: Path(self.sandbox.name)
        self.db = DatabaseManager()
        today = date.today()
        empty = dashboard_snapshot(self.db, today)
        assert not empty['events'] and not empty['shifts'] and not empty['tasks']
        assert empty['income'] == empty['expenses'] == 0
        ids = []
        for offset in (-2, 0, 2, 4, 6):
            day = (today + timedelta(days=offset)).isoformat()
            ids.append(self.db.add_event(f'Testveranstaltung {offset}', 'Testort', '', day, day))
        self.db.add_event('Kein Event: Testtermin', '', '', today.isoformat(), today.isoformat(), entry_type='APPOINTMENT')
        for event in ids:
            plan = self.db.add_shift_plan(event)
            shift = self.db.add_shift(plan, 'Test: Ausschank', start_time='18:00', end_time='20:00', needed=2)
            self.db.add_shift_helper(shift, 'Testhelfer')
            filled = self.db.add_shift(plan, 'Voll besetzt', needed=1)
            self.db.add_shift_helper(filled, 'Testhelfer')
        checklist = self.db.add_checklist('Test: Vorbereitung')
        self.db.add_checklist_item(checklist, 'Test: Material bereitstellen', deadline=today.isoformat(), responsible='Testperson')
        self.db.add_checklist_item(checklist, 'Test: Ohne Frist')
        done = self.db.add_checklist_item(checklist, 'Bereits erledigt')
        self.db.update_checklist_item(done, done=True)
        first = today.replace(day=1)
        self.db.add_cash_book_entry(first.isoformat(), income=100, expenses=20, closing_balance=80)
        self.db.add_cash_book_entry(first.isoformat(), opening_balance=80, income=10.25, expenses=2.10, closing_balance=88.15)
        self.db.add_cash_book_entry((first-timedelta(days=1)).isoformat(), income=999, closing_balance=999)
        data = dashboard_snapshot(self.db, today)
        assert [e['id'] for e in data['events']] == ids[1:4]
        assert len(data['shifts']) == 4 and all(s['missing'] == 1 for s in data['shifts'])
        assert len(data['tasks']) == 2 and data['tasks'][0]['deadline'] == today.isoformat()
        assert len(data['monthly']) == 1
        assert data['income'] == Decimal('110.25') and data['expenses'] == Decimal('22.10')
        # Tagesumsatz stammt ausschließlich aus Verkäufen, nicht dem Kassenbuch.
        assert data['daily_revenue'] == 0
        self.db.save_sale(None, 'BAR', 99, 0, 99, 99, 0, [])
        yesterday = today - timedelta(days=1)
        self.db.cursor.execute('UPDATE sales SET sale_date = ?',
                               (yesterday.strftime(config.DATE_FORMAT),))
        self.db.commit()
        assert dashboard_snapshot(self.db, today)['daily_revenue'] == 0
        self.db.save_sale(None, 'BAR', 12.50, 0, 12.50, 20, 7.50, [])
        self.db.save_sale(None, 'KARTE', 4.25, 0, 4.25, 4.25, 0, [])
        self.db.save_sale(None, 'BAR', -2.50, 0, -2.50, -2.50, 0, [])
        assert dashboard_snapshot(self.db, today)['daily_revenue'] == 14.25
        assert dashboard_snapshot(self.db, yesterday)['daily_revenue'] == 99
        tomorrow_month = (first.replace(day=28)+timedelta(days=4)).replace(day=1)
        assert dashboard_snapshot(self.db, tomorrow_month)['income'] == 0
        print('DASHBOARD_DATA_OK: Events, Besetzung, Aufgaben, Monatsgrenzen und Summen', flush=True)
        self.cases = iter((('light',1280,900), ('dark',1280,900), ('light',390,844)))
        self.box = BoxLayout()
        self.layout = None
        self.output = Path(__file__).resolve().parents[1] / 'berichte/design-vorschau'
        self.output.mkdir(parents=True, exist_ok=True)
        Clock.schedule_once(self.next_case, 0)
        return self.box

    def next_case(self, *_):
        case = next(self.cases, None)
        if self.layout:
            self.layout.home_screen.stop()
            self.layout.header.stop()
        if case is None:
            print('DASHBOARD_UI_OK: Hell/Dunkel, schmal, Header, Ziele, Aktualisierung und Uhr', flush=True)
            self.stop()
            return
        self.mode, self.width, height = case
        theme.set_mode(self.mode)
        Window.size = (self.width, height)
        theme.set_orientation('portrait' if self.width < height else 'landscape')
        from layouts.main_layout import MainLayout
        self.box.clear_widgets()
        self.layout = MainLayout()
        self.layout.screen_manager.transition = NoTransition()
        self.box.add_widget(self.layout)
        Clock.schedule_once(self.verify, 1)

    def verify(self, *_):
        home = self.layout.home_screen
        assert home.snapshot['daily_revenue'] == 14.25
        assert home.metric_values['revenue'].text == '14,25 €'
        self.db.save_sale(None, 'BAR', 1, 0, 1, 1, 0, [])
        self.layout.refresh_revenue()
        assert home.metric_values['revenue'].text == '15,25 €'
        self.db.save_sale(None, 'BAR', -1, 0, -1, -1, 0, [])
        self.layout.refresh_revenue()
        header = self.layout.header
        assert header.height == dp(86)
        assert header.logo.source == str(config.LOGO_PATH)
        assert header.event_container.parent is None and header.status_container.parent is None
        assert header.navigation.right <= header.right + 1
        assert abs(header.navigation.right - (header.right - dp(12))) < 2
        assert header.logo_container.right <= header.navigation.x + 1
        assert home.snapshot['income'] == Decimal('110.25')
        # Einzelne Dashboard-Zeilen öffnen ihre konkrete Auswahl.
        for card, key, target, selection, id_key in (
                (home.event_card, 'events', config.SCREEN_EVENTS, 'selected_entry_id', 'id'),
                (home.shift_card, 'shifts', config.SCREEN_SHIFTPLAN, 'selected_plan_id', 'plan_id'),
                (home.task_card, 'tasks', config.SCREEN_CHECKLIST, 'selected_checklist_id', 'checklist_id')):
            for index in range(len(home.snapshot[key])):
                item = home.snapshot[key][index]
                list(reversed(card.rows.children))[index].dispatch('on_release')
                screen = self.layout.get_screen(target)
                assert self.layout.screen_manager.current == config.SCREEN_PLANNER
                assert self.layout.planner_screen.tab_manager.current == target
                assert getattr(screen, selection) == item[id_key]
                self.layout.show_home()
        for card, target in ((home.event_card, config.SCREEN_EVENTS), (home.shift_card, config.SCREEN_SHIFTPLAN),
                             (home.task_card, config.SCREEN_CHECKLIST), (home.month_card, config.SCREEN_CASHBOOK)):
            assert card.right <= home.right + 1
            card.open_button.dispatch('on_release')
            assert self.layout.get_screen(target) is self.layout.screen_manager.current_screen.tab_manager.current_screen
            assert home._clock_event is None
            header.logo.dispatch('on_press')
            assert self.layout.screen_manager.current == config.SCREEN_HOME
            assert home._clock_event is not None
        # Keine zusätzlichen Timer durch erneuten Eintritt.
        timer = home._clock_event
        home.on_pre_enter()
        assert home._clock_event is timer
        Clock.schedule_once(self.capture, .6)

    def capture(self, *_):
        from widgets.dashboard import ProgressTrack
        home = self.layout.home_screen
        bars = [w for w in home.shift_card.walk(restrict=True) if isinstance(w, ProgressTrack)]
        assert bars and all(w.fraction == .5 for w in bars)
        money_bars = [w.fraction for w in home.month_card.walk(restrict=True) if isinstance(w, ProgressTrack)]
        assert len(money_bars) == 2 and 1 in money_bars
        assert any(abs(value - 22.10 / 110.25) < .001 for value in money_bars)
        assert len(home.event_card.rows.children) == 3
        self.layout.export_to_png(str(self.output / f'dashboard-{self.mode}-{self.width}.png'))
        if self.width == 1280:
            self.layout.home_screen.scroll.scroll_y = 0
            Clock.schedule_once(self.capture_bottom, .3)
            return
        Clock.schedule_once(self.next_case, .1)

    def capture_bottom(self, *_):
        self.layout.export_to_png(str(self.output / f'dashboard-{self.mode}-details.png'))
        Clock.schedule_once(self.next_case, .1)

    def on_stop(self):
        if getattr(self, 'layout', None):
            self.layout.home_screen.stop()
        self.db.close()
        self.sandbox.cleanup()


if __name__ == '__main__':
    DashboardCheck().run()
