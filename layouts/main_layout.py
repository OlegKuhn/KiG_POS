"""
=========================================================
KiG POS
=========================================================

Modul:
    M001.0

Datei:
    main_layout.py

Beschreibung:
    Hauptlayout der Anwendung.

Enthält:

    • HeaderBar
    • ScreenManager
    • FooterBar

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager

from kivy.graphics import Color, Rectangle

import config
import theme

from database import DatabaseManager

from widgets.common.confirm_popup import ConfirmPopup
from widgets.kig_headerbar import KiGHeaderBar
from widgets.kig_footerbar import KiGFooterBar

from screens.home_screen import HomeScreen
from screens.cash_screen import CashScreen
from screens.cash_book_screen import CashBookScreen
from screens.checklist_screen import ChecklistScreen
from screens.shift_plan_screen import ShiftPlanScreen
from screens.events_screen import EventsScreen
from screens.products_screen import ProductsScreen
from screens.statistics_screen import StatisticsScreen
from screens.settings_screen import SettingsScreen
from screens.userguide_screen import UserguideScreen

class MainLayout(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.bind(
            pos=self._update_background,
            size=self._update_background
        )

        with self.canvas.before:
            Color(*theme.BACKGROUND)

            self.background = Rectangle()

        self.db = DatabaseManager()

        #
        # Header
        #

        self.header = KiGHeaderBar()
        self.header.set_home_callback(
            self.show_home
        )
        self.header.set_event_name(
            "KiG POS"
        )

        # Der Wahlspruch steht auf dem Telefon nicht: Dort bricht er
        # zweizeilig um und drückt den Namen an den oberen Rand. Auf
        # den zwei Zeilen, die er kostet, steht sonst eine Kachelreihe.
        self.header.set_event_info(
            "" if theme.is_narrow()
            else "Gemeinsam feiern. Gemeinsam stark."
        )

        self.header.set_revenue(self.db.get_daily_revenue())

        #
        # ScreenManager
        #

        self.screen_manager = ScreenManager()
        self.screen_manager.size_hint = (1, 1)


        self.home_screen = HomeScreen(
            name=config.SCREEN_HOME
        )
        self.cash_screen = CashScreen(
            name=config.SCREEN_CASH,
            revenue_changed_callback=self.refresh_revenue
        )

        self.events_screen = EventsScreen(
            name=config.SCREEN_EVENTS
        )

        self.cash_book_screen = CashBookScreen(
            name=config.SCREEN_CASHBOOK
        )

        self.checklist_screen = ChecklistScreen(
            name=config.SCREEN_CHECKLIST
        )

        self.shift_plan_screen = ShiftPlanScreen(
            name=config.SCREEN_SHIFTPLAN
        )

        self.products_screen = ProductsScreen(
            name=config.SCREEN_PRODUCTS
        )

        self.statistics_screen = StatisticsScreen(
            name=config.SCREEN_STATISTICS,
            revenue_changed_callback=self.refresh_revenue
        )

        self.settings_screen = SettingsScreen(
            name=config.SCREEN_SETTINGS
        )

        self.userguide_screen = UserguideScreen(
            name=config.SCREEN_USE
        )

        self.home_screen.size_hint = (1, 1)

        self.screen_manager.add_widget(self.home_screen)
        self.screen_manager.add_widget(self.cash_screen)
        self.screen_manager.add_widget(self.events_screen)
        self.screen_manager.add_widget(self.cash_book_screen)
        self.screen_manager.add_widget(self.checklist_screen)
        self.screen_manager.add_widget(self.shift_plan_screen)
        self.screen_manager.add_widget(self.products_screen)
        self.screen_manager.add_widget(self.statistics_screen)
        self.screen_manager.add_widget(self.settings_screen)
        self.screen_manager.add_widget(self.userguide_screen)

        #
        # Footer
        #

        self.footer = KiGFooterBar()

        self.footer.set_version(config.VERSION)

        self.footer.set_build(config.BUILD)

        # Ohne diese Zeile passiert beim Tippen auf "Programm beenden"
        # nichts - die Fußzeile bringt die Klicklogik zwar mit, kannte
        # bis hierher aber niemanden, den sie benachrichtigen könnte.
        self.footer.set_exit_callback(self.request_exit)

        #
        # Widgets
        #

        self.add_widget(
            self.header
        )

        self.add_widget(
            self.screen_manager
        )

        self.add_widget(
            self.footer
        )

    def _update_background(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

    def refresh_revenue(self):
        self.header.set_revenue(self.db.get_daily_revenue())

    def show_screen(self, screen_name):
        self.screen_manager.current = screen_name

    def show_home(self):
        self.screen_manager.current = config.SCREEN_HOME

    # =====================================================
    # Programm beenden
    # =====================================================

    def request_exit(self):
        """Fragt vor dem Beenden nach.

        Mitten in einer Veranstaltung wäre ein versehentlich
        geschlossenes Programm ärgerlich - die Schaltfläche sitzt
        dauerhaft am unteren Bildschirmrand und ist schnell getroffen.
        """

        ConfirmPopup(
            message="Soll KiG POS wirklich beendet werden?",
            title="Programm beenden",
            confirm_text="Beenden",
            on_confirm=self._exit_app,
        ).open()

    @staticmethod
    def _exit_app():

        app = App.get_running_app()

        if app is not None:
            app.stop()
