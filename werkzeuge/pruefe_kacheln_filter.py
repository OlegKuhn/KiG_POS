"""Vier Artikelspalten und reservierter Filterbereich mit isolierten Daten."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.config import Config
Config.set('graphics', 'width', '1440')
Config.set('graphics', 'height', '960')
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import NoTransition
import storage, config
from models.article import Article


class LayoutCheck(App):
    def build(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix='kig-layout-test-')
        storage.data_dir = lambda: Path(self.sandbox.name)
        from layouts.main_layout import MainLayout
        self.layout = MainLayout()
        self.layout.screen_manager.transition = NoTransition()
        self.output = Path('berichte/design-vorschau')
        Clock.schedule_once(self.prepare, 1)
        return self.layout

    def prepare(self, *_):
        self.layout.show_screen(config.SCREEN_CASH)
        self.panel = self.layout.cash_screen.left_panel.article_panel_widget
        names = ['Apfelschorle naturtrüb', 'Alkoholfreies Weizenbier', 'Cola', 'Mineralwasser spritzig']
        self.panel.set_articles([Article(i, 1, name, 2.5, 128) for i, name in enumerate(names)])
        Clock.schedule_once(self.tiles, .8)

    def tiles(self, *_):
        assert self.panel.grid.cols == 4
        for tile in self.panel.grid.children:
            assert tile.lbl_title.max_lines == 2 and not tile.lbl_title.shorten
            assert tile.lbl_stock.top < tile.category_marker.pos[1]
            assert tile.lbl_stock.y >= tile.lbl_price.top
            assert tile.lbl_stock.text_size_sp == 17
        self.layout.export_to_png(str(self.output / 'kasse-vier-spalten.png'))
        self.targets = iter((config.SCREEN_CASHBOOK, config.SCREEN_STATISTICS))
        self.next_screen()

    def next_screen(self, *_):
        self.target = next(self.targets, None)
        if self.target is None:
            print('LAYOUT_OK: Vier Spalten, Namensumbruch, Bestand und Filtergrenzen', flush=True)
            self.stop()
            return
        self.layout.show_screen(self.target)
        self.bar = self.layout.get_screen(self.target).filterleiste
        Clock.schedule_once(self.open_filter, .3)

    def open_filter(self, *_):
        manager = self.layout.earnings_screen.tab_manager
        self.content_geometry = (*manager.pos, *manager.size)
        self.closed_height = self.bar.height
        self.bar.aufklappen()
        Clock.schedule_once(self.filter_open, .6)

    def filter_open(self, *_):
        earnings = self.layout.earnings_screen
        assert earnings.tab_manager.y >= earnings.filter_area.top - 1
        assert earnings.filter_area.height >= self.bar.height
        assert earnings.tab_manager.y >= self.bar.top - 1
        assert (*earnings.tab_manager.pos, *earnings.tab_manager.size) == self.content_geometry
        assert self.bar.height == self.closed_height
        assert self.bar.inhalt_karte.top > earnings.filter_area.top
        assert self.bar.inhalt_karte.y >= self.bar.zeilen_karte.top
        assert self.bar.inhalt_karte.x >= self.bar.x
        assert abs(self.bar.inhalt_karte.right - self.bar.right) < 1
        assert self.bar.y >= self.layout.y
        self.layout.export_to_png(str(self.output / f'{self.target}-filter-offen.png'))
        self.layout.get_screen(self.target).filter_confirm_button.dispatch('on_release')
        assert not self.bar.offen
        if self.target == config.SCREEN_STATISTICS:
            self.layout.statistics_screen.children[0].scroll_y = 0
            Clock.schedule_once(self.statistics_bottom, .5)
        else:
            Clock.schedule_once(self.next_screen, .2)

    def statistics_bottom(self, *_):
        screen = self.layout.statistics_screen
        scroll = screen.children[0]
        root = scroll.children[0]
        panel = root.children[0]
        buttons = panel.children[0]
        assert buttons.to_window(*buttons.pos)[1] >= self.bar.to_window(self.bar.x, self.bar.top)[1]
        self.layout.export_to_png(str(self.output / 'statistics-bottom.png'))
        if not getattr(self, 'reentry_checked', False):
            self.reentry_checked = True
            self.layout.show_home()
            self.layout.show_screen(config.SCREEN_STATISTICS)
            Clock.schedule_once(self.statistics_bottom, .5)
        else:
            Clock.schedule_once(self.next_screen, .2)

    def on_stop(self):
        self.layout.db.close()
        self.sandbox.cleanup()


if __name__ == '__main__':
    LayoutCheck().run()
