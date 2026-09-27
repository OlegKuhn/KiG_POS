"""Kopfnavigation zu vorhandenen Screens; keine neuen Datenfunktionen."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
import config
import theme


class NavigationButton(ButtonBehavior, BoxLayout):
    def __init__(self, title, icon, tone='orange', **kwargs):
        self.tone = tone
        super().__init__(orientation='vertical', size_hint_x=None, width=dp(106),
                         padding=dp(4), spacing=dp(4), **kwargs)
        with self.canvas.before:
            self.fill = Color(0, 0, 0, 0)
            self.shape = RoundedRectangle(radius=[dp(10)])
        self.image = Image(source=str(config.ASSETS_DIR / 'icons' / icon),
                           size_hint_y=None, height=dp(36), fit_mode='contain')
        self.label = Label(text=title, color=theme.HEADER_TEXT, font_size='12sp', bold=True)
        self.add_widget(self.image)
        self.add_widget(self.label)
        self.bind(pos=self._geometry, size=self._geometry)

    def _geometry(self, *_):
        self.shape.pos = (self.x + dp(12), self.y)
        self.shape.size = (max(0, self.width - dp(24)), dp(3))

    def select(self, active):
        color = theme.section_color(self.tone)
        self.fill.rgba = color if active else (0, 0, 0, 0)
        self.label.color = theme.HEADER_TEXT


class DesignNavigation(ScrollView):
    def __init__(self, manager, **kwargs):
        super().__init__(do_scroll_y=False, size_hint_y=None, height=dp(60), bar_width=dp(3), **kwargs)
        self.manager = manager
        row = BoxLayout(size_hint_x=None, spacing=dp(5))
        row.bind(minimum_width=row.setter('width'))
        self.buttons = {}
        for text, destination, icon in (
            ('Kasse', config.SCREEN_CASH, 'cash.png'),
            ('Planner', config.SCREEN_PLANNER, 'planner.png'),
            ('Artikel', config.SCREEN_PRODUCTS, 'articles.png'),
            ('Erträge', config.SCREEN_EARNINGS, 'cashbook.png'),
            ('Handbuch', config.SCREEN_USE, 'use.png'),
            ('Einstellungen', config.SCREEN_SETTINGS, 'settings.png'),
        ):
            tone = {config.SCREEN_CASH: 'orange', config.SCREEN_PLANNER: 'teal',
                    config.SCREEN_PRODUCTS: 'amber', config.SCREEN_EARNINGS: 'sage',
                    config.SCREEN_USE: 'blue', config.SCREEN_SETTINGS: 'slate'}[destination]
            button = NavigationButton(text, icon, tone=tone)
            button.bind(on_release=lambda _, target=destination: setattr(manager, 'current', target))
            self.buttons[destination] = button
            row.add_widget(button)
        self.add_widget(row)
        manager.bind(current=self._selection)
        self.bind(width=self._widths)
        self._selection()

    def _widths(self, *_):
        width = max(dp(106), (self.width - dp(5) * (len(self.buttons) - 1)) / len(self.buttons))
        for button in self.buttons.values():
            button.width = width

    def _selection(self, *_):
        for destination, button in self.buttons.items():
            active = self.manager.current == destination
            button.select(active)
