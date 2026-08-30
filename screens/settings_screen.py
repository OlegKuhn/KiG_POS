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

import dateiwahl
import demo
import geraet
import storage
import teilen
import theme
import uebergabe
import zusammenfuehren

from database import DatabaseManager
from widgets.common.confirm_popup import ConfirmPopup
from widgets.common.exporthinweis import (
    export_hinweis, hinweisfeld_vorbereiten,
)
from widgets.common.kig_popup import KiGPopup
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_panel import RoundedPanel
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

        # Zuletzt geschriebene Datei - sie haengt am Teilen-Knopf.
        self.letzte_ausgabe = None

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
        # Auf jedem Gerät vorhanden: Ein Tablet im Ständer ist quer
        # ebenso sinnvoll wie ein Telefon hochkant.

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
        inhalt.add_widget(orientation_row)

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

        uebergabe_row = self._option_row()

        self.uebergeben_button = SettingsOptionButton(
            "Kasse übergeben", "abgeben", lambda _wert: self.kasse_uebergeben(),
        )
        uebergabe_row.add_widget(self.uebergeben_button)

        self.uebernehmen_button = SettingsOptionButton(
            "Übergabe einspielen", "uebernehmen",
            lambda _wert: self.uebergabe_einspielen(),
        )
        uebergabe_row.add_widget(self.uebernehmen_button)

        inhalt.add_widget(uebergabe_row)

        ausstattung_row = self._option_row()

        self.ausstatten_button = SettingsOptionButton(
            "Gerät ausstatten", "ausstatten",
            lambda _wert: self.geraet_ausstatten(),
        )
        ausstattung_row.add_widget(self.ausstatten_button)

        self.einrichten_button = SettingsOptionButton(
            "Ausstattung einspielen", "einrichten",
            lambda _wert: self.ausstattung_einspielen(),
        )
        ausstattung_row.add_widget(self.einrichten_button)

        inhalt.add_widget(ausstattung_row)

        zugaenge_row = self._option_row()

        self.bereitstellen_button = SettingsOptionButton(
            "Buchungen bereitstellen", "bereitstellen",
            lambda _wert: self.zugaenge_bereitstellen(),
        )
        zugaenge_row.add_widget(self.bereitstellen_button)

        self.einsammeln_button = SettingsOptionButton(
            "Buchungen einsammeln", "einsammeln",
            lambda _wert: self.zugaenge_einsammeln(),
        )
        zugaenge_row.add_widget(self.einsammeln_button)

        inhalt.add_widget(zugaenge_row)

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

        teilen_row = self._option_row()

        self.teilen_button = SettingsOptionButton(
            "Datei teilen", "teilen", lambda _wert: self.teilen_clicked(),
        )
        teilen_row.add_widget(self.teilen_button)

        self.bluetooth_button = SettingsOptionButton(
            "Per Bluetooth senden", "bluetooth",
            lambda _wert: self.per_bluetooth_clicked(),
        )
        teilen_row.add_widget(self.bluetooth_button)

        inhalt.add_widget(teilen_row)

        uebergabe_hint = KiGLabel(text=(
            "Artikel, Preise und Rezepte gehören dem Hauptgerät - dem, "
            "das die Kasse zuletzt übernommen hat. Alle anderen dürfen "
            "buchen, Listen führen und Schichten eintragen, aber die "
            "Stammdaten nicht ändern.\n\n"
            "\"Gerät ausstatten\" schreibt eine Kopie für einen "
            "weiteren Stand: Das andere Gerät bekommt alle Artikel und "
            "Preise und darf buchen, die Kasse bleibt aber hier. So "
            "arbeiten mehrere Tablets gleichzeitig.\n\n"
            "\"Kasse übergeben\" reicht das Hauptgerät weiter. "
            "\"Buchungen bereitstellen\" schreibt eine Datei mit dem "
            "eigenen Stand, ohne etwas abzugeben; \"Buchungen "
            "einsammeln\" holt aus so einer Datei alles heraus, was hier "
            "noch fehlt - Verkäufe, Kassenbuch, Listen. Zweimal "
            "eingesammelt ändert nichts.\n\n"
            "\"Datei teilen\" schickt die zuletzt geschriebene Datei "
            "weiter - per Mail, Messenger oder wohin auch immer. "
            "\"Per Bluetooth senden\" nimmt den kuerzesten Weg zum "
            "Geraet daneben: Am anderen Geraet annehmen, dann dort "
            "ueber \"Datei suchen\" einspielen."
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

    def kasse_uebergeben(self):
        """Gibt das Schreibrecht an ein anderes Gerät ab."""

        db = DatabaseManager()

        if db.nur_ansicht:
            self.uebergabe_status.text = (
                "Die Kasse liegt bereits bei einem anderen Gerät - "
                "abgeben kann nur, wer sie hat."
            )
            return

        inhalt = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        inhalt.add_widget(Label(
            text=(
                "An welches Gerät geht die Kasse?\n\n"
                "Der Name erscheint danach auf allen Geräten als "
                "Besitzer. Die Kennung des anderen Geräts steht dort "
                "unter \"Gerät und Übergabe\"."
            ),
            color=theme.TEXT_PRIMARY, font_size="15sp",
            size_hint_y=None, height=dp(96),
            halign="left", valign="top",
            text_size=(dp(420), dp(96)),
        ))

        name_feld = RoundedInput(
            hint_text="Name, z. B. Tablet", multiline=False,
            size_hint_y=None, height=dp(56),
        )
        name_feld.foreground_color = theme.INPUT_TEXT
        name_feld.hint_text_color = theme.INPUT_HINT
        inhalt.add_widget(name_feld)

        id_feld = RoundedInput(
            hint_text="Kennung, z. B. TAB-3f9a2c", multiline=False,
            size_hint_y=None, height=dp(56),
        )
        id_feld.foreground_color = theme.INPUT_TEXT
        id_feld.hint_text_color = theme.INPUT_HINT
        inhalt.add_widget(id_feld)

        popup = KiGPopup(
            title="Kasse übergeben", content=inhalt,
            size_hint=(0.6, None), height=dp(430), auto_dismiss=False,
        )

        knoepfe = BoxLayout(
            size_hint_y=None, height=dp(52), spacing=dp(theme.ROW_SPACING)
        )
        knoepfe.add_widget(self._popup_button("Abbrechen", popup.dismiss))
        knoepfe.add_widget(self._popup_button(
            "Übergeben",
            lambda: (
                popup.dismiss(),
                self._uebergabe_bestaetigen(id_feld.text, name_feld.text),
            ),
            hervorgehoben=True,
        ))
        inhalt.add_widget(knoepfe)

        popup.open()

    def _uebergabe_bestaetigen(self, an_id, an_name):

        an_id = (an_id or "").strip()
        an_name = (an_name or "").strip()

        if not an_id or not an_name:
            self.uebergabe_status.text = (
                "Name und Kennung des anderen Geräts werden gebraucht."
            )
            return

        ConfirmPopup(
            title="Kasse übergeben",
            message=(
                f"Kasse an \"{an_name}\" übergeben?\n\n"
                f"Dieses Gerät kann danach nur noch zusehen. Zum "
                f"Weiterarbeiten muss es die Kasse zurückbekommen."
            ),
            confirm_text="Übergeben",
            on_confirm=lambda: self._uebergabe_ausfuehren(an_id, an_name),
        ).open()

    def _uebergabe_ausfuehren(self, an_id, an_name):

        db = DatabaseManager()

        # Zweite Sicherung, direkt vor der Tat.
        #
        # Beim Öffnen des Dialogs wurde das schon geprüft - aber
        # zwischen Frage und Antwort kann die Kasse längst weg sein,
        # etwa weil die Rückfrage zweimal ausgelöst wurde. Genau das
        # ist passiert: zwei Übergaben vier Sekunden auseinander, die
        # zweite von "Computer" an "Computer".
        if db.nur_ansicht:

            self.uebergabe_status.text = (
                "Die Kasse liegt bereits bei einem anderen Gerät - "
                "abgeben kann nur, wer sie hat."
            )
            return

        try:
            ziel, stand = uebergabe.abgeben(
                db, an_id, an_name, storage.export_dir("uebergabe")
            )

        except Exception as fehler:
            self.uebergabe_status.text = f"Übergabe fehlgeschlagen: {fehler}"
            return

        self.letzte_ausgabe = ziel

        self.uebergabe_status.text = export_hinweis(
            ziel, was=f"Übergeben an {an_name} (Stand {stand})"
        )

        # Der Kopfbereich zeigt ab jetzt "Nur Ansicht".
        app = App.get_running_app()

        if app is not None and hasattr(app, "rebuild_main"):
            app.rebuild_main()

    def uebergabe_einspielen(self):
        """Öffnet eine Übergabedatei und fragt, was drinsteht."""

        self._datei_waehlen(
            titel="Übergabe einspielen",
            weiter=self._datei_pruefen,
            hinweis=(
                "Die Übergabedatei vom anderen Gerät zuerst in diesen "
                "Ordner kopieren."
            ),
        )

    def _datei_waehlen(self, titel, weiter, hinweis):
        """Zeigt die vorhandenen Dateien und reicht die gewählte an
        `weiter`.

        Dieselbe Auswahl für Übergabe und Einsammeln - beide holen
        ihre Dateien aus demselben Ordner, und zwei verschiedene
        Auswahldialoge wären nur zwei Stellen zum Auseinanderlaufen.

        Auf dem Rechner steht zusätzlich, was in Downloads, auf dem
        Desktop oder im Bluetooth-Ordner liegt: Genau dort landet eine
        empfangene Datei (siehe dateiwahl.uebergabedateien).
        """

        ordner = storage.export_dir("uebergabe")

        dateien = dateiwahl.uebergabedateien(ordner, uebergabe.ENDUNG)

        inhalt = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        popup = KiGPopup(
            title=titel, content=inhalt,
            size_hint=(0.62, None), height=dp(460), auto_dismiss=False,
        )

        if not dateien:

            inhalt.add_widget(Label(
                text=(
                    f"Keine Datei gefunden.\n\n"
                    f"Gesucht wird hier:\n{ordner}\n\n"
                    f"und in Downloads, auf dem Desktop und im "
                    f"Bluetooth-Ordner - dort landet, was von außen "
                    f"kommt.\n\n{hinweis}"
                    if not dateiwahl.verfuegbar() else
                    f"In diesem Ordner liegt nichts:\n{ordner}\n\n"
                    f"Kam die Datei per Mail oder Messenger, liegt sie "
                    f"woanders - meist unter \"Download\". "
                    f"\"Datei suchen\" öffnet die Dateiauswahl des "
                    f"Geräts; dort ist sie zu finden."
                ),
                color=theme.TEXT_SECONDARY, font_size="14sp",
                halign="left", valign="top",
                text_size=(dp(460), dp(220)),
            ))

        else:

            inhalt.add_widget(Label(
                text="Welche Datei?",
                color=theme.TEXT_PRIMARY, font_size="16sp",
                size_hint_y=None, height=dp(34),
            ))

            liste = BoxLayout(
                orientation="vertical",
                spacing=dp(theme.SPACE_XS),
                size_hint_y=None,
            )
            liste.bind(minimum_height=liste.setter("height"))

            scroll = ScrollView(do_scroll_x=False, bar_width=dp(8))
            scroll.add_widget(liste)
            inhalt.add_widget(scroll)

            for pfad, herkunft in dateien:

                # Woher die Datei stammt, steht dabei - sonst wäre bei
                # zwei gleich benannten nicht zu erkennen, welche die
                # eben empfangene ist.
                beschriftung = (
                    f"{pfad.name}\n({herkunft})" if herkunft else pfad.name
                )

                knopf = self._popup_button(
                    beschriftung,
                    lambda p=pfad: (popup.dismiss(), weiter(p)),
                )
                knopf.font_size = "13sp"
                knopf.halign = "center"
                knopf.size_hint_y = None
                knopf.height = dp(50)

                liste.add_widget(knopf)

        fusszeile = BoxLayout(
            size_hint_y=None, height=dp(52), spacing=dp(theme.ROW_SPACING)
        )

        # Auf Android sucht die App nur in ihrem eigenen Ordner, und an
        # den kommt kein Dateimanager heran. Eine per Mail geschickte
        # Uebergabe liegt unter "Download" - dorthin reicht die App nur
        # ueber die Dateiauswahl des Systems (siehe dateiwahl.py).
        if dateiwahl.verfuegbar():

            fusszeile.add_widget(self._popup_button(
                "Datei suchen",
                lambda: self._systemauswahl(popup, ordner, weiter),
                hervorgehoben=True,
            ))

        fusszeile.add_widget(self._popup_button("Schließen", popup.dismiss))

        inhalt.add_widget(fusszeile)

        popup.open()

    def _systemauswahl(self, popup, ordner, weiter):
        """Holt eine Datei über die Dateiauswahl des Geräts.

        Sie wird in den Übergabeordner kopiert; von da an ist sie eine
        Datei wie jede andere und läuft durch dieselbe Prüfung.
        """

        popup.dismiss()

        self.uebergabe_status.text = "Dateiauswahl geöffnet..."

        def geholt(pfad):

            self.uebergabe_status.text = f"Übernommen: {pfad.name}"

            weiter(pfad)

        def schiefgegangen(meldung):

            self.uebergabe_status.text = meldung

        dateiwahl.auswaehlen(ordner, geholt, schiefgegangen)

    def _datei_pruefen(self, pfad):
        """Zeigt, was in der Datei steht, und fragt nach."""

        db = DatabaseManager()

        besitz = db.get_besitz()
        eigener_stand = besitz["stand"] if besitz else 0

        befund = uebergabe.pruefen(pfad, db.geraet["id"], eigener_stand)

        if not befund["lesbar"]:
            self.uebergabe_status.text = befund["grund"]
            return

        if befund["zu_alt"]:
            self.uebergabe_status.text = (
                f"Abgelehnt: Diese Datei hat Stand {befund['stand']}, "
                f"hier gilt schon Stand {eigener_stand}. Ihr Inhalt ist "
                f"älter - einspielen würde neuere Buchungen verlieren."
            )
            return

        beschreibung = (
            f"Von: {befund['besitzer_name']}\n"
            f"Stand: {befund['stand']}\n"
            f"Enthält: {befund['artikel']} Artikel, "
            f"{befund['verkaeufe']} Verkäufe"
        )

        if befund["letzter_verkauf"]:
            beschreibung += f"\nLetzter Verkauf: {befund['letzter_verkauf']}"

        if befund["fuer_mich"]:

            ConfirmPopup(
                title="Übergabe einspielen",
                message=(
                    f"{beschreibung}\n\n"
                    f"Diese Datei ist für dieses Gerät bestimmt. Der "
                    f"bisherige Stand hier wird ersetzt (eine Sicherung "
                    f"wird vorher angelegt)."
                ),
                confirm_text="Übernehmen",
                on_confirm=lambda: self._uebernahme_ausfuehren(pfad, False),
            ).open()

            return

        ConfirmPopup(
            title="Übernahme erzwingen",
            message=(
                f"{beschreibung}\n\n"
                f"ACHTUNG: Diese Datei ist NICHT an dieses Gerät "
                f"gerichtet, sondern an \"{befund['besitzer_name']}\". "
                f"Übernimm sie nur, wenn jenes Gerät nicht mehr "
                f"erreichbar ist - sonst arbeiten hinterher zwei Geräte "
                f"an getrennten Ständen weiter."
            ),
            confirm_text="Trotzdem übernehmen",
            confirm_color=theme.ERROR,
            on_confirm=lambda: self._uebernahme_ausfuehren(pfad, True),
        ).open()

    def _uebernahme_ausfuehren(self, pfad, erzwingen):

        db = DatabaseManager()

        try:
            sicherung = uebergabe.uebernehmen(db, pfad, erzwingen=erzwingen)

        except Exception as fehler:
            self.uebergabe_status.text = f"Einspielen fehlgeschlagen: {fehler}"
            return

        self.uebergabe_status.text = (
            f"Übernommen. Sicherung des vorherigen Standes: {sicherung.name}"
        )

        app = App.get_running_app()

        if app is not None and hasattr(app, "rebuild_main"):
            app.rebuild_main()

    # =====================================================
    # Weitere Geräte ausstatten
    # =====================================================

    def geraet_ausstatten(self):
        """Schreibt eine Kopie für einen weiteren Stand.

        Anders als die Übergabe wechselt dabei nichts: Dieses Gerät
        bleibt Hauptgerät und darf weiter Preise ändern.
        """

        db = DatabaseManager()

        if db.nur_ansicht:
            self.uebergabe_status.text = (
                "Ausstatten kann nur das Hauptgerät - hier liegt die "
                "Kasse gerade nicht."
            )
            return

        try:
            ziel, stand = uebergabe.ausstatten(
                db, storage.export_dir("uebergabe")
            )

        except Exception as fehler:
            self.uebergabe_status.text = f"Ausstatten fehlgeschlagen: {fehler}"
            return

        self.letzte_ausgabe = ziel

        self.uebergabe_status.text = export_hinweis(
            ziel, was=f"Kopie für ein weiteres Gerät (Stand {stand})"
        )

    def ausstattung_einspielen(self):
        """Richtet dieses Gerät mit den Daten eines anderen ein."""

        self._datei_waehlen(
            titel="Ausstattung einspielen",
            weiter=self._ausstattung_pruefen,
            hinweis=(
                "Die Datei \"kigpos_ausstattung_...\" vom Hauptgerät "
                "zuerst in diesen Ordner kopieren."
            ),
        )

    def _ausstattung_pruefen(self, pfad):
        """Zeigt, was in der Kopie steht, und fragt nach."""

        db = DatabaseManager()

        besitz = db.get_besitz()
        eigener_stand = besitz["stand"] if besitz else 0

        befund = uebergabe.pruefen(pfad, db.geraet["id"], eigener_stand)

        if not befund["lesbar"]:
            self.uebergabe_status.text = befund["grund"]
            return

        # Wer nach dem Einspielen die Kasse hat, steht in der Datei -
        # und das ist fast immer das ausstattende Gerät.
        wird_hauptgeraet = befund["besitzer_id"] == db.geraet["id"]

        rolle = (
            "Dieses Gerät wird damit Hauptgerät."
            if wird_hauptgeraet else
            f"Dieses Gerät wird Nebengerät: buchen ja, Artikel und "
            f"Preise ändern nein - die bleiben bei "
            f"\"{befund['besitzer_name']}\"."
        )

        ConfirmPopup(
            title="Ausstattung einspielen",
            message=(
                f"{befund['artikel']} Artikel, {befund['verkaeufe']} "
                f"Verkäufe.\n\n"
                f"ACHTUNG: Die bisherigen Daten dieses Geräts werden "
                f"ersetzt. Eine Sicherung wird vorher angelegt.\n\n"
                f"{rolle}"
            ),
            confirm_text="Einspielen",
            on_confirm=lambda: self._ausstattung_ausfuehren(pfad),
        ).open()

    def _ausstattung_ausfuehren(self, pfad):

        db = DatabaseManager()

        try:
            sicherung, nur_ansicht = uebergabe.einrichten(db, pfad)

        except Exception as fehler:
            self.uebergabe_status.text = f"Einspielen fehlgeschlagen: {fehler}"
            return

        rolle = "Nebengerät" if nur_ansicht else "Hauptgerät"

        self.uebergabe_status.text = (
            f"Eingerichtet als {rolle}. Sicherung des vorherigen "
            f"Standes: {sicherung.name}"
        )

        app = App.get_running_app()

        if app is not None and hasattr(app, "rebuild_main"):
            app.rebuild_main()

    # =====================================================
    # Buchungen mehrerer Geräte
    # =====================================================

    def zugaenge_bereitstellen(self):
        """Schreibt eine Datei mit dem eigenen Stand.

        Anders als die Übergabe wechselt dabei nichts - dieses Gerät
        bucht weiter.
        """

        db = DatabaseManager()

        try:
            ziel, verkaeufe = zusammenfuehren.bereitstellen(
                db, storage.export_dir("uebergabe")
            )

        except Exception as fehler:
            self.uebergabe_status.text = f"Fehlgeschlagen: {fehler}"
            return

        self.letzte_ausgabe = ziel

        self.uebergabe_status.text = export_hinweis(
            ziel, was=f"Bereitgestellt ({verkaeufe} Verkäufe)"
        )

    def teilen_clicked(self):
        """Gibt die zuletzt geschriebene Datei weiter (siehe teilen.py).

        Gemeint ist die Übergabe- oder Bereitstellungsdatei - genau die
        muss ja auf das andere Gerät.
        """

        erfolg, meldung = teilen.teilen(
            self.letzte_ausgabe, betreff="KiG POS Übergabe"
        )

        self.uebergabe_status.text = meldung

    def per_bluetooth_clicked(self):
        """Schickt die zuletzt geschriebene Datei über Bluetooth.

        Der kürzeste Weg zwischen zwei Geräten, die nebeneinander
        liegen: kein Kabel, kein Netz, kein Konto.
        """

        erfolg, meldung = teilen.per_bluetooth(
            self.letzte_ausgabe, betreff="KiG POS Übergabe"
        )

        self.uebergabe_status.text = meldung

    def zugaenge_einsammeln(self):
        """Holt aus einer bereitgestellten Datei alles, was hier
        fehlt."""

        self._datei_waehlen(
            titel="Buchungen einsammeln",
            weiter=self._zugaenge_pruefen,
            hinweis=(
                "Die Datei des anderen Geräts zuerst in diesen Ordner "
                "kopieren."
            ),
        )

    def _zugaenge_pruefen(self, pfad):

        db = DatabaseManager()

        befund = zusammenfuehren.vorschau(db, pfad)

        if not befund["lesbar"]:
            self.uebergabe_status.text = befund["grund"]
            return

        if not befund["gesamt"]:
            self.uebergabe_status.text = (
                f"Aus \"{pfad.name}\" gibt es nichts Neues - alles war "
                f"schon da."
            )
            return

        aufzaehlung = "\n".join(
            f"  {anzahl} {zusammenfuehren.BEZEICHNUNGEN.get(tabelle, tabelle)}"
            for tabelle, anzahl in befund["neu"].items()
        )

        herkunft = befund["geraet"] or "einem anderen Gerät"

        ConfirmPopup(
            title="Buchungen einsammeln",
            message=(
                f"Von {herkunft} kämen dazu:\n\n{aufzaehlung}\n\n"
                f"Nur Neues wird übernommen; Artikel und Preise bleiben "
                f"unverändert. Die Bestandsbewegungen kommen mit - der "
                f"Bestand stimmt danach über beide Geräte."
            ),
            confirm_text="Einsammeln",
            on_confirm=lambda: self._zugaenge_uebernehmen(pfad),
        ).open()

    def _zugaenge_uebernehmen(self, pfad):

        db = DatabaseManager()

        try:
            uebernommen = zusammenfuehren.einsammeln(db, pfad)

        except Exception as fehler:
            self.uebergabe_status.text = f"Einsammeln fehlgeschlagen: {fehler}"
            return

        self.uebergabe_status.text = zusammenfuehren.bericht(uebernommen)

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
