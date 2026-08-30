"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/uebertragung_dialog.py

Beschreibung:
    Der geführte Weg von Gerät zu Gerät.

    Statt sechs Schaltflächen, bei denen man wissen muss,
    welche zu welcher Gegenseite gehört, gibt es nur noch
    zwei Fragen: sende ich, oder empfange ich? Alles
    Weitere fragt der Dialog nacheinander ab.

    Senden:

        1. Wer ist da?        Suche im Netz
        2. Anklopfen          die Gegenseite bestätigt
        3. Was soll rüber?    Datenbank, Kasse, Buchungen
        4. Übertragen         mit Rückmeldung von drüben

    Empfangen:

        1. Warten             mit eigener Adresse, falls die
                              Suche nichts findet
        2. Annehmen?          wer klopft, steht dabei
        3. Einspielen         und melden, was daraus wurde

    Die Reihenfolge ist Absicht: Erst sagt die Gegenseite
    ja, dann erst wird ausgewählt, WAS geht. So kann man
    nicht versehentlich die Kasse an ein Gerät abgeben,
    das gar nicht bereit ist.

    Ohne Netz bleibt der Dateiweg: Beim Senden schreibt der
    Dialog die Datei und öffnet die Teilen-Auswahl, beim
    Empfangen sucht er sie (siehe teilen.py, dateiwahl.py).

    Alles Netzwerkgeschehen läuft in eigenen Fäden; jede
    Rückmeldung wird über Clock in den Takt der Oberfläche
    zurückgeholt.

Version:
    1.0.0
=========================================================
"""

import threading

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import dateiwahl
import datenpaket
import funk
import storage
import teilen
import theme

from database import DatabaseManager
from widgets.common.kig_popup import KiGPopup


class AblaufPopup(KiGPopup):
    """Ein Dialog, der seinen Inhalt Schritt für Schritt austauscht.

    Immer gleich aufgebaut: oben der Text, darunter die möglichen
    Antworten. So bleibt bei jedem Schritt sichtbar, was gerade
    passiert und was man tun kann.
    """

    def __init__(self, titel, **kwargs):

        super().__init__(**kwargs)

        self.title = titel

        self.size_hint = (0.7, None)
        self.height = dp(460)
        self.auto_dismiss = False

        inhalt = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        with inhalt.canvas.before:
            Color(*theme.CARD)
            self._hintergrund = Rectangle(pos=inhalt.pos, size=inhalt.size)

        inhalt.bind(
            pos=self._hintergrund_setzen, size=self._hintergrund_setzen
        )

        self.text = Label(
            text="", color=theme.TEXT_PRIMARY, font_size="15sp",
            halign="left", valign="top", size_hint_y=None,
        )
        self.text.bind(
            width=lambda instanz, breite: setattr(
                instanz, "text_size", (breite, None)
            ),
            texture_size=lambda instanz, groesse: setattr(
                instanz, "height", groesse[1]
            ),
        )

        kopf = ScrollView(do_scroll_x=False, bar_width=dp(6))
        kopf.add_widget(self.text)
        inhalt.add_widget(kopf)

        self.knopfbereich = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            size_hint_y=None,
        )
        self.knopfbereich.bind(
            minimum_height=self.knopfbereich.setter("height")
        )

        auswahl = ScrollView(do_scroll_x=False, bar_width=dp(6))
        auswahl.add_widget(self.knopfbereich)
        inhalt.add_widget(auswahl)

        self.content = inhalt

    def _hintergrund_setzen(self, instanz, _wert):

        self._hintergrund.pos = instanz.pos
        self._hintergrund.size = instanz.size

    # -----------------------------------------------------

    def zeige(self, text, knoepfe=()):
        """Setzt Text und Antworten neu.

        knoepfe: Folge von (Beschriftung, Rückruf, hervorgehoben)
        """

        self.text.text = text

        self.knopfbereich.clear_widgets()

        for eintrag in knoepfe:

            beschriftung, rueckruf = eintrag[0], eintrag[1]
            hervor = eintrag[2] if len(eintrag) > 2 else False

            knopf = Button(
                text=beschriftung,
                size_hint_y=None, height=dp(52),
                background_normal="", background_down="",
                background_color=(
                    theme.PRIMARY_ORANGE if hervor else theme.SURFACE
                ),
                color=theme.TEXT_WHITE if hervor else theme.TEXT_PRIMARY,
                font_size="15sp", bold=True,
                halign="center", valign="middle",
            )
            knopf.bind(
                size=lambda instanz, groesse: setattr(
                    instanz, "text_size", groesse
                )
            )
            knopf.bind(on_release=lambda _i, r=rueckruf: r())

            self.knopfbereich.add_widget(knopf)


class EmpfangenDialog(AblaufPopup):
    """Wartet auf ein sendendes Gerät."""

    def __init__(self, on_fertig=None, **kwargs):

        super().__init__("Daten empfangen", **kwargs)

        self.on_fertig = on_fertig

        self.db = DatabaseManager()

        self.empfaenger = funk.Empfaenger(
            name=self.db.geraet["name"],
            kennung=self.db.geraet["id"],
            zielordner=storage.export_dir("uebergabe"),
        )

        self.bind(on_dismiss=lambda *_a: self.empfaenger.stop())

        self._warten_anzeigen()

        self.empfaenger.start(
            on_anfrage=self._anfrage,
            on_datei=self._datei,
            on_fehler=self._fehler,
            on_stand=self._stand,
        )

    # -----------------------------------------------------

    def _im_takt(self, funktion, *args):
        """Zurück in den Takt der Oberfläche - die Rückrufe kommen aus
        einem Netzwerkfaden."""

        Clock.schedule_once(lambda _dt: funktion(*args), 0)

    def _warten_anzeigen(self):

        adresse = funk.eigene_adresse()

        self.zeige(
            f"Dieses Gerät wartet als \"{self.db.geraet['name']}\".\n\n"
            f"Am anderen Gerät \"Daten senden\" wählen - dieses hier "
            f"sollte in der Liste stehen.\n\n"
            f"Findet die Suche nichts, dort die Adresse von Hand "
            f"eingeben:\n{adresse}\n\n"
            f"Beide Geräte müssen im selben WLAN sein.",
            (
                ("Kein Netz? Datei suchen", self._datei_suchen),
                ("Abbrechen", self.dismiss),
            ),
        )

    # -----------------------------------------------------
    # Rückrufe aus dem Netzwerkfaden
    # -----------------------------------------------------

    def _anfrage(self, name, kennung, antworten):

        self._im_takt(self._anfrage_zeigen, name, kennung, antworten)

    def _anfrage_zeigen(self, name, kennung, antworten):

        def ja():
            antworten(True)
            self.zeige(f"Angenommen. \"{name}\" sendet ...", ())

        def nein():
            antworten(False)
            self._warten_anzeigen()

        self.zeige(
            f"\"{name}\" möchte Daten an dieses Gerät senden.\n\n"
            f"Kennung: {kennung}\n\n"
            f"Was genau, wählt die Gegenseite als Nächstes.",
            (
                ("Annehmen", ja, True),
                ("Ablehnen", nein),
            ),
        )

    def _datei(self, art, pfad):
        """Läuft im Netzwerkfaden - das Einspielen selbst gehört aber
        in den Takt der Oberfläche, weil danach neu aufgebaut wird."""

        ergebnis = {"meldung": "Empfangen."}

        fertig = threading.Event()

        def einspielen():

            try:
                ergebnis["meldung"] = datenpaket.einspielen(
                    self.db, art, pfad
                )

            except Exception as fehler:
                ergebnis["meldung"] = f"Einspielen fehlgeschlagen: {fehler}"

            finally:
                fertig.set()

            self._abschluss(art, ergebnis["meldung"])

        self._im_takt(einspielen)

        # Die Gegenseite wartet auf die Rückmeldung - erst antworten,
        # wenn wirklich eingespielt ist.
        fertig.wait(60)

        return ergebnis["meldung"]

    def _abschluss(self, art, meldung):

        self.zeige(
            f"{datenpaket.BESCHRIFTUNG.get(art, art)} empfangen.\n\n"
            f"{meldung}",
            (("Schließen", self._schliessen_und_melden, True),),
        )

    def _schliessen_und_melden(self):

        self.dismiss()

        if callable(self.on_fertig):
            self.on_fertig()

    def _fehler(self, meldung):

        self._im_takt(
            self.zeige,
            f"{meldung}",
            (
                ("Nochmal warten", self._neu_warten),
                ("Schließen", self.dismiss),
            ),
        )

    def _neu_warten(self):

        self.empfaenger.stop()

        self.empfaenger = funk.Empfaenger(
            name=self.db.geraet["name"],
            kennung=self.db.geraet["id"],
            zielordner=storage.export_dir("uebergabe"),
        )

        self._warten_anzeigen()

        self.empfaenger.start(
            on_anfrage=self._anfrage,
            on_datei=self._datei,
            on_fehler=self._fehler,
            on_stand=self._stand,
        )

    def _stand(self, meldung):

        self._im_takt(self.zeige, meldung, ())

    # -----------------------------------------------------
    # Rückfall: Datei
    # -----------------------------------------------------

    def _datei_suchen(self):

        self.empfaenger.stop()

        ordner = storage.export_dir("uebergabe")

        dateien = dateiwahl.uebergabedateien(ordner)

        knoepfe = []

        for pfad, herkunft in dateien:

            beschriftung = (
                f"{pfad.name} ({herkunft})" if herkunft else pfad.name
            )

            knoepfe.append(
                (beschriftung, lambda p=pfad: self._datei_einspielen(p))
            )

        if dateiwahl.verfuegbar():
            knoepfe.append(("Datei suchen ...", self._systemauswahl))

        knoepfe.append(("Zurück", self._neu_warten))

        self.zeige(
            "Welche Datei soll eingespielt werden?\n\n"
            "Gesucht wird im eigenen Ordner und dort, wo Empfangenes "
            "landet."
            if dateien or dateiwahl.verfuegbar() else
            f"Keine Datei gefunden.\n\nGesucht wurde in:\n{ordner}",
            knoepfe,
        )

    def _systemauswahl(self):

        def geholt(pfad):
            self._datei_einspielen(pfad)

        def schiefgegangen(meldung):
            self.zeige(meldung, (("Zurück", self._datei_suchen),))

        dateiwahl.auswaehlen(
            storage.export_dir("uebergabe"), geholt, schiefgegangen
        )

    def _datei_einspielen(self, pfad):
        """Aus einer Datei ist nicht ersichtlich, was sie ist - danach
        wird deshalb gefragt."""

        knoepfe = [
            (
                datenpaket.BESCHRIFTUNG[art],
                lambda a=art: self._datei_art_gewaehlt(a, pfad),
            )
            for art in datenpaket.ARTEN
        ]

        knoepfe.append(("Zurück", self._datei_suchen))

        self.zeige(
            f"{pfad.name}\n\nWas ist das?\n\n"
            + "\n".join(
                f"{datenpaket.BESCHRIFTUNG[a]}: {datenpaket.ERKLAERUNG[a]}"
                for a in datenpaket.ARTEN
            ),
            knoepfe,
        )

    def _datei_art_gewaehlt(self, art, pfad):

        try:
            meldung = datenpaket.einspielen(self.db, art, pfad)

        except Exception as fehler:
            meldung = f"Einspielen fehlgeschlagen: {fehler}"

        self._abschluss(art, meldung)


class SendenDialog(AblaufPopup):
    """Sucht ein Gerät und schickt ihm etwas."""

    def __init__(self, on_fertig=None, **kwargs):

        super().__init__("Daten senden", **kwargs)

        self.on_fertig = on_fertig

        self.db = DatabaseManager()

        self.verbindung = None
        self.gegenseite = None

        self._suchen()

    # -----------------------------------------------------

    def _im_takt(self, funktion, *args):

        Clock.schedule_once(lambda _dt: funktion(*args), 0)

    def _suchen(self):

        self.zeige("Suche Geräte im Netz ...", ())

        def arbeiten():

            try:
                gefunden = funk.suchen()

            except Exception as fehler:
                self._im_takt(
                    self.zeige, f"Suche nicht möglich: {fehler}",
                    (("Schließen", self.dismiss),)
                )
                return

            # Sich selbst nicht anbieten.
            gefunden = [
                g for g in gefunden
                if g.get("kennung") != self.db.geraet["id"]
            ]

            self._im_takt(self._auswahl_zeigen, gefunden)

        threading.Thread(target=arbeiten, daemon=True).start()

    def _auswahl_zeigen(self, gefunden):

        knoepfe = [
            (
                f"{g['name']}  ({g['adresse']})",
                lambda ziel=g: self._anklopfen(ziel),
                True,
            )
            for g in gefunden
        ]

        knoepfe.append(("Nochmal suchen", self._suchen))
        knoepfe.append(("Stattdessen als Datei", self._als_datei))
        knoepfe.append(("Abbrechen", self.dismiss))

        if gefunden:
            text = (
                "Diese Geräte warten gerade auf Daten.\n\n"
                "Steht das gesuchte nicht dabei, muss dort erst "
                "\"Daten empfangen\" gewählt werden."
            )
        else:
            text = (
                "Kein wartendes Gerät gefunden.\n\n"
                "Am anderen Gerät \"Daten empfangen\" wählen, und "
                "beide müssen im selben WLAN sein.\n\n"
                "Manche Netze geben Suchrufe nicht weiter - dann "
                "bleibt der Weg über die Datei."
            )

        self.zeige(text, knoepfe)

    # -----------------------------------------------------

    def _anklopfen(self, ziel):

        self.zeige(
            f"Frage bei \"{ziel['name']}\" an ...\n\n"
            f"Dort muss jetzt jemand annehmen.",
            (),
        )

        def arbeiten():

            try:
                verbindung, antwort = funk.anfragen(
                    ziel["adresse"], ziel.get("port", funk.PORT_VERBINDUNG),
                    self.db.geraet["name"], self.db.geraet["id"],
                )

            except Exception as fehler:
                self._im_takt(
                    self.zeige,
                    f"Verbindung fehlgeschlagen: {fehler}",
                    (("Zurück", self._suchen), ("Abbrechen", self.dismiss)),
                )
                return

            if not antwort.get("ok"):

                try:
                    verbindung.close()
                except OSError:
                    pass

                self._im_takt(
                    self.zeige,
                    f"\"{ziel['name']}\" hat abgelehnt.",
                    (("Zurück", self._suchen), ("Schließen", self.dismiss)),
                )
                return

            self.verbindung = verbindung
            self.gegenseite = {
                "name": antwort.get("name", ziel["name"]),
                "kennung": antwort.get("kennung", ziel.get("kennung", "")),
            }

            self._im_takt(self._art_fragen)

        threading.Thread(target=arbeiten, daemon=True).start()

    def _art_fragen(self):

        name = self.gegenseite["name"]

        # Die Kasse kann nur weitergeben, wer sie hat. Ein Nebengerät
        # würde sonst ein Schreibrecht verschenken, das ihm gar nicht
        # gehört - und hinterher gäbe es zwei Geräte, die sich beide
        # für zuständig halten.
        moeglich = [
            art for art in datenpaket.ARTEN
            if art != datenpaket.KASSE or not self.db.nur_ansicht
        ]

        knoepfe = []

        for art in moeglich:

            knoepfe.append((
                datenpaket.BESCHRIFTUNG[art],
                lambda a=art: self._senden(a),
                art == datenpaket.DATENBANK,
            ))

        knoepfe.append(("Abbrechen", self._abbrechen))

        text = (
            f"\"{name}\" nimmt an. Was soll übertragen werden?\n\n"
            + "\n\n".join(
                f"{datenpaket.BESCHRIFTUNG[a]} - {datenpaket.ERKLAERUNG[a]}"
                for a in moeglich
            )
        )

        if self.db.nur_ansicht:
            text += (
                "\n\nDie Kasse steht nicht zur Wahl: Dieses Gerät ist "
                "Nebengerät und hat sie nicht."
            )

        self.zeige(text, knoepfe)

    def _senden(self, art):

        name = self.gegenseite["name"]

        self.zeige(
            f"{datenpaket.BESCHRIFTUNG[art]} wird vorbereitet und an "
            f"\"{name}\" gesendet ...",
            (),
        )

        def arbeiten():

            try:
                pfad, meldung = datenpaket.erzeugen(
                    self.db, art, storage.export_dir("uebergabe"),
                    an_id=self.gegenseite["kennung"],
                    an_name=self.gegenseite["name"],
                )

                antwort = funk.datei_senden(self.verbindung, pfad, art)

            except Exception as fehler:
                self._im_takt(
                    self.zeige,
                    f"Senden fehlgeschlagen: {fehler}",
                    (("Schließen", self._abbrechen),),
                )
                return

            finally:
                self._schliessen()

            self._im_takt(
                self.zeige,
                f"{meldung}\n\nRückmeldung von \"{name}\":\n{antwort}",
                (("Schließen", self._fertig, True),),
            )

        threading.Thread(target=arbeiten, daemon=True).start()

    # -----------------------------------------------------

    def _schliessen(self):

        try:
            if self.verbindung is not None:
                self.verbindung.close()
        except OSError:
            pass

        self.verbindung = None

    def _abbrechen(self):

        self._schliessen()
        self.dismiss()

    def _fertig(self):

        self.dismiss()

        if callable(self.on_fertig):
            self.on_fertig()

    # -----------------------------------------------------
    # Rückfall: Datei
    # -----------------------------------------------------

    def _als_datei(self):

        knoepfe = [
            (
                datenpaket.BESCHRIFTUNG[art],
                lambda a=art: self._datei_erzeugen(a),
            )
            for art in datenpaket.ARTEN
            # Die Kasse braucht einen Empfänger - ohne Verbindung
            # weiß niemand, wer das wäre.
            if art != datenpaket.KASSE
        ]

        knoepfe.append(("Zurück", self._suchen))

        self.zeige(
            "Ohne Verbindung wird eine Datei geschrieben, die du "
            "weitergeben kannst - per Bluetooth, Mail oder Kabel.\n\n"
            "Die Kasse lässt sich so nicht übergeben: Dafür muss "
            "feststehen, wer sie bekommt.\n\n"
            "Was soll in die Datei?",
            knoepfe,
        )

    def _datei_erzeugen(self, art):

        try:
            pfad, meldung = datenpaket.erzeugen(
                self.db, art, storage.export_dir("uebergabe")
            )

        except Exception as fehler:
            self.zeige(
                f"Fehlgeschlagen: {fehler}",
                (("Zurück", self._als_datei),),
            )
            return

        def teilen_jetzt():
            erfolg, hinweis = teilen.teilen(pfad, betreff="KiG POS")
            self.zeige(hinweis, (("Schließen", self._fertig, True),))

        def bluetooth_jetzt():
            erfolg, hinweis = teilen.per_bluetooth(pfad, betreff="KiG POS")
            self.zeige(hinweis, (("Schließen", self._fertig, True),))

        self.zeige(
            f"{meldung}\n\n{pfad.name}\n\nOrdner: {pfad.parent}",
            (
                ("Per Bluetooth senden", bluetooth_jetzt, True),
                ("Teilen ...", teilen_jetzt),
                ("Nur schreiben, fertig", self._fertig),
            ),
        )
