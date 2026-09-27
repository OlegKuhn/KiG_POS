"""Gemeinsamer Planner mit bestehenden Kalender-, Schicht- und Aufgabenansichten."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from widgets.cash.design import SectionButton
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition

import config
import theme


class PlannerScreen(Screen):
    TABS = (
        ('Kalender', config.SCREEN_EVENTS),
        ('Schichtplan', config.SCREEN_SHIFTPLAN),
        ('Checkliste', config.SCREEN_CHECKLIST),
    )

    def __init__(self, calendar, shifts, checklist, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical')
        tabs = BoxLayout(size_hint_y=None, height=dp(64),
                         spacing=dp(8), padding=(dp(16), dp(6)))
        self.tab_manager = ScreenManager(transition=NoTransition())
        self.buttons = {}
        for title, target in self.TABS:
            tone = {config.SCREEN_EVENTS: 'teal', config.SCREEN_SHIFTPLAN: 'amber', config.SCREEN_CHECKLIST: 'lavender'}[target]
            button = SectionButton(tone=tone, text=title, bold=True, font_size='16sp')
            button.bind(on_release=lambda _, name=target: self.select_tab(name))
            tabs.add_widget(button)
            self.buttons[target] = button
        for screen in (calendar, shifts, checklist):
            self.tab_manager.add_widget(screen)
        self.tab_manager.bind(current=self._selection)
        root.add_widget(tabs)
        root.add_widget(self.tab_manager)
        self.add_widget(root)
        self._selection()

    def select_tab(self, name):
        self.tab_manager.current = name

    def _selection(self, *_):
        for name, button in self.buttons.items():
            active = name == self.tab_manager.current
            button.select(active)

    def _forward(self, event):
        # Der innere ScreenManager bleibt beim Verlassen bestehen. Deshalb
        # auch beim erneuten Öffnen die Daten der aktiven Ansicht auffrischen.
        screen = self.tab_manager.current_screen
        if screen is not None:
            screen.dispatch(event)

    def on_pre_enter(self, *args):
        self._forward('on_pre_enter')

    def on_enter(self, *args):
        self._forward('on_enter')

    def on_pre_leave(self, *args):
        self._forward('on_pre_leave')

    def on_leave(self, *args):
        self._forward('on_leave')
