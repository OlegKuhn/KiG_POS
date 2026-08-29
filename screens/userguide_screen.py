"""
=========================================================
KiG POS
=========================================================

Datei:
    userguide_screen.py

Beschreibung:
    Benutzerhandbuch der Anwendung.

    Links eine Liste der Themen (ein Thema je Screen der
    Anwendung), rechts die zugehörige Schritt-für-Schritt-
    Anleitung inklusive Screenshots. Die eigentlichen Inhalte
    liegen in widgets/userguide/content.py.

Version:
    1.0.0
=========================================================
"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

import teilen
import theme

from widgets.common.exporthinweis import export_hinweis

from widgets.userguide.content import TOPICS
from widgets.userguide.userguide_topic_panel import UserguideTopicPanel
from widgets.userguide.userguide_content_panel import UserguideContentPanel

# Der PDF-Export braucht reportlab. Auf dem Windows-Rechner ist das
# Teil der Installation; auf Android hängt es davon ab, ob sich die
# Bibliothek mitbauen ließ. Fehlt sie, soll das Handbuch trotzdem
# lesbar sein - deshalb hier kein harter Import, der sonst die ganze
# Anwendung am Start hindern würde.
try:
    from widgets.userguide.pdf_export import export_userguide_pdf
    PDF_EXPORT_FEHLER = None

except Exception as fehler:
    export_userguide_pdf = None
    PDF_EXPORT_FEHLER = str(fehler)


class UserguideScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Im Hochformat steht die Themenliste über der Anleitung statt
        # daneben (siehe theme.set_orientation).
        hochformat = theme.is_portrait()

        self.topic_panel = UserguideTopicPanel(
            on_select_topic=self.select_topic,
            on_export_pdf=self.export_pdf,
            on_teilen=self.teilen_clicked,
            size_hint=(1, 0.32) if hochformat else (0.3, 1)
        )

        self.content_panel = UserguideContentPanel(
            size_hint=(1, 0.68) if hochformat else (0.7, 1)
        )

        root = BoxLayout(
            orientation="vertical" if hochformat else "horizontal",
            padding=dp(theme.SCREEN_PADDING),
            spacing=dp(theme.SCREEN_SPACING)
        )
        root.add_widget(self.topic_panel)
        root.add_widget(self.content_panel)
        self.add_widget(root)

        self._loaded = False

        # Zuletzt ausgegebene Datei - sie haengt am Teilen-Knopf.
        self.letzte_ausgabe = None

    def on_pre_enter(self, *args):

        if self._loaded:
            return

        self._loaded = True

        self.topic_panel.set_topics(TOPICS)
        self.topic_panel.select_first()

        if export_userguide_pdf is None:
            self.topic_panel.set_export_available(False)

    def select_topic(self, topic):

        self.content_panel.set_topic(topic)

    # =====================================================
    # PDF-Export
    # =====================================================

    def export_pdf(self):
        """Erzeugt das komplette Handbuch als PDF.

        Das Zusammenbauen dauert wegen der eingebetteten Screenshots
        einen Moment. Damit die Oberfläche in dieser Zeit nicht
        einfriert wirkt, wird der Knopf zuerst gesperrt und die
        eigentliche Arbeit erst im nächsten Frame erledigt - so kann
        Kivy den Zwischenstand vorher noch zeichnen.
        """

        if export_userguide_pdf is None:
            self.topic_panel.set_export_status(
                f"PDF-Export nicht verfügbar ({PDF_EXPORT_FEHLER})"
            )
            return

        self.topic_panel.set_export_busy(True)
        self.topic_panel.set_export_status("")

        Clock.schedule_once(lambda _dt: self._run_export(), 0)

    def _run_export(self):

        try:
            path = export_userguide_pdf(TOPICS)
        except Exception as error:
            self.topic_panel.set_export_status(f"Export fehlgeschlagen: {error}")
        else:
            self.letzte_ausgabe = path

            self.topic_panel.set_export_status(
                export_hinweis(path, was="Gespeichert")
            )
        finally:
            self.topic_panel.set_export_busy(False)

    def teilen_clicked(self):
        """Gibt die zuletzt ausgegebene Datei weiter (siehe teilen.py)."""

        erfolg, meldung = teilen.teilen(self.letzte_ausgabe, betreff="KiG POS Handbuch")

        self.topic_panel.set_export_status(meldung)
