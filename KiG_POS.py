"""
=========================================================
KiG POS
=========================================================

Datei:
    main.py

Beschreibung:
    Einstiegspunkt der Anwendung.
e
Version:
    1.0.0
=========================================================
"""

import traceback

from kivy.app import App
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp, Metrics
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform

import config
import demo
import storage
import theme

from database import DatabaseManager, NurAnsichtFehler

from screens.main_screen import MainScreen
from screens.splash_wrapper import SplashWrapper
from widgets.common.hinweis_popup import HinweisPopup


# =========================================================
# Plattform
# =========================================================
#
# Auf Android gibt es kein Fenster, dessen Größe die Anwendung
# bestimmen könnte - das Gerät gibt sie vor. Alles, was hier mit
# Fenstergrößen zu tun hat, bleibt dort deshalb wirkungslos.

IS_ANDROID = platform == "android"


# =========================================================
# Fensterkonfiguration
# =========================================================

def _bildpunkt_faktor():
    """Liefert Metrics.density - und lässt Kivys Umrechnung heil.

    Kivy hält dpi, density und fontscale in einem internen
    Zwischenspeicher und trägt beim Nachfragen nur den Teil ein, nach
    dem gefragt wurde. Wer als Erstes nach density fragt, bekommt dpi
    und density gesetzt; fontscale bleibt auf seinem Startwert -1
    stehen. Jede Größenangabe in "sp" wird von da an mit -1
    multipliziert - die Schrift bekommt eine negative Größe und ist
    unsichtbar. Sichtbar bleiben nur die Rahmen: Kacheln ohne Text,
    und zwar in der ganzen Anwendung.

    Getroffen hat es allein das Hochformat unter Windows, weil nur dort
    die Fensterhöhe aus der Bildschirmauflösung umgerechnet wird (siehe
    _portrait_window_height) - und damit als Erstes nach density
    gefragt wird.

    fontscale wird deshalb zuerst gelesen. Das kostet nichts, legt
    kein Fenster an und füllt den Zwischenspeicher vollständig.

    NUR für den Rechner. Auf Android holt sich Kivy die Werte über
    einen ganz anderen Weg (Java statt Fenstertreiber), und der liefert
    beim direkten Nachfragen die Dichte 0. Danach sind dp() und sp()
    ebenfalls 0, und die Anwendung beendet sich beim ersten Schalter
    mit "float division by zero". Deshalb wird dort nichts angestoßen -
    siehe _umrechnung_sicherstellen, das ohne Metrics auskommt.
    """

    _ = Metrics.fontscale

    return Metrics.density


def _umrechnung_sicherstellen():
    """Stellt sicher, dass dp() und sp() brauchbare Werte liefern.

    Fragt bewusst NICHT bei Metrics nach, sondern rechnet einfach:
    Der erste Aufruf von dp() füllt Kivys Zwischenspeicher von selbst
    und auf dem Weg, der zur Plattform passt. Kommt dabei etwas
    Unbrauchbares heraus - auf dem E-Ink-Tablet war die Dichte 0 -,
    wird es hier geradegerückt.

    Ohne diese Prüfung ist jede Größe im Programm 0: Die Oberfläche
    baut sich unsichtbar auf und stürzt beim ersten Schalter ab.
    """

    if dp(10) > 0 and sp(10) > 0:
        return

    print("Warnung: dp/sp liefern unbrauchbare Werte - "
          f"dp(10)={dp(10)}, sp(10)={sp(10)}. Wird korrigiert.")

    # sp hängt zusätzlich an fontscale; 1.0 ist der Normalfall
    # (abweichend nur, wenn im System größere Schrift eingestellt ist).
    if sp(10) <= 0:
        Metrics.fontscale = 1.0

    if dp(10) <= 0:

        # Aus der Bildschirmauflösung ergibt sich der Faktor direkt.
        # Android rechnet gegen 160 dpi (1 dp = 1/160 Zoll), die
        # Rechner-Plattformen gegen 96 dpi - so hält es Kivy selbst.
        bezug = 160.0 if IS_ANDROID else 96.0

        dichte = 0.0

        try:
            aufloesung = float(Metrics.dpi)
            if aufloesung > 0:
                dichte = aufloesung / bezug
        except Exception:
            pass

        Metrics.density = dichte if dichte > 0 else 1.0

    print(f"Korrigiert: dp(10)={dp(10)}, sp(10)={sp(10)}")


def _screen_height():
    """Höhe des Bildschirms in Pixeln (0 = unbekannt).

    Nur unter Windows ermittelbar; überall sonst (und falls der
    Aufruf scheitert) wird 0 zurückgegeben und der konfigurierte
    Wert unverändert verwendet.
    """

    try:
        import ctypes

        return int(ctypes.windll.user32.GetSystemMetrics(1))

    except Exception:
        return 0


def _portrait_window_height():
    """Fensterhöhe fürs Hochformat, begrenzt auf den Bildschirm.

    Ein Fenster, das höher ist als der Bildschirm, schiebt die
    Fußzeile - und damit "Programm beenden" - aus dem sichtbaren
    Bereich. Deshalb hier lieber etwas niedriger als gewünscht.
    """

    bildschirm = _screen_height()

    if bildschirm <= 0:
        return config.PORTRAIT_WINDOW_HEIGHT

    # GetSystemMetrics liefert echte Bildpunkte, Window.size erwartet
    # die unskalierte Fenstergröße - bei 125 % Windows-Skalierung sind
    # das zwei verschiedene Zahlen. Ohne diese Umrechnung wäre das
    # Fenster ein Viertel höher als gedacht.
    verfuegbar = (
        (bildschirm - config.PORTRAIT_SCREEN_MARGIN) / _bildpunkt_faktor()
    )

    return int(max(
        config.PORTRAIT_MIN_HEIGHT,
        min(
            config.PORTRAIT_WINDOW_HEIGHT,
            verfuegbar
        )
    ))


def _ausrichtung_bestimmen(db):
    """Liefert die Ausrichtung, mit der die Oberfläche aufgebaut wird.

    Normalerweise die gespeicherte Einstellung. Beim allerersten Start
    ist noch keine gewählt - dann entscheidet die Form des Bildschirms
    und wird festgehalten:

        Windows      1500 x 875   -> Querformat
        Telefon      1080 x 2400  -> Hochformat
        E-Ink-Tablet 1860 x 2480  -> Hochformat, in der Hand gedreht
                                     dann Querformat

    Ab da gilt, was in den Einstellungen steht - auf jedem Gerät
    gleichermaßen. Deshalb wird hier auch nicht nach Android
    unterschieden: Die Anwendung soll überall dieselbe sein.
    """

    gespeichert = db.get_setting("screen_orientation")

    if gespeichert in (theme.ORIENTATION_LANDSCAPE, theme.ORIENTATION_PORTRAIT):
        return gespeichert

    abgeleitet = (
        theme.ORIENTATION_PORTRAIT
        if Window.height > Window.width
        else theme.ORIENTATION_LANDSCAPE
    )

    db.set_setting("screen_orientation", abgeleitet)

    return abgeleitet


def apply_window_orientation(orientation):
    """Setzt Fenstergröße und Mindestmaße passend zur Ausrichtung.

    In Vollbild und im randlosen Modus bestimmt der Bildschirm die
    Größe - dort werden nur die Mindestmaße angepasst.

    Auf Android geschieht nichts: Dort füllt die Anwendung ohnehin den
    Bildschirm, und die Ausrichtung legt das Gerät fest.
    """

    if IS_ANDROID:
        return

    if orientation == theme.ORIENTATION_PORTRAIT:

        breite = config.PORTRAIT_WINDOW_WIDTH
        hoehe = _portrait_window_height()

        min_breite = config.PORTRAIT_MIN_WIDTH
        min_hoehe = min(config.PORTRAIT_MIN_HEIGHT, hoehe)

    else:

        breite = config.WINDOW_WIDTH
        hoehe = config.WINDOW_HEIGHT

        min_breite = config.MIN_WIDTH
        min_hoehe = config.MIN_HEIGHT

    # Erst die Mindestmaße, dann die Größe: Das noch gesetzte
    # Mindestmaß der anderen Ausrichtung würde die neue Fenstergröße
    # sonst blockieren (1200 Mindestbreite gegen 800 Wunschbreite).
    Window.minimum_width = min_breite
    Window.minimum_height = min_hoehe

    if config.WINDOW_MODE == "window":
        Window.size = (breite, hoehe)


if IS_ANDROID:

    # Auf Android gibt das Gerät die Fenstergröße vor; die Ausrichtung
    # der Oberfläche wird in build() aus der Einstellung bestimmt
    # (siehe _ausrichtung_bestimmen).
    pass

elif config.WINDOW_MODE == "window":

    Window.fullscreen = False
    Window.borderless = False

elif config.WINDOW_MODE == "fullscreen":

    Window.fullscreen = "auto"

elif config.WINDOW_MODE == "borderless":

    Window.fullscreen = False
    Window.borderless = True
    Window.maximize()

# Startgröße im Querformat; die gespeicherte Ausrichtung wird in
# KiGPOS.build() gelesen und ggf. sofort angewendet.
apply_window_orientation(theme.get_orientation())


# =========================================================
# Netz für den Schreibschutz
# =========================================================

class NurAnsichtNetz(ExceptionHandler):
    """Fängt ab, wenn ein Nebengerät doch etwas ändern wollte.

    Der Schreibschutz sitzt am Datenbankcursor (siehe
    database.NurAnsichtCursor) und wirft dort eine Ausnahme. Fliegt
    die aus einem Tastendruck heraus, beendet Kivy die Anwendung -
    auf dem Tablet sieht das aus wie ein hängendes Programm, und
    genau so wurde es auch gemeldet.

    Die Bedienung ist auf einem Nebengerät bereits gesperrt (siehe
    products_screen). Dieses Netz ist die zweite Reihe: für Wege, die
    dabei übersehen wurden, und für alles, was später dazukommt. Es
    zeigt den Grund als wegtippbaren Hinweis, und die Anwendung läuft
    weiter.
    """

    def handle_exception(self, ausnahme):

        if not isinstance(ausnahme, NurAnsichtFehler):
            return ExceptionManager.RAISE

        traceback.print_exc()

        # Erst im nächsten Frame: Wir stecken gerade mitten in der
        # Ereignisverarbeitung, aus der die Ausnahme kam.
        Clock.schedule_once(
            lambda _dt: HinweisPopup(
                title="Nur Ansicht",
                message=str(ausnahme),
            ).open(),
            0,
        )

        return ExceptionManager.PASS


def _nur_ansicht_netz_einhaengen():

    for vorhandenes in ExceptionManager.handlers:
        if isinstance(vorhandenes, NurAnsichtNetz):
            return

    ExceptionManager.add_handler(NurAnsichtNetz())


# =========================================================
# Anwendung
# =========================================================

class KiGPOS(App):

    title = config.APP_NAME

    # Vereinslogo in Fenster und Taskleiste. Ohne diese Zeile zeigt
    # Kivy dort sein eigenes Zeichen - im Verein sitzt aber niemand
    # vor "einem Kivy-Programm", sondern vor der Vereinskasse.
    #
    # Ausdrücklich die PNG-Fassung: Eine .ico-Datei nimmt Kivy zwar
    # widerspruchslos an, lädt sie aber nicht - das Fenster behält
    # dann sein altes Zeichen. Am laufenden Fenster nachgemessen
    # (WM_GETICON), siehe config.ICON_APP_FENSTER.
    icon = str(config.ICON_APP_FENSTER)

    def build(self):

        # Die Bildschirmtastatur soll das Feld nicht verdecken, in das
        # gerade geschrieben wird.
        #
        # Auf dem Tablet klappt sie über die untere Bildschirmhälfte -
        # und genau dort steht in allen Listen das Feld für den neuen
        # Eintrag. Man tippte also blind.
        #
        # "below_target" schiebt den Fensterinhalt so weit nach oben,
        # dass das gerade beschriebene Feld direkt über der Tastatur
        # steht: nur so weit wie nötig, und alles Übrige bleibt an
        # seinem Platz. Kivy reicht die Einstellung an Android weiter
        # (siehe window_sdl2.py: request_keyboard -> show_keyboard).
        #
        # Auf dem Boox Go 10.3 nachgeprüft: Das Feld rutscht hoch, man
        # sieht beim Tippen, was man schreibt. Auf dem Rechner ist
        # davon nichts zu sehen - dort gibt es keine
        # Bildschirmtastatur.
        Window.softinput_mode = "below_target"

        # Netz für den Schreibschutz - siehe NurAnsichtNetz.
        _nur_ansicht_netz_einhaengen()

        # Kivys Umrechnung von "sp" und "dp" in Ordnung bringen, bevor
        # die erste Beschriftung entsteht: auf dem Rechner anstoßen
        # (sonst wird die Schrift unsichtbar, siehe _bildpunkt_faktor),
        # überall nachrechnen (siehe _umrechnung_sicherstellen).
        if not IS_ANDROID:
            _bildpunkt_faktor()

        _umrechnung_sicherstellen()

        # Der Demo-Modus wird bewusst nicht gespeichert: Jeder Start
        # beginnt im normalen Modus. Eine Kopie, die von einem Absturz
        # uebrig geblieben ist, wird hier weggeraeumt (siehe demo.py).
        try:
            demo.aufraeumen(storage.data_dir())
        except Exception:
            traceback.print_exc()

        # Gespeicherten Farbmodus VOR dem Aufbau der Oberfläche
        # anwenden, damit bereits die erste Bildschirmzeichnung im
        # richtigen Modus erfolgt.
        #
        # Schlägt der Datenbankzugriff fehl, bricht die Anwendung ohne
        # diese Absicherung wortlos ab - sichtbar wäre nur ein
        # Fehlertext in der Konsole, die im Betrieb niemand offen hat.
        # Stattdessen erscheint ein verständlicher Hinweis.
        try:
            db = DatabaseManager()

            # Gehört die Kasse diesem Gerät? Wenn nicht, läuft alles
            # ab hier im Nur-Ansicht-Modus (siehe uebergabe.py).
            # Eine frische Datenbank gehört dem, der sie anlegt.
            db.besitz_sicherstellen()

            theme.set_mode(db.get_setting("theme_mode") or "light")

            # Ausrichtung ebenfalls VOR dem Aufbau setzen - die Screens
            # fragen sie beim Bauen ab (siehe theme.is_portrait).
            theme.set_orientation(_ausrichtung_bestimmen(db))
            apply_window_orientation(theme.get_orientation())

            # Und die Größe: Ein Telefon braucht eine andere Anordnung
            # als ein Tablet, auch wenn beide hochkant stehen (siehe
            # theme.is_narrow).
            #
            # Gemessen wird die KÜRZERE Seite, nicht die aktuelle
            # Breite. Sonst hinge die Anordnung daran, wie das Gerät
            # beim Start gerade in der Hand lag: Ein Telefon, quer
            # gestartet, bekäme die Tabletanordnung auf einem
            # handtellergroßen Schirm. Die kürzere Seite ändert sich
            # beim Drehen nicht - ein Telefon bleibt ein Telefon.
            #
            # Über dp(1) statt über Metrics.density - dieser Weg ist
            # auf allen Geräten schon geradegerückt (siehe
            # _umrechnung_sicherstellen).
            theme.set_breite(
                min(Window.width, Window.height) / dp(1)
            )

        except Exception as error:
            traceback.print_exc()
            return self._build_error_screen(error)

        self.manager = ScreenManager()

        self.splash = SplashWrapper(name="splash")
        self.main = MainScreen(name="main")

        self.splash.on_finished = self.show_main_layout

        self.manager.add_widget(self.splash)
        self.manager.add_widget(self.main)

        self.manager.current = "splash"

        self.splash.run_startup()

        # Zurück-Taste bzw. Zurück-Wischgeste des Telefons abfangen.
        # Ohne diese Zeile beendet Android die Anwendung sofort - mitten
        # im Verkauf wäre das ärgerlich.
        if IS_ANDROID:
            Window.bind(on_keyboard=self._android_back)

        return self.manager

    # -----------------------------------------------------

    def show_main_layout(self):

        self.manager.current = "main"

    # =====================================================
    # Zurück-Taste (Android)
    # =====================================================

    def _android_back(self, _window, key, *_args):
        """Zurück führt zur Startseite; von dort wird nachgefragt.

        Rückgabe True heißt: erledigt, Android soll nichts weiter tun.
        """

        # 27 = ESC, darauf bildet Android die Zurück-Taste ab.
        if key != 27:
            return False

        # Während des Startbildschirms passiert nichts.
        if self.manager.current != "main":
            return True

        layout = self.main.main_layout

        if layout.screen_manager.current != config.SCREEN_HOME:
            layout.show_home()
            return True

        layout.request_exit()

        return True

    # =====================================================
    # Startfehler
    # =====================================================

    def _build_error_screen(self, error):
        """Zeigt statt der Oberfläche einen lesbaren Hinweis.

        Enthält den Speicherort der Datenbank: Damit lässt sich am
        Veranstaltungsabend zumindest die Sicherung aus dem Ordner
        "backups" daneben zurückspielen.
        """

        wurzel = BoxLayout(
            orientation="vertical",
            padding=dp(theme.SCREEN_PADDING * 2),
            spacing=dp(theme.CARD_SPACING),
        )

        titel = Label(
            text="KiG POS kann nicht gestartet werden",
            color=theme.PRIMARY_ORANGE, font_size="26sp", bold=True,
            size_hint_y=None, height=dp(50),
            halign="center", valign="middle",
        )
        titel.bind(size=lambda i, v: setattr(i, "text_size", v))
        wurzel.add_widget(titel)

        # Den TATSÄCHLICHEN Speicherort zeigen: Solange die Anwendung
        # läuft, liegt die Datenbank in user_data_dir und nicht in
        # config.DATABASE_DIR (siehe DatabaseManager.get_database_path).
        # Ein falscher Pfad wäre hier besonders ärgerlich - genau dort
        # sucht man ja nach der Sicherung.
        try:
            speicherort = self.user_data_dir
        except Exception:
            speicherort = config.DATABASE_DIR

        text = Label(
            text=(
                "Die Datenbank konnte nicht geöffnet werden.\n\n"
                f"Grund: {error}\n\n"
                f"Speicherort: {speicherort}\n\n"
                "Läuft KiG POS vielleicht bereits in einem anderen Fenster? "
                "Andernfalls hilft eine Sicherung aus dem Unterordner "
                "\"backups\" neben der Datenbank."
            ),
            color=theme.TEXT_PRIMARY, font_size="16sp",
            halign="center", valign="top",
        )
        text.bind(size=lambda i, v: setattr(i, "text_size", v))
        wurzel.add_widget(text)

        beenden = Button(
            text="Beenden", size_hint=(None, None), size=(dp(200), dp(56)),
            pos_hint={"center_x": 0.5},
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="17sp", bold=True,
        )
        beenden.bind(on_release=lambda *_args: self.stop())
        wurzel.add_widget(beenden)

        return wurzel

    # =====================================================
    # Farbmodus
    # =====================================================

    def apply_theme_mode(self, mode):
        """Wechselt zwischen hellem und dunklem Modus.

        Da Widgets ihre Farben zur Konstruktionszeit fest in ihre
        canvas-Instructions übernehmen, wird die komplette
        Hauptoberfläche (Header, Screens, Footer) mit dem neuen
        Modus neu aufgebaut - nur so wirkt sich der Wechsel
        tatsächlich sichtbar aus.
        """

        db = DatabaseManager()

        theme.set_mode(mode)
        db.set_setting("theme_mode", mode)

        self.rebuild_main()

    # =====================================================
    # Bildschirmausrichtung
    # =====================================================

    def apply_orientation(self, orientation):
        """Wechselt zwischen Quer- und Hochformat.

        Wie beim Farbmodus lesen die Widgets die Ausrichtung zur
        Konstruktionszeit - die Oberfläche wird deshalb komplett neu
        aufgebaut. Zusätzlich ändert sich hier das Fenster selbst,
        damit die neue Anordnung auch die passende Fläche vorfindet.
        """

        db = DatabaseManager()

        theme.set_orientation(orientation)
        db.set_setting("screen_orientation", orientation)

        apply_window_orientation(orientation)

        self.rebuild_main()

    # =====================================================
    # Demo-Modus
    # =====================================================

    def apply_demo_mode(self, aktiv):
        """Schaltet den Demo-Modus ein oder aus.

        Beim Einschalten wird der aktuelle Stand der Datenbank
        eingefroren (kopiert) und die Anwendung arbeitet ab da auf der
        Kopie; beim Ausschalten verschwindet die Kopie samt allem, was
        darin angestellt wurde.

        Die Reihenfolge ist wichtig:

            1. Verbindung schließen - erst dann steht alles in der
               Datei und nicht mehr im WAL-Journal, und nur dann ist
               die Kopie vollständig.
            2. Umschalten (kopieren bzw. verwerfen).
            3. Datenbank neu aufbauen - der DatabaseManager ist ein
               Singleton und hängt sonst an der alten Datei.
            4. Oberfläche neu aufbauen: Die Screens halten eigene
               Verweise auf die Datenbank, und die Farben stecken
               ohnehin in den Widgets.
        """

        alte_db = DatabaseManager()

        datenordner = storage.data_dir()

        alte_db.close()

        DatabaseManager._instance = None

        if aktiv:
            demo.starten(datenordner)
        else:
            demo.beenden(datenordner)

        neue_db = DatabaseManager()

        # Auch die Demo-Kopie trägt einen Besitzer - den aus dem
        # Augenblick des Einfrierens. Gehörte die Kasse damals einem
        # anderen Gerät, bleibt es auch in der Demo beim Zusehen.
        neue_db.besitz_sicherstellen()

        theme.set_accent("demo" if aktiv else "normal")

        # Farbmodus und Ausrichtung stehen in der Datenbank - und die
        # ist jetzt eine andere. Beides neu einlesen, damit die Demo
        # aussieht wie das Original.
        theme.set_mode(neue_db.get_setting("theme_mode") or "light")

        self.rebuild_main()

    def rebuild_main(self):
        """Baut MainScreen (und damit alle Screens/Panels) neu auf."""

        old_main = self.main
        was_current = self.manager.current == "main"

        new_main = MainScreen(name="main")

        self.manager.remove_widget(old_main)
        self.manager.add_widget(new_main)

        self.main = new_main

        if was_current:
            self.manager.current = "main"


# =========================================================
# Start
# =========================================================

if __name__ == "__main__":

    KiGPOS().run()