"""
=========================================================
KiG POS
=========================================================

Datei:
    berichte/pdf_bericht.py

Beschreibung:
    Ein PDF-Bericht im Aussehen der KiG-Ausgaben.

    Jede Seite wird als Bild in A4 gezeichnet und am Ende zu
    einem PDF zusammengefügt. Das kann Pillow allein - und
    Pillow ist auch auf dem Tablet dabei. reportlab, mit dem
    das Handbuch als PDF entsteht, fehlt in der Android-Fassung;
    ein Bericht, der nur am Rechner geht, hilft an der Bar
    nicht.

    Aufbau:

        erste Seite    Logo, Titel, wofür die Zahlen gelten,
                       orangefarbene Linie
        weitere Seiten kleiner Kopf mit Logo und Titel
        jede Seite     unten "KiG POS", Datum und "Seite x von y"

    Bausteine (in dieser Reihenfolge aufrufen, die Seiten
    brechen von selbst um):

        bericht = PdfBericht("Verkaufsstatistik", "September 2026")
        bericht.ueberschrift("Kennzahlen")
        bericht.kennzahlen((("Einnahmen", "120,00 €"), ...))
        bericht.kreisdiagramm(((name, betrag, "#1976D2"), ...))
        bericht.balkendiagramm(((name, betrag, "#1976D2"), ...))
        bericht.tabelle(kopf, zeilen, anteile, ausrichtung)
        bericht.speichern(pfad)

    Der Text ist Teil des Bildes und lässt sich im PDF nicht
    markieren - zum Ausdrucken, Ablegen und Weiterschicken
    genügt das.

Version:
    1.0.0
=========================================================
"""

import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

import config


# A4 bei 150 dpi
DPI = 150
BREITE, HOEHE = 1240, 1754
RAND = 90
UNTEN = HOEHE - 110

ORANGE = (244, 70, 17)
ORANGE_HELL = (253, 236, 229)
TEXT = (34, 34, 34)
GRAU = (107, 107, 107)
LINIE = (217, 217, 217)
ZEBRA = (247, 247, 247)
WEISS = (255, 255, 255)
ROT = (198, 40, 40)
GRUEN = (46, 125, 50)


def _schriftordner():
    """Die Schriften, die Kivy mitbringt - am Rechner wie auf dem
    Tablet vorhanden."""

    # kivy_data_dir statt des Paketordners: Im fertigen Windows-Programm
    # liegt kivy/__init__ im Archiv, die Schriften aber in einem
    # eigenen Ordner - Kivy weiss selbst am besten, wo.
    try:
        from kivy import kivy_data_dir
        return os.path.join(kivy_data_dir, "fonts")
    except ImportError:
        return ""


def schrift(groesse, fett=False):

    name = "Roboto-Bold.ttf" if fett else "Roboto-Regular.ttf"

    pfad = os.path.join(_schriftordner(), name)

    try:
        return ImageFont.truetype(pfad, groesse)
    except OSError:
        return ImageFont.load_default()


def farbe_aus_hex(wert, ersatz=ORANGE):
    """"#1976D2" -> (25, 118, 210)."""

    try:
        wert = (wert or "").lstrip("#")
        return tuple(int(wert[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, TypeError):
        return ersatz


class PdfBericht:

    def __init__(self, titel, untertitel=""):

        self.titel = titel
        self.untertitel = untertitel
        self.erstellt = datetime.now()

        self.seiten = []
        self.seite = None
        self.malen = None
        self.y = 0

        self._logo = self._logo_laden()

        self._neue_seite()

    # =====================================================
    # Seiten
    # =====================================================

    @staticmethod
    def _logo_laden():

        pfad = getattr(config, "LOGO_PATH", None)

        if not pfad or not os.path.exists(pfad):
            return None

        try:
            with Image.open(pfad) as original:
                return original.convert("RGBA")
        except OSError:
            return None

    def _logo_setzen(self, x, y, hoehe):

        if self._logo is None:
            return 0

        breite = round(self._logo.width * hoehe / self._logo.height)
        klein = self._logo.resize((breite, hoehe), Image.LANCZOS)

        self.seite.paste(klein, (x, y), klein)

        return breite

    def _neue_seite(self):

        self.seite = Image.new("RGB", (BREITE, HOEHE), WEISS)
        self.malen = ImageDraw.Draw(self.seite)
        self.seiten.append(self.seite)

        if len(self.seiten) == 1:
            self._grosser_kopf()
        else:
            self._kleiner_kopf()

    def _grosser_kopf(self):

        malen = self.malen

        self._logo_setzen(RAND, RAND - 20, 110)

        rechts = "KiG POS"
        f = schrift(22, fett=True)
        malen.text(
            (BREITE - RAND - malen.textlength(rechts, font=f), RAND + 60),
            rechts, font=f, fill=ORANGE,
        )

        y = RAND + 110
        malen.text((RAND, y), self.titel, font=schrift(46, fett=True), fill=TEXT)

        y += 64
        teile = [t for t in (
            self.untertitel,
            f"erstellt am {self.erstellt:%d.%m.%Y} um {self.erstellt:%H:%M}",
        ) if t]
        malen.text((RAND, y), "   ·   ".join(teile), font=schrift(20), fill=GRAU)

        y += 44
        malen.rectangle((RAND, y, BREITE - RAND, y + 4), fill=ORANGE)

        self.y = y + 40

    def _kleiner_kopf(self):

        malen = self.malen

        breite = self._logo_setzen(RAND, RAND - 30, 56)

        f = schrift(24, fett=True)
        malen.text(
            (RAND + breite + 24, RAND - 18), self.titel, font=f, fill=TEXT
        )

        y = RAND + 36
        malen.rectangle((RAND, y, BREITE - RAND, y + 2), fill=ORANGE)

        self.y = y + 34

    def _platz(self, hoehe):
        """Neue Seite, wenn das Folgende nicht mehr darauf passt."""

        if self.y + hoehe > UNTEN:
            self._neue_seite()
            return True

        return False

    # =====================================================
    # Text
    # =====================================================

    def _kuerzen(self, text, font, breite):
        """Kürzt mit "…", bis der Text in die Breite passt."""

        text = str(text)

        if self.malen.textlength(text, font=font) <= breite:
            return text

        while text and self.malen.textlength(text + "…", font=font) > breite:
            text = text[:-1]

        return text + "…"

    def ueberschrift(self, text, platz_danach=120):
        """Abschnittsüberschrift. platz_danach: so viel muss darunter
        noch auf die Seite passen - sonst stünde die Überschrift allein
        unten und ihr Diagramm auf der nächsten Seite."""

        self._platz(80 + platz_danach)

        self.y += 14
        self.malen.text((RAND, self.y), text, font=schrift(30, fett=True), fill=ORANGE)

        self.y += 44
        self.malen.rectangle((RAND, self.y, BREITE - RAND, self.y + 1), fill=ORANGE_HELL)

        self.y += 22

    def text(self, inhalt, grau=True, groesse=20):

        font = schrift(groesse)

        # Einfacher Umbruch nach Wörtern
        zeile = ""
        zeilen = []

        for wort in str(inhalt).split():
            probe = f"{zeile} {wort}".strip()
            if self.malen.textlength(probe, font=font) > BREITE - 2 * RAND:
                zeilen.append(zeile)
                zeile = wort
            else:
                zeile = probe

        if zeile:
            zeilen.append(zeile)

        for zeile in zeilen:
            self._platz(groesse + 14)
            self.malen.text((RAND, self.y), zeile, font=font, fill=GRAU if grau else TEXT)
            self.y += groesse + 12

        self.y += 8

    def abstand(self, hoehe=20):

        self.y += hoehe

    # =====================================================
    # Kennzahlen
    # =====================================================

    def kennzahlen(self, paare, spalten=3, hervorheben=()):
        """Kacheln mit Bezeichnung und Wert, `spalten` je Reihe.

        hervorheben: Bezeichnungen, deren Wert orange steht.
        """

        abstand = 20
        breite = (BREITE - 2 * RAND - (spalten - 1) * abstand) / spalten
        hoehe = 108

        for start in range(0, len(paare), spalten):

            self._platz(hoehe + abstand)

            for position, (bezeichnung, wert) in enumerate(paare[start:start + spalten]):

                x = RAND + position * (breite + abstand)

                self.malen.rounded_rectangle(
                    (x, self.y, x + breite, self.y + hoehe),
                    radius=14, fill=ZEBRA, outline=LINIE, width=1,
                )

                self.malen.rectangle(
                    (x, self.y + 14, x + 5, self.y + hoehe - 14), fill=ORANGE
                )

                self.malen.text(
                    (x + 26, self.y + 16), bezeichnung,
                    font=schrift(19), fill=GRAU,
                )

                self.malen.text(
                    (x + 26, self.y + 46),
                    self._kuerzen(wert, schrift(36, fett=True), breite - 40),
                    font=schrift(36, fett=True),
                    fill=ORANGE if bezeichnung in hervorheben else TEXT,
                )

            self.y += hoehe + abstand

        self.y += 10

    # =====================================================
    # Diagramme
    # =====================================================

    def kreisdiagramm(self, eintraege, betrag_text=str):
        """Kreis links, Legende rechts.

        eintraege: ((Name, Betrag, "#RRGGBB"), ...) - nur positive
        Beträge ergeben ein Tortenstück.
        """

        eintraege = [e for e in eintraege if e[1] and e[1] > 0]

        if not eintraege:
            return

        gesamt = sum(e[1] for e in eintraege)

        durchmesser = 420
        zeilen_hoehe = 44
        hoehe = max(durchmesser, len(eintraege) * zeilen_hoehe) + 20

        self._platz(min(hoehe, UNTEN - 300))

        # Dreifach gerechnet und verkleinert - sonst hat der Kreis
        # Treppenkanten.
        fein = 3
        kreis = Image.new("RGB", (durchmesser * fein, durchmesser * fein), WEISS)
        kreis_malen = ImageDraw.Draw(kreis)

        winkel = -90.0

        for _name, betrag, farbe in eintraege:

            weite = 360.0 * betrag / gesamt

            kreis_malen.pieslice(
                (0, 0, durchmesser * fein - 1, durchmesser * fein - 1),
                winkel, winkel + weite,
                fill=farbe_aus_hex(farbe), outline=WEISS, width=2 * fein,
            )

            winkel += weite

        kreis = kreis.resize((durchmesser, durchmesser), Image.LANCZOS)

        self.seite.paste(kreis, (RAND, self.y))

        # Legende
        x = RAND + durchmesser + 60
        y = self.y + 10
        rest = BREITE - RAND - x

        f = schrift(21)
        f_fett = schrift(21, fett=True)

        for name, betrag, farbe in eintraege:

            if y + zeilen_hoehe > UNTEN:
                break

            self.malen.rounded_rectangle(
                (x, y + 4, x + 24, y + 28), radius=5, fill=farbe_aus_hex(farbe)
            )

            anteil = f"{100 * betrag / gesamt:.1f} %".replace(".", ",")
            wert = betrag_text(betrag)

            breite_wert = self.malen.textlength(wert, font=f_fett)
            breite_anteil = 110

            self.malen.text(
                (x + 40, y + 2),
                self._kuerzen(name, f, rest - 40 - breite_wert - breite_anteil - 20),
                font=f, fill=TEXT,
            )
            self.malen.text(
                (BREITE - RAND - breite_wert - breite_anteil, y + 2),
                wert, font=f_fett, fill=TEXT,
            )
            self.malen.text(
                (BREITE - RAND - self.malen.textlength(anteil, font=f), y + 2),
                anteil, font=f, fill=GRAU,
            )

            y += zeilen_hoehe

        self.y += hoehe + 10

    def balkendiagramm(self, eintraege, betrag_text=str, zusatz_text=None):
        """Waagerechte Balken, der größte ganz ausgefahren.

        eintraege:   ((Name, Betrag, "#RRGGBB"), ...)
        zusatz_text: optional f(eintrag_index) -> kleiner grauer Text
                     unter dem Namen (z. B. "12 Stück")
        """

        if not eintraege:
            return

        groesster = max((e[1] for e in eintraege), default=0) or 1

        name_breite = 330
        wert_breite = 150
        zeilen_hoehe = 46 if zusatz_text is None else 58
        balken_x = RAND + name_breite + 16
        balken_max = BREITE - RAND - wert_breite - 16 - balken_x

        f = schrift(21)
        f_klein = schrift(16)
        f_fett = schrift(21, fett=True)

        for position, (name, betrag, farbe) in enumerate(eintraege):

            self._platz(zeilen_hoehe)

            self.malen.text(
                (RAND, self.y + 4),
                self._kuerzen(name, f, name_breite), font=f, fill=TEXT,
            )

            if zusatz_text is not None:
                self.malen.text(
                    (RAND, self.y + 32), zusatz_text(position),
                    font=f_klein, fill=GRAU,
                )

            laenge = max(0, balken_max * (betrag or 0) / groesster)

            if laenge >= 1:
                self.malen.rectangle(
                    (balken_x, self.y + 6, balken_x + laenge, self.y + 34),
                    fill=farbe_aus_hex(farbe),
                )

            wert = betrag_text(betrag)

            self.malen.text(
                (BREITE - RAND - self.malen.textlength(wert, font=f_fett), self.y + 4),
                wert, font=f_fett, fill=ROT if (betrag or 0) < 0 else TEXT,
            )

            self.y += zeilen_hoehe

        self.y += 16

    # =====================================================
    # Tabelle
    # =====================================================

    def tabelle(self, kopf, zeilen, anteile, ausrichtung=None, summe=None,
                farben=None):
        """Tabelle über die ganze Breite; bricht um und wiederholt die
        Kopfzeile auf jeder neuen Seite.

        anteile:     Breitenanteile der Spalten (Summe 1)
        ausrichtung: je Spalte "left" oder "right"
        summe:       optional eine fette Summenzeile
        farben:      optional f(zeile) -> Schriftfarbe (RGB) oder None
        """

        ausrichtung = ausrichtung or ("left",) * len(kopf)

        gesamt = BREITE - 2 * RAND
        breiten = [gesamt * anteil for anteil in anteile]

        kopf_hoehe = 46
        zeilen_hoehe = 40
        innen = 12

        f = schrift(19)
        f_fett = schrift(19, fett=True)

        def kopfzeile():

            self.malen.rectangle(
                (RAND, self.y, BREITE - RAND, self.y + kopf_hoehe), fill=ORANGE
            )

            x = RAND

            for text, breite, wohin in zip(kopf, breiten, ausrichtung):
                self._zelle(text, x, breite, kopf_hoehe, f_fett, WEISS, wohin, innen)
                x += breite

            self.y += kopf_hoehe

        self._platz(kopf_hoehe + zeilen_hoehe * 2)
        kopfzeile()

        for position, werte in enumerate(zeilen):

            if self._platz(zeilen_hoehe):
                kopfzeile()

            if position % 2 == 1:
                self.malen.rectangle(
                    (RAND, self.y, BREITE - RAND, self.y + zeilen_hoehe), fill=ZEBRA
                )

            farbe = farben(werte) if callable(farben) else None

            x = RAND

            for wert, breite, wohin in zip(werte, breiten, ausrichtung):
                self._zelle(wert, x, breite, zeilen_hoehe, f, farbe or TEXT, wohin, innen)
                x += breite

            self.malen.line(
                (RAND, self.y + zeilen_hoehe, BREITE - RAND, self.y + zeilen_hoehe),
                fill=LINIE, width=1,
            )

            self.y += zeilen_hoehe

        if summe is not None:

            self._platz(zeilen_hoehe)

            self.malen.rectangle(
                (RAND, self.y, BREITE - RAND, self.y + zeilen_hoehe), fill=ORANGE_HELL
            )
            self.malen.rectangle(
                (RAND, self.y, BREITE - RAND, self.y + 3), fill=ORANGE
            )

            x = RAND

            for wert, breite, wohin in zip(summe, breiten, ausrichtung):
                self._zelle(wert, x, breite, zeilen_hoehe, f_fett, TEXT, wohin, innen)
                x += breite

            self.y += zeilen_hoehe

        self.y += 24

    def _zelle(self, wert, x, breite, hoehe, font, farbe, wohin, innen):

        text = self._kuerzen("" if wert is None else wert, font, breite - 2 * innen)

        laenge = self.malen.textlength(text, font=font)

        if wohin == "right":
            tx = x + breite - innen - laenge
        else:
            tx = x + innen

        # Senkrecht mittig: Roboto sitzt bei 19 px etwa 5 px unter
        # der Oberkante.
        ty = self.y + (hoehe - font.size) / 2 - 3

        self.malen.text((tx, ty), text, font=font, fill=farbe)

    # =====================================================
    # Speichern
    # =====================================================

    def _fusszeilen(self):

        anzahl = len(self.seiten)
        f = schrift(16)

        for nummer, seite in enumerate(self.seiten, start=1):

            malen = ImageDraw.Draw(seite)

            y = HOEHE - 70

            malen.line((RAND, y - 14, BREITE - RAND, y - 14), fill=LINIE, width=1)

            links = f"KiG POS · {self.titel}"
            rechts = f"Seite {nummer} von {anzahl}"
            mitte = f"{self.erstellt:%d.%m.%Y %H:%M}"

            malen.text((RAND, y), links, font=f, fill=GRAU)
            malen.text(
                ((BREITE - malen.textlength(mitte, font=f)) / 2, y),
                mitte, font=f, fill=GRAU,
            )
            malen.text(
                (BREITE - RAND - malen.textlength(rechts, font=f), y),
                rechts, font=f, fill=GRAU,
            )

    def speichern(self, pfad):

        self._fusszeilen()

        erste, *weitere = self.seiten

        # quality und subsampling=0: Die Seiten werden als JPEG
        # abgelegt, und bei den Voreinstellungen franste orange
        # Schrift aus.
        erste.save(
            str(pfad), "PDF", resolution=DPI, save_all=True,
            append_images=weitere, quality=92, subsampling=0,
            title=self.titel, author="KiG POS",
        )

        return pfad
