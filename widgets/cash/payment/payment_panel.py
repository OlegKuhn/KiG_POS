"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    payment_panel.py

Beschreibung:
    Der Bezahlvorgang als ein Dialog.

    Früher waren es zwei Panels, die von rechts hereinfuhren:
    die Aufstellung und daneben der Nummernblock. Wer den
    Betrag eintippte, sah die Summe im Warenkorb dahinter -
    und beim Entwerten wanderte der Nummernblock zwischen
    Bargeld, KiG Karte und Gutschein hin und her, ohne dass
    man ihm das ansah.

    Jetzt steht alles in einem Dialog:

        Kasse
        Bezahlen · KiG Karte                    [Schließen]

        Schnellwahl                    ┌──────────────────┐
        [5][10][20][50][100]           │        10,00 €   │
        [KiG Karte · -5,00 €][Gutschein]├──────────────────┤
        1 × 10 €                       │  7   8   9       │
        Zu zahlen          8,00 €      │  4   5   6       │
        Gegeben           10,00 €      │  1   2   3       │
        Rückgeld           2,00 €      │  C   0   <-      │
                                       │   Bestätigen     │
        ────────────────────────────────────────────────────
                          [Abbrechen] [Zahlung abschließen]

    Die Überschrift sagt, worauf der Nummernblock gerade
    zählt: "Bezahlen" fürs Bargeld, "Bezahlen · KiG Karte"
    oder "· Gutschein", solange eine der beiden Tasten
    gewählt ist. "Bestätigen" führt zurück zum Bargeld.

    Die Aufstellung selbst (Schnellwahl, entwertete Beträge,
    Rückgeld) steht in payment_summary.py - sie rechnet, der
    Dialog stellt dar.

Version:
    2.0.0
=========================================================
"""

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import theme

from widgets.cash.design import CashButton
from widgets.cash.payment.payment_summary import PaymentSummary
from widgets.common.kig_popup import KiGPopup
from widgets.common.numpad.numpad_panel import NumpadPanel
from widgets.kig_label import KiGLabel


class Zahlenfeld(NumpadPanel):
    """Der Nummernblock, fest im Dialog eingebaut.

    Als Panel blendet er sich nach "Bestätigen" oder "Abbrechen"
    selbst aus und vergisst dabei seine Rückrufe (siehe
    NumpadPanel.close). Im Dialog bleibt er stehen: Nach dem
    Kartenbetrag wird gleich das Bargeld eingetippt.
    """

    # Tasten so hoch, wie die Spalte hergibt - nie höher
    TASTE_MAX = 78

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # Ohne eigenen Kasten: Als Panel hebt sich der Nummernblock vom
        # Bildschirm ab, im Dialog stünde ein zweiter Kasten im Kasten.
        self.canvas.before.clear()

    def _update_canvas(self, *_args):
        return

    def close(self):
        return

    def slide_open(self):
        return

    def slide_close(self, on_closed=None):
        return

    def _update_button_size(self, *_args):
        """Die Tasten füllen ihre Spalte.

        Als Panel sind sie quadratisch; im Dialog ist die Spalte
        breiter als hoch - quadratische Tasten ließen dort rechts und
        links je einen Finger breit Luft und wurden dafür winzig.
        """

        tasten = self.grid.children

        if not tasten:
            return

        abstand = self.grid.spacing[0]

        breite = (self.grid_container.width - 2 * abstand) / 3
        hoehe = (self.grid_container.height - 3 * abstand) / 4

        if breite <= 0 or hoehe <= 0:
            return

        for taste in tasten:
            taste.width = breite
            taste.height = min(hoehe, dp(self.TASTE_MAX))


class PaymentPanel(KiGPopup):
    """Der Bezahldialog: Aufstellung links, Nummernblock rechts."""

    PADDING = theme.CARD_PADDING
    SPACING = theme.CARD_SPACING

    KOPF_HOEHE = 64
    FUSS_HOEHE = 60

    # Querformat: so groß wie nötig, aber nie über den Bildschirm
    BREITE = 940
    HOEHE = 700

    def __init__(
            self,
            cancel_callback=None,
            ok_callback=None,
            shortcut_callback=None,
            entwertung_callback=None,
            **kwargs
    ):

        # Der Dialog bringt seine Überschrift selbst mit (mit der
        # Zeile "Kasse" darüber) - Kivys eigene bliebe darüber leer.
        kwargs.setdefault("title", "")
        kwargs.setdefault("separator_height", 0)
        kwargs.setdefault("auto_dismiss", False)

        super().__init__(**kwargs)

        self.title_size = 0

        # KiGPopup setzt den orangen Trennstrich für seine Überschrift.
        # Dieser Dialog hat keine - der Strich stünde allein unter dem
        # oberen Rand.
        self.separator_height = 0

        # Nach außen unverändert: Der Screen ruft weiterhin diese
        # Rückrufe (siehe cash_screen.pay_clicked).
        self.cancel_callback = cancel_callback
        self.ok_callback = ok_callback
        self.shortcut_callback = shortcut_callback
        self.entwertung_callback = entwertung_callback

        # Worauf zählt der Nummernblock gerade: "bar", "kig_karte"
        # oder "gutschein"
        self._aktiv = "bar"

        # Ein Tipp auf die Schnellwahl setzt den Nummernblock - dessen
        # Rückmeldung darf die Aufstellung der Scheine dann nicht
        # wieder wegwerfen (siehe _betrag_geaendert).
        self._schnellwahl_laeuft = False

        self.size_hint = (None, None)
        self.size = self._groesse()

        Window.bind(size=lambda *_a: setattr(self, "size", self._groesse()))

        # =====================================================
        # Gerüst
        # =====================================================

        wurzel = BoxLayout(
            orientation="vertical",
            padding=dp(self.PADDING),
            spacing=dp(self.SPACING),
        )

        wurzel.add_widget(self._kopf())
        wurzel.add_widget(self._koerper())
        wurzel.add_widget(self._trennlinie())
        wurzel.add_widget(self._fuss())

        self.content = wurzel

    # =====================================================
    # Bausteine
    # =====================================================

    def _groesse(self):

        if theme.is_portrait():
            return (Window.width * 0.96, Window.height * 0.94)

        return (
            min(Window.width * 0.88, dp(self.BREITE)),
            min(Window.height * 0.94, dp(self.HOEHE)),
        )

    def _kopf(self):

        kopf = BoxLayout(
            size_hint_y=None,
            height=dp(self.KOPF_HOEHE),
            spacing=dp(theme.ROW_SPACING),
        )

        beschriftung = BoxLayout(orientation="vertical")

        # Kleine Zeile darüber: In welchem Bereich steht der Dialog?
        ueber = KiGLabel(text="Kasse")
        ueber.set_font_size(12)
        ueber.set_bold(True)
        ueber.set_color(theme.TEXT_SECONDARY)
        ueber.set_alignment("left")
        ueber.set_vertical_alignment("bottom")
        beschriftung.add_widget(ueber)

        self.lbl_title = KiGLabel(text="Bezahlen")
        self.lbl_title.set_font_size(28)
        self.lbl_title.set_bold(True)
        self.lbl_title.set_alignment("left")
        self.lbl_title.set_vertical_alignment("top")
        beschriftung.add_widget(self.lbl_title)

        kopf.add_widget(beschriftung)

        self.btn_schliessen = CashButton(
            text="Schließen", font_size="16sp", bold=True,
            size_hint=(None, None),
            size=(dp(130), dp(44)),
            pos_hint={"center_y": 0.5},
        )
        self.btn_schliessen.bind(on_release=lambda *_a: self._abbrechen())

        kopf.add_widget(self.btn_schliessen)

        return kopf

    def _koerper(self):

        self.summary = PaymentSummary(
            shortcut_callback=self._schein_gewaehlt,
            entwertung_callback=self._entwertung_gewaehlt,
        )

        self.numpad = self._numpad_bauen()

        # Im Hochformat untereinander statt nebeneinander - für zwei
        # Spalten fehlt dort die Breite.
        if theme.is_portrait():

            inhalt = BoxLayout(
                orientation="vertical",
                spacing=dp(self.SPACING),
                size_hint_y=None,
            )
            inhalt.bind(minimum_height=inhalt.setter("height"))

            self.summary.size_hint_y = None
            self.summary.height = dp(296)

            # Etwas Luft zum Rollbalken - sonst klebt "2,00 €" daran.
            self.summary.padding = (0, 0, dp(theme.SPACE_S), 0)

            self.numpad.size_hint_y = None
            self.numpad.height = dp(360)

            inhalt.add_widget(self.summary)
            inhalt.add_widget(self.numpad)

            self.rollbereich = ScrollView(do_scroll_x=False, bar_width=dp(6))
            self.rollbereich.add_widget(inhalt)

            return self.rollbereich

        koerper = BoxLayout(
            orientation="horizontal",
            spacing=dp(theme.SPACE_XL),
        )

        koerper.add_widget(self.summary)
        koerper.add_widget(self.numpad)

        return koerper

    def _numpad_bauen(self):
        """Der bekannte Nummernblock - hier fest im Dialog statt als
        eigenes Panel.

        Er bringt Anzeige, Tasten und "Bestätigen" mit; "Abbrechen"
        entfällt, dafür gibt es unten die Fußzeile des Dialogs.
        """

        numpad = Zahlenfeld()

        # Der Nummernblock ist sonst ein Panel, das sich einblendet.
        # Hier steht er fest - also aus dem Schiebebetrieb nehmen.
        numpad.size_hint = (1, 1)
        numpad.opacity = 1
        numpad.disabled = False
        numpad.padding = 0

        numpad.button_layout.remove_widget(numpad.btn_cancel)
        numpad.button_layout.size_hint_y = None
        numpad.button_layout.height = dp(64)

        # Die Anzeige über die ganze Spalte, wie im Entwurf.
        numpad.display.size_hint = (1, None)
        numpad.display.height = dp(84)
        numpad.display_container.height = dp(84)

        numpad.mode = "price"
        numpad.confirm_callback = self._numpad_bestaetigt
        numpad.cancel_callback = None
        numpad.change_callback = self._betrag_geaendert

        return numpad

    def _trennlinie(self):

        linie = Widget(size_hint_y=None, height=dp(1))

        with linie.canvas:
            Color(*theme.CARD_BORDER)
            strich = Rectangle()

        def zeichnen(*_args):
            strich.pos = linie.pos
            strich.size = linie.size

        linie.bind(pos=zeichnen, size=zeichnen)

        return linie

    def _fuss(self):

        fuss = BoxLayout(
            size_hint_y=None,
            height=dp(self.FUSS_HOEHE),
            spacing=dp(theme.ROW_SPACING),
        )

        fuss.add_widget(Widget())

        self.btn_cancel = CashButton(
            text="Abbrechen", font_size="17sp", bold=True,
            size_hint_x=None,
            width=dp(160),
        )
        self.btn_cancel.bind(on_release=lambda *_a: self._abbrechen())

        # Der eine Knopf, der den Verkauf bucht - als einziger gefüllt.
        self.btn_ok = CashButton(
            text="Zahlung abschließen",
            active=True,
            font_size="17sp", bold=True,
            size_hint_x=None,
            width=dp(240),
        )
        self.btn_ok.bind(on_release=lambda *_a: self._abschliessen())

        fuss.add_widget(self.btn_cancel)
        fuss.add_widget(self.btn_ok)

        return fuss

    # =====================================================
    # Nummernblock und Aufstellung
    # =====================================================

    def _betrag_geaendert(self, wert):
        """Am Nummernblock wurde getippt."""

        betrag = wert / 100

        if self._aktiv == "bar":

            self.summary.set_paid(betrag)

            # Kommt der Betrag NICHT aus der Schnellwahl, sondern vom
            # Nummernblock, stimmt die Aufstellung der gelegten Scheine
            # nicht mehr - dann lieber keine als eine falsche.
            if not self._schnellwahl_laeuft:
                self.summary.scheine_zuruecksetzen()

            return

        self.summary.set_entwertet(self._aktiv, betrag)

    def _numpad_bestaetigt(self, _wert):
        """"Bestätigen" unter dem Nummernblock: zurück zum Bargeld."""

        self._feld_waehlen("bar")

    def _schein_gewaehlt(self, betrag):
        """Ein Tipp auf einen Schein in der Schnellwahl.

        Der Schein wird DAZUGELEGT, nicht ersetzt: Wer 40 Euro
        bekommt, tippt zweimal auf 20 - so, wie das Geld auch auf den
        Tresen wandert.
        """

        # Die Schnellwahl gehört dem Bargeld; ein halb eingetippter
        # Kartenbetrag wird dabei übernommen.
        if self._aktiv != "bar":
            self._feld_waehlen("bar")

        neuer_wert = self.numpad.get_value() + int(round(betrag * 100))

        self._schnellwahl_laeuft = True

        try:
            self.numpad.set_value(neuer_wert)
        finally:
            self._schnellwahl_laeuft = False

        self.summary.schein_gelegt(betrag)

        if callable(self.shortcut_callback):
            self.shortcut_callback(betrag)

    def _entwertung_gewaehlt(self, art):
        """Ein Tipp auf "KiG Karte" oder "Gutschein"."""

        self._feld_waehlen("bar" if self._aktiv == art else art)

        if callable(self.entwertung_callback):
            self.entwertung_callback(art)

    def _feld_waehlen(self, feld):
        """Worauf der Nummernblock zählt - und was oben steht."""

        self._aktiv = feld

        self.summary.entwertung_markieren(None if feld == "bar" else feld)

        beschriftungen = dict(PaymentSummary.ENTWERTUNGEN)

        self.lbl_title.text = (
            "Bezahlen" if feld == "bar"
            else f"Bezahlen · {beschriftungen.get(feld, feld)}"
        )

        wert = (
            self.summary.paid if feld == "bar"
            else self.summary.entwertet(feld)
        )

        self._schnellwahl_laeuft = True

        try:
            self.numpad.set_value(int(round(wert * 100)))
        finally:
            self._schnellwahl_laeuft = False

    # =====================================================
    # Knöpfe der Fußzeile
    # =====================================================

    def _abbrechen(self):

        if callable(self.cancel_callback):
            self.cancel_callback()
            return

        self.close()

    def _abschliessen(self):

        if callable(self.ok_callback):
            self.ok_callback()

    # =====================================================
    # Dialog
    # =====================================================

    def open(self, total=None, *args, **kwargs):
        """Öffnet den Dialog für diesen Betrag.

        total=None öffnet ihn nur wieder (Kivy ruft open() beim
        erneuten Anzeigen ohne Betrag auf).
        """

        # Erst beim Öffnen: Beim Bau der Kasse steht das Fenster noch
        # auf Kivys Vorgabemaß - ein damals gerechneter Dialog wäre
        # in einem kleinen Fenster breiter als der Bildschirm.
        self.size = self._groesse()

        # Im Hochformat rollt der Inhalt - oben anfangen, nicht
        # mitten in der Schnellwahl.
        if getattr(self, "rollbereich", None) is not None:
            self.rollbereich.scroll_y = 1

        if total is not None:

            self.summary.set_total(total)
            self.summary.set_paid(0.0)

            # Jeder Zahlvorgang faengt bei null an - auch die gelegten
            # Scheine und die entwerteten Beträge.
            self.summary.scheine_zuruecksetzen()
            self.summary.entwertungen_zuruecksetzen()

            self._feld_waehlen("bar")

        return super().open(*args, **kwargs)

    def close(self):

        self.dismiss()

    def on_dismiss(self, *args):

        # Wer den Dialog mit der Zurück-Taste schließt, bricht den
        # Zahlvorgang ab - nicht nur die Anzeige.
        self._aktiv = "bar"

        return super().on_dismiss(*args)

    # =====================================================
    # Schnittstelle (unverändert gegenüber dem alten Panel)
    # =====================================================

    def set_paid_amount(self, amount):

        self.summary.set_paid(amount)

    def schein_gelegt(self, betrag):

        self.summary.schein_gelegt(betrag)

    def scheine_zuruecksetzen(self):

        self.summary.scheine_zuruecksetzen()

    def set_entwertet(self, art, betrag):

        return self.summary.set_entwertet(art, betrag)

    def entwertet(self, art):

        return self.summary.entwertet(art)

    def entwertung_markieren(self, art):

        self.summary.entwertung_markieren(art)

    @property
    def geoeffnet(self):
        """Steht der Dialog gerade auf dem Bildschirm?"""

        return self._window is not None

    def schnellwahl(self, betrag):
        """Legt einen Schein - wie ein Tipp auf die Schnellwahl."""

        self._schein_gewaehlt(betrag)

    @property
    def geoeffnet(self):
        """Steht der Dialog gerade auf dem Bildschirm?"""

        return self._window is not None

    def schnellwahl(self, betrag):
        """Legt einen Schein - wie ein Tipp auf die Schnellwahl."""

        self._schein_gewaehlt(betrag)

    @property
    def zu_zahlen(self):

        return self.summary.zu_zahlen

    @property
    def paid(self):

        return self.summary.paid

    @property
    def total(self):

        return self.summary.total

    @property
    def change(self):

        return self.summary.change
