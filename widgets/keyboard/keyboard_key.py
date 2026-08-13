"""
=========================================================
KiG POS
=========================================================

Datei:
    keyboard_key.py

Beschreibung:
    Einzelne Taste der Bildschirmtastatur.
=========================================================
"""

from kivy.animation import Animation

import theme

from widgets.common.kig_action_tile import KiGActionTile


class KeyboardKey(KiGActionTile):
    """
    Einzelne Taste der Bildschirmtastatur.

    display_text:
        Sichtbare Beschriftung.

    key_value:
        Interner Wert der Taste.
    """

    def __init__(
            self,
            display_text,
            key_value,
            callback,
            width_factor=1.0,
            **kwargs
    ):

        # -------------------------------------------------
        # Werte VOR super() speichern
        # -------------------------------------------------

        self.key_value = key_value
        self.key_callback = callback

        # -------------------------------------------------
        # Basisklasse
        # -------------------------------------------------

        super().__init__(
            text=display_text,
            callback=self._key_released,
            **kwargs
        )

        # -------------------------------------------------
        # Größe
        # -------------------------------------------------

        self.size_hint_x = width_factor
        self.size_hint_y = 1

        # -------------------------------------------------
        # Farben
        # -------------------------------------------------

        self.normal_color = theme.CARD

        self.press_color = (
            1.0,
            0.82,
            0.60,
            1.0
        )

    # =====================================================
    # Taste ausgelöst
    # =====================================================

    def _key_released(self, *_args):
        """
        Führt die Tastenaktion aus und zeigt kurz
        die Touch-Rückmeldung an.
        """

        # -------------------------------------------------
        # Alte Animation stoppen
        # -------------------------------------------------

        Animation.cancel_all(
            self,
            "background_color"
        )

        # -------------------------------------------------
        # Ausgangsfarbe sicherstellen
        # -------------------------------------------------

        self.background_color = self.normal_color

        # -------------------------------------------------
        # Kurz blass orange
        # -------------------------------------------------

        animation = Animation(
            background_color=self.press_color,
            duration=0.06
        )

        # -------------------------------------------------
        # Danach zurück zur normalen Farbe
        # -------------------------------------------------

        animation += Animation(
            background_color=self.normal_color,
            duration=0.12
        )

        animation.start(self)

        # -------------------------------------------------
        # Internen Tastenwert melden
        # -------------------------------------------------

        if callable(self.key_callback):
            self.key_callback(
                self.key_value
            )