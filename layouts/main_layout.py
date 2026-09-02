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

from datetime import date

import config
import theme

from database import DatabaseManager

from widgets.common.confirm_popup import ConfirmPopup
from widgets.kig_headerbar import KiGHeaderBar

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
        # Der Wahlspruch steht auf dem Telefon nicht: Dort bricht er
        # zweizeilig um und drückt den Namen an den oberen Rand. Auf
        # den zwei Zeilen, die er kostet, steht sonst eine Kachelreihe.
        self.header.set_event_info(
            "" if theme.is_narrow()
            else "Gemeinsam feiern. Gemeinsam stark."
        )

        self.veranstaltung_anzeigen()

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
        # Widgets
        #
        #
        # Ohne Fusszeile: Sie trug Version, Buildnummer und "Programm
        # beenden" - eine Zeile, die auf jedem Bildschirm Platz kostete
        # und deren einzige Schaltflaeche man versehentlich traf. Alle
        # drei stehen jetzt in den Einstellungen.

        self.add_widget(
            self.header
        )

        self.add_widget(
            self.screen_manager
        )

        # Am unteren Rand, wo die Fusszeile stand: die Filterleiste des
        # gerade sichtbaren Bildschirms - zugeklappt eine Zeile, die
        # sagt, wonach gefiltert wird (siehe
        # widgets/common/filterleiste.py). Bildschirme ohne Filter
        # lassen den Streifen leer; in der Kasse steht dort der
        # Warenkorb.
        self.filterbereich = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=0,
        )

        self.filterbereich.bind(
            minimum_height=self.filterbereich.setter("height")
        )

        self.add_widget(
            self.filterbereich
        )

        # Beim Wechsel des Bildschirms nachsehen, ob heute etwas
        # ansteht: Wer im Kalender gerade eine Veranstaltung angelegt
        # hat, sieht sie danach oben stehen. Und die Filterleiste
        # wechselt mit.
        self.screen_manager.bind(
            current=lambda *_args: self._bildschirm_gewechselt()
        )

        self.filterleiste_zeigen()

    def _update_background(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

    def refresh_revenue(self):
        self.header.set_revenue(self.db.get_daily_revenue())

    def _bildschirm_gewechselt(self):

        self.veranstaltung_anzeigen()
        self.filterleiste_zeigen()

    def filterleiste_zeigen(self):
        """Haengt die Filterleiste des sichtbaren Bildschirms unten ein.

        Die Leiste gehoert dem Bildschirm - sie steht nur an einer
        gemeinsamen Stelle, damit sie ueberall gleich sitzt.
        """

        self.filterbereich.clear_widgets()

        bildschirm = self.screen_manager.current_screen

        leiste = getattr(bildschirm, "filterleiste", None)

        if leiste is None:
            self.filterbereich.height = 0
            return

        if leiste.parent is not None:
            leiste.parent.remove_widget(leiste)

        # Zugeklappt beginnen: Wer den Bildschirm wechselt, will
        # zuerst sehen, was darauf steht.
        leiste.zuklappen()
        leiste.aktualisieren()

        self.filterbereich.add_widget(leiste)

    def veranstaltung_anzeigen(self):
        """Traegt die heutige Veranstaltung in die Kopfzeile ein.

        Bis hierher stand dort fest verdrahtet "KiG POS" - der Kalender
        wurde nie gefragt, auch wenn ein Fest eingetragen war.

        Auf dem Telefon bleibt die Mitte leer: Dort reicht die Breite
        gerade fuer Logo und Tagesumsatz, ein Name brach Buchstabe fuer
        Buchstabe um.
        """

        if theme.is_narrow():
            self.header.set_event_name("")
            return

        heute = date.today().isoformat()

        eintrag = self.db.get_event_for_date(heute)

        self.header.set_event_name(
            eintrag["name"] if eintrag else config.APP_NAME
        )

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
