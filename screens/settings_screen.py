"""
=========================================================
KiG POS
=========================================================

Datei:
    settings_screen.py

Beschreibung:
    Einstellungen der Anwendung.

    • Farbmodus: hell oder dunkel (siehe theme.py /
      KiGPOS.apply_theme_mode)
    • Bildschirmausrichtung: Quer- oder Hochformat (siehe
      theme.set_orientation / KiGPOS.apply_orientation)

    Beide Einstellungen werden in der Datenbank gespeichert und
    beim nächsten Start wieder angewendet.

Version:
    2.1.0
=========================================================
"""

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


class SettingsOptionButton(Button):
    """Auswählbare Kachel für eine Einstellung, im Stil von CategoryCard."""

    def __init__(self, label, value, callback, **kwargs):
        super().__init__(**kwargs)

        self.value = value
        self.callback = callback

        self.text = label
        self.font_size = "18sp"
        self.bold = True

        self.background_normal = ""
        self.background_down = ""

        self.size_hint_y = None
        self.height = dp(64)

        self.unselect()

        self.bind(on_release=lambda *_args: self.callback(self.value))

    def select(self):

        self.background_color = theme.PRIMARY_ORANGE
        self.color = theme.TEXT_WHITE

    def unselect(self):

        self.background_color = theme.SURFACE
        self.color = theme.TEXT_PRIMARY


class SettingsScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        root = BoxLayout(padding=dp(theme.SCREEN_PADDING))

        panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING)
        )

        title = KiGLabel(text="Einstellungen")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(42)
        panel.add_widget(title)

        #
        # Farbmodus
        #

        panel.add_widget(self._section_label("Farbmodus"))

        mode_row = self._option_row()

        self.light_button = SettingsOptionButton(
            "☀  Hell", "light", self.select_mode
        )
        self.dark_button = SettingsOptionButton(
            "🌙  Dunkel", "dark", self.select_mode
        )

        if theme.get_mode() == "dark":
            self.dark_button.select()
        else:
            self.light_button.select()

        mode_row.add_widget(self.light_button)
        mode_row.add_widget(self.dark_button)
        panel.add_widget(mode_row)

        #
        # Bildschirmausrichtung
        #
        # Auf jedem Gerät vorhanden: Ein Tablet im Ständer ist quer
        # ebenso sinnvoll wie ein Telefon hochkant.

        panel.add_widget(self._section_label("Bildschirmausrichtung"))

        orientation_row = self._option_row()

        self.landscape_button = SettingsOptionButton(
            "Querformat", theme.ORIENTATION_LANDSCAPE, self.select_orientation
        )
        self.portrait_button = SettingsOptionButton(
            "Hochformat", theme.ORIENTATION_PORTRAIT, self.select_orientation
        )

        if theme.is_portrait():
            self.portrait_button.select()
        else:
            self.landscape_button.select()

        orientation_row.add_widget(self.landscape_button)
        orientation_row.add_widget(self.portrait_button)
        panel.add_widget(orientation_row)

        # Ohne diesen Hinweis wirkt es wie ein Fehler, wenn nach dem
        # Umschalten plötzlich das ganze Fenster seine Größe ändert.
        hint = KiGLabel(text=(
            "Im Hochformat stehen zusammengehörige Bereiche untereinander "
            "statt nebeneinander - gedacht für hochkant montierte "
            "Bildschirme und Telefone. Am Rechner wird das Fenster dabei "
            "passend angepasst, auf einem Gerät mit Drehsensor drehst du "
            "es einfach."
        ))
        hint.set_font_size(14)
        hint.set_alignment("left")
        hint.set_color(theme.TEXT_SECONDARY)
        hint.size_hint_y = None
        hint.height = dp(46)
        panel.add_widget(hint)

        # Restlicher Platz bleibt für künftige Einstellungen frei.
        panel.add_widget(BoxLayout())

        root.add_widget(panel)
        self.add_widget(root)

    # =====================================================
    # Bausteine
    # =====================================================

    @staticmethod
    def _section_label(text):

        label = KiGLabel(text=text)
        label.set_font_size(18)
        label.set_bold(True)
        label.set_alignment("left")
        label.set_color(theme.TEXT_PRIMARY)
        label.size_hint_y = None
        label.height = dp(30)

        return label

    @staticmethod
    def _option_row():

        return BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            spacing=dp(theme.ROW_SPACING)
        )

    # =====================================================
    # Auswahl
    # =====================================================

    def select_mode(self, mode):

        if mode == theme.get_mode():
            return

        app = App.get_running_app()

        if app is not None:
            app.apply_theme_mode(mode)

    def select_orientation(self, orientation):

        if orientation == theme.get_orientation():
            return

        app = App.get_running_app()

        if app is not None:
            app.apply_orientation(orientation)
