"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    payment_summary.py

Beschreibung:
    Anzeige und Schnellwahl beim Bezahlen.

    Oben die Scheine, die an der Bar tatsächlich über den
    Tresen gehen. Ein Tipp LEGT EINEN SCHEIN DAZU - wer 40
    Euro bekommt, tippt zweimal auf 20. Genau so, wie das
    Geld auch auf den Tresen gelegt wird.

    Darunter steht, was gelegt wurde ("2 × 20 €"). Ohne
    diese Zeile müsste man sich merken, wie oft man getippt
    hat - und genau dabei verzählt man sich.

    Darunter "KiG Karte" und "Gutschein": Ein Tipp öffnet den
    Nummernblock für den Betrag, der damit beglichen wird. Er
    geht von dem ab, was bar zu zahlen ist - der Verkauf selbst
    bleibt so hoch, wie er ist (siehe database.save_sale).

    Unten steht, was zählt: gegeben und Rückgeld. Ist etwas
    entwertet, stehen darüber die abgezogenen Beträge und was
    danach noch zu zahlen bleibt.

    Der zu zahlende Betrag steht bewusst NICHT mehr hier -
    er steht schon groß im Warenkorb daneben. Zweimal
    dieselbe Zahl auf einem Bildschirm heißt, dass jemand
    sie vergleicht statt sie zu lesen.

Version:
    2.0.0

Build:
    0002
=========================================================
"""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

import geldformat
import theme

from widgets.cash.design import CashButton
from widgets.kig_label import KiGLabel


class PaymentSummary(BoxLayout):
    """
    Schnellwahl und Zahlungsinformationen.
    """

    SPACING = theme.CARD_SPACING

    # Die Scheine, die im Vereinsheim vorkommen. Kleiner als 5 EUR
    # lohnt die Abkürzung nicht - da ist der Nummernblock schneller.
    SCHNELLWAHL = (5, 10, 20, 50, 100)

    # Alle fünf in einer Reihe: Im Bezahldialog ist die Spalte breit
    # genug dafür (früher waren es drei in einem 350 dp schmalen
    # Panel).
    SPALTEN = 5

    # Knapp bemessen: Mit KiG Karte und Gutschein muss eine Reihe
    # mehr in die Höhe des Tablets passen.
    BUTTON_HEIGHT = 48
    CAPTION_HEIGHT = 26
    ROW_HEIGHT = 40

    # Die beiden Arten, einen Teil des Betrags nicht bar zu begleichen:
    # Schlüssel (so heißen auch die Spalten in sales) und Beschriftung.
    ENTWERTUNGEN = (
        ("kig_karte", "KiG Karte"),
        ("gutschein", "Gutschein"),
    )

    def __init__(self, shortcut_callback=None, entwertung_callback=None,
                 **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.spacing = dp(self.SPACING)

        self.shortcut_callback = shortcut_callback
        self.entwertung_callback = entwertung_callback

        self._paid = 0.0
        self._total = 0.0

        # Mit KiG Karte und Gutschein beglichen - und welcher der
        # beiden Beträge gerade am Nummernblock eingetippt wird.
        self._entwertet = {art: 0.0 for art, _text in self.ENTWERTUNGEN}
        self._aktive_entwertung = None

        # Welcher Schein wurde wie oft gelegt? Nur für die Anzeige -
        # maßgeblich ist immer der Betrag im Nummernblock.
        self._scheine = {}

        # =====================================================
        # Oben: Schnellwahl
        # =====================================================

        self.add_widget(self._caption("Schnellwahl"))

        spalten = self.SPALTEN

        zeilen = -(-len(self.SCHNELLWAHL) // spalten)

        self.shortcut_grid = GridLayout(
            cols=spalten,
            spacing=dp(theme.ROW_SPACING),
            size_hint=(1, None),
            height=(
                zeilen * dp(self.BUTTON_HEIGHT)
                + (zeilen - 1) * dp(theme.ROW_SPACING)
            ),
        )

        self.shortcut_buttons = []

        for betrag in self.SCHNELLWAHL:

            knopf = CashButton(
                text=f"{betrag} €",
                font_size="19sp", bold=True,
            )

            knopf.bind(
                on_release=lambda _instanz, wert=betrag:
                self._shortcut_gewaehlt(wert)
            )

            self.shortcut_buttons.append(knopf)
            self.shortcut_grid.add_widget(knopf)

        self.add_widget(self.shortcut_grid)

        # =====================================================
        # KiG Karte und Gutschein
        # =====================================================

        self.entwertung_buttons = {}

        entwertung_reihe = BoxLayout(
            orientation="horizontal",
            spacing=dp(theme.ROW_SPACING),
            size_hint=(1, None),
            height=dp(self.BUTTON_HEIGHT),
        )

        for art, text in self.ENTWERTUNGEN:

            # Der entwertete Betrag steht im Knopf selbst, hinter dem
            # Namen: "KiG Karte · -5,00 €".
            knopf = CashButton(
                text=text, soft=True,
                font_size="17sp", bold=True,
                halign="center", valign="middle",
            )
            knopf.bind(size=knopf.setter("text_size"))

            knopf.bind(
                on_release=lambda _instanz, wert=art:
                self._entwertung_gewaehlt(wert)
            )

            self.entwertung_buttons[art] = knopf
            entwertung_reihe.add_widget(knopf)

        self.add_widget(entwertung_reihe)

        # Was gelegt wurde ("2 × 20 €") - in einem eigenen, ruhigen
        # Feld unter den Tasten. Es bleibt leer, solange nichts über
        # die Schnellwahl kam.
        self.scheine_feld = BoxLayout(
            size_hint=(1, None),
            height=dp(34),
            padding=(dp(theme.SPACE_M), 0),
        )

        with self.scheine_feld.canvas.before:
            self._scheine_farbe = Color(*theme.SURFACE)
            self._scheine_flaeche = RoundedRectangle(radius=[dp(7)])

        self.scheine_feld.bind(
            pos=self._scheine_feld_zeichnen,
            size=self._scheine_feld_zeichnen,
        )

        self.lbl_scheine = KiGLabel()
        self.lbl_scheine.set_font_size(15)
        self.lbl_scheine.set_alignment("left")
        self.lbl_scheine.set_color(theme.TEXT_SECONDARY)

        self.scheine_feld.add_widget(self.lbl_scheine)

        self.add_widget(self.scheine_feld)

        # =====================================================
        # Unten: gegeben und Rückgeld
        # =====================================================

        # Ein Abstandhalter dazwischen: Schnellwahl ist Bedienung,
        # das Darunter ist Ergebnis. Die Trennung soll man sehen.
        self.add_widget(BoxLayout())

        # Die drei Zeilen, um die es geht. "Zu zahlen" steht
        # hervorgehoben: Seit der Bezahlvorgang ein Dialog ist, liegt
        # er über dem Warenkorb - der Betrag ist sonst nirgends mehr
        # zu sehen.
        self.ergebnis = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            size_hint=(1, None),
        )
        self.ergebnis.bind(minimum_height=self.ergebnis.setter("height"))

        self.lbl_due = self._value_label()
        self.lbl_due.set_color(theme.PRIMARY_ORANGE)

        self.due_row = self._row("Zu zahlen", self.lbl_due, hervorgehoben=True)

        self.lbl_paid = self._value_label(24)

        self.paid_row = self._row("Gegeben", self.lbl_paid)

        self.lbl_change = self._value_label()

        self.change_row = self._row("Rückgeld", self.lbl_change)

        self.ergebnis.add_widget(self.due_row)
        self.ergebnis.add_widget(self.paid_row)
        self.ergebnis.add_widget(self.change_row)

        self.add_widget(self.ergebnis)

        self.update()

    # =====================================================
    # Bausteine
    # =====================================================

    @staticmethod
    def _caption(text):

        label = KiGLabel(text=text)
        label.set_font_size(16)
        label.set_bold(True)
        label.set_alignment("left")
        label.set_color(theme.TEXT_SECONDARY)
        label.size_hint_y = None
        label.height = dp(PaymentSummary.CAPTION_HEIGHT)

        return label

    @staticmethod
    def geld(betrag):
        """Betrag mit Komma - die Regel steht in geldformat.py."""

        return geldformat.geld(betrag)

    @staticmethod
    def _value_label(schrift=28):

        label = KiGLabel()
        label.set_font_size(schrift)
        label.set_bold(True)
        label.set_alignment("right")
        label.set_color(theme.TEXT_PRIMARY)

        return label

    def _scheine_feld_zeichnen(self, *_args):

        self._scheine_flaeche.pos = self.scheine_feld.pos
        self._scheine_flaeche.size = self.scheine_feld.size

    def _row(self, text, wert_label, hervorgehoben=False):
        """Eine Zeile der Tabelle: links die Bezeichnung, rechts der
        Betrag. Hervorgehoben heißt: auf hellem Orange."""

        zeile = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(self.ROW_HEIGHT),
            spacing=dp(theme.ROW_SPACING),
            padding=(dp(theme.SPACE_M), 0) if hervorgehoben else (0, 0),
        )

        if hervorgehoben:

            # Dasselbe helle Orange wie ein gewählter Knopf - gemischt
            # statt fest hinterlegt, damit es im dunklen Modus stimmt.
            hell = tuple(
                a * 0.12 + b * 0.88
                for a, b in zip(theme.PRIMARY_ORANGE, theme.CARD)
            )

            with zeile.canvas.before:
                Color(*hell)
                flaeche = RoundedRectangle(radius=[dp(7)])

            def zeichnen(*_args):
                flaeche.pos = zeile.pos
                flaeche.size = zeile.size

            zeile.bind(pos=zeichnen, size=zeichnen)

        beschriftung = KiGLabel(text=text)
        beschriftung.set_font_size(17)
        beschriftung.set_bold(hervorgehoben)
        beschriftung.set_alignment("left")
        beschriftung.set_color(
            theme.TEXT_PRIMARY if hervorgehoben else theme.TEXT_SECONDARY
        )

        zeile.add_widget(beschriftung)
        zeile.add_widget(wert_label)

        return zeile

    # =====================================================
    # Schnellwahl
    # =====================================================

    def _shortcut_gewaehlt(self, betrag):

        if callable(self.shortcut_callback):
            self.shortcut_callback(betrag)

    def _entwertung_gewaehlt(self, art):

        if callable(self.entwertung_callback):
            self.entwertung_callback(art)

    # -----------------------------------------------------

    def set_entwertet(self, art, betrag):
        """Setzt den mit KiG Karte oder Gutschein beglichenen Betrag.

        Mehr als der Bon kann nicht entwertet werden - Rückgeld auf
        eine Karte oder einen Gutschein gibt es nicht. Die KiG Karte
        wird zuerst angerechnet, der Gutschein höchstens mit dem, was
        danach noch offen ist.

        Liefert den Betrag, der tatsächlich angerechnet wurde.
        """

        self._entwertet[art] = max(0.0, round(float(betrag), 2))

        self._entwertet_kappen()

        self.update()

        return self._entwertet[art]

    def _entwertet_kappen(self):

        rest = self._total

        for art, _text in self.ENTWERTUNGEN:

            self._entwertet[art] = round(
                min(self._entwertet[art], max(rest, 0)), 2
            )

            rest -= self._entwertet[art]

    def entwertet(self, art):

        return self._entwertet.get(art, 0.0)

    def entwertung_markieren(self, art):
        """Hebt den Knopf hervor, dessen Betrag gerade eingetippt
        wird (None: keiner)."""

        self._aktive_entwertung = art

        self.update()

    def entwertungen_zuruecksetzen(self):

        self._entwertet = {art: 0.0 for art, _text in self.ENTWERTUNGEN}
        self._aktive_entwertung = None

        self.update()

    # -----------------------------------------------------

    def schein_gelegt(self, betrag):
        """Merkt sich, dass dieser Schein einmal mehr gelegt wurde."""

        self._scheine[betrag] = self._scheine.get(betrag, 0) + 1

        self.update()

    def scheine_zuruecksetzen(self):
        """Vergisst die gelegten Scheine.

        Nötig, sobald der Betrag von woanders herkommt - beim Tippen
        am Nummernblock, beim Löschen und bei jedem neuen
        Zahlvorgang. Sonst stünde unter der Schnellwahl "2 × 20 €",
        während oben längst ein ganz anderer Betrag steht.
        """

        if not self._scheine:
            return

        self._scheine = {}

        self.update()

    def _scheine_beschriften(self):
        """Zeigt, was gelegt wurde: "2 × 20 €   1 × 5 €"."""

        if not self._scheine:
            self.lbl_scheine.text = ""
            return

        # Große Scheine zuerst - so, wie man Geld auch hinlegt.
        teile = [
            f"{anzahl} × {betrag} €"
            for betrag, anzahl in sorted(
                self._scheine.items(), reverse=True
            )
        ]

        self.lbl_scheine.text = "   ".join(teile)

    def _schnellwahl_faerben(self):
        """Hebt die Scheine hervor, die gelegt wurden."""

        for knopf, betrag in zip(self.shortcut_buttons, self.SCHNELLWAHL):

            knopf.select(bool(self._scheine.get(betrag, 0)))

    # =====================================================
    # Setter
    # =====================================================

    def set_paid(self, amount):
        """
        Setzt den gegebenen Betrag.
        """

        self._paid = amount

        self.update()

    # -----------------------------------------------------

    def set_total(self, amount):
        """
        Setzt den zu zahlenden Betrag.

        Angezeigt wird er hier nicht (er steht im Warenkorb) -
        gebraucht wird er für das Rückgeld.
        """

        self._total = amount

        self._entwertet_kappen()

        self.update()

    # =====================================================
    # Eigenschaften
    # =====================================================

    @property
    def paid(self):

        return self._paid

    @property
    def total(self):

        return self._total

    @property
    def zu_zahlen(self):
        """Was nach KiG Karte und Gutschein noch bar zu zahlen ist."""

        return round(
            max(self._total - sum(self._entwertet.values()), 0.0), 2
        )

    @property
    def change(self):

        if self._paid >= self.zu_zahlen:
            return self._paid - self.zu_zahlen

        return 0.0

    # =====================================================
    # Anzeige aktualisieren
    # =====================================================

    def update(self):
        """
        Aktualisiert die Anzeige.
        """

        self.lbl_paid.text = self.geld(self.paid)

        self.lbl_change.text = self.geld(self.change)

        # Reicht das Gegebene noch nicht, ist das Rückgeld keine
        # Aussage - dann steht dort 0,00, und zwar zurückhaltend.
        self.lbl_change.set_color(
            theme.SUCCESS if self.paid >= self.zu_zahlen and self.paid
            else theme.TEXT_SECONDARY
        )

        for art, text in self.ENTWERTUNGEN:

            betrag = self._entwertet[art]

            knopf = self.entwertung_buttons[art]

            knopf.text = (
                f"{text} · -{self.geld(betrag)}" if betrag else text
            )

            knopf.select(bool(betrag) or self._aktive_entwertung == art)

        self.lbl_due.text = self.geld(self.zu_zahlen)

        self._scheine_beschriften()

        self._schnellwahl_faerben()
