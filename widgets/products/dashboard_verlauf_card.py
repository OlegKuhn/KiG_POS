"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/products/dashboard_verlauf_card.py

Beschreibung:
    Der Bestandsverlauf eines Artikels als Tabelle.

    Früher stand jede Bewegung als eigene, 142 dp hohe Kachel
    unter dem Bestand - mit "Bearbeitet von:" in einer eigenen
    Zeile. Auf einer Bildschirmhöhe waren so kaum drei
    Bewegungen zu sehen. Als Tabelle sind es zwanzig, und
    Datum, Grund und Mengen stehen untereinander, wo man sie
    vergleichen kann.

        Datum         Grund          Bearbeiter  Änderung  Bestand
        13.09. 11:17  Bruch          Oleg        -3        45
        13.09. 11:17  Wareneingang               +48       48

    Neueste zuerst - so, wie get_stock_history sie liefert.

    Der Bearbeiter steht nur bei einer Korrektur von Hand - dort
    fragt der Dialog nach dem Namen. Verkauf und Wareneingang bucht
    das Programm selbst; "Kasse" oder "Einkauf" in jeder zweiten
    Zeile sagte nichts, was der Grund nicht schon sagt.

Version:
    1.0.0
=========================================================
"""

from datetime import datetime

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.kig_label import KiGLabel


# Ueberschrift, Anteil an der Breite, Ausrichtung. Kopf und Zeilen lesen
# beide hieraus - sonst stehen Ueberschrift und Wert nicht uebereinander.
SPALTEN = (
    ("Datum", 0.25, "left"),
    ("Grund", 0.25, "left"),
    ("Bearbeiter", 0.20, "left"),
    ("Änderung", 0.15, "right"),
    ("Bestand", 0.15, "right"),
)

# Wer so heisst, ist kein Mensch, sondern das Programm selbst
# (siehe cash_screen.py und database.book_goods_receipt).
AUTOMATISCH = {"", "kasse", "einkauf"}


def bearbeiter(eintrag):
    """Der Name dessen, der den Bestand von Hand geaendert hat - leer
    bei Verkauf und Wareneingang."""

    try:
        name = (eintrag["changed_by"] or "").strip()
    except (KeyError, IndexError, TypeError):
        return ""

    return "" if name.lower() in AUTOMATISCH else name


def _zahl(wert):
    """Ganze Zahlen ohne Nachkommastellen, sonst mit Komma."""

    try:
        wert = float(wert or 0)
    except (TypeError, ValueError):
        return str(wert)

    if wert.is_integer():
        return str(int(wert))

    return f"{wert:.2f}".replace(".", ",")


def _datum(zeitstempel):
    """"2026-09-13 11:17:11" wird "13.09.26 11:17"."""

    if not zeitstempel:
        return "-"

    # Der Korrektur-Dialog schreibt deutsch ("13.09.2026 11:17:11"),
    # alles andere ISO.
    for muster in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                   "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(str(zeitstempel), muster).strftime(
                "%d.%m.%y %H:%M"
            )
        except ValueError:
            continue

    return str(zeitstempel)


class _Zeile(BoxLayout):
    """Eine Bewegung."""

    HOEHE = 34

    def __init__(self, eintrag, dunkel, **kwargs):

        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(self.HOEHE),
            padding=(dp(theme.SPACE_S), 0),
            **kwargs
        )

        # Jede zweite Zeile leicht hinterlegt - in einer langen Tabelle
        # rutscht das Auge sonst in die Nachbarzeile.
        if dunkel:
            with self.canvas.before:
                Color(*theme.SURFACE)
                self._grund = RoundedRectangle(radius=[dp(6)])

            self.bind(pos=self._nachziehen, size=self._nachziehen)

        alt = eintrag["old_quantity"] or 0
        neu = eintrag["new_quantity"] or 0

        try:
            aenderung = float(neu) - float(alt)
        except (TypeError, ValueError):
            aenderung = 0

        vorzeichen = "+" if aenderung > 0 else ""

        werte = (
            _datum(eintrag["changed_at"]),
            eintrag["reason"] or "-",
            bearbeiter(eintrag),
            f"{vorzeichen}{_zahl(aenderung)}",
            _zahl(neu),
        )

        for position, (wert, (_titel, anteil, ausrichtung)) in enumerate(
                zip(werte, SPALTEN)
        ):

            farbe = theme.TEXT_PRIMARY

            # Abgaenge rot: Ein Minus ist das, wonach man in einem
            # Bestandsverlauf sucht.
            if position == 3 and aenderung < 0:
                farbe = theme.ERROR

            beschriftung = Label(
                text=str(wert), color=farbe, font_size="13sp",
                bold=position == 4,
                halign=ausrichtung, valign="middle",
                size_hint_x=anteil,
                shorten=True, shorten_from="right",
            )

            beschriftung.bind(
                size=lambda instanz, groesse: setattr(
                    instanz, "text_size", groesse
                )
            )

            self.add_widget(beschriftung)

    def _nachziehen(self, *_args):

        self._grund.pos = self.pos
        self._grund.size = self.size


class VerlaufCard(RoundedPanel):
    """Die Karte mit dem Bestandsverlauf."""

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        titel = KiGLabel(text="Bestandsverlauf")
        titel.set_font_size(20)
        titel.set_bold(True)
        titel.set_alignment("left")
        titel.set_color(theme.PRIMARY_ORANGE)
        titel.size_hint_y = None
        titel.height = dp(30)
        self.add_widget(titel)

        kopf = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26),
            padding=(dp(theme.SPACE_S), 0),
        )

        for titeltext, anteil, ausrichtung in SPALTEN:

            spalte = Label(
                text=titeltext, color=theme.TEXT_SECONDARY,
                font_size="12sp", bold=True,
                halign=ausrichtung, valign="middle",
                size_hint_x=anteil,
            )

            spalte.bind(
                size=lambda instanz, groesse: setattr(
                    instanz, "text_size", groesse
                )
            )

            kopf.add_widget(spalte)

        self.add_widget(kopf)

        self.zeilen = BoxLayout(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
        )
        self.zeilen.bind(minimum_height=self.zeilen.setter("height"))

        rollbereich = ScrollView(do_scroll_x=False, bar_width=dp(8))
        rollbereich.add_widget(self.zeilen)

        self.add_widget(rollbereich)

    def set_history(self, eintraege):

        self.zeilen.clear_widgets()

        if not eintraege:

            leer = KiGLabel(text="Noch keine Bestandsänderungen.")
            leer.set_font_size(14)
            leer.set_alignment("left")
            leer.set_color(theme.TEXT_SECONDARY)
            leer.size_hint_y = None
            leer.height = dp(36)

            self.zeilen.add_widget(leer)

            return

        for position, eintrag in enumerate(eintraege):
            self.zeilen.add_widget(_Zeile(eintrag, dunkel=position % 2 == 1))

    def inhaltshoehe(self):
        """Fuer die gestapelte Fassung auf dem Telefon."""

        return (
            dp(30) + dp(26) + min(self.zeilen.height, dp(34 * 8))
            + dp(theme.CARD_SPACING) * 2 + dp(theme.CARD_PADDING) * 2
        )
