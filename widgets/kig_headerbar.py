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
    • Veranstaltungsname
    • Veranstaltungsinformation
    • Datum
    • Uhrzeit
    • Tagesumsatz

Version:
    1.0 Final

Build:
    0001

=========================================================
"""

from datetime import datetime

from kivy.clock import Clock

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

import theme


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

    LOGO_SIZE = 120

    LOGO_AREA_WIDTH = 140

    STATUS_AREA_WIDTH = 160

    PADDING_LEFT = 20

    PADDING_RIGHT = 20

    PADDING_TOP = 10

    PADDING_BOTTOM = 10

    CONTENT_SPACING = 15

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

        with self.canvas.after:
            Color(*theme.HEADER_SEPARATOR)

            self.separator = Line(width=1)


        #
        # Hauptlayout
        #

        self.content = BoxLayout(

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

        self.logo = KiGLogoButton()

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
            (0, 0, 0, 1)
        )

        self.lbl_event_info.set_color(
            (0, 0, 0, 0.5)
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

            height=dp(70)

        )

        #
        # Datum / Uhrzeit
        #

        self.lbl_datetime = KiGLabel()

        self.lbl_datetime.set_text("--.-- | --:--")

        self.lbl_datetime.set_font_size(15)

        self.lbl_datetime.set_bold(True)

        self.lbl_datetime.set_color(
            (0, 0, 0, 1)
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
            theme.TEXT_SECONDARY
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
            theme.PRIMARY_ORANGE
        )

        #
        # Labels hinzufügen
        #

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