"""
=========================================================
KiG POS
=========================================================

Datei:
    main_screen.py

Beschreibung:
    Hauptscreen der Anwendung.

Enthält das MainLayout.

Version:
    1.0.0
=========================================================
"""

from kivy.uix.screenmanager import Screen

from layouts.main_layout import MainLayout


class MainScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.main_layout = MainLayout()

        self.add_widget(
            self.main_layout
        )