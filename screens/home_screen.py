"""
=========================================================
KiG POS
=========================================================

Modul:
    M100.0

Datei:
    home_screen.py

Beschreibung:
    HomeScreen der Anwendung.

Der HomeScreen enthält die zentrale Navigation
zu allen Hauptbereichen.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView


from widgets.home.home_tile import HomeTile
from widgets.kig_label import KiGLabel

import config
import theme

class HomeScreen(Screen):
    """
    Startbildschirm der Anwendung.
    """

    # Höchstens so viele Kacheln nebeneinander. Vier, weil die
    # größte Gruppe (Administrativ) genau vier hat und auf einem
    # breiten Bildschirm in einer Reihe stehen soll.
    MAX_COLUMNS = 4

    # Höhe einer Gruppenüberschrift
    GROUP_TITLE_HEIGHT = 28

    # =====================================================
    # Konstruktor
    # =====================================================

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        #
        # Hauptlayout
        #

        # Scrollbar: Passen nur ein oder zwei Kacheln nebeneinander,
        # wird das Raster höher als der Bildschirm - auf einem Telefon
        # ragten die untersten Kacheln sonst einfach hinaus.
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(8))

        self.root_layout = AnchorLayout(

            anchor_x="center",

            anchor_y="center",

            size_hint_y=None
        )

        self.scroll.add_widget(
            self.root_layout
        )

        self.add_widget(
            self.scroll
        )

        #
        # Gruppen
        #

        # Die Kacheln haben auf jedem Gerät dieselbe physische Größe
        # (siehe KiGTile: dp). Wie viele nebeneinander passen, hängt
        # deshalb vom Bildschirm ab - auf einem Telefon eine, am
        # Rechner vier.
        #
        # Sie stehen nicht in starren Dreierreihen, sondern in
        # drei Gruppen: Was im Betrieb gebraucht wird, was verwaltet
        # wird, und was hilft. Jede Gruppe bricht für sich um.
        self.groups_layout = BoxLayout(

            orientation="vertical",

            spacing=dp(theme.TILE_SPACING),

            padding=dp(theme.SCREEN_PADDING),

            size_hint=(None, None)
        )

        self.groups_layout.bind(
            minimum_height=self.groups_layout.setter("height")
        )

        self.bind(size=self._update_columns)

        self.root_layout.add_widget(
            self.groups_layout
        )
        # =====================================================
        # Kacheln
        # =====================================================

        #
        # Kasse
        #

        self.tile_cash = HomeTile()

        self.tile_cash.set_icon(
            str(config.ICON_CASH)
        )

        self.tile_cash.set_title("KASSE")

        self.tile_cash.set_subtitle(
            "Verkauf starten"
        )

        #
        # Statistik
        #

        self.tile_statistics = HomeTile()

        self.tile_statistics.set_icon(
            str(config.ICON_STATISTICS)
        )

        self.tile_statistics.set_title(
            "STATISTIK"
        )

        self.tile_statistics.set_subtitle(
            "Auswertungen"
        )

        #
        # Veranstaltungen
        #

        self.tile_events = HomeTile()

        self.tile_events.set_icon(
            str(config.ICON_EVENTS)
        )

        self.tile_events.set_title(
            "EVENTS"
        )

        self.tile_events.set_subtitle(
            "Veranstaltungen verwalten"
        )

        #
        # Kassenbuch
        #

        self.tile_cashbook = HomeTile()

        self.tile_cashbook.set_icon(
            str(config.ICON_CASHBOOK)
        )

        self.tile_cashbook.set_title(
            "KASSENBUCH"
        )

        self.tile_cashbook.set_subtitle(
            "Kassenbestand festhalten"
        )

        #
        # Checkliste
        #

        self.tile_checklist = HomeTile()

        self.tile_checklist.set_icon(
            str(config.ICON_CHECKLIST)
        )

        self.tile_checklist.set_title(
            "CHECKLISTE"
        )

        self.tile_checklist.set_subtitle(
            "Aufgaben abhaken"
        )

        #
        # Artikelverwaltung (Artikel, Einkauf, Inventar, Rezepte)
        #

        self.tile_articles = HomeTile()

        self.tile_articles.set_icon(
            str(config.ICON_ARTICLES)
        )

        self.tile_articles.set_title(
            "ARTIKEL"
        )

        self.tile_articles.set_subtitle(
            "Artikel, Bestand, Einkauf & Rezepte"
        )

        #
        # Bedienungsanleitung
        #

        self.tile_use = HomeTile()

        self.tile_use.set_icon(
            str(config.ICON_USE)
        )

        self.tile_use.set_title(
            "USERGUIDE"
        )

        self.tile_use.set_subtitle(
            "Benutzerhandbuch"
        )

        #
        # Einstellungen
        #

        self.tile_settings = HomeTile()

        self.tile_settings.set_icon(
            str(config.ICON_SETTINGS)
        )

        self.tile_settings.set_title(
            "EINSTELLUNGEN"
        )

        self.tile_settings.set_subtitle(
            "Programm konfigurieren"
        )

        # =====================================================
        # Gruppen füllen
        # =====================================================

        self.groups = []

        for ueberschrift, kacheln in (
            ("Operativ", (self.tile_cash, self.tile_cashbook)),
            ("Administrativ", (
                self.tile_articles, self.tile_events,
                self.tile_checklist, self.tile_statistics,
            )),
            ("Support", (self.tile_use, self.tile_settings)),
        ):
            self.groups.append(
                self._add_group(ueberschrift, kacheln)
            )

        #
        # Grid automatisch an Inhalt anpassen
        #

        # Der Ankerbereich ist so hoch wie das Raster - mindestens aber
        # so hoch wie das Sichtfenster. Passt alles, bleiben die Kacheln
        # dadurch mittig; passt es nicht, entsteht Scrollhöhe.
        self.groups_layout.bind(height=self._update_scroll_height)
        self.scroll.bind(height=self._update_scroll_height)

        # =====================================================
        # Navigation
        # =====================================================

        self.tile_cash.set_callback(
            self.open_cash
        )

        self.tile_statistics.set_callback(
            self.open_statistics
        )

        self.tile_events.set_callback(
            self.open_events
        )

        self.tile_cashbook.set_callback(
            self.open_cashbook
        )

        self.tile_checklist.set_callback(
            self.open_checklist
        )

        self.tile_articles.set_callback(
            self.open_articles
        )

        self.tile_use.set_callback(
            self.open_userguide
        )

        self.tile_settings.set_callback(
            self.open_settings
        )

    # =====================================================
    # Spaltenzahl
    # =====================================================

    def _update_scroll_height(self, *_args):

        self.root_layout.height = max(
            self.groups_layout.height, self.scroll.height
        )

    def _add_group(self, ueberschrift, kacheln):
        """Eine Gruppe: Überschrift und darunter ihre Kacheln.

        Liefert (Überschrift, Raster, Kacheln) - der Bildschirm braucht
        beides später, um die Spaltenzahl anzupassen.
        """

        titel = KiGLabel(text=ueberschrift)
        titel.set_font_size(16)
        titel.set_bold(True)
        titel.set_alignment("left")
        titel.set_color(theme.TEXT_SECONDARY)
        titel.size_hint = (None, None)
        titel.height = dp(self.GROUP_TITLE_HEIGHT)

        self.groups_layout.add_widget(titel)

        raster = GridLayout(
            cols=len(kacheln),
            spacing=dp(theme.TILE_SPACING),
            size_hint=(None, None),
        )

        raster.bind(minimum_size=raster.setter("size"))

        for kachel in kacheln:
            raster.add_widget(kachel)

        self.groups_layout.add_widget(raster)

        return titel, raster, tuple(kacheln)

    def _update_columns(self, *_args):
        """Passt an, wie viele Kacheln je Gruppe nebeneinander stehen.

        Die Kacheln behalten ihre Größe - es ändert sich nur, wie viele
        in eine Reihe passen. Damit sieht die Startseite auf dem
        Telefon, auf dem E-Ink-Tablet und am Rechner gleich aus, nur
        unterschiedlich breit umbrochen.

        Alle Gruppen sind gleich breit, auch wenn eine davon weniger
        Kacheln hat: Sonst stünden die Reihen versetzt untereinander.
        """

        kachel_breite = dp(HomeTile.WIDTH)
        abstand = dp(theme.TILE_SPACING)
        rand = dp(theme.SCREEN_PADDING)

        verfuegbar = self.width - 2 * rand

        passend = int((verfuegbar + abstand) // (kachel_breite + abstand))
        passend = max(1, min(self.MAX_COLUMNS, passend))

        breiteste = 1

        for _titel, raster, kacheln in self.groups:

            spalten = max(1, min(passend, len(kacheln)))

            if raster.cols != spalten:
                raster.cols = spalten

            breiteste = max(breiteste, spalten)

        breite = breiteste * kachel_breite + (breiteste - 1) * abstand

        self.groups_layout.width = breite + 2 * rand

        for titel, _raster, _kacheln in self.groups:
            titel.width = breite
            titel.text_size = (breite, titel.height)

    # =====================================================
    # Callbacks
    # =====================================================

    def open_cash(self):

        self.manager.current = config.SCREEN_CASH


    # -----------------------------------------------------

    def open_statistics(self):

        self.manager.current = config.SCREEN_STATISTICS


    # -----------------------------------------------------

    def open_events(self):

        self.manager.current = config.SCREEN_EVENTS

    # -----------------------------------------------------

    def open_cashbook(self):

        self.manager.current = config.SCREEN_CASHBOOK

    # -----------------------------------------------------

    def open_checklist(self):

        self.manager.current = config.SCREEN_CHECKLIST

    # -----------------------------------------------------

    def open_articles(self):

        self.manager.current = config.SCREEN_PRODUCTS


    # ---------------------------------------------A--------

    def open_settings(self):

        self.manager.current = config.SCREEN_SETTINGS

    # -----------------------------------------------------

    def open_userguide(self):

        self.manager.current = config.SCREEN_USE