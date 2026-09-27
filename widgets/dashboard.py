"""Farbige Dashboard-Karten mit vorhandenen Symbolen und echten Datenbalken."""
from pathlib import Path
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
import theme
from widgets.cash.design import CashButton


def accent(tone):
    return theme.section_color(tone)


class AccentPanel(BoxLayout):
    def __init__(self, tone=None, strength=.09, **kwargs):
        super().__init__(**kwargs)
        base = theme.CARD
        tint = accent(tone) if tone else base
        fill = tuple(a * strength + b * (1 - strength) for a, b in zip(tint, base))
        with self.canvas.before:
            self.fill_color = Color(*fill)
            self.background = RoundedRectangle(radius=[dp(10)])
            Color(*theme.CARD_BORDER[:3], .45)
            self.edge = Line(width=.7)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.background.pos, self.background.size = self.pos, self.size
        self.edge.rounded_rectangle = (*self.pos, *self.size, dp(10))


def icon_badge(name, tone, size=44):
    badge = AccentPanel(tone=tone, strength=.18, padding=dp(9),
                        size_hint=(None, None), size=(dp(size), dp(size)),
                        pos_hint={'center_y': .5})
    source = Path(__file__).resolve().parents[1] / 'assets/icons' / f'{name}.png'
    if theme.get_mode() == 'dark':
        # Die vorhandenen Symbole sind dunkel; helle Plaketten halten
        # sie auch auf dem dunklen Dashboard gut erkennbar.
        badge.fill_color.rgba = tuple(c * .35 + .65 for c in accent(tone)[:3]) + (1,)
    badge.add_widget(Image(source=str(source), fit_mode='contain'))
    return badge


class ProgressTrack(Widget):
    def __init__(self, fraction, tone, **kwargs):
        super().__init__(size_hint_y=None, height=dp(9), **kwargs)
        self.fraction = max(0, min(1, float(fraction)))
        with self.canvas:
            Color(*theme.CARD_BORDER[:3], .4)
            self.track = RoundedRectangle(radius=[dp(4)])
            Color(*accent(tone))
            self.fill = RoundedRectangle(radius=[dp(4)])
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _draw(self, *_):
        self.track.pos, self.track.size = self.pos, self.size
        self.fill.pos = self.pos
        self.fill.size = (self.width * self.fraction, self.height)


class DashboardLink(ButtonBehavior, AccentPanel):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_release=lambda *_: callback())
        self.bind(state=self._pressed)

    def _pressed(self, *_):
        self.fill_color.rgba = theme.TILE_PRESS_COLOR if self.state == 'down' else theme.CARD


def detail_row(orientation='horizontal', callback=None):
    cls = DashboardLink if callback else AccentPanel
    options = {'callback': callback} if callback else {}
    row = cls(orientation=orientation, size_hint_y=None,
                      padding=dp(10), spacing=dp(8), **options)
    row.bind(minimum_height=row.setter('height'))
    return row


class DashboardCard(AccentPanel):
    def __init__(self, title, target, navigate, tone, icon, subtitle, **kwargs):
        from screens.home_screen import text_label
        super().__init__(orientation='vertical', size_hint_y=None, height=dp(330),
                         padding=dp(12), spacing=dp(10), **kwargs)
        self.tone = tone
        self.head = AccentPanel(tone=tone, size_hint_y=None, height=dp(66), padding=dp(8), spacing=dp(10))
        self.badge = icon_badge(icon, tone)
        self.head.add_widget(self.badge)
        words = BoxLayout(orientation='vertical')
        self.title = text_label(title, size=18, bold=True, height=30)
        self.subtitle = text_label(subtitle, size=12, color=theme.TEXT_SECONDARY, height=22)
        words.add_widget(self.title)
        words.add_widget(self.subtitle)
        self.head.add_widget(words)
        self.open_button = CashButton(text='Öffnen', size_hint_x=None, width=dp(72), font_size='14sp', active=True, soft=True)
        self.open_button.bind(on_release=lambda *_: navigate(target))
        self.head.add_widget(self.open_button)
        self.add_widget(self.head)
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.rows = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=(0, 0, dp(4), 0))
        self.rows.bind(minimum_height=self.rows.setter('height'))
        self.scroll.add_widget(self.rows)
        self.add_widget(self.scroll)

    def compact(self, small):
        self.title.font_size = '16sp' if small else '18sp'
        self.title.height = dp(48 if small else 30)
        self.subtitle.opacity = 0 if small else 1
        self.subtitle.height = 0 if small else dp(22)
        self.badge.size = (dp(32 if small else 44), dp(32 if small else 44))
        self.head.spacing = dp(6 if small else 10)
        self.open_button.width = dp(62 if small else 72)

    def line(self, title, detail='', warning=False, callback=None):
        from screens.home_screen import text_label
        row = detail_row(callback=callback)
        if self.tone == 'lavender' and detail:
            marker = text_label('!', size=24, bold=True, color=theme.ERROR, height=36) if warning else icon_badge('checklist', self.tone, 34)
            marker.size_hint_x = None
            marker.width = dp(34)
            row.add_widget(marker)
        words = BoxLayout(orientation='vertical', size_hint_y=None)
        words.bind(minimum_height=words.setter('height'))
        words.add_widget(text_label(title, size=16, bold=True, color=theme.ERROR if warning else theme.TEXT_PRIMARY))
        if detail:
            words.add_widget(text_label(detail, size=13, color=theme.TEXT_SECONDARY))
        row.add_widget(words)
        self.rows.add_widget(row)
