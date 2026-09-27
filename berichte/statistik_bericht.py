"""
=========================================================
KiG POS
=========================================================

Datei:
    berichte/statistik_bericht.py

Beschreibung:
    Die Verkaufsstatistik zum Ausdrucken - als Excel-Mappe und
    als PDF, beide für dieselbe Auswahl (Zeitraum, Event,
    Kategorie) wie auf dem Bildschirm.

    Excel, Blatt "Zusammenfassung":
        Kennzahlen, Umsatz nach Kategorie mit Kreisdiagramm,
        Verkäufe je Artikel mit Balkendiagramm - die Farben sind
        die der Kategorien, wie in der App.
    Excel, Blatt "Einzelverkäufe":
        jede verkaufte Einheit, mit Filter in der Kopfzeile.

    PDF:
        Kennzahlen als Kacheln, Kreis mit Legende, Balken je
        Artikel und die Tabelle je Artikel. Die Einzelverkäufe
        stehen nur in Excel - als PDF wären es schnell zwanzig
        Seiten, die niemand liest.

    Die Daten holt sammeln() einmal aus der Datenbank; excel()
    und pdf() schreiben nur noch.

Version:
    1.0.0
=========================================================
"""

from datetime import datetime

import geldformat

from berichte.excel_layout import Exportblatt, ORANGE
from berichte.pdf_bericht import PdfBericht, ROT


# Ersatzfarben wie im Kreisdiagramm der App (category_pie.py) - eine
# Kategorie ohne eigene Farbe soll im Bericht dieselbe haben wie am
# Bildschirm.
FALLBACK_FARBEN = (
    "#1976D2", "#F57C00", "#43A047", "#7B1FA2",
    "#00838F", "#C62828", "#5D4037", "#616161",
)


def _farbe(wert, position):

    wert = (wert or "").strip()

    if len(wert.lstrip("#")) >= 6:
        try:
            int(wert.lstrip("#")[:6], 16)
            return "#" + wert.lstrip("#")[:6].upper()
        except ValueError:
            pass

    return FALLBACK_FARBEN[position % len(FALLBACK_FARBEN)]


def _datum(iso):

    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return str(iso or "-")


# =========================================================
# Daten
# =========================================================

def sammeln(db, auswahl, beschreibung):
    """Alles für den Bericht in einem Wörterbuch.

    auswahl:      (date_from, date_to, event_id, category_id)
    beschreibung: in Worten, wofür die Zahlen gelten
                  ("Sommerfest | Getränke | 01.09. - 13.09.2026")
    """

    kennzahlen = db.get_period_totals(*auswahl)
    artikel = db.get_article_sales(*auswahl)
    kategorien_roh = db.get_category_revenues(*auswahl)
    einzeln = db.get_statistic_sale_items(*auswahl)

    # Farbe je Kategorie einmal festlegen - Kreis, Balken und
    # Tabellen benutzen dieselbe.
    farben = {}
    kategorien = []

    for position, (name, betrag, farbe) in enumerate(kategorien_roh):
        farben[name] = _farbe(farbe, position)
        kategorien.append((name, betrag, farben[name]))

    for eintrag in artikel:
        eintrag["farbe_hex"] = farben.get(eintrag["kategorie"], FALLBACK_FARBEN[0])

    return {
        "beschreibung": beschreibung,
        "kennzahlen": kennzahlen,
        "artikel": artikel,
        "kategorien": kategorien,
        "einzeln": einzeln,
        "manual": [dict(row) for row in db.get_manual_entries(*auswahl)],
    }


# Die vier Zahlen, die auf die erste Seite gehören.
#
# Wer den Bericht aufschlägt, will wissen, was hereinkam, was es
# gekostet hat, was übrig blieb und wie viel dafür über die Theke
# ging. Alles Weitere (Bons, manuelle Buchungen, Entwertetes) sind
# Aufschlüsselungen davon - sie stehen hinten in einer eigenen
# Aufstellung, statt die Übersicht auf zwei Reihen zu dehnen.
UEBERBLICK = (
    "Einnahmen",
    "Wareneinsatz + Ausgaben",
    "Gewinn",
    "Verkaufte Einheiten",
)


def _kennzahlen_paare(kennzahlen):
    """(Bezeichnung, Wert, Format) - in der Reihenfolge des Berichts."""

    paare = [
        ("Einnahmen", kennzahlen["revenue"], "geld"),
        ("Wareneinsatz + Ausgaben", kennzahlen["expenses"], "geld"),
        ("Gewinn", kennzahlen["profit"], "geld"),
        ("Verkaufte Einheiten", kennzahlen["quantity"], "zahl"),
        ("Bons", kennzahlen["receipts"], "zahl"),
    ]

    if kennzahlen.get('manual_income') or kennzahlen.get('manual_expenses'):
        paare += [
            ('Davon manuelle Einnahmen', kennzahlen['manual_income'], 'geld'),
            ('Davon manuelle Ausgaben', kennzahlen['manual_expenses'], 'geld'),
        ]

    if kennzahlen.get("kig_karte") or kennzahlen.get("gutschein"):
        paare += [
            ("Entwertet: KiG Karte", kennzahlen["kig_karte"], "geld"),
            ("Entwertet: Gutschein", kennzahlen["gutschein"], "geld"),
            ("Bar eingenommen", kennzahlen["bar"], "geld"),
        ]

    return paare


def _kennzahlen_geteilt(kennzahlen):
    """(Überblick, Weitere) - vier Zahlen vorn, der Rest dahinter."""

    alle = _kennzahlen_paare(kennzahlen)

    return (
        [p for p in alle if p[0] in UEBERBLICK],
        [p for p in alle if p[0] not in UEBERBLICK],
    )


# =========================================================
# Excel
# =========================================================

def excel(daten, pfad):
    """Schreibt die Mappe nach `pfad` und liefert den Pfad."""

    from openpyxl import Workbook
    from openpyxl.chart import BarChart, PieChart, Reference
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.series import DataPoint

    mappe = Workbook()

    # -----------------------------------------------------
    # Zusammenfassung
    # -----------------------------------------------------

    blatt = Exportblatt(
        mappe.active, "Verkaufsstatistik", daten["beschreibung"],
        breiten=(30, 18, 11, 15, 15, 3, 14, 14, 14, 14, 14, 14),
        quer=False,
    )
    blatt.blatt.title = "Zusammenfassung"

    kennzahlen = daten["kennzahlen"]

    ueberblick, weitere = _kennzahlen_geteilt(kennzahlen)

    def kennzahlen_block(titel, paare):

        if not paare:
            return

        blatt.ueberschrift(titel)
        blatt.kennzahlen(
            [(bezeichnung, round(wert or 0, 2))
             for bezeichnung, wert, _f in paare],
            formate=[format_ for _b, _w, format_ in paare],
        )

    kennzahlen_block("Kennzahlen", ueberblick)

    # ---- Kategorien mit Kreis --------------------------------

    kategorien = daten["kategorien"]
    gesamt = sum(betrag for _n, betrag, _f in kategorien) or 1

    blatt.ueberschrift("Umsatz nach Kategorie")

    kreis_zeile = blatt.zeile

    erste, letzte = blatt.tabelle(
        ("Kategorie", "Umsatz", "Anteil"),
        [
            (name, round(betrag, 2), betrag / gesamt)
            for name, betrag, _farbe in kategorien
        ],
        formate=("text", "geld", "prozent"),
        summe=("Summe", round(sum(b for _n, b, _f in kategorien), 2), 1 if kategorien else 0),
    )

    if kategorien and letzte >= erste:

        kreis = PieChart()
        # Ohne eigenen Titel - die Überschrift steht daneben.
        kreis.height = 7.5
        kreis.width = 11

        kreis.add_data(
            Reference(blatt.blatt, min_col=2, min_row=erste - 1, max_row=letzte),
            titles_from_data=True,
        )
        kreis.set_categories(
            Reference(blatt.blatt, min_col=1, min_row=erste, max_row=letzte)
        )

        reihe = kreis.series[0]

        for position, (_name, _betrag, farbe) in enumerate(kategorien):
            punkt = DataPoint(idx=position)
            punkt.graphicalProperties.solidFill = farbe.lstrip("#")
            punkt.graphicalProperties.line.solidFill = "FFFFFF"
            reihe.dPt.append(punkt)

        reihe.dLbls = DataLabelList()
        reihe.dLbls.showPercent = True
        reihe.dLbls.showVal = False
        reihe.dLbls.showCatName = False
        reihe.dLbls.showSerName = False
        reihe.dLbls.showLeaderLines = False

        blatt.blatt.add_chart(kreis, f"G{kreis_zeile}")

        # Der Kreis ist gut 15 Zeilen hoch - der nächste Abschnitt
        # soll nicht darunter liegen.
        blatt.zeile = max(blatt.zeile, kreis_zeile + 16)

    # ---- Artikel mit Balken ----------------------------------

    artikel = daten["artikel"]

    blatt.ueberschrift("Verkäufe je Artikel")

    balken_zeile = blatt.zeile

    erste, letzte = blatt.tabelle(
        ("Artikel", "Kategorie", "Menge", "Umsatz", "Gewinn"),
        [
            (e["name"], e["kategorie"], e["menge"], round(e["umsatz"], 2),
             round(e["gewinn"], 2))
            for e in artikel
        ],
        formate=("text", "text", "zahl", "geld", "geld"),
        summe=(
            "Summe", "",
            sum(e["menge"] for e in artikel),
            round(sum(e["umsatz"] for e in artikel), 2),
            round(sum(e["gewinn"] for e in artikel), 2),
        ),
    )

    if artikel and letzte >= erste:

        balken = BarChart()
        balken.type = "bar"
        balken.style = 10
        balken.legend = None
        # Seit openpyxl 3.1 sind Achsen ausgeblendet, solange man es
        # nicht anders sagt - dann fehlten die Artikelnamen.
        balken.x_axis.delete = False
        balken.y_axis.delete = False
        balken.y_axis.numFmt = '#,##0 "€"'
        balken.y_axis.majorGridlines = None

        # Größter Umsatz oben - wie in der App
        balken.x_axis.scaling.orientation = "maxMin"

        # ... und die Euro-Skala trotzdem unten statt oben
        balken.y_axis.crosses = "max"

        balken.width = 16
        balken.height = max(7.5, 0.6 * len(artikel) + 2)

        balken.add_data(
            Reference(blatt.blatt, min_col=4, min_row=erste - 1, max_row=letzte),
            titles_from_data=True,
        )
        balken.set_categories(
            Reference(blatt.blatt, min_col=1, min_row=erste, max_row=letzte)
        )

        reihe = balken.series[0]
        reihe.graphicalProperties.solidFill = ORANGE

        for position, eintrag in enumerate(artikel):
            punkt = DataPoint(idx=position)
            punkt.graphicalProperties.solidFill = eintrag["farbe_hex"].lstrip("#")
            punkt.graphicalProperties.line.solidFill = eintrag["farbe_hex"].lstrip("#")
            reihe.dPt.append(punkt)

        blatt.blatt.add_chart(balken, f"G{balken_zeile}")

    # Erst hier, ganz unten: Bons, manuelle Buchungen und Entwertetes
    # sind Aufschlüsselungen der vier Zahlen oben - sie sollen ihnen
    # nicht den ersten Blick nehmen.
    kennzahlen_block("Weitere Kennzahlen", weitere)

    blatt.drucken(titel_wiederholen=False)

    # -----------------------------------------------------
    # Nach Kategorie
    # -----------------------------------------------------

    kategorie_blatt = Exportblatt(
        mappe.create_sheet("Nach Kategorie"),
        "Verkäufe nach Kategorie", daten["beschreibung"],
        breiten=(34, 11, 15, 15, 11),
        quer=False,
    )

    for name, _farbe, eintraege, summen in nach_kategorie(daten):

        anteil = f"{100 * summen['anteil']:.1f}".replace(".", ",")

        kategorie_blatt.ueberschrift(f"{name}  ·  {anteil} % des Umsatzes")

        kategorie_blatt.tabelle(
            ("Artikel", "Menge", "Umsatz", "Gewinn", "Anteil"),
            [
                (
                    e["name"], e["menge"], round(e["umsatz"], 2),
                    round(e["gewinn"], 2),
                    e["umsatz"] / summen["umsatz"] if summen["umsatz"] else 0,
                )
                for e in eintraege
            ],
            formate=("text", "zahl", "geld", "geld", "prozent"),
            summe=(
                f"Summe {name}", summen["menge"], round(summen["umsatz"], 2),
                # "Anteil" ist der Anteil in der Kategorie - zusammen 100 %
                round(summen["gewinn"], 2), 1 if eintraege else 0,
            ),
        )

    kategorie_blatt.drucken(titel_wiederholen=False)

    # -----------------------------------------------------
    # Einzelverkäufe
    # -----------------------------------------------------

    einzeln = daten["einzeln"]

    zweites = Exportblatt(
        mappe.create_sheet("Einzelverkäufe"),
        "Einzelverkäufe", daten["beschreibung"],
        breiten=(22, 12, 16, 38, 8, 12, 12, 12),
    )

    zweites.tabelle(
        ("Event", "Datum", "Kategorie", "Artikel", "Menge", "Verkauf",
         "Einkauf", "Gewinn"),
        [
            (
                z["event_name"], _datum(z["business_date"]), z["category_name"],
                z["article_name"], z["quantity"], z["unit_price"],
                z["purchase_price"], z["profit"],
            )
            for z in einzeln
        ],
        formate=("text", "text", "text", "text", "zahl", "geld", "geld", "geld"),
        summe=(
            "Summe", "", "", "",
            sum(z["quantity"] for z in einzeln),
            round(sum(z["quantity"] * z["unit_price"] for z in einzeln), 2),
            round(sum(z["quantity"] * z["purchase_price"] for z in einzeln), 2),
            round(sum(z["profit"] for z in einzeln), 2),
        ),
        # Stornos rot, wie in der App
        hervorheben=lambda werte: "C62828" if (werte[4] or 0) < 0 else None,
        filter_setzen=True,
    )

    zweites.drucken()

    # -----------------------------------------------------
    # Manuelle Buchungen
    # -----------------------------------------------------

    if daten.get('manual'):

        manual = Exportblatt(
            mappe.create_sheet('Manuelle Buchungen'),
            'Manuelle Buchungen', daten['beschreibung'],
            breiten=(16, 28, 36, 22, 16),
        )

        # Je eine Tabelle: Einnahmen und Ausgaben stehen in einer
        # gemeinsamen Liste mit Vorzeichen nebeneinander, lassen sich
        # aber nicht getrennt summieren.
        for titel, art in (
            ('Manuelle Einnahmen', 'INCOME'),
            ('Manuelle Ausgaben', 'EXPENSE'),
        ):

            zeilen = manuelle_buchungen(daten, art)

            manual.ueberschrift(titel)

            manual.tabelle(
                ('Datum', 'Event', 'Bezeichnung', 'Beleg', 'Betrag'),
                [(d, e, n, beleg, round(betrag, 2))
                 for d, e, n, beleg, betrag in zeilen],
                formate=('text', 'text', 'text', 'text', 'geld'),
                summe=('Summe', '', '', '', round(_manual_summe(zeilen), 2)),
            )

        # Und die Rechnung dahinter: Diese Betraege stecken in den
        # Kennzahlen der Zusammenfassung.
        rechnung = _gesamtrechnung(daten)

        gesamt_posten, gesamt_ein, gesamt_aus = rechnung[-1]

        manual.ueberschrift('Gesamtsumme')

        manual.tabelle(
            ('Posten', 'Einnahmen', 'Ausgaben', 'Gewinn'),
            [(posten, round(ein, 2), round(aus, 2), round(ein - aus, 2))
             for posten, ein, aus in rechnung[:-1]],
            formate=('text', 'geld', 'geld', 'geld'),
            summe=(
                gesamt_posten, round(gesamt_ein, 2), round(gesamt_aus, 2),
                round(gesamt_ein - gesamt_aus, 2),
            ),
        )

        manual.drucken()

    mappe.save(pfad)

    return pfad


# =========================================================
# PDF
# =========================================================

def nach_kategorie(daten):
    """Die Artikel je Kategorie, in der Reihenfolge der Kategorien
    (größter Umsatz zuerst), innerhalb ebenso.

    Liefert [(name, farbe, artikel, summen), ...]; summen mit menge,
    umsatz, gewinn und anteil am Gesamtumsatz.
    """

    gesamt = sum(betrag for _n, betrag, _f in daten["kategorien"]) or 1

    gruppen = []

    for name, betrag, farbe in daten["kategorien"]:

        artikel = [e for e in daten["artikel"] if e["kategorie"] == name]

        gruppen.append((name, farbe, artikel, {
            "menge": sum(e["menge"] for e in artikel),
            "umsatz": betrag,
            "gewinn": sum(e["gewinn"] for e in artikel),
            "anteil": betrag / gesamt,
        }))

    return gruppen


def _zahl(wert):

    return f"{wert:g}".replace(".", ",")


def topseller(daten):
    """Je Kategorie der Artikel, der am häufigsten verkauft wurde (bei
    gleicher Menge der mit mehr Umsatz) - in der Reihenfolge der
    Kategorien. Liefert [(kategorie, farbe, artikel), ...]."""

    ergebnis = []

    for name, farbe, eintraege, _summen in nach_kategorie(daten):

        if not eintraege:
            continue

        bester = max(eintraege, key=lambda e: (e["menge"], e["umsatz"]))

        ergebnis.append((name, farbe, bester))

    return ergebnis


def manuelle_buchungen(daten, art):
    """Die manuellen Buchungen einer Art als Zeilen, Beträge positiv.

    art: "INCOME" oder "EXPENSE". Ein Vorzeichen braucht es hier
    nicht - in welche Richtung der Betrag zählt, sagt die Überschrift
    der Tabelle.
    """

    return [
        (_datum(r['entry_date']), r['event_name'], r['description'],
         r['reference'], r['amount_cents'] / 100)
        for r in daten.get('manual', [])
        if r['kind'] == art
    ]


def _manual_summe(zeilen):

    return sum(betrag for *_rest, betrag in zeilen)


def _gesamtrechnung(daten):
    """(Posten, Einnahmen, Ausgaben) - woraus die Gesamtsumme besteht.

    Die manuellen Buchungen stecken in den Kennzahlen der ersten
    Seite, sind dort aber nicht zu sehen. Hier steht die Rechnung
    offen: Verkäufe plus manuelle Buchungen ergibt, was vorn steht.
    """

    kennzahlen = daten["kennzahlen"]

    manuelle_einnahmen = kennzahlen.get("manual_income", 0) or 0
    manuelle_ausgaben = kennzahlen.get("manual_expenses", 0) or 0

    return [
        ("Verkäufe",
         kennzahlen["revenue"] - manuelle_einnahmen,
         kennzahlen["expenses"] - manuelle_ausgaben),
        ("Manuelle Buchungen", manuelle_einnahmen, manuelle_ausgaben),
        ("Gesamt", kennzahlen["revenue"], kennzahlen["expenses"]),
    ]


def _manual_pdf(bericht, daten):
    """Die manuellen Buchungen: je eine Tabelle für Einnahmen und
    Ausgaben, dahinter die Rechnung zur Gesamtsumme."""

    geld = geldformat.geld

    einnahmen = manuelle_buchungen(daten, "INCOME")
    ausgaben = manuelle_buchungen(daten, "EXPENSE")

    if not (einnahmen or ausgaben):
        return

    bericht.seitenumbruch()

    bericht.ueberschrift("Manuelle Buchungen")

    bericht.text(
        "Buchungen ohne Verkauf - Spenden, Standgebühr, Einkäufe. "
        "Sie sind in den Einnahmen und Ausgaben der ersten Seite "
        "enthalten."
    )

    for titel, zeilen in (
        ("Manuelle Einnahmen", einnahmen),
        ("Manuelle Ausgaben", ausgaben),
    ):

        bericht.ueberschrift(titel)

        if not zeilen:
            bericht.text("Keine im gewählten Zeitraum.")
            continue

        bericht.tabelle(
            ("Datum", "Event", "Bezeichnung / Beleg", "Betrag"),
            [
                (datum, event, name + (" / " + beleg if beleg else ""),
                 geld(betrag))
                for datum, event, name, beleg, betrag in zeilen
            ],
            anteile=(0.15, 0.24, 0.43, 0.18),
            ausrichtung=("left", "left", "left", "right"),
            summe=("Summe", "", "", geld(_manual_summe(zeilen))),
        )

    # ---- Wie sich die Gesamtsumme zusammensetzt ----

    bericht.ueberschrift("Gesamtsumme")

    rechnung = _gesamtrechnung(daten)

    bericht.tabelle(
        ("Posten", "Einnahmen", "Ausgaben", "Gewinn"),
        [
            (posten, geld(ein), geld(aus), geld(ein - aus))
            for posten, ein, aus in rechnung[:-1]
        ],
        anteile=(0.34, 0.22, 0.22, 0.22),
        ausrichtung=("left", "right", "right", "right"),
        summe=(
            rechnung[-1][0],
            geld(rechnung[-1][1]),
            geld(rechnung[-1][2]),
            geld(rechnung[-1][1] - rechnung[-1][2]),
        ),
    )


def pdf(daten, pfad):
    """Schreibt den Bericht als PDF nach `pfad` und liefert den Pfad.

    Seite 1   der Überblick: vier Kennzahlen, der Kreis je Kategorie
              und der Topseller jeder Kategorie
    Seite 2   die Verkäufe nach Kategorie: je Kategorie Summe und
              ihre Artikel als Balken (gleicher Maßstab für alle)
    danach    die Artikel als Tabelle - in derselben Reihenfolge wie
              auf Seite 2, auf die Kategorien verteilt
    danach    die übrigen Kennzahlen und die manuellen Buchungen
    """

    geld = geldformat.geld

    bericht = PdfBericht("Verkaufsstatistik", daten["beschreibung"])

    kennzahlen = daten["kennzahlen"]

    ueberblick, weitere = _kennzahlen_geteilt(kennzahlen)

    def kacheln(paare, spalten=4):
        bericht.kennzahlen(
            [
                (bezeichnung, geld(wert) if format_ == "geld" else _zahl(wert))
                for bezeichnung, wert, format_ in paare
            ],
            spalten=spalten,
            hervorheben=("Gewinn",),
        )

    # -----------------------------------------------------
    # Seite 1: Überblick
    # -----------------------------------------------------

    bericht.ueberschrift("Kennzahlen")

    kacheln(ueberblick)

    def weitere_kennzahlen():
        """Alles, was nicht auf die erste Seite gehört - auf einer
        eigenen Seite dahinter."""

        if not weitere:
            return

        bericht.seitenumbruch()
        bericht.ueberschrift("Weitere Kennzahlen")
        kacheln(weitere, spalten=3)

    if not daten["artikel"]:
        bericht.text("Im gewählten Zeitraum wurde nichts verkauft.")
        weitere_kennzahlen()
        _manual_pdf(bericht, daten)
        bericht.speichern(pfad)
        return pfad

    artikel = daten["artikel"]

    bericht.ueberschrift("Umsatz nach Kategorie", platz_danach=360)
    bericht.kreisdiagramm(daten["kategorien"], betrag_text=geld, durchmesser=340)

    # Der meistverkaufte Artikel jeder Kategorie - Balken nach Stückzahl,
    # in der Farbe der Kategorie
    beste = topseller(daten)

    bericht.ueberschrift("Topseller je Kategorie", platz_danach=58 * 2)
    bericht.balkendiagramm(
        [(e["name"], e["menge"], farbe) for _name, farbe, e in beste],
        betrag_text=lambda menge: f"{_zahl(menge)} Stück",
        zusatz_text=lambda i: f"{beste[i][0]} · {geld(beste[i][2]['umsatz'])}",
    )

    # -----------------------------------------------------
    # Seite 2: Verkäufe nach Kategorie
    # -----------------------------------------------------

    bericht.seitenumbruch()

    bericht.ueberschrift("Verkäufe nach Kategorie")

    gruppen = nach_kategorie(daten)

    groesster = max((e["umsatz"] for e in artikel), default=0)

    for name, farbe, eintraege, summen in gruppen:

        anteil = f"{100 * summen['anteil']:.1f} %".replace(".", ",")

        bericht.gruppenkopf(
            name,
            f"{_zahl(summen['menge'])} Stück  ·  {geld(summen['umsatz'])}  ·  {anteil}",
            farbe,
        )

        bericht.balkendiagramm(
            [(e["name"], e["umsatz"], farbe) for e in eintraege],
            betrag_text=geld,
            zusatz_text=lambda i, liste=eintraege: (
                f"{_zahl(liste[i]['menge'])} Stück · Gewinn {geld(liste[i]['gewinn'])}"
            ),
            groesster=groesster,
        )

    # -----------------------------------------------------
    # Ab Seite 3: die Artikel als Tabelle
    # -----------------------------------------------------

    bericht.seitenumbruch()

    bericht.ueberschrift("Verkäufe je Artikel")

    zeilen = []

    for name, farbe, eintraege, summen in gruppen:

        zeilen.append({
            "gruppe": name,
            "rechts": f"{_zahl(summen['menge'])} Stück  ·  {geld(summen['umsatz'])}",
            "farbe": farbe,
        })

        for e in eintraege:
            zeilen.append((
                e["name"], _zahl(e["menge"]), geld(e["umsatz"]), geld(e["gewinn"]),
            ))

    bericht.tabelle(
        ("Artikel", "Menge", "Umsatz", "Gewinn"),
        zeilen,
        anteile=(0.46, 0.14, 0.2, 0.2),
        ausrichtung=("left", "right", "right", "right"),
        summe=(
            "Summe",
            _zahl(sum(e["menge"] for e in artikel)),
            geld(sum(e["umsatz"] for e in artikel)),
            geld(sum(e["gewinn"] for e in artikel)),
        ),
        farben=lambda werte: ROT if werte[3].startswith("-") else None,
    )

    # -----------------------------------------------------
    # Dahinter: die übrigen Kennzahlen und die Buchungen
    # -----------------------------------------------------

    weitere_kennzahlen()

    _manual_pdf(bericht, daten)
    bericht.speichern(pfad)

    return pfad
