"""
=========================================================
KiG POS
=========================================================

Modul:
    M003.6

Datei:
    kig_progressbar.py

Beschreibung:
    Premium ProgressBar für KiG POS.

Version:
    1.0.0

Build:
    0001

Status:
    Entwicklung

=========================================================
"""

from kivy.clock import Clock

from kivy.graphics import (
    Color,
    RoundedRectangle
)

from kivy.properties import (
    NumericProperty,
    BooleanProperty
)

from widgets.kig_widget import KiGWidget

import theme


class KiGProgressBar(KiGWidget):
    """
    Premium ProgressBar
    """

    # =====================================================
    # Eigenschaften
    # =====================================================

    value = NumericProperty(0)

    maximum = NumericProperty(100)

    animated = BooleanProperty(True)

    animation_speed = NumericProperty(0.18)

    # Position des wandernden Glanzes
    highlight_offset = NumericProperty(-80)

    # =====================================================
    # Konstruktor
    # =====================================================

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # Zielwert der Animation

        self._target_value = 0

        # Timer

        self._progress_event = None

        self._highlight_event = None

        # =================================================
        # Canvas
        # =================================================

        with self.canvas.before:

            #
            # Schatten
            #

            Color(0, 0, 0, 0.12)

            self.shadow = RoundedRectangle(
                pos=(0, 0),
                size=(0, 0),
                radius=[theme.PROGRESS_RADIUS]
            )

            #
            # Hintergrund
            #

            Color(*theme.PROGRESS_BACKGROUND)

            self.background = RoundedRectangle(
                pos=(0, 0),
                size=(0, 0),
                radius=[theme.PROGRESS_RADIUS]
            )

        with self.canvas:

            #
            # Orange Balken
            #

            Color(*theme.PRIMARY_ORANGE)

            self.progress = RoundedRectangle(
                pos=(0, 0),
                size=(0, 0),
                radius=[theme.PROGRESS_RADIUS]
            )

            #
            # Glanzstreifen
            #

            Color(1, 1, 1, 0.22)

            self.highlight = RoundedRectangle(
                pos=(0, 0),
                size=(0, 0),
                radius=[theme.PROGRESS_RADIUS]
            )

        # =================================================
        # Events
        # =================================================

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            value=self.update_canvas
        )

        # Wandernden Glanz starten

        self._highlight_event = Clock.schedule_interval(
            self._animate_highlight,
            1 / 60
        )

        # Erste Darstellung

        self.update_canvas()

    # =====================================================
    # Canvas aktualisieren
    # =====================================================

    def update_canvas(self, *args):
        """
        Aktualisiert sämtliche Zeichenobjekte der ProgressBar.
        """

        #
        # Schatten
        #

        self.shadow.pos = (
            self.x,
            self.y - 2
        )

        self.shadow.size = (
            self.width,
            self.height
        )

        #
        # Hintergrund
        #

        self.background.pos = (
            self.x,
            self.y
        )

        self.background.size = (
            self.width,
            self.height
        )

        #
        # Fortschritt berechnen
        #

        if self.maximum <= 0:
            progress_width = 0

        else:
            progress_width = (
                self.width *
                max(
                    0,
                    min(
                        self.value / self.maximum,
                        1
                    )
                )
            )

        #
        # Orange Balken
        #

        self.progress.pos = (
            self.x,
            self.y
        )

        self.progress.size = (
            progress_width,
            self.height
        )

        #
        # Highlight
        #

        highlight_width = min(
            60,
            progress_width * 0.40
        )

        self.highlight.pos = (
            self.x + self.highlight_offset,
            self.y + self.height * 0.58
        )

        self.highlight.size = (
            max(0, highlight_width),
            self.height * 0.18
        )

    # =====================================================
    # Fortschrittsanimation
    # =====================================================

    def _animate_progress(self, dt):
        """
        Animiert den Fortschritt weich zum Zielwert.
        """

        difference = self._target_value - self.value

        #
        # Ziel erreicht
        #

        if abs(difference) < 0.2:

            self.value = self._target_value

            if self._progress_event is not None:

                self._progress_event.cancel()
                self._progress_event = None

            return False

        #
        # Weiche Bewegung
        #

        self.value += difference * self.animation_speed

        return True

    # =====================================================
    # Wandernder Glanz
    # =====================================================

    def _animate_highlight(self, dt):
        """
        Animiert den Lichtreflex.
        """

        progress_width = self.progress.size[0]

        #
        # Kein sichtbarer Fortschritt
        #

        if progress_width <= 0:

            self.highlight.pos = (
                self.x,
                self.y
            )

            self.highlight.size = (
                0,
                0
            )

            return True

        #
        # Geschwindigkeit
        #

        self.highlight_offset += 90 * dt

        #
        # Von vorne beginnen
        #

        if self.highlight_offset > progress_width:

            self.highlight_offset = -60

        #
        # Darstellung aktualisieren
        #

        self.update_canvas()

        return True

    # =====================================================
    # Fortschritt setzen
    # =====================================================

    def set_value(self, value):
        """
        Setzt einen neuen Fortschrittswert.
        """

        #
        # Bereich begrenzen
        #

        value = max(
            0,
            min(
                value,
                self.maximum
            )
        )

        #
        # Ohne Animation
        #

        if not self.animated:

            self.value = value
            return

        #
        # Zielwert merken
        #

        self._target_value = value

        #
        # Animation bereits aktiv?
        #

        if self._progress_event is None:

            self._progress_event = Clock.schedule_interval(
                self._animate_progress,
                1 / 60
            )

    # =====================================================
    # Fortschritt zurücksetzen
    # =====================================================

    def reset(self):
        """
        Setzt die ProgressBar zurück.
        """

        #
        # Laufende Animation stoppen
        #

        if self._progress_event is not None:

            self._progress_event.cancel()
            self._progress_event = None

        #
        # Werte zurücksetzen
        #

        self._target_value = 0
        self.highlight_offset = -80
        self.value = 0

        #
        # Darstellung aktualisieren
        #

        self.update_canvas()

    # =====================================================
    # Fortschritt abschließen
    # =====================================================

    def complete(self):
        """
        Setzt die ProgressBar auf 100 %.
        """

        self.set_value(self.maximum)

    # =====================================================
    # Animationen stoppen
    # =====================================================

    def stop(self):
        """
        Stoppt alle laufenden Animationen.
        """

        if self._progress_event is not None:

            self._progress_event.cancel()
            self._progress_event = None

        if self._highlight_event is not None:

            self._highlight_event.cancel()
            self._highlight_event = None

    # =====================================================
    # Widget wird entfernt
    # =====================================================

    def on_parent(self, instance, parent):
        """
        Stoppt Timer automatisch,
        wenn das Widget entfernt wird.
        """

        if parent is None:

            self.stop()