"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.1

Datei:
    kig_headerbar.py

Beschreibung:
    Premium HeaderBar für KiG POS.

Die HeaderBar wird auf sämtlichen Screens
der Anwendung verwendet und enthält:

    • Home-Button (KiG Logo)
    • rechtsbündige Navigation
    • Demo- und Gerätehinweise

Titel, Datum, Uhrzeit und Umsatz werden im Dashboard angezeigt.

Version:
    1.0 Final

Build:
    0001

=========================================================
"""

from datetime import datetime

from kivy.clock import Clock
from kivy.utils import platform

from kivy.graphics import (
    Color,
    Rectangle,
    Line
)

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout

from widgets.kig_widget import KiGWidget
from widgets.kig_label import KiGLabel
from widgets.kig_logobutton import KiGLogoButton
from widgets.kig_divider import (
    KiGDividerVertical,
    KiGDividerHorizontal
)

from kivy.metrics import dp

import demo
import config
import theme
from widgets.common.wood_header import WoodHeader


# Auf einem Tablet zeigt das Betriebssystem Datum und Uhrzeit
# ohnehin dauerhaft an - die Kopfzeile spart sich beides und
# gibt den Platz dem Inhalt. Am Rechner im Vollbild gibt es diese
# Anzeige nicht, dort bleibt die Uhr.
IS_ANDROID = platform == "android"


class KiGHeaderBar(KiGWidget):
    """
    Premium HeaderBar von KiG POS.

    Die HeaderBar besitzt drei Bereiche:

        links:
            Vereinslogo

        mitte:
            Veranstaltung

        rechts:
            Datum
            Uhrzeit
            Tagesumsatz
    """

    # =====================================================
    # Layout-Konstanten
    # =====================================================

    HEADER_HEIGHT = theme.HEADER_HEIGHT

    # Breite des Veranstaltungsbereichs in der Mitte (Querformat).
    EVENT_AREA_WIDTH = 500

    # Demo-Hinweis in der Kopfzeile
    DEMO_AREA_WIDTH = 150

    BESITZ_AREA_WIDTH = 190
    BESITZ_FONT_SIZE = 17
    DEMO_FONT_SIZE = 34

    LOGO_SIZE = 120

    LOGO_AREA_WIDTH = 140

    STATUS_AREA_WIDTH = 160

    PADDING_LEFT = 20

    PADDING_RIGHT = 20

    PADDING_TOP = 10

    PADDING_BOTTOM = 10

    CONTENT_SPACING = 15

    # Hoehe des rechten Blocks: Uhr (22) + Trenner + "Tagesumsatz" +
    # Betrag. Ohne Uhr faellt die erste Zeile weg.
    STATUS_HOEHE = 70
    STATUS_HOEHE_OHNE_UHR = 46

    SHADOW_HEIGHT = 2

    SEPARATOR_HEIGHT = 1

    EVENT_FONT_SIZE = 28

    EVENT_INFO_FONT_SIZE = 16

    DATE_FONT_SIZE = 15

    REVENUE_TITLE_SIZE = 12

    REVENUE_FONT_SIZE = 20

    # =====================================================
    # Konstruktor
    # =====================================================

    def __init__(self, **kwargs):

        # Auf Android zeigt das Geraet die Uhrzeit selbst - die Zeile
        # entfaellt, und die Kopfzeile darf flacher werden.
        if IS_ANDROID:

            self.STATUS_HOEHE = self.STATUS_HOEHE_OHNE_UHR

            # Die gesparte Zeile darf auch die Kopfzeile selbst
            # flacher machen - 90 dp waren fuer Uhr UND Umsatz
            # gerechnet.
            self.HEADER_HEIGHT = 70

        super().__init__(**kwargs)

        #
        # Größe
        #

        self.size_hint_y = None
        self.height = dp(self.HEADER_HEIGHT)

        #
        # Home-Callback
        #

        self.on_home = None

        #
        # Hintergrund
        #

        with self.canvas.before:

            Color(*theme.HEADER_BACKGROUND)

            self.background = Rectangle()

            #
            # Leichter Schatten
            #

            Color(0, 0, 0, 0.05)

            self.shadow = Rectangle()

        #
        # Vordergrund
        #

        self.wood = WoodHeader(self)

        with self.canvas.after:
            Color(*theme.HEADER_SEPARATOR)

            self.separator = Line(width=1)


        #
        # Hauptlayout
        #

        self.content = BoxLayout(

            size_hint=(None, None),

            orientation="horizontal",

            spacing=dp(self.CONTENT_SPACING),

            padding=(

                dp(self.PADDING_LEFT),

                dp(self.PADDING_TOP),

                dp(self.PADDING_RIGHT),

                dp(self.PADDING_BOTTOM)

            )

        )

        self.add_widget(self.content)

        #
        # Linker Bereich
        #

        self.logo_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(None, 1),
            width=dp(self.LOGO_AREA_WIDTH)
        )

        #
        # Mittlerer Bereich
        #

        self.event_container = AnchorLayout(

            anchor_x="center",

            anchor_y="center"

        )

        #
        # Rechter Bereich
        #

        self.status_container = AnchorLayout(

            anchor_x="right",

            anchor_y="center",

            size_hint=(None, 1),

            width=dp(self.STATUS_AREA_WIDTH)

        )

        #
        # Container hinzufügen
        #
        self.content.add_widget(self.logo_container)

        self.content.add_widget(
            KiGDividerVertical()
        )

        # Im Demo-Modus steht hier gross DEMO. Zusammen mit der gruenen
        # Akzentfarbe soll auf einen Blick klar sein, dass gerade auf
        # einer Kopie gearbeitet wird und nichts Echtes passiert
        # (siehe demo.py).
        if demo.ist_aktiv():

            self.content.add_widget(self._build_demo_badge())

            self.content.add_widget(
                KiGDividerVertical()
            )

        # Gehoeren die Stammdaten einem anderen Geraet, steht das
        # hier - sonst tippt jemand eine Viertelstunde lang Artikel
        # ein und wundert sich, dass nichts gespeichert wird
        # (siehe uebergabe.py).
        besitzstreifen = self._build_besitz_hinweis()

        if besitzstreifen is not None:

            self.content.add_widget(besitzstreifen)

            self.content.add_widget(
                KiGDividerVertical()
            )

        self.content.add_widget(self.event_container)

        self.content.add_widget(
            KiGDividerVertical()
        )

        self.content.add_widget(self.status_container)

        #
        # Layout aktualisieren
        #

        self.bind(

            pos=self._update_layout,

            size=self._update_layout

        )

        #
        # Erstes Layout
        #

        Clock.schedule_once(

            self._finish_layout,

            0

        )

    # =====================================================
    # Logo
    # =====================================================

        self.logo = KiGLogoButton(logo_source=str(config.LOGO_PATH))

        self.logo.set_logo_size(
            dp(self.LOGO_SIZE)
        )

        #
        # Home-Callback verbinden
        #

        self.logo.set_home_callback(
            self.go_home
        )

        #
        # Logo zum Container hinzufügen
        #

        self.logo_container.add_widget(
            self.logo
        )

    # =====================================================
    # Veranstaltungsbereich
    # =====================================================

        # Feste Breite nur im Querformat: Logo (140) + Status (160) +
        # 500 für den Veranstaltungsnamen ergeben mehr, als ein
        # hochkantes Fenster (800) hergibt - der Name würde über die
        # Trennlinien hinauslaufen. Im Hochformat füllt der Bereich
        # deshalb einfach den verbleibenden Platz.
        self.event_layout = BoxLayout(

            orientation="vertical",

            spacing=-2,

            size_hint=(1, None) if theme.is_portrait() else (None, None),

            width=dp(self.EVENT_AREA_WIDTH),

            height=dp(58)

        )

        #
        # Veranstaltungsname
        #

        self.lbl_event = KiGLabel()

        self.lbl_event.set_text(
            "Keine Veranstaltung"
        )

        self.lbl_event.set_font_size(
            self.EVENT_FONT_SIZE
        )

        self.lbl_event.set_bold(True)

        self.lbl_event.set_alignment(
            "center"
        )

        #
        # Zusatzinformation
        #

        self.lbl_event_info = KiGLabel()

        self.lbl_event_info.set_text("")

        self.lbl_event_info.set_font_size(
            self.EVENT_INFO_FONT_SIZE
        )

        self.lbl_event_info.set_alignment(
            "center"
        )

        #
        # Schwarze Schrift
        #

        self.lbl_event.set_color(
            theme.HEADER_TEXT
        )

        self.lbl_event_info.set_color(
            theme.HEADER_MUTED
        )

        #
        # Labels hinzufügen
        #

        self.event_layout.add_widget(
            self.lbl_event
        )

        self.event_layout.add_widget(
            self.lbl_event_info
        )

        #
        # Eventbereich einfügen
        #

        self.event_container.add_widget(
            self.event_layout
        )

    # =====================================================
    # Statusbereich
    # =====================================================

        self.status_layout = BoxLayout(

            orientation="vertical",

            spacing=2,

            size_hint=(1, None),

            height=dp(self.STATUS_HOEHE)

        )

        #
        # Datum / Uhrzeit
        #

        self.lbl_datetime = KiGLabel()

        self.lbl_datetime.set_text("--.-- | --:--")

        self.lbl_datetime.set_font_size(self.DATE_FONT_SIZE)

        self.lbl_datetime.set_bold(True)

        self.lbl_datetime.set_color(
            theme.HEADER_TEXT
        )

        self.lbl_datetime.size_hint_y = None
        self.lbl_datetime.height = dp(22)

        self.lbl_datetime.halign = "right"
        self.lbl_datetime.valign = "middle"

        self.lbl_datetime.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.lbl_datetime.set_alignment("right")

        #
        # Tagesumsatz
        #

        self.lbl_revenue_title = KiGLabel()

        self.lbl_revenue_title.set_text(
            "Tagesumsatz"
        )

        self.lbl_revenue_title.set_font_size(
            self.REVENUE_TITLE_SIZE
        )

        self.lbl_revenue_title.set_alignment(
            "right"
        )

        self.lbl_revenue_title.set_color(
            theme.HEADER_MUTED
        )

        #
        # Umsatz
        #

        self.lbl_revenue = KiGLabel()

        self.lbl_revenue.set_text(
            "0,00 €"
        )

        self.lbl_revenue.set_font_size(
            self.REVENUE_FONT_SIZE
        )

        self.lbl_revenue.set_bold(True)

        self.lbl_revenue.set_alignment(
            "right"
        )

        self.lbl_revenue.set_color(
            theme.HEADER_ACCENT
        )

        #
        # Labels hinzufügen
        #

        if not IS_ANDROID:

            self.status_layout.add_widget(
                self.lbl_datetime
            )

            self.status_layout.add_widget(
                KiGDividerHorizontal(
                    padding=10
                )
            )

        self.status_layout.add_widget(
            self.lbl_revenue_title
        )

        self.status_layout.add_widget(
            self.lbl_revenue
        )

        #
        # Statusbereich hinzufügen
        #

        self.status_container.add_widget(
            self.status_layout
        )

        #
        # Uhr starten
        #

        self.update_datetime()

        if not IS_ANDROID:
            Clock.schedule_interval(
                self.update_datetime,
                1
            )

    # =====================================================
    # Erstes Layout
    # =====================================================

    def _finish_layout(self, dt):
        """
        Wird einmal nach dem ersten
        Layoutdurchlauf aufgerufen.
        """

        self._update_layout()

    # =====================================================
    # Layout aktualisieren
    # =====================================================

    def _update_layout(self, *args):
        """
        Aktualisiert sämtliche Layoutbereiche.
        """

        #
        # Hintergrund
        #

        self.background.pos = self.pos
        self.background.size = self.size

        #
        # Schatten
        #

        self.shadow.pos = (
            self.x,
            self.y - self.SHADOW_HEIGHT
        )

        self.shadow.size = (
            self.width,
            self.SHADOW_HEIGHT
        )

        #
        # Trennlinie
        #

        self.separator.points = (
            self.x,
            self.y,
            self.right,
            self.y
        )

        #
        # Hauptlayout
        #

        self.content.pos = self.pos
        self.content.size = self.size

    def set_navigation(self, navigation):
        """Schmaler Holzheader: Originallogo links, Navigation rechts."""
        self.navigation = navigation
        self.stop()
        self.height = dp(86)
        # Demo- und Gerätehinweise bleiben erhalten; Titel, Uhr und Umsatz
        # gehören jetzt zum Dashboard.
        badges = [child for child in reversed(self.content.children)
                  if isinstance(child, BoxLayout)]
        self.content.clear_widgets()
        self.content.padding = (dp(12), dp(8), dp(12), dp(8))
        self.content.spacing = dp(8)
        self.logo_container.width = dp(116)
        self.logo.size = (dp(108), dp(70))
        self.logo.size_hint = (None, None)
        self.logo.fit_mode = 'contain'
        self.content.add_widget(self.logo_container)
        for badge in badges:
            self.content.add_widget(badge)
        self.navigation_slot = AnchorLayout(anchor_x='right', anchor_y='center')
        navigation.size_hint = (None, 1)
        self.navigation_slot.add_widget(navigation)
        self.content.add_widget(self.navigation_slot)
        self.navigation_slot.bind(width=self._navigation_layout)
        self._navigation_layout()
        self._update_layout()

    def _navigation_layout(self, *_):
        slot = getattr(self, 'navigation_slot', None)
        if slot is not None:
            compact = self.width < dp(600)
            self.logo_container.width = dp(80 if compact else 116)
            self.logo.size = (dp(76 if compact else 108), dp(64 if compact else 70))
            count = len(self.navigation.buttons)
            self.navigation.width = min(slot.width, dp(106 * count + 5 * max(0, count - 1)))

    def go_home(self):
        """
        Führt den Home-Callback aus.
        """

        if callable(self.on_home):

            self.on_home()

    # =====================================================
    # Home-Callback setzen
    # =====================================================

    def set_home_callback(self, callback):
        """
        Speichert den Callback des Home-Buttons.
        """

        self.on_home = callback

    # =====================================================
    # Veranstaltungsname
    # =====================================================

    def set_event_name(self, text):
        """
        Setzt den Veranstaltungsnamen.
        """
        if hasattr(self, "lbl_event"):
            self.lbl_event.set_text(text)

    # =====================================================
    # Veranstaltungsinformation
    # =====================================================

    def set_event_info(self, text):
        """
        Setzt die Zusatzinformation.
        """
        if hasattr(self, "lbl_event_info"):
            self.lbl_event_info.set_text(text)

    # =====================================================
    # Tagesumsatz
    # =====================================================

    def set_revenue(self, value):
        """
        Aktualisiert den Tagesumsatz.
        """

        if hasattr(self, "lbl_revenue"):

            text = (
                f"{value:,.2f} €"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            self.lbl_revenue.set_text(text)

    # =====================================================
    # Datum / Uhrzeit
    # =====================================================

    # =====================================================
    # Demo-Hinweis
    # =====================================================

    def _build_demo_badge(self):
        """Das Wort DEMO in der Kopfzeile."""

        behaelter = BoxLayout(
            size_hint=(None, 1),
            width=dp(self.DEMO_AREA_WIDTH),
        )

        label = KiGLabel(text="DEMO")
        label.set_font_size(self.DEMO_FONT_SIZE)
        label.set_bold(True)
        label.set_alignment("center")
        label.set_color(theme.PRIMARY_ORANGE)

        behaelter.add_widget(label)

        return behaelter

    def _build_besitz_hinweis(self):
        """Streifen "Nebengeraet", solange die Stammdaten einem
        anderen Geraet gehoeren. Liefert None auf dem Hauptgeraet.

        Buchen darf ein Nebengeraet - nur Artikel, Preise und Rezepte
        werden an einer Stelle gepflegt (siehe
        database.STAMMDATEN_TABELLEN)."""

        from database import DatabaseManager

        try:
            db = DatabaseManager()

            if not db.nur_ansicht:
                return None

            besitz = db.get_besitz()

        except Exception:
            # Die Kopfzeile darf an so etwas nie scheitern.
            return None

        behaelter = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(self.BESITZ_AREA_WIDTH),
        )

        titel = KiGLabel(text="NEBENGERÄT")
        titel.set_font_size(self.BESITZ_FONT_SIZE)
        titel.set_bold(True)
        titel.set_alignment("center")
        titel.set_color(theme.WARNING)

        behaelter.add_widget(titel)

        name = besitz["geraet_name"] if besitz else "einem anderen Geraet"

        hinweis = KiGLabel(text=f"Stammdaten bei {name}")
        hinweis.set_font_size(12)
        hinweis.set_alignment("center")
        hinweis.set_color(theme.HEADER_MUTED)

        behaelter.add_widget(hinweis)

        return behaelter

    def update_datetime(self, dt=None):
        """
        Aktualisiert Datum und Uhrzeit.
        """

        if hasattr(self, "lbl_datetime"):

            self.lbl_datetime.set_text(
                datetime.now().strftime("%d.%m. | %H:%M")
            )


    # =====================================================
    # Timer stoppen
    # =====================================================

    def stop(self):
        """
        Stoppt alle laufenden Timer der HeaderBar.
        """

        Clock.unschedule(self.update_datetime)

    # =====================================================
    # Widget entfernt
    # =====================================================

    def on_parent(self, instance, parent):
        """
        Wird aufgerufen, wenn die HeaderBar aus dem
        Widgetbaum entfernt wird.
        """

        if parent is None:
            self.stop()

    # =====================================================
    # Aktualisierung erzwingen
    # =====================================================

    def refresh(self):
        """
        Aktualisiert den kompletten Header.
        """

        self.update_datetime()
        self._update_layout()

    # =====================================================
    # Header zurücksetzen
    # =====================================================

    def reset(self):
        """
        Setzt den Header auf den Standardzustand zurück.
        """

        self.set_event_name("Keine Veranstaltung")
        self.set_event_info("")
        self.set_revenue(0.0)
        self.update_datetime()

    # =====================================================
    # Sichtbarkeit
    # =====================================================

    def show(self):
        """
        Blendet die HeaderBar ein.
        """

        self.opacity = 1
        self.disabled = False

    # =====================================================
    # Ausblenden
    # =====================================================

    def hide(self):
        """
        Blendet die HeaderBar aus.
        """

        self.opacity = 0
        self.disabled = True
