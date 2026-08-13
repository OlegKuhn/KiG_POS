"""
=========================================================
KiG POS
=========================================================

Datei:
    splash_wrapper.py

Beschreibung:
    Wrapper für den SplashScreen.

Ermöglicht die Verwendung des bisherigen SplashScreens
innerhalb eines ScreenManagers, ohne den SplashScreen
selbst verändern zu müssen.

Version:
    1.0.0
=========================================================
"""

from kivy.uix.screenmanager import Screen

from screens.splash_screen import SplashScreen


class SplashWrapper(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.splash = SplashScreen()

        self.add_widget(
            self.splash
        )

    # ---------------------------------------------

    @property
    def on_finished(self):
        return self.splash.on_finished

    @on_finished.setter
    def on_finished(self, callback):
        self.splash.on_finished = callback

    # ---------------------------------------------

    def run_startup(self):

        self.splash.run_startup()