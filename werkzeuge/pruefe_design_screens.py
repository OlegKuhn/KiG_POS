"""Alle Hauptscreens mit separater Datenbank aufbauen und fotografieren."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.config import Config
Config.set('graphics', 'width', '1440')
Config.set('graphics', 'height', '960')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import NoTransition
import storage
import theme
import config
from database import DatabaseManager


class ScreensCheck(App):
    def build(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix='kig-screen-test-')
        storage.data_dir = lambda: Path(self.sandbox.name)
        theme.set_mode('light')
        self.output = Path(__file__).resolve().parents[1] / 'berichte' / 'design-vorschau'
        self.output.mkdir(parents=True, exist_ok=True)
        from layouts.main_layout import MainLayout
        self.layout = MainLayout()
        self.layout.screen_manager.transition = NoTransition()
        self.targets = iter((config.SCREEN_CASH, config.SCREEN_STATISTICS,
                             config.SCREEN_PRODUCTS, config.SCREEN_EVENTS,
                             config.SCREEN_CHECKLIST, config.SCREEN_SHIFTPLAN,
                             config.SCREEN_CASHBOOK, config.SCREEN_SETTINGS,
                             config.SCREEN_USE))
        Clock.schedule_once(self.next_screen, 0.5)
        return self.layout

    def next_screen(self, *_):
        target = next(self.targets, None)
        if target is None:
            earnings = self.layout.earnings_screen
            assert list(earnings.buttons) == [config.SCREEN_CASHBOOK, config.SCREEN_STATISTICS]
            nav = self.layout.navigation.buttons
            assert config.SCREEN_EARNINGS in nav
            assert nav[config.SCREEN_EARNINGS].image.source.endswith('cashbook.png')
            for name in earnings.buttons:
                assert name not in nav
                self.layout.home_screen._open(name)
                assert self.layout.screen_manager.current == config.SCREEN_EARNINGS
                assert earnings.tab_manager.current == name
                self.layout.show_home()
            nav[config.SCREEN_EARNINGS].dispatch('on_release')
            for name, button in earnings.buttons.items():
                button.dispatch('on_release')
                assert earnings.tab_manager.current == name
                if name == config.SCREEN_CASHBOOK:
                    assert self.layout.cash_book_screen.filterleiste.parent is earnings.filter_area
                else:
                    assert self.layout.statistics_screen.filterleiste.parent is earnings.filter_area
                bar = earnings.filter_area.children[0]
                bar.umschalten()
                assert bar.offen
                assert bar.inhalt.parent is not None
                bar.zuklappen()
                root = earnings.children[0]
                root.do_layout()
                assert earnings.filter_area.top <= earnings.tab_manager.y + 1
            print('ERTRAEGE_OK: Register, Filter, Header, Startseite und Wiedereinstieg', flush=True)
            planner = self.layout.planner_screen
            assert list(planner.buttons) == [config.SCREEN_EVENTS, config.SCREEN_SHIFTPLAN, config.SCREEN_CHECKLIST]
            assert config.SCREEN_PLANNER in self.layout.navigation.buttons
            for name in planner.buttons:
                assert name not in self.layout.navigation.buttons
                self.layout.home_screen._open(name)
                assert self.layout.screen_manager.current == config.SCREEN_PLANNER
                assert planner.tab_manager.current == name
                self.layout.show_home()
            self.layout.navigation.buttons[config.SCREEN_PLANNER].dispatch('on_release')
            for name, button in planner.buttons.items():
                button.dispatch('on_release')
                assert planner.tab_manager.current == name
                assert planner.tab_manager.current_screen.parent is planner.tab_manager
            print('PLANNER_OK: Register, Header, Startseite und Wiedereinstieg', flush=True)
            settings = self.layout.settings_screen
            for name, children in settings.settings_sections.items():
                settings.show_section(name)
                assert len(settings.settings_body.children) == len(children)
            settings.show_section('Darstellung')
            products = self.layout.products_screen
            for name in products.category_selector.values:
                products.category_selector.text = name
            products.category_selector.text = 'Alle Kategorien'
            assert products.selected_category is None
            print('SCREENS_OK: 9 Screens, 4 Einstellungsbereiche, Kategoriefilter', flush=True)
            self.stop()
            return
        self.layout.show_screen(target)
        self.target = target
        Clock.schedule_once(self.capture, 0.5)

    def capture(self, *_):
        self.layout.export_to_png(str(self.output / f'screen-{self.target}.png'))
        print(f'SCREEN_OK: {self.target}', flush=True)
        Clock.schedule_once(self.next_screen, 0.1)

    def on_stop(self):
        DatabaseManager().close()
        self.sandbox.cleanup()


if __name__ == '__main__':
    ScreensCheck().run()
