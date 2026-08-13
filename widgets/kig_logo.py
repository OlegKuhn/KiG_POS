"""
=========================================================
KiG POS
=========================================================

Datei:
    kig_logo.py

Beschreibung:
    Eigenes Widget zur Anzeige des KiG-Vereinslogos.

Dieses Widget wird später verwendet auf:

    • SplashScreen
    • HomeScreen
    • Einstellungen
    • Statistik
    • Druckvorschau

Das Logo wird immer mit den gleichen
Abmessungen und Proportionen dargestellt.

Version:
    0.1.0

Build:
    0001
=========================================================
"""

from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.uix.image import Image

import config
import theme


class KiGLogo(Image):
    """
    Eigenes Widget zur Darstellung des Vereinslogos.

    Im dunklen Modus wird automatisch die helle Logovariante
    (config.LOGO_PATH_DARK) verwendet, da das Original schwarze
    Linienkunst ist und auf dunklem Grund sonst kaum sichtbar wäre.
    """

    # Maximale Größe des Logos
    logo_size = NumericProperty(config.SPLASH_LOGO_SIZE)

    # Bildquelle. Wird von __init__() bei jeder neuen Instanz anhand
    # des AKTUELLEN Farbmodus gesetzt, sofern nicht explizit
    # übergeben - als Klassenattribut eingefroren würde das einen
    # späteren Moduswechsel nicht mitbekommen.
    logo_source = StringProperty(str(config.LOGO_PATH))

    def __init__(self, **kwargs):
        """
        Initialisiert das Logo.
        """

        kwargs.setdefault("logo_source", self._default_source())

        super().__init__(**kwargs)

        self.source = self.logo_source

    @staticmethod
    def _default_source():

        if theme.get_mode() == "dark":
            return str(config.LOGO_PATH_DARK)

        return str(config.LOGO_PATH)

        # Größe wird manuell gesetzt
        self.size_hint = (None, None)

        self.size = (self.logo_size, self.logo_size)

        # Bild zentrieren
        self.fit_mode = "contain"

        # Bild zentrieren
        self.mipmap = True

    # -----------------------------------------------------

    def set_logo_size(self, size: int):
        """
        Ändert die Größe des Logos.

        Parameter
        ---------
        size : int
            Größe in Pixel.
        """

        self.logo_size = size

        self.size = (
            size,
            size
        )

    # -----------------------------------------------------

    def reset_size(self):
        """
        Setzt die Standardgröße aus der config.py.
        """

        self.set_logo_size(config.SPLASH_LOGO_SIZE)