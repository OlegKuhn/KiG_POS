"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    kig_logobutton.py

Beschreibung:
    Klickbares Vereinslogo.

Der KiGLogoButton erweitert das bestehende
KiGLogo um eine Button-Funktion.

Version:
    1.0.0

Build:
    0001

Status:
    Entwicklung

=========================================================
"""

from kivy.uix.behaviors import ButtonBehavior

from widgets.kig_logo import KiGLogo


class KiGLogoButton(ButtonBehavior, KiGLogo):
    """
    Klickbares Vereinslogo.
    """

    # =====================================================
    # Konstruktor
    # =====================================================

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        #
        # Callback
        #

        self.on_home = None

        #
        # Standardverhalten
        #

        self.always_release = True

        self.markup = False

        #
        # Bildgröße übernehmen
        #

        self.set_logo_size(self.logo_size)

    # =====================================================
    # Home-Callback setzen
    # =====================================================

    def set_home_callback(self, callback):
        """
        Setzt den Callback, der beim Anklicken
        des Logos ausgeführt wird.
        """

        self.on_home = callback

    # =====================================================
    # Home aufrufen
    # =====================================================

    def go_home(self):
        """
        Führt den Home-Callback aus.
        """

        if callable(self.on_home):

            self.on_home()

    # =====================================================
    # Logo angeklickt
    # =====================================================

    def on_press(self):
        """
        Wird beim Anklicken des Logos aufgerufen.
        """

        self.go_home()