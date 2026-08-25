"""
=========================================================
KiG POS - Geräteprüfung
=========================================================

Datei:
    werkzeuge/geraete_pruefen.py

Beschreibung:
    Baut die komplette Oberfläche für mehrere Geräte auf und meldet
    jede Stelle, an der etwas über seinen Rahmen hinausragt.

    Ein Android-Emulator wird dafür nicht gebraucht. Entscheidend
    für das Layout sind nur zwei Zahlen: die Bildschirmgröße in
    Bildpunkten und die Bildschirmdichte. Beides lässt sich hier
    einstellen - die Fenstergröße des Prüfrechners spielt keine
    Rolle, weil die Oberfläche nicht angezeigt, sondern nur
    vermessen wird.

    Aufruf (aus dem Projektordner):

        .venv\\Scripts\\python.exe werkzeuge\\geraete_pruefen.py

    Rückgabewert 0 = alles passt, 1 = mindestens ein Überlauf.

    Die Prüfung läuft in einer eigenen Anwendung mit eigenem
    Datenordner - die echte Datenbank wird nicht angefasst.

Version:
    1.0.0
=========================================================
"""

import io
import shutil
import sys
import time

from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJEKT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJEKT))

import config

DATENORDNER = Path.home() / "AppData" / "Roaming" / "geraetepruefung"

if DATENORDNER.exists():
    shutil.rmtree(DATENORDNER)

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import Metrics
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import NoTransition, Screen
from kivy.uix.scrollview import ScrollView

import theme

from database import DatabaseManager


# =========================================================
# Geräte
# =========================================================
#
# breite/hoehe   echte Bildpunkte des Bildschirms
# dichte         Bildpunkte je Entwurfseinheit (dp)
#                = gemeldete dpi / 160
#
# Die Werte stammen aus "adb shell wm size" und "wm density"
# bzw. für Windows aus kivy.metrics.

GERAETE = [
    {
        "name": "Windows-Rechner (125 % Skalierung)",
        "breite": 1500, "hoehe": 875, "dichte": 1.25,
        "ausrichtung": theme.ORIENTATION_LANDSCAPE,
    },
    {
        "name": "Windows-Rechner, Hochformat",
        "breite": 825, "hoehe": 990, "dichte": 1.25,
        "ausrichtung": theme.ORIENTATION_PORTRAIT,
    },
    {
        "name": "Onyx Boox Go 10.3, hochkant",
        "breite": 1860, "hoehe": 2480, "dichte": 1.875,
        "ausrichtung": theme.ORIENTATION_PORTRAIT,
    },
    {
        "name": "Onyx Boox Go 10.3, quer",
        "breite": 2480, "hoehe": 1860, "dichte": 1.875,
        "ausrichtung": theme.ORIENTATION_LANDSCAPE,
    },
    {
        "name": "Galaxy S24 Ultra, hochkant",
        "breite": 1440, "hoehe": 3120, "dichte": 3.5,
        "ausrichtung": theme.ORIENTATION_PORTRAIT,
    },
    {
        "name": "Kleines Telefon (HD+), hochkant",
        "breite": 720, "hoehe": 1600, "dichte": 2.0,
        "ausrichtung": theme.ORIENTATION_PORTRAIT,
    },
]

SCREENS = (
    config.SCREEN_HOME,
    config.SCREEN_CASH,
    config.SCREEN_PRODUCTS,
    config.SCREEN_STATISTICS,
    config.SCREEN_EVENTS,
    config.SCREEN_CASHBOOK,
    config.SCREEN_CHECKLIST,
    config.SCREEN_SHIFTPLAN,
    config.SCREEN_SETTINGS,
    config.SCREEN_USE,
)

# Ein halber Bildpunkt Rundungsunschärfe ist unvermeidlich; erst
# darüber ist es ein echter Überlauf.
TOLERANZ = 1.5


class GeraetePruefungApp(App):
    """Prüfanwendung.

    Wichtig: Die zu prüfende Oberfläche wird NICHT als Fensterinhalt
    verwendet, sondern freistehend aufgebaut und auf Gerätegröße
    gesetzt. So lassen sich auch Bildschirme prüfen, die größer sind
    als der Monitor des Prüfrechners.
    """

    def build(self):
        from kivy.uix.widget import Widget

        self.db = DatabaseManager()
        self._grunddaten_anlegen()

        return Widget()

    # -----------------------------------------------------

    def _grunddaten_anlegen(self):
        """Ein paar Artikel und Verkäufe - leere Screens verbergen
        Überläufe, weil dann schlicht nichts da ist, was herausragen
        könnte."""

        kategorien = {k["name"]: k["id"] for k in self.db.get_categories()}

        for name, kategorie, preis, einkauf, bestand in (
            ("Cola", "Alkoholfrei", 2.50, 0.60, 98),
            ("Apfelschorle", "Alkoholfrei", 2.50, 0.60, 55),
            ("Spezi", "Alkoholfrei", 2.50, 0.60, 41),
            ("Gold Ochsen", "Alkohol", 3.00, 1.10, 28),
            ("Weizen", "Alkohol", 3.20, 1.20, 33),
            ("Weinschorle lieblich", "Alkohol", 4.00, 1.40, 12),
        ):
            self.db.add_article(
                category_id=kategorien[kategorie], name=name, price=preis,
                purchase_price=einkauf, cash_visible=True,
            )
            artikel_id = self.db.get_article_id_by_name(name)
            self.db.update_stock(artikel_id, bestand)

            self.db.save_sale(
                event_id=None, payment_type="BAR", subtotal=preis,
                deposit_total=0, total=preis, received=preis, change=0,
                items=[{
                    "article_id": artikel_id, "name": name, "quantity": 2,
                    "price": preis, "purchase_price": einkauf,
                    "line_total": preis * 2,
                }],
            )

    # -----------------------------------------------------

    def on_start(self):
        Clock.schedule_once(lambda _dt: self.durchlauf(), 0.4)

    def durchlauf(self):
        try:
            self.fehlerzahl = self._alle_geraete()
        finally:
            self.stop()

    # -----------------------------------------------------
    # Hilfsmittel
    # -----------------------------------------------------

    @staticmethod
    def rechnen(sekunden=0.35):
        """Lässt Kivy die Layouts durchrechnen."""

        ende = time.time() + sekunden

        while time.time() < ende:
            Clock.tick()
            time.sleep(0.01)

    def ueberlauf(self, widget, pfad="", tiefe=0):
        """Sammelt Kinder, die aus ihrem Elternteil herausragen.

        Unterhalb von ScrollViews wird nicht weitergesucht - dort ist
        genau das gewollt, der Inhalt scrollt ja.
        """

        treffer = []

        if isinstance(widget, ScrollView) or tiefe > 4:
            return treffer

        # Screen und RelativeLayout verschieben das Koordinatensystem
        # ihrer Kinder auf den Ursprung.
        if isinstance(widget, (RelativeLayout, Screen)):
            links, unten = 0, 0
        else:
            links, unten = widget.x, widget.y

        rechts = links + widget.width
        oben = unten + widget.height

        for kind in widget.children:

            if kind.opacity == 0 or kind.width <= 0 or kind.height <= 0:
                continue

            name = f"{pfad}/{type(kind).__name__}"

            if (kind.x < links - TOLERANZ
                    or kind.right > rechts + TOLERANZ
                    or kind.y < unten - TOLERANZ
                    or kind.top > oben + TOLERANZ):

                treffer.append(
                    f"{name}: Position {kind.x:.0f},{kind.y:.0f} "
                    f"Groesse {kind.width:.0f}x{kind.height:.0f} "
                    f"ragt aus {type(widget).__name__} "
                    f"{widget.width:.0f}x{widget.height:.0f}"
                )

            treffer.extend(self.ueberlauf(kind, name, tiefe + 1))

        return treffer

    # -----------------------------------------------------
    # Prüfung
    # -----------------------------------------------------

    def _alle_geraete(self):

        gesamtfehler = 0

        print()
        print("=" * 66)
        print("KiG POS - Oberflaeche auf mehreren Geraeten pruefen")
        print("=" * 66)

        for geraet in GERAETE:
            gesamtfehler += self._ein_geraet(geraet)

        print()
        print("=" * 66)

        if gesamtfehler:
            print(f"{gesamtfehler} STELLEN RAGEN HERAUS")
        else:
            print("ALLE GERAETE OK - nichts ragt heraus")

        print("=" * 66)

        return gesamtfehler

    def _ein_geraet(self, geraet):

        breite = geraet["breite"]
        hoehe = geraet["hoehe"]

        # Beides VOR dem Aufbau setzen: Die Widgets rechnen ihre Maße
        # im Konstruktor aus.
        Metrics.density = geraet["dichte"]
        theme.set_orientation(geraet["ausrichtung"])

        print()
        print(f"--- {geraet['name']}")
        print(f"    {breite} x {hoehe} Bildpunkte, Dichte {geraet['dichte']}, "
              f"{'Hochformat' if theme.is_portrait() else 'Querformat'}")

        from layouts.main_layout import MainLayout

        layout = MainLayout()
        layout.screen_manager.transition = NoTransition()

        # Freistehend auf Gerätegröße bringen.
        layout.size_hint = (None, None)
        layout.size = (breite, hoehe)

        self.rechnen()

        fehler = 0

        for screen_name in SCREENS:

            layout.screen_manager.current = screen_name
            self.rechnen(0.25)

            screen = layout.screen_manager.get_screen(screen_name)
            treffer = self.ueberlauf(screen, screen_name)

            if treffer:
                fehler += len(treffer)
                print(f"    FEHLER in '{screen_name}':")
                for eintrag in treffer:
                    print(f"       {eintrag}")

        if not fehler:
            print(f"    alle {len(SCREENS)} Screens ohne Ueberlauf -- OK")

        # Zusätzlich: Wie viele Kacheln passen je Gruppe nebeneinander
        # und passt die Startseite ohne Rollen? Kein Fehler, aber die
        # Zahlen, die man sehen will.
        home = layout.home_screen

        spalten = [raster.cols for _titel, raster, _kacheln in home.groups]

        passt = (
            "ohne Rollen"
            if home.groups_layout.height <= home.scroll.height + 1
            else f"rollt ({home.groups_layout.height - home.scroll.height:.0f} px)"
        )

        print(f"    Startseite: Gruppen mit {spalten} Kacheln je Reihe, "
              f"{passt}")

        return fehler


anwendung = GeraetePruefungApp()
anwendung.run()

if DATENORDNER.exists():
    shutil.rmtree(DATENORDNER, ignore_errors=True)

sys.exit(1 if getattr(anwendung, "fehlerzahl", 1) else 0)
