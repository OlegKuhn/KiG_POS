"""Überschrift und horizontal scrollbar bleibende Aktionen in einer Zeile."""
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView


class TitleActions(BoxLayout):
    def __init__(self, title, actions, **kwargs):
        super().__init__(size_hint_y=None, height=dp(48), spacing=dp(12), **kwargs)
        self.actions = actions
        title.size_hint_y = 1
        title.shorten = True
        title.shorten_from = 'right'
        self.add_widget(title)
        self.action_scroll = ScrollView(do_scroll_y=False, size_hint_x=None, bar_width=dp(3))
        actions.size_hint = (None, 1)
        actions.bind(minimum_width=actions.setter('width'))
        self.action_scroll.add_widget(actions)
        self.add_widget(self.action_scroll)
        self.bind(width=self._fit)
        actions.bind(minimum_width=self._fit)
        self._fit()

    def _fit(self, *_):
        self.action_scroll.width = min(self.actions.minimum_width,
                                       max(dp(100), self.width - dp(172)))
