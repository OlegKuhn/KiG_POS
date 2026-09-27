"""Kontrast- und Wechseltests ohne Zugriff auf Kassendaten."""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import theme


def contrast(a, b):
    def luminance(color):
        channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                    for v in color[:3]]
        return sum(v * weight for v, weight in zip(channels, (0.2126, 0.7152, 0.0722)))
    values = sorted((luminance(a), luminance(b)))
    return (values[1] + 0.05) / (values[0] + 0.05)


class DarkModeTests(unittest.TestCase):
    def tearDown(self):
        theme.set_accent('normal')
        theme.set_mode('light')

    def test_text_contrast(self):
        for accent in ('normal', 'demo'):
            theme.set_accent(accent)
            theme.set_mode('dark')
            for foreground in ('TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_LIGHT'):
                for background in ('CARD', 'SURFACE', 'ZEILE_ALT', 'HEADER_BACKGROUND',
                                   'CART_BACKGROUND', 'SELECTION_BACKGROUND', 'TILE_PRESS_COLOR'):
                    with self.subTest(accent=accent, foreground=foreground, background=background):
                        self.assertGreaterEqual(contrast(getattr(theme, foreground),
                                                        getattr(theme, background)), 4.5)
            for background in ('PRIMARY_ORANGE', 'PRIMARY_ORANGE_LIGHT', 'PRIMARY_ORANGE_DARK',
                               'SUCCESS', 'ERROR'):
                self.assertGreaterEqual(contrast(theme.TEXT_ON_ACCENT, getattr(theme, background)), 4.5)
            self.assertGreaterEqual(contrast(theme.INPUT_HINT, theme.SURFACE), 4.5)
            self.assertGreaterEqual(contrast(theme.BORDER_COLOR, theme.SURFACE), 3)

    def test_mode_switch_does_not_restore_light_press_color(self):
        theme.set_mode('dark')
        expected = theme.TILE_PRESS_COLOR
        theme.set_accent('demo')
        theme.set_accent('normal')
        self.assertEqual(theme.TILE_PRESS_COLOR, expected)
        theme.set_mode('light')
        self.assertEqual(theme.TEXT_ON_ACCENT, theme.TEXT_WHITE)
        self.assertEqual(theme.PRIMARY_ORANGE, theme._LIGHT_COLORS['PRIMARY_ORANGE'])
        self.assertEqual(theme.TILE_PRESS_COLOR, theme._LIGHT_COLORS['TILE_PRESS_COLOR'])

    def test_project_syntax(self):
        paths = list(ROOT.glob('*.py'))
        for folder in ('widgets', 'screens', 'layouts', 'werkzeuge'):
            paths.extend((ROOT / folder).rglob('*.py'))
        for path in paths:
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))


if __name__ == '__main__':
    if '--widgets' in sys.argv:
        sys.argv.remove('--widgets')
        from kivy.config import Config
        Config.set('graphics', 'width', '800')
        Config.set('graphics', 'height', '600')
        from kivy.base import EventLoop
        from widgets.common.rounded_input import RoundedInput
        from widgets.common.rounded_spinner import RoundedSpinner
        from widgets.common.kig_text_tile import KiGTextTile
        from widgets.common.numpad.numpad_button import NumpadButton
        from widgets.products.category_card import CategoryCard
        EventLoop.ensure_window()
        for mode in ('light', 'dark', 'light', 'dark'):
            theme.set_mode(mode)
            field = RoundedInput(text='Test', multiline=False)
            assert tuple(field.foreground_color) == theme.INPUT_TEXT
            spinner = RoundedSpinner(text='Kategorie', values=['Kategorie'])
            assert tuple(spinner.color) == theme.INPUT_TEXT
            tile = KiGTextTile(text='Artikel')
            tile.select()
            assert tuple(tile.background_color) == theme.SELECTION_BACKGROUND
            assert tuple(tile.border_color.rgba) == theme.PRIMARY_ORANGE
            tile.unselect()
            assert tuple(tile.background_color) == theme.CARD
            category = CategoryCard({'name': 'Getraenke'})
            category.select()
            assert tuple(category.color) == theme.TEXT_ON_ACCENT
            number = NumpadButton('7')
            if mode == 'dark':
                assert tuple(number.lbl_title.color) == theme.TEXT_PRIMARY
        print('WIDGETS_OK: Felder, Auswahl, Dropdown und Nummernblock')
    unittest.main()
