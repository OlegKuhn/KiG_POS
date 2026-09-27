"""Erträge: Kassenbuch und Statistik mit unveränderten Datenfunktionen."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from widgets.cash.design import SectionButton
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition

import config
import theme


class EarningsScreen(Screen):
    TABS = (
        ('Kassenbuch', config.SCREEN_CASHBOOK),
        ('Statistik', config.SCREEN_STATISTICS),
    )
    eigene_filter = True

    def __init__(self, cashbook, statistics, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical')
        tabs = BoxLayout(size_hint_y=None, height=dp(64),
                         spacing=dp(8), padding=(dp(16), dp(6)))
        self.filter_area = BoxLayout(orientation='vertical', size_hint_y=None, height=0)
        self.filter_area.bind(minimum_height=self.filter_area.setter('height'))
        self.tab_manager = ScreenManager(transition=NoTransition())
        self.buttons = {}
        for title, target in self.TABS:
            tone = 'sage'
            button = SectionButton(tone=tone, text=title, bold=True, font_size='16sp')
            button.bind(on_release=lambda _, name=target: self.select_tab(name))
            tabs.add_widget(button)
            self.buttons[target] = button
        for screen in (cashbook, statistics):
            self.tab_manager.add_widget(screen)
        self.tab_manager.bind(current=self._selection)
        root.add_widget(tabs)
        root.add_widget(self.tab_manager)
        root.add_widget(self.filter_area)
        self.add_widget(root)
        self._selection()

    def select_tab(self, name):
        self.tab_manager.current = name

    def _selection(self, *_):
        for name, button in self.buttons.items():
            active = name == self.tab_manager.current
            button.select(active)
        self._show_filter()

    def _show_filter(self):
        # Die Filter der aktiven Ansicht sitzen als Bildschirm-Fußleiste
        # unter dem Inhalt und klappen von dort nach oben auf.
        for old in self.filter_area.children[:]:
            old.zuklappen()
        self.filter_area.clear_widgets()
        self.filter_area.height = 0
        screen = self.tab_manager.current_screen
        bar = getattr(screen, 'filterleiste', None)
        if bar is not None and not getattr(screen, 'eigene_filter', False):
            if bar.parent is not None:
                bar.parent.remove_widget(bar)
            bar.zuklappen()
            bar.aktualisieren()
            self.filter_area.add_widget(bar)
            # Entfernen und Einhängen können im selben Layout-Zyklus
            # passieren. minimum_height bleibt dann unverändert und
            # löst die Bindung nach dem Zurücksetzen auf 0 nicht aus.
            self.filter_area.height = bar.height

    def _forward(self, event):
        screen = self.tab_manager.current_screen
        if screen is not None:
            screen.dispatch(event)

    def on_pre_enter(self, *args):
        self._forward('on_pre_enter')
        self._show_filter()

    def on_enter(self, *args):
        self._forward('on_enter')

    def on_pre_leave(self, *args):
        for bar in self.filter_area.children:
            bar.zuklappen()
        self._forward('on_pre_leave')

    def on_leave(self, *args):
        self._forward('on_leave')
