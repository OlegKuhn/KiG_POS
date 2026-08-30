"""
=========================================================
KiG POS
=========================================================

Datei:
    settings_screen.py

Beschreibung:
    Einstellungen der Anwendung.

    • Farbmodus: hell oder dunkel (siehe theme.py /
      KiGPOS.apply_theme_mode)
    • Bildschirmausrichtung: Quer- oder Hochformat (siehe
      theme.set_orientation / KiGPOS.apply_orientation)

    Beide Einstellungen werden in der Datenbank gespeichert und
    beim nächsten Start wieder angewendet.

Version:
    2.1.0
=========================================================
"""

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

import demo
import geraet
import storage
import theme

from database import DatabaseManager
from widgets.common.confirm_popup import ConfirmPopup
from widgets.common.exporthinweis import hinweisfeld_vorbereiten
from widgets.common.kig_popup import KiGPopup
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_panel import RoundedPanel
from widgets.common.uebertragung_dialog import (
    EmpfangenDialog, SendenDialog,
)
from widgets.kig_label import KiGLabel


class SettingsOptionButton(Button):
    """Auswählbare Kachel für eine Einstellung, im Stil von CategoryCard."""

    def __init__(self, label, value, callback, **kwargs):
        super().__init__(**kwargs)

        self.value = value
        self.callback = callback

        self.text = label
        self.font_size = "18sp"
        self.bold = True

        self.background_normal = ""
        self.background_down = ""

        self.size_hint_y = None
        self.height = dp(64)

        self.unselect()

        self.bind(on_release=lambda *_args: self.callback(self.value))

    def select(self):

        self.background_color = theme.PRIMARY_ORANGE
        self.color = theme.TEXT_WHITE

    def unselect(self):

        self.background_color = theme.SURFACE
        self.color = theme.TEXT_PRIMARY


class SettingsScreen(Screen):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        root = BoxLayout(padding=dp(theme.SCREEN_PADDING))

        panel = RoundedPanel(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING)
        )

        title = KiGLabel(text="Einstellungen")
        title.set_font_size(26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(42)
        panel.add_widget(title)

        # Die Einstellungen wachsen mit jeder Funktion; ohne
        # Rollbereich ragt der unterste Abschnitt aus der Karte, sobald
        # das Fenster etwas kleiner ist.
        inhalt = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            size_hint_y=None,
        )
        inhalt.bind(minimum_height=inhalt.setter("height"))

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(8))
        scroll.add_widget(inhalt)
        panel.add_widget(scroll)

        #
        # Farbmodus
        #

        inhalt.add_widget(self._section_label("Farbmodus"))

        mode_row = self._option_row()

        # Sonne und Mond standen hier als Zeichen - Kivys Schrift
        # kennt beide nicht und setzte ein leeres Kaestchen davor.
        # Die Woerter sagen ohnehin alles.
        self.light_button = SettingsOptionButton(
            "Hell", "light", self.select_mode
        )
        self.dark_button = SettingsOptionButton(
            "Dunkel", "dark", self.select_mode
        )

        if theme.get_mode() == "dark":
            self.dark_button.select()
        else:
            self.light_button.select()

        mode_row.add_widget(self.light_button)
        mode_row.add_widget(self.dark_button)
        inhalt.add_widget(mode_row)

        #
        # Bildschirmausrichtung
        #
        # Auf dem Tablet und am Rechner zur Wahl: Ein Tablet im Ständer
        # ist quer ebenso sinnvoll wie hochkant.
        #
        # Auf einem Telefon nicht. Quer blieben dort von 915 dp Höhe
        # noch 412 - abzüglich Kopf- und Fußzeile keine 300, und darin
        # sollen Kategorien, Artikel und Warenkorb untereinander Platz
        # finden. Die Wahl wird deshalb gar nicht erst angeboten (und
        # das Gerät selbst festgehalten, siehe
        # KiGPOS._drehung_festhalten).

        self.schmal = theme.is_narrow()

        if not self.schmal:

            inhalt.add_widget(self._section_label("Bildschirmausrichtung"))

        orientation_row = self._option_row()

        self.landscape_button = SettingsOptionButton(
            "Querformat", theme.ORIENTATION_LANDSCAPE, self.select_orientation
        )
        self.portrait_button = SettingsOptionButton(
            "Hochformat", theme.ORIENTATION_PORTRAIT, self.select_orientation
        )

        if theme.is_portrait():
            self.portrait_button.select()
        else:
            self.landscape_button.select()

        orientation_row.add_widget(self.landscape_button)
        orientation_row.add_widget(self.portrait_button)

        # Ohne diesen Hinweis wirkt es wie ein Fehler, wenn nach dem
        # Umschalten plötzlich das ganze Fenster seine Größe ändert.
        hint = KiGLabel(text=(
            "Im Hochformat stehen zusammengehörige Bereiche untereinander "
            "statt nebeneinander - gedacht für hochkant montierte "
            "Bildschirme und Telefone. Am Rechner wird das Fenster dabei "
            "passend angepasst, auf einem Gerät mit Drehsensor drehst du "
            "es einfach."
        ))
        hint.set_font_size(14)
        hint.set_alignment("left")
        hint.set_color(theme.TEXT_SECONDARY)
        # Waechst mit dem Text: Auf einem Telefon braucht
        # derselbe Satz doppelt so viele Zeilen wie am Rechner,
        # und eine feste Hoehe schnitt den Rest einfach ab.
        hinweisfeld_vorbereiten(hint, dp(46))

        if not self.schmal:
            inhalt.add_widget(orientation_row)
            inhalt.add_widget(hint)

        #
        # Demo-Modus
        #

        inhalt.add_widget(self._section_label("Demo"))

        demo_row = self._option_row()

        self.demo_button = SettingsOptionButton(
            "Demo beenden" if demo.ist_aktiv() else "Demo starten",
            "demo", lambda _wert: self.toggle_demo(),
        )

        if demo.ist_aktiv():
            self.demo_button.select()

        demo_row.add_widget(self.demo_button)

        # Zweite Haelfte bleibt leer, damit der Knopf dieselbe Breite
        # hat wie die Knoepfe darueber.
        demo_row.add_widget(BoxLayout())

        inhalt.add_widget(demo_row)

        demo_hint = KiGLabel(text=(
            "Im Demo-Modus arbeitet das Programm auf einer Kopie der "
            "Datenbank: Alles lässt sich ausprobieren, Verkäufe, Artikel "
            "und Listen werden gespeichert - aber nur in der Kopie. Die "
            "Akzentfarbe wird grün und oben steht DEMO.\n\n"
            "Beim Beenden des Demo-Modus wird die Kopie verworfen; es "
            "gilt wieder der Stand von vorher. Nach einem Programmstart "
            "läuft immer der normale Modus."
        ))
        demo_hint.set_font_size(14)
        demo_hint.set_alignment("left")
        demo_hint.set_color(theme.TEXT_SECONDARY)
        # Waechst mit dem Text: Auf einem Telefon braucht
        # derselbe Satz doppelt so viele Zeilen wie am Rechner,
        # und eine feste Hoehe schnitt den Rest einfach ab.
        hinweisfeld_vorbereiten(demo_hint, dp(76))
        inhalt.add_widget(demo_hint)

        #
        # Datenaustausch zwischen Geräten
        #

        inhalt.add_widget(self._section_label("Gerät und Übergabe"))

        self.geraet_label = KiGLabel(text="")
        self.geraet_label.set_font_size(15)
        self.geraet_label.set_alignment("left")
        self.geraet_label.set_color(theme.TEXT_PRIMARY)
        self.geraet_label.size_hint_y = None
        self.geraet_label.height = dp(52)
        inhalt.add_widget(self.geraet_label)

        # Zwei Fragen statt sechs Schaltflächen: sende ich, oder
        # empfange ich? Alles Weitere fragt der Dialog nacheinander ab
        # (siehe widgets/common/uebertragung_dialog.py).
        #
        # Vorher standen hier "Kasse übergeben", "Übergabe einspielen",
        # "Gerät ausstatten", "Ausstattung einspielen", "Buchungen
        # bereitstellen" und "Buchungen einsammeln" nebeneinander - man
        # musste wissen, welche zu welcher Gegenseite gehört, und auf
        # einem Telefon fand man sie ohnehin kaum.
        uebertragung_row = self._option_row()

        self.senden_button = SettingsOptionButton(
            "Daten senden", "senden", lambda _wert: self.daten_senden(),
        )
        uebertragung_row.add_widget(self.senden_button)

        self.empfangen_button = SettingsOptionButton(
            "Daten empfangen", "empfangen",
            lambda _wert: self.daten_empfangen(),
        )
        uebertragung_row.add_widget(self.empfangen_button)

        inhalt.add_widget(uebertragung_row)

        protokoll_row = self._option_row()

        self.protokoll_button = SettingsOptionButton(
            "Übergaben anzeigen", "protokoll",
            lambda _wert: self.uebergaben_anzeigen(),
        )
        protokoll_row.add_widget(self.protokoll_button)

        self.umbenennen_button = SettingsOptionButton(
            "Gerät umbenennen", "umbenennen",
            lambda _wert: self.geraet_umbenennen(),
        )
        protokoll_row.add_widget(self.umbenennen_button)

        inhalt.add_widget(protokoll_row)

        uebergabe_hint = KiGLabel(text=(
            "Artikel, Preise und Rezepte gehören dem Hauptgerät - dem, "
            "das die Kasse zuletzt übernommen hat. Alle anderen dürfen "
            "buchen, Listen führen und Schichten eintragen, aber die "
            "Stammdaten nicht ändern.\n\n"
            "Zum Übertragen zuerst am EMPFANGENDEN Gerät \"Daten "
            "empfangen\" wählen - es wartet dann. Am sendenden dann "
            "\"Daten senden\": Es sucht im WLAN, die Gegenseite nimmt "
            "an, und erst danach wird gewählt, was hinübergeht:\n\n"
            "Datenbank - Artikel und Preise für einen weiteren Stand. "
            "Das andere Gerät darf mitverkaufen, die Kasse bleibt "
            "hier.\n\n"
            "Kasse - das Schreibrecht selbst. Danach darf das andere "
            "Gerät ändern und dieses nur noch zusehen.\n\n"
            "Buchungen - nur was dazugekommen ist. Zweimal "
            "eingesammelt ändert nichts.\n\n"
            "Ohne gemeinsames WLAN führt derselbe Dialog über eine "
            "Datei: schreiben, per Bluetooth oder Mail hinüber, dort "
            "wieder einlesen."
        ))
        uebergabe_hint.set_font_size(14)
        uebergabe_hint.set_alignment("left")
        uebergabe_hint.set_color(theme.TEXT_SECONDARY)
        # Waechst mit dem Text: Auf einem Telefon braucht
        # derselbe Satz doppelt so viele Zeilen wie am Rechner,
        # und eine feste Hoehe schnitt den Rest einfach ab.
        hinweisfeld_vorbereiten(uebergabe_hint, dp(290))
        inhalt.add_widget(uebergabe_hint)

        self.uebergabe_status = Label(
            text="", color=theme.TEXT_SECONDARY, font_size="13sp",
            halign="left", valign="middle",
        )
        hinweisfeld_vorbereiten(self.uebergabe_status, dp(8))
        inhalt.add_widget(self.uebergabe_status)

        self._geraet_anzeigen()

        root.add_widget(panel)
        self.add_widget(root)

    # =====================================================
    # Bausteine
    # =====================================================

    @staticmethod
    def _section_label(text):

        label = KiGLabel(text=text)
        label.set_font_size(18)
        label.set_bold(True)
        label.set_alignment("left")
        label.set_color(theme.TEXT_PRIMARY)
        label.size_hint_y = None
        label.height = dp(30)

        return label

    @staticmethod
    def _option_row():

        return BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            spacing=dp(theme.ROW_SPACING)
        )

    # =====================================================
    # Auswahl
    # =====================================================

    def select_mode(self, mode):

        if mode == theme.get_mode():
            return

        app = App.get_running_app()

        if app is not None:
            app.apply_theme_mode(mode)

    def select_orientation(self, orientation):

        if orientation == theme.get_orientation():
            return

        app = App.get_running_app()

        if app is not None:
            app.apply_orientation(orientation)

    # =====================================================
    # Demo-Modus
    # =====================================================

    # =====================================================
    # Gerät und Übergabe
    # =====================================================

    def _geraet_anzeigen(self):
        """Zeigt an, wer dieses Gerät ist und wem die Kasse gehört."""

        db = DatabaseManager()

        besitz = db.get_besitz()

        eigen = f"Dieses Gerät: {db.geraet['name']}   ({db.geraet['id']})"

        if besitz is None:
            zustand = "Die Kasse gehört noch niemandem."

        elif besitz["geraet_id"] == db.geraet["id"]:
            zustand = (
                f"Hauptgerät - Stand {besitz['stand']}, "
                f"seit {self._kurzes_datum(besitz['seit'])}."
            )

        else:
            zustand = (
                f"Nebengerät: buchen ja, Stammdaten liegen bei "
                f"{besitz['geraet_name']} - Stand {besitz['stand']}, "
                f"seit {self._kurzes_datum(besitz['seit'])}."
            )

        self.geraet_label.set_text(f"{eigen}\n{zustand}")

        self.geraet_label.set_color(
            theme.WARNING if db.nur_ansicht else theme.TEXT_PRIMARY
        )

    @staticmethod
    def _kurzes_datum(zeitstempel):

        if not zeitstempel:
            return "unbekannt"

        try:
            from datetime import datetime

            return datetime.strptime(
                zeitstempel, "%Y-%m-%d %H:%M:%S"
            ).strftime("%d.%m.%Y %H:%M")

        except (TypeError, ValueError):
            return str(zeitstempel)

    def geraet_umbenennen(self):
        """Der Name steht in jeder Übergabe - "Tablet" liest sich
        besser als "TAB-3f9a2c"."""

        db = DatabaseManager()

        inhalt = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        feld = RoundedInput(
            text=db.geraet["name"], multiline=False,
            size_hint_y=None, height=dp(56),
        )
        feld.foreground_color = theme.INPUT_TEXT

        inhalt.add_widget(Label(
            text="Wie soll dieses Gerät heißen?",
            color=theme.TEXT_PRIMARY, font_size="16sp",
            size_hint_y=None, height=dp(34),
        ))
        inhalt.add_widget(feld)

        popup = KiGPopup(
            title="Gerät umbenennen", content=inhalt,
            size_hint=(0.55, None), height=dp(300), auto_dismiss=False,
        )

        knoepfe = BoxLayout(
            size_hint_y=None, height=dp(52), spacing=dp(theme.ROW_SPACING)
        )
        knoepfe.add_widget(self._popup_button("Abbrechen", popup.dismiss))
        knoepfe.add_widget(self._popup_button(
            "Übernehmen",
            lambda: (popup.dismiss(), self._namen_speichern(feld.text)),
            hervorgehoben=True,
        ))
        inhalt.add_widget(knoepfe)

        popup.open()

        feld.focus = True

    def _namen_speichern(self, name):

        db = DatabaseManager()

        daten = geraet.umbenennen(storage.data_dir(), name)

        if daten is None:
            return

        db.geraet = daten

        # Steht dieses Gerät als Besitzer in der Datenbank, wandert
        # der neue Name gleich mit - sonst hieße es dort weiter alt.
        besitz = db.get_besitz()

        if besitz and besitz["geraet_id"] == daten["id"] and not db.nur_ansicht:
            db.besitz_uebernehmen(
                daten["id"], daten["name"], stand=besitz["stand"]
            )

        self._geraet_anzeigen()

    # =====================================================
    # Daten von Gerät zu Gerät
    # =====================================================
    #
    # Der ganze Ablauf steckt in zwei Dialogen (siehe
    # widgets/common/uebertragung_dialog.py). Hier stehen nur noch die
    # beiden Einstiege - und die eine Regel, die vorher gilt.

    def daten_senden(self):
        """Sucht ein wartendes Gerät und schickt ihm etwas."""

        SendenDialog(on_fertig=self._neu_aufbauen).open()

    def daten_empfangen(self):
        """Wartet auf ein sendendes Gerät."""

        EmpfangenDialog(on_fertig=self._neu_aufbauen).open()

    @staticmethod
    def _neu_aufbauen():
        """Nach einer Übertragung kann sich alles geändert haben -
        Artikel, Preise, wer die Kasse hat."""

        app = App.get_running_app()

        if app is not None and hasattr(app, "rebuild_main"):
            app.rebuild_main()


    def uebergaben_anzeigen(self):
        """Das Protokoll: wer hat wann an wen übergeben?"""

        db = DatabaseManager()

        inhalt = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        popup = KiGPopup(
            title="Übergaben", content=inhalt,
            size_hint=(0.62, None), height=dp(460), auto_dismiss=False,
        )

        eintraege = db.get_uebergaben()

        if not eintraege:

            inhalt.add_widget(Label(
                text="Noch keine Übergabe.",
                color=theme.TEXT_SECONDARY, font_size="15sp",
                halign="left", valign="top",
            ))

        else:

            liste = BoxLayout(
                orientation="vertical",
                spacing=dp(theme.SPACE_XS),
                size_hint_y=None,
            )
            liste.bind(minimum_height=liste.setter("height"))

            scroll = ScrollView(do_scroll_x=False, bar_width=dp(8))
            scroll.add_widget(liste)
            inhalt.add_widget(scroll)

            for eintrag in eintraege:

                von = eintrag["von_name"] or "Erstanlage"

                zeile = Label(
                    text=(
                        f"Stand {eintrag['stand']:>3}   "
                        f"{self._kurzes_datum(eintrag['zeitpunkt'])}   "
                        f"{von} → {eintrag['an_name']}"
                    ),
                    color=theme.TEXT_PRIMARY, font_size="14sp",
                    size_hint_y=None, height=dp(40),
                    halign="left", valign="middle",
                )
                zeile.bind(
                    size=lambda instanz, groesse: setattr(
                        instanz, "text_size", groesse
                    )
                )

                liste.add_widget(zeile)

        schliessen = self._popup_button("Schließen", popup.dismiss)
        schliessen.size_hint_y = None
        schliessen.height = dp(52)
        inhalt.add_widget(schliessen)

        popup.open()

    @staticmethod
    def _popup_button(text, callback, hervorgehoben=False):

        button = Button(
            text=text, background_normal="", background_down="",
            background_color=(
                theme.PRIMARY_ORANGE if hervorgehoben else theme.SURFACE
            ),
            color=theme.TEXT_WHITE if hervorgehoben else theme.TEXT_PRIMARY,
            font_size="15sp", bold=True,
        )
        button.bind(on_release=lambda *_args: callback())

        return button

    def toggle_demo(self):
        """Startet den Demo-Modus oder verlässt ihn.

        Beides mit Rückfrage: Beim Start wird die Datenbank
        eingefroren, beim Beenden alles Ausprobierte verworfen - in
        beiden Fällen soll klar sein, was gleich passiert.
        """

        app = App.get_running_app()

        if app is None:
            return

        if demo.ist_aktiv():

            ConfirmPopup(
                title="Demo beenden",
                message=(
                    "Demo-Modus beenden?\n\n"
                    "Alles, was im Demo-Modus angelegt oder geändert "
                    "wurde, wird verworfen. Es gilt wieder der Stand "
                    "von vor dem Start."
                ),
                confirm_text="Beenden",
                on_confirm=lambda: app.apply_demo_mode(False),
            ).open()

            return

        ConfirmPopup(
            title="Demo starten",
            message=(
                "Demo-Modus starten?\n\n"
                "Der aktuelle Stand der Datenbank wird eingefroren. "
                "Ab dann arbeitest du auf einer Kopie - an den echten "
                "Daten ändert sich nichts."
            ),
            confirm_text="Starten",
            confirm_color=theme.SUCCESS,
            on_confirm=lambda: app.apply_demo_mode(True),
        ).open()
