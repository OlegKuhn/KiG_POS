"""
=========================================================
KiG POS
=========================================================

Datei:
    berichte/schichtplan_bericht.py

Beschreibung:
    Der Schichtplan zum Aushängen - als Matrix.

                 18:00   19:00   20:00   21:00   22:00
        Theke    [ 18:00–21:00      ][ 21:00–24:00 ...
                 [ Anna, Bea   2/3  ][ Sara       1/1
        Grill                  [ 20:00–22:00 ]
                               [ Oleg, Tim   ]

    Nach rechts läuft die Zeit, nach unten stehen die
    Tätigkeiten. Jede Schicht ist ein Block über ihre Zeit, darin
    die Namen der Helfer. Die Farbe ist die Ampel aus der App:

        grün    besetzt
        orange  teilweise besetzt
        rot     noch niemand

    Wer zur selben Zeit in zwei Schichten steht, trägt ein "!"
    vor dem Namen; darunter steht, wo es sich überschneidet.

    Excel: Blatt "Plan" mit der Matrix (zusammengeführte Zellen
    als Blöcke), Blatt "Liste" mit der Tabelle wie bisher.
    PDF:   dieselbe Matrix im Querformat, bei vielen Tätigkeiten
    über mehrere Seiten mit wiederholter Zeitleiste.

    Schichten ohne lesbare Uhrzeit passen in keine Zeitachse -
    sie stehen unter der Matrix in einer eigenen Tabelle.

Version:
    1.0.0
=========================================================
"""

import schichtzeiten

from berichte.excel_layout import (
    GRAU, LINIE, ORANGE, ROT, TEXT, WEISS, ZEBRA,
    Exportblatt, blattname,
)


# Ampel: (hell für die Fläche, kräftig für Rand und Zahl)
AMPEL_EXCEL = {
    "voll": ("E8F5E9", "2E7D32"),
    "teil": ("FFF3E0", "EF6C00"),
    "leer": ("FFEBEE", "C62828"),
    "ohne": ("F2F2F2", "6B6B6B"),
}

AMPEL_PDF = {
    "voll": ((232, 245, 233), (46, 125, 50)),
    "teil": ((255, 243, 224), (239, 108, 0)),
    "leer": ((255, 235, 238), (198, 40, 40)),
    "ohne": ((242, 242, 242), (107, 107, 107)),
}

LEGENDE = (
    "Grün: besetzt  ·  Orange: teilweise besetzt  ·  Rot: noch niemand"
    "  ·  \"!\" vor einem Namen: zur selben Zeit noch woanders eingetragen"
)


def status(schicht):

    benoetigt = schicht.get("needed") or 0
    besetzt = len(schicht.get("helfer") or ())

    if benoetigt <= 0:
        return "ohne"

    if besetzt >= benoetigt:
        return "voll"

    if besetzt <= 0:
        return "leer"

    return "teil"


def namen_mit_markierung(schicht, konflikte):
    """Die Helfer der Schicht, doppelt eingetragene mit "!"."""

    markiert = konflikte.get(schicht["id"], set())

    return [
        f"! {name}" if schichtzeiten.name_schluessel(name) in markiert else name
        for name in schicht.get("helfer") or ()
    ]


def zusammenfassung(schichten):
    """ "5 von 6 Plätzen besetzt, 1 Schicht braucht noch Helfer"."""

    plaetze = sum(s.get("needed") or 0 for s in schichten)
    besetzt = sum(len(s.get("helfer") or ()) for s in schichten)
    offen = sum(
        1 for s in schichten
        if len(s.get("helfer") or ()) < (s.get("needed") or 0)
    )

    text = f"{besetzt} von {plaetze} Plätzen besetzt"

    if offen:
        text += (
            f", {offen} {'Schicht braucht' if offen == 1 else 'Schichten brauchen'}"
            f" noch Helfer"
        )

    return text


# =========================================================
# Excel
# =========================================================

def excel(titel, untertitel, schichten, pfad, alle_schichten=None):
    """Schreibt die Mappe mit Matrix und Liste.

    schichten:      die auszugebenden Schichten (ggf. nur die eines
                    Helfers) - Wörterbücher mit id, task, start_time,
                    end_time, needed und helfer
    alle_schichten: der ganze Plan - geprüft wird auf
                    Überschneidungen immer im ganzen Plan
    """

    from openpyxl import Workbook

    alle_schichten = alle_schichten if alle_schichten is not None else schichten

    # Zum Aushängen nach Uhrzeit - in der App stehen sie in der
    # Reihenfolge, in der sie angelegt wurden. So beginnt auch die
    # Matrix oben mit dem, was zuerst dran ist.
    schichten = schichtzeiten.nach_zeit(schichten)

    konflikte = schichtzeiten.konflikte_je_schicht(alle_schichten)

    mappe = Workbook()

    _excel_matrix(mappe.active, titel, untertitel, schichten, konflikte, alle_schichten)
    _excel_liste(mappe.create_sheet("Liste"), titel, untertitel, schichten, konflikte)

    mappe.save(pfad)

    return pfad


def _excel_matrix(ws, titel, untertitel, schichten, konflikte, alle_schichten):

    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    raster = schichtzeiten.raster(schichten)

    if raster is None:
        anfang, ende, schritt = 18 * 60, 22 * 60, 30
    else:
        anfang, ende, schritt = raster

    spalten = (ende - anfang) // schritt

    # Eine halbe Stunde gut zwei Zeichen breit - ein Abend von 18 bis
    # 2 Uhr passt so quer auf eine Seite.
    slot_breite = 4.2 if schritt >= 30 else 2.4

    blatt = Exportblatt(
        ws, titel, untertitel,
        breiten=(22,) + (slot_breite,) * spalten,
        quer=True,
    )
    ws.title = "Plan"

    duenn = Side(style="thin", color=LINIE)
    stunde_linie = Side(style="thin", color="BFBFBF")

    # ---- Zeitleiste ----------------------------------------

    zeit_zeile = blatt.zeile

    kopf = ws.cell(row=zeit_zeile, column=1, value="Tätigkeit")
    kopf.font = Font(bold=True, color=WEISS, size=10)
    kopf.fill = PatternFill("solid", fgColor=ORANGE)
    kopf.alignment = Alignment(vertical="center", indent=1)

    je_stunde = 60 // schritt

    for index in range(spalten):

        zelle = ws.cell(row=zeit_zeile, column=2 + index)
        zelle.fill = PatternFill("solid", fgColor=ORANGE)

        minute = anfang + index * schritt

        if minute % 60 == 0:
            zelle.value = schichtzeiten.uhrzeit(minute)
            zelle.font = Font(bold=True, color=WEISS, size=10)
            zelle.alignment = Alignment(horizontal="left", vertical="center")

            # Die Stunde über ihre halben Stunden - sonst stünde
            # "18:00" gequetscht in einer Spalte von zwei Zeichen.
            letzte = min(spalten, index + je_stunde)
            if letzte - index > 1:
                ws.merge_cells(
                    start_row=zeit_zeile, start_column=2 + index,
                    end_row=zeit_zeile, end_column=1 + letzte,
                )

    ws.row_dimensions[zeit_zeile].height = 22

    zeile = zeit_zeile + 1

    # ---- Bahnen ----------------------------------------------

    for taetigkeit, bahn in schichtzeiten.bahnen(schichten):

        meiste_namen = max(len(s.get("helfer") or ()) for s in bahn)

        # Zeitspanne, Namen, Zahl - jede Zeile 12 Punkt
        ws.row_dimensions[zeile].height = max(48, 13 * (meiste_namen + 2) + 6)

        name = ws.cell(row=zeile, column=1, value=taetigkeit)
        name.font = Font(bold=True, size=10, color=TEXT)
        name.fill = PatternFill("solid", fgColor=ZEBRA)
        name.alignment = Alignment(vertical="center", indent=1, wrap_text=True)
        name.border = Border(bottom=duenn, right=duenn)

        # Feines Stundenraster hinter den Blöcken
        for index in range(spalten):
            zelle = ws.cell(row=zeile, column=2 + index)
            minute = anfang + index * schritt
            zelle.border = Border(
                left=stunde_linie if minute % 60 == 0 else None,
                bottom=duenn,
            )

        for schicht in bahn:

            von, bis = schichtzeiten.zeitraum(schicht["start_time"], schicht["end_time"])

            erste = 2 + (von - anfang) // schritt
            letzte = 1 + -(-(bis - anfang) // schritt)
            letzte = max(erste, letzte)

            hell, kraeftig = AMPEL_EXCEL[status(schicht)]

            namen = namen_mit_markierung(schicht, konflikte)

            text = "\n".join(
                [schichtzeiten.spanne_text(schicht["start_time"], schicht["end_time"])]
                + (namen or ["noch niemand"])
                + [f"{len(schicht.get('helfer') or ())} / {schicht.get('needed') or 0}"]
            )

            rand = Side(style="medium", color=kraeftig)

            for spalte in range(erste, letzte + 1):
                zelle = ws.cell(row=zeile, column=spalte)
                zelle.fill = PatternFill("solid", fgColor=hell)
                zelle.border = Border(
                    left=rand if spalte == erste else None,
                    right=rand if spalte == letzte else None,
                    top=rand, bottom=rand,
                )

            block = ws.cell(row=zeile, column=erste, value=text)

            # Schwarz auf der Ampelfarbe; wer doppelt steht, trägt das
            # "!" - eine ganz rote Schrift machte Bea mit verdächtig.
            block.font = Font(size=9, color=TEXT)
            block.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True, indent=0,
            )

            if letzte > erste:
                ws.merge_cells(
                    start_row=zeile, start_column=erste,
                    end_row=zeile, end_column=letzte,
                )

        zeile += 1

    blatt.zeile = zeile + 1

    legende = blatt.text(LEGENDE, grau=True)
    legende.alignment = Alignment(wrap_text=False)

    # ---- Überschneidungen ------------------------------------

    eigene_ids = {s["id"] for s in schichten}

    treffer = [
        t for t in schichtzeiten.ueberschneidungen(alle_schichten)
        if t["schichten"][0]["id"] in eigene_ids or t["schichten"][1]["id"] in eigene_ids
    ]

    if treffer:
        blatt.ueberschrift("Überschneidungen")
        for t in treffer:
            blatt.text(schichtzeiten.konflikt_text(t), farbe=ROT, fett=True)

    # ---- Ohne Uhrzeit ------------------------------------------
    #
    # Als Textzeilen, nicht als Tabelle: Die Spalten dieses Blatts sind
    # halbe Stunden breit. Vollständig stehen sie im Blatt "Liste".

    ohne = schichtzeiten.ohne_zeit(schichten)

    if ohne:
        blatt.ueberschrift("Schichten ohne Uhrzeit")
        for s in ohne:
            blatt.text(
                f"{s['task'] or 'Schicht'}: "
                f"{', '.join(namen_mit_markierung(s, konflikte)) or 'noch niemand'}"
                f"  ({len(s.get('helfer') or ())} / {s.get('needed') or 0})"
            )

    blatt.drucken(titel_wiederholen=False)

    # Ein Aushang ist eine Seite: Bis zu 14 Zeilen passen auch in der
    # Höhe darauf. Ein größerer Plan läuft über mehrere Seiten mit
    # wiederholter Zeitleiste.
    if len(schichtzeiten.bahnen(schichten)) <= 14:
        ws.page_setup.fitToHeight = 1

    # Die Zeitleiste auf jeder gedruckten Seite
    ws.print_title_rows = f"{zeit_zeile}:{zeit_zeile}"
    ws.freeze_panes = f"B{zeit_zeile + 1}"


def _excel_liste(ws, titel, untertitel, schichten, konflikte):

    blatt = Exportblatt(
        ws, titel, untertitel,
        breiten=(28, 14, 8, 8, 10, 52),
    )
    ws.title = blattname("Liste")

    zeilen = []

    for schicht in schichten:

        besetzt = len(schicht.get("helfer") or ())
        fehlen = max(0, (schicht.get("needed") or 0) - besetzt)

        zeilen.append((
            schicht["task"],
            schichtzeiten.spanne_text(schicht["start_time"], schicht["end_time"]),
            schicht.get("needed") or 0,
            besetzt,
            fehlen if fehlen else "",
            ", ".join(namen_mit_markierung(schicht, konflikte)),
        ))

    plaetze = sum(s.get("needed") or 0 for s in schichten)
    besetzt = sum(len(s.get("helfer") or ()) for s in schichten)

    blatt.tabelle(
        ("Tätigkeit", "Zeit", "Soll", "Ist", "fehlen", "Helfer"),
        zeilen,
        formate=("text", "text", "zahl", "zahl", "zahl", "text"),
        summe=(
            "Summe", "", plaetze, besetzt,
            (plaetze - besetzt) if plaetze > besetzt else "", "",
        ),
        umbrechen=(0, 5),
        # Wo noch Helfer fehlen, steht die Zeile rot.
        hervorheben=lambda werte: ROT if werte[4] else None,
    )

    blatt.drucken()


# =========================================================
# PDF
# =========================================================

def pdf(titel, untertitel, schichten, pfad, alle_schichten=None):
    """Dieselbe Matrix als PDF im Querformat."""

    from berichte.pdf_bericht import (
        GRAU as P_GRAU, LINIE as P_LINIE, ORANGE as P_ORANGE, RAND,
        ROT as P_ROT, TEXT as P_TEXT, WEISS as P_WEISS, ZEBRA as P_ZEBRA,
        PdfBericht, schrift,
    )

    alle_schichten = alle_schichten if alle_schichten is not None else schichten

    # Nach Uhrzeit, wie in der Excel-Mappe
    schichten = schichtzeiten.nach_zeit(schichten)

    konflikte = schichtzeiten.konflikte_je_schicht(alle_schichten)

    bericht = PdfBericht(titel, untertitel, quer=True)

    raster = schichtzeiten.raster(schichten)
    reihen = schichtzeiten.bahnen(schichten)

    if raster is not None and reihen:

        anfang, ende, schritt = raster

        name_breite = 230
        x0 = RAND + name_breite
        x1 = bericht.breite - RAND
        pro_minute = (x1 - x0) / (ende - anfang)

        f_zeit = schrift(18, fett=True)
        f_name = schrift(20, fett=True)
        f_block = schrift(17)
        f_block_fett = schrift(17, fett=True)

        zeitleiste_hoehe = 40

        def zeitleiste():

            m = bericht.malen
            y = bericht.y

            m.rectangle((RAND, y, x1, y + zeitleiste_hoehe), fill=P_ORANGE)
            m.text((RAND + 12, y + 9), "Tätigkeit", font=f_zeit, fill=P_WEISS)

            for minute in range(anfang, ende + 1, 60):
                x = x0 + (minute - anfang) * pro_minute
                if minute < ende:
                    m.text((x + 6, y + 9), schichtzeiten.uhrzeit(minute),
                           font=f_zeit, fill=P_WEISS)
                m.line((x, y, x, y + zeitleiste_hoehe), fill=P_WEISS, width=1)

            bericht.y += zeitleiste_hoehe

        bericht._platz(zeitleiste_hoehe + 120)
        zeitleiste()

        for position, (taetigkeit, bahn) in enumerate(reihen):

            meiste_namen = max(len(s.get("helfer") or ()) or 1 for s in bahn)
            hoehe = max(96, 30 + 24 * (meiste_namen + 1) + 10)

            if bericht._platz(hoehe):
                zeitleiste()

            m = bericht.malen
            y = bericht.y

            if position % 2 == 1:
                m.rectangle((RAND, y, x1, y + hoehe), fill=P_ZEBRA)

            m.text(
                (RAND + 12, y + 10),
                bericht._kuerzen(taetigkeit, f_name, name_breite - 24),
                font=f_name, fill=P_TEXT,
            )

            # Stundenraster
            for minute in range(anfang, ende + 1, 60):
                x = x0 + (minute - anfang) * pro_minute
                m.line((x, y, x, y + hoehe), fill=P_LINIE, width=1)

            m.line((RAND, y + hoehe, x1, y + hoehe), fill=P_LINIE, width=1)

            for schicht in bahn:

                von, bis = schichtzeiten.zeitraum(schicht["start_time"], schicht["end_time"])

                bx0 = x0 + (von - anfang) * pro_minute + 3
                bx1 = x0 + (bis - anfang) * pro_minute - 3
                by0 = y + 6
                by1 = y + hoehe - 6

                hell, kraeftig = AMPEL_PDF[status(schicht)]

                m.rounded_rectangle((bx0, by0, bx1, by1), radius=8,
                                    fill=hell, outline=kraeftig, width=3)

                innen = bx1 - bx0 - 20
                tx = bx0 + 10
                ty = by0 + 6

                m.text((tx, ty), bericht._kuerzen(
                    schichtzeiten.spanne_text(schicht["start_time"], schicht["end_time"]),
                    f_block_fett, innen), font=f_block_fett, fill=P_TEXT)

                ty += 24

                namen = namen_mit_markierung(schicht, konflikte) or ["noch niemand"]

                for name in namen:
                    farbe = P_ROT if name.startswith("! ") or name == "noch niemand" else P_TEXT
                    m.text((tx, ty), bericht._kuerzen(name, f_block, innen),
                           font=f_block, fill=farbe)
                    ty += 24

                zahl = f"{len(schicht.get('helfer') or ())} / {schicht.get('needed') or 0}"
                m.text(
                    (bx1 - 10 - m.textlength(zahl, font=f_block_fett), by1 - 26),
                    zahl, font=f_block_fett, fill=kraeftig,
                )

            bericht.y += hoehe

        bericht.abstand(18)

    bericht.text(LEGENDE, grau=True, groesse=18)

    eigene_ids = {s["id"] for s in schichten}

    treffer = [
        t for t in schichtzeiten.ueberschneidungen(alle_schichten)
        if t["schichten"][0]["id"] in eigene_ids or t["schichten"][1]["id"] in eigene_ids
    ]

    if treffer:
        bericht.ueberschrift("Überschneidungen", platz_danach=60)
        for t in treffer:
            bericht.text(schichtzeiten.konflikt_text(t), groesse=20, farbe=P_ROT)

    ohne = schichtzeiten.ohne_zeit(schichten)

    if ohne:
        bericht.ueberschrift("Schichten ohne Uhrzeit")
        bericht.tabelle(
            ("Tätigkeit", "Helfer", "Ist / Soll"),
            [
                (
                    s["task"] or "Schicht",
                    ", ".join(namen_mit_markierung(s, konflikte)) or "noch niemand",
                    f"{len(s.get('helfer') or ())} / {s.get('needed') or 0}",
                )
                for s in ohne
            ],
            anteile=(0.3, 0.55, 0.15),
            ausrichtung=("left", "left", "right"),
        )

    bericht.speichern(pfad)

    return pfad
