"""Planner-Interaktionen und Layout mit isolierten Testdaten prüfen."""
import sys
import tempfile
from pathlib import Path
from datetime import date, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.config import Config
Config.set('graphics', 'width', '1440')
Config.set('graphics', 'height', '1000')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import NoTransition
import storage, theme, config
from database import DatabaseManager


class PlannerCheck(App):
    def build(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix='kig-planner-test-')
        storage.data_dir = lambda: Path(self.sandbox.name)
        self.db = DatabaseManager()
        today = date.today()
        self.event_id = self.db.add_event('Test: Herbstfest', 'Vereinsheim', 'Testverein',
                                        today.isoformat(), (today + timedelta(days=2)).isoformat())
        self.plan_id = self.db.add_shift_plan(self.event_id)
        shift = self.db.add_shift(self.plan_id, 'Test: Ausschank', '18:00', '22:00', needed=3)
        self.db.add_shift_helper(shift, 'Testperson')
        checklist = self.db.add_checklist('Test: Vorbereitung')
        self.db.add_checklist_item(checklist, 'Test: Material',
                                   deadline=(today - timedelta(days=1)).isoformat())
        for offset in (0, 3, 7):
            day = (today + timedelta(days=offset)).isoformat()
            self.db.add_event('Test: Vorbereitung', '', '', day, day, entry_type='APPOINTMENT')
        from layouts.main_layout import MainLayout
        self.layout = MainLayout()
        self.layout.screen_manager.transition = NoTransition()
        self.layout.show_screen(config.SCREEN_EVENTS)
        self.screen = self.layout.events_screen
        self.output = Path('berichte/design-vorschau')
        self.output.mkdir(parents=True, exist_ok=True)
        Clock.schedule_once(self.check, 1)
        return self.layout

    def check(self, *_):
        screen = self.screen
        entry = next(e for e in screen.entries if e['id'] == self.event_id)
        screen.select_entry(entry)
        assert screen.selected_entry_id == self.event_id
        assert entry in screen.entries_on(date.today() + timedelta(days=1))
        screen.open_selected_shifts(entry)
        assert self.layout.planner_screen.tab_manager.current == config.SCREEN_SHIFTPLAN
        assert self.layout.shift_plan_screen.selected_plan_id == self.plan_id
        self.layout.show_screen(config.SCREEN_EVENTS)
        screen.open_checklists()
        assert self.layout.planner_screen.tab_manager.current == config.SCREEN_CHECKLIST
        self.layout.show_screen(config.SCREEN_EVENTS)
        screen.select_day(date.today() + timedelta(days=90))
        assert screen.selected_entry_id is None
        screen.show_today()
        screen.select_entry(entry)
        current = (screen.visible_year, screen.visible_month)
        screen.next_month()
        screen.previous_month()
        assert (screen.visible_year, screen.visible_month) == current
        Clock.schedule_once(self.capture, .8)

    def capture(self, *_):
        assert self.screen.main_row.orientation == 'horizontal'
        from widgets.planner_overview import shift_problems, checklist_problems
        assert checklist_problems(self.db) == (1, 0)
        assert shift_problems(dict(task='Bar', besetzt=1, needed=2, start_time='18:00', end_time='02:00')) == ['Unterbesetzt']
        assert shift_problems(dict(task='Bar', besetzt=2, needed=2, start_time='18:00', end_time='02:00')) == []
        assert 'Uhrzeit prüfen' in shift_problems(dict(task='Bar', besetzt=2, needed=2, start_time='25:00', end_time=''))
        warning = next(w for w in self.screen.summary_bodies[2].children if hasattr(w, 'warning'))
        assert warning.warning and tuple(warning.color) == tuple(theme.ERROR)
        shifts_panel = self.screen.summary_bodies[2].parent.parent
        assert abs(self.screen.detail_panel.x - shifts_panel.x) < 1
        assert abs(self.screen.detail_panel.width - shifts_panel.width) < 1
        assert len(self.screen.toolbar.children) == 2
        self.layout.export_to_png(str(self.output / 'planner-rustikal.png'))
        Window.size = (dp(760), dp(1000))
        Clock.schedule_once(self.narrow, .8)

    def narrow(self, *_):
        assert self.screen.main_row.orientation == 'vertical'
        self.layout.export_to_png(str(self.output / 'planner-rustikal-schmal.png'))
        # Editor bleibt über den bestehenden Speicherweg angebunden.
        class Popup:
            def dismiss(self):
                pass
        self.screen.save_entry(Popup(), date.today(), None, 'Termin', 'Test: neuer Termin')
        assert any(e['name'] == 'Test: neuer Termin' for e in self.screen.entries)
        print('PLANNER_OK: Auswahl, mehrtägige Events, Navigation, Monatswechsel, Speichern, Layout', flush=True)
        self.stop()

    def on_stop(self):
        self.db.close()
        self.sandbox.cleanup()


if __name__ == '__main__':
    PlannerCheck().run()
