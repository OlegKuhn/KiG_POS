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
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

import demo
import theme

from widgets.common.confirm_popup import ConfirmPopup
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

        # Die Einstellungen wachsen mit jeder Funktion; ohne
        # Rollbereich ragt der unterste Abschnitt aus der Karte, sobald
        # das Fenster etwas kleiner ist.
        inhalt = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            size_hint_y=None,
        )
        inhalt.bind(minimum_height=inhalt.setter("height"))

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(8))
        scroll.add_widget(inhalt)
        panel.add_widget(scroll)

        #
        # Farbmodus
        #

        inhalt.add_widget(self._section_label("Farbmodus"))

        mode_row = self._option_row()

        # Sonne und Mond standen hier als Zeichen - Kivys Schrift
        # kennt beide nicht und setzte ein leeres Kaestchen davor.
        # Die Woerter sagen ohnehin alles.
        self.light_button = SettingsOptionButton(
            "Hell", "light", self.select_mode
        )
        self.dark_button = SettingsOptionButton(
            "Dunkel", "dark", self.select_mode
        )

        if theme.get_mode() == "dark":
            self.dark_button.select()
        else:
            self.light_button.select()

        mode_row.add_widget(self.light_button)
        mode_row.add_widget(self.dark_button)
        inhalt.add_widget(mode_row)

        #
        # Bildschirmausrichtung
        #
        # Auf jedem Gerät vorhanden: Ein Tablet im Ständer ist quer
        # ebenso sinnvoll wie ein Telefon hochkant.

        inhalt.add_widget(self._section_label("Bildschirmausrichtung"))

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
        inhalt.add_widget(orientation_row)

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
        inhalt.add_widget(hint)

        #
        # Demo-Modus
        #

        inhalt.add_widget(self._section_label("Demo"))

        demo_row = self._option_row()

        self.demo_button = SettingsOptionButton(
            "Demo beenden" if demo.ist_aktiv() else "Demo starten",
            "demo", lambda _wert: self.toggle_demo(),
        )

        if demo.ist_aktiv():
            self.demo_button.select()

        demo_row.add_widget(self.demo_button)

        # Zweite Haelfte bleibt leer, damit der Knopf dieselbe Breite
        # hat wie die Knoepfe darueber.
        demo_row.add_widget(BoxLayout())

        inhalt.add_widget(demo_row)

        demo_hint = KiGLabel(text=(
            "Im Demo-Modus arbeitet das Programm auf einer Kopie der "
            "Datenbank: Alles lässt sich ausprobieren, Verkäufe, Artikel "
            "und Listen werden gespeichert - aber nur in der Kopie. Die "
            "Akzentfarbe wird grün und oben steht DEMO.\n\n"
            "Beim Beenden des Demo-Modus wird die Kopie verworfen; es "
            "gilt wieder der Stand von vorher. Nach einem Programmstart "
            "läuft immer der normale Modus."
        ))
        demo_hint.set_font_size(14)
        demo_hint.set_alignment("left")
        demo_hint.set_color(theme.TEXT_SECONDARY)
        demo_hint.size_hint_y = None
        demo_hint.height = dp(76)
        inhalt.add_widget(demo_hint)

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

    # =====================================================
    # Demo-Modus
    # =====================================================

    def toggle_demo(self):
        """Startet den Demo-Modus oder verlässt ihn.

        Beides mit Rückfrage: Beim Start wird die Datenbank
        eingefroren, beim Beenden alles Ausprobierte verworfen - in
        beiden Fällen soll klar sein, was gleich passiert.
        """

        app = App.get_running_app()

        if app is None:
            return

        if demo.ist_aktiv():

            ConfirmPopup(
                title="Demo beenden",
                message=(
                    "Demo-Modus beenden?\n\n"
                    "Alles, was im Demo-Modus angelegt oder geändert "
                    "wurde, wird verworfen. Es gilt wieder der Stand "
                    "von vor dem Start."
                ),
                confirm_text="Beenden",
                on_confirm=lambda: app.apply_demo_mode(False),
            ).open()

            return

        ConfirmPopup(
            title="Demo starten",
            message=(
                "Demo-Modus starten?\n\n"
                "Der aktuelle Stand der Datenbank wird eingefroren. "
                "Ab dann arbeitest du auf einer Kopie - an den echten "
                "Daten ändert sich nichts."
            ),
            confirm_text="Starten",
            confirm_color=theme.SUCCESS,
            on_confirm=lambda: app.apply_demo_mode(True),
        ).open()
