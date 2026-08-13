"""
=========================================================
KiG POS
=========================================================

Modul:
    M003.7

Datei:
    splash_screen.py

Beschreibung:
    Splash Screen von KiG POS.

Version:
    0.2.0

Build:
    0002

Status:
    Entwicklung

=========================================================
"""

from kivy.graphics import (
    Color,
    Rectangle,
    Line
)

from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock

import config
import theme

from widgets.kig_logo import KiGLogo
from widgets.kig_label import KiGLabel
from widgets.kig_progressbar import KiGProgressBar


class SplashScreen(FloatLayout):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # ==================================================
        # Callback
        # ==================================================

        self.on_finished = None

        # ==================================================
        # Hintergrund
        # ==================================================

        with self.canvas.before:

            Color(*theme.BACKGROUND)

            self.background = Rectangle(
                pos=self.pos,
                size=self.size
            )

        # ==================================================
        # Logo
        # ==================================================

        self.logo = KiGLogo()

        self.logo.size_hint = (None, None)

        self.logo.width = theme.SPLASH_LOGO_WIDTH

        self.logo.height = theme.SPLASH_LOGO_WIDTH * 0.67

        self.logo.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_LOGO_CENTER_Y
        }

        self.add_widget(self.logo)

        # ==================================================
        # Titel
        # ==================================================

        self.title = KiGLabel()

        self.title.text = "KiG POS"

        self.title.set_font_size(theme.FONT_TITLE)

        self.title.set_bold(True)

        self.title.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_TITLE_CENTER_Y
        }

        self.add_widget(self.title)

        # ==================================================
        # Untertitel
        # ==================================================

        self.subtitle = KiGLabel()

        self.subtitle.text = (
            "Kassensystem für Vereinsveranstaltungen"
        )

        self.subtitle.set_font_size(
            theme.FONT_SUBTITLE
        )

        self.subtitle.set_color(
            theme.TEXT_SECONDARY
        )

        self.subtitle.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_SUBTITLE_CENTER_Y
        }

        self.add_widget(self.subtitle)

        # ==================================================
        # Trennlinie
        # ==================================================

        with self.canvas:

            Color(0.82, 0.82, 0.82, 1)

            self.separator_dark = Line(
                width=1.2,
                points=[]
            )

            Color(1, 1, 1, 0.8)

            self.separator_light = Line(
                width=1,
                points=[]
            )

        # ==================================================
        # Slogan
        # ==================================================

        self.slogan = KiGLabel()

        self.slogan.text = (
            "Gemeinsam feiern. Gemeinsam stark."
        )

        self.slogan.set_font_size(
            theme.FONT_NORMAL
        )

        self.slogan.set_color(
            theme.TEXT_SECONDARY
        )

        self.slogan.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_SLOGAN_CENTER_Y
        }

        self.add_widget(self.slogan)

        # ==================================================
        # ProgressBar
        # ==================================================

        self.progress = KiGProgressBar()

        self.progress.size_hint = (
            0.62,
            None
        )

        self.progress.height = 18

        self.progress.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_PROGRESS_CENTER_Y
        }

        self.add_widget(self.progress)

        # ==================================================
        # Status
        # ==================================================

        self.status = KiGLabel()

        self.status.text = "Starte KiG POS..."

        self.status.set_font_size(
            theme.FONT_STATUS
        )

        self.status.set_color(
            theme.TEXT_SECONDARY
        )

        self.status.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_STATUS_CENTER_Y
        }

        self.add_widget(self.status)

        # ==================================================
        # Version
        # ==================================================

        self.version = KiGLabel()

        self.version.text = (
            f"Version {config.VERSION} • "
            f"Build {config.BUILD}"
        )

        self.version.set_font_size(
            theme.FONT_VERSION
        )

        self.version.set_color(
            theme.TEXT_LIGHT
        )

        self.version.pos_hint = {
            "center_x": 0.5,
            "center_y": theme.SPLASH_VERSION_CENTER_Y
        }

        self.add_widget(self.version)

        # ==================================================
        # Layout aktualisieren
        # ==================================================

        self.bind(
            pos=self.update_layout,
            size=self.update_layout
        )

        self.update_layout()

    # =====================================================
    # Layout aktualisieren
    # =====================================================

    def update_layout(self, *args):
        """
        Aktualisiert alle gezeichneten Elemente des Splash Screens.
        """

        # -------------------------------------------------
        # Hintergrund
        # -------------------------------------------------

        self.background.pos = self.pos
        self.background.size = self.size

        # -------------------------------------------------
        # Trennlinie
        # -------------------------------------------------

        line_width = self.width * 0.72

        start_x = (self.width - line_width) / 2
        end_x = start_x + line_width

        line_y = self.height * theme.SPLASH_SEPARATOR_CENTER_Y

        #
        # Dunkle Linie
        #

        self.separator_dark.points = (
            start_x,
            line_y,
            end_x,
            line_y
        )

        #
        # Helle Linie
        #

        self.separator_light.points = (
            start_x,
            line_y - 1,
            end_x,
            line_y - 1
        )

        # -------------------------------------------------
        # Logo
        # -------------------------------------------------

        self.logo.width = theme.SPLASH_LOGO_WIDTH
        self.logo.height = (
            theme.SPLASH_LOGO_WIDTH * 0.67
        )

        # -------------------------------------------------
        # ProgressBar
        # -------------------------------------------------

        self.progress.height = 18

        # -------------------------------------------------
        # Fenstergröße speichern
        # -------------------------------------------------

        self.window_width = self.width
        self.window_height = self.height

    # =====================================================
    # Status ändern
    # =====================================================

    def set_status(self, text: str):
        """
        Aktualisiert den Statustext unter der ProgressBar.
        """

        self.status.text = text

    # =====================================================
    # Fortschritt ändern
    # =====================================================

    def set_progress(self, value: float):
        """
        Übergibt den Fortschritt an die KiGProgressBar.
        """

        self.progress.set_value(value)

    # =====================================================
    # Initialisierung vorbereiten
    # =====================================================

    def start_initialization(self):
        """
        Erstellt die Initialisierungsschritte.
        Der eigentliche Ablauf wird in Teil 4 gestartet.
        """

        self._current_step = 0

        self._startup_steps = [

            (
                5,
                "Starte KiG POS..."
            ),

            (
                15,
                "Lade Konfiguration..."
            ),

            (
                30,
                "Lade Theme..."
            ),

            (
                45,
                "Verbinde Datenbank..."
            ),

            (
                60,
                "Prüfe Standarddaten..."
            ),

            (
                75,
                "Lade Einstellungen..."
            ),

            (
                90,
                "Initialisiere Oberfläche..."
            ),

            (
                100,
                "KiG POS wird gestartet..."
            )

        ]

    # =====================================================
    # Nächster Initialisierungsschritt
    # =====================================================

    def _next_step(self, dt):
        """
        Führt den nächsten Initialisierungsschritt aus.
        """

        #
        # Sind alle Schritte abgeschlossen?
        #

        if self._current_step >= len(self._startup_steps):

            self.finish()

            return False

        #
        # Aktuellen Schritt laden
        #

        progress, status = self._startup_steps[self._current_step]

        #
        # Oberfläche aktualisieren
        #

        self.set_status(status)

        self.set_progress(progress)

        #
        # Nächsten Schritt vorbereiten
        #

        self._current_step += 1

        return True

    # =====================================================
    # Startvorgang starten
    # =====================================================

    def run_startup(self):
        """
        Startet den Splash Screen.
        """

        #
        # Initialisierung vorbereiten
        #

        self.start_initialization()

        #
        # Ersten Status sofort anzeigen
        #

        if self._startup_steps:

            progress, status = self._startup_steps[0]

            self.set_status(status)

            self.set_progress(progress)

            self._current_step = 1

        #
        # Timer starten
        #

        self._startup_event = Clock.schedule_interval(
            self._next_step,
            0.60
        )

    # =====================================================
    # Initialisierung abgeschlossen
    # =====================================================

    def finish(self):
        """
        Beendet den Splash Screen.
        """

        #
        # Timer stoppen
        #

        if hasattr(self, "_startup_event"):

            self._startup_event.cancel()

            self._startup_event = None

        #
        # Fortschritt abschließen
        #

        self.set_progress(100)

        #
        # Letzten Status anzeigen
        #

        self.set_status(
            "KiG POS erfolgreich gestartet."
        )

        self.canvas.clear()
        self.canvas.before.clear()
        self.canvas.after.clear()


        #
        # Callback aufrufen
        #

        if callable(self.on_finished):

            self.on_finished()