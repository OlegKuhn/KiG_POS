"""
=========================================================
KiG POS
=========================================================

Datei:
    zusammenfuehren.py

Beschreibung:
    Buchungen mehrerer Geräte einsammeln.

    Gedacht für den Fall, dass an einem Abend zwei Stände
    kassieren: Jedes Gerät bucht in seine eigene Datenbank,
    hinterher werden die Zugänge auf einem Gerät
    zusammengeführt.

    Zusammengeführt wird ausschließlich, was DAZUKOMMT -
    Verkäufe, Kassenbuchzeilen, Checklisten, Schichtpläne,
    Kalendereinträge. Für solche Zeilen gibt es keinen
    Konflikt: Sie sind entweder schon da oder nicht.

    Nicht zusammengeführt wird, was GEÄNDERT wird: Artikel,
    Preise, Kategorien, Rezepte. Die pflegt nur das
    Hauptgerät (siehe database.STAMMDATEN_TABELLEN) - eben
    damit hier nichts zu entscheiden ist. Änderte sie jedes
    Gerät für sich, müsste beim Zusammenführen jemand
    festlegen, welcher Preis gilt; das kann keine Technik.

    Erkannt wird jede Zeile an ihrer uid, die
    geräteübergreifend eindeutig ist. Zweimal dieselbe Datei
    einzusammeln ändert deshalb nichts.

    Der Bestand wandert mit: Seit er als Summe von
    Bewegungen geführt wird (siehe
    database._create_stock_movements_table), ist auch er
    etwas, das nur dazukommt. Zwei Geräte, die je einen
    Abgang buchen, ergeben zusammen zwei Abgänge.

Version:
    1.0.0
=========================================================
"""

import sqlite3

from datetime import datetime
from pathlib import Path

from database import MERGE_TABELLEN


ENDUNG = ".kigdb"


# Verweise zwischen den Tabellen: Spalte -> Tabelle, auf die sie
# zeigt. Beim Einfügen wird die fremde Nummer über die uid auf die
# hiesige umgeschrieben - sonst zeigte ein eingesammelter Bon auf
# irgendein Event dieses Geräts.
VERWEISE = {
    "sales": {"event_id": "events"},
    "sale_items": {"sale_id": "sales"},
    "checklist_items": {"checklist_id": "checklists"},
    "shift_plans": {"event_id": "events"},
    "shifts": {"plan_id": "shift_plans"},
    "shift_helpers": {"shift_id": "shifts"},
}


# Sprechende Namen für die Rückmeldung.
BEZEICHNUNGEN = {
    "events": "Kalendereinträge",
    "sales": "Verkäufe",
    "sale_items": "Verkaufspositionen",
    "stock_movements": "Bestandsbewegungen",
    "cash_book_entries": "Kassenbuchzeilen",
    "checklists": "Checklisten",
    "checklist_items": "Aufgaben",
    "shift_plans": "Schichtpläne",
    "shifts": "Schichten",
    "shift_helpers": "eingetragene Helfer",
}


def dateiname(geraet_name):
    """Name der Datei, die ein Gerät zum Einsammeln bereitstellt."""

    sicher = "".join(
        zeichen if zeichen.isalnum() or zeichen in " -_" else "_"
        for zeichen in (geraet_name or "geraet")
    ).strip().replace(" ", "_")

    return (
        f"kigpos_zugaenge_{sicher or 'geraet'}_"
        f"{datetime.now():%Y-%m-%d_%H-%M}{ENDUNG}"
    )


def bereitstellen(db, ziel_ordner):
    """Schreibt eine Kopie dieser Datenbank zum Einsammeln.

    Anders als die Übergabe (siehe uebergabe.py) wechselt dabei
    NICHTS: Dieses Gerät behält alle Rechte und bucht weiter. Die
    Kopie ist nur die Nachricht "das habe ich gebucht".

    Liefert (pfad, anzahl_verkaeufe).
    """

    db.uids_nachtragen()

    ziel_ordner = Path(ziel_ordner)
    ziel_ordner.mkdir(parents=True, exist_ok=True)

    ziel = ziel_ordner / dateiname(db.geraet["name"])

    kopie = sqlite3.connect(ziel)

    try:
        db.connection.backup(kopie)
    finally:
        kopie.close()

    db.cursor.execute("SELECT COUNT(*) FROM sales")

    return ziel, db.cursor.fetchone()[0]


def _oeffnen(pfad):

    verbindung = sqlite3.connect(f"file:{Path(pfad)}?mode=ro", uri=True)
    verbindung.row_factory = sqlite3.Row

    return verbindung


def _spalten(verbindung, tabelle):

    return [
        zeile["name"]
        for zeile in verbindung.execute(f"PRAGMA table_info({tabelle})")
    ]


def vorschau(db, pfad):
    """Was käme dazu, wenn diese Datei eingesammelt würde?

    Ändert nichts. Liefert ein Wörterbuch mit Anzahl je Tabelle,
    dazu Herkunft und Lesbarkeit - alles, was der Rückfragedialog
    braucht.
    """

    ergebnis = {
        "lesbar": False,
        "grund": "",
        "geraet": "",
        "neu": {},
        "gesamt": 0,
        "eigene_datei": False,
    }

    pfad = Path(pfad)

    if not pfad.is_file():
        ergebnis["grund"] = "Datei nicht gefunden."
        return ergebnis

    try:
        fremd = _oeffnen(pfad)

    except sqlite3.Error as fehler:
        ergebnis["grund"] = f"Datei nicht lesbar ({fehler})."
        return ergebnis

    try:
        vorhanden = {
            zeile["name"]
            for zeile in fremd.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        if "sales" not in vorhanden or "besitz" not in vorhanden:
            ergebnis["grund"] = "Das ist keine Datenbank von KiG POS."
            return ergebnis

        besitz = fremd.execute("SELECT * FROM besitz WHERE id = 1").fetchone()

        if besitz is not None:
            ergebnis["geraet"] = besitz["geraet_name"]
            ergebnis["eigene_datei"] = (
                besitz["geraet_id"] == db.geraet["id"]
            )

        for tabelle in MERGE_TABELLEN:

            if tabelle not in vorhanden:
                continue

            if "uid" not in _spalten(fremd, tabelle):
                ergebnis["grund"] = (
                    "Die Datei stammt aus einer älteren Fassung ohne "
                    "eindeutige Kennungen - sie lässt sich nicht "
                    "zusammenführen."
                )
                return ergebnis

            fremde_uids = {
                zeile["uid"]
                for zeile in fremd.execute(
                    f"SELECT uid FROM {tabelle} WHERE uid IS NOT NULL"
                )
            }

            if not fremde_uids:
                continue

            db.cursor.execute(
                f"SELECT uid FROM {tabelle} WHERE uid IS NOT NULL"
            )

            eigene_uids = {zeile["uid"] for zeile in db.cursor.fetchall()}

            neu = len(fremde_uids - eigene_uids)

            if neu:
                ergebnis["neu"][tabelle] = neu
                ergebnis["gesamt"] += neu

        ergebnis["lesbar"] = True

    except sqlite3.Error as fehler:
        ergebnis["grund"] = f"Datei unvollständig ({fehler})."

    finally:
        fremd.close()

    return ergebnis


def einsammeln(db, pfad):
    """Fügt alles hinzu, was in der Datei steht und hier fehlt.

    Liefert ein Wörterbuch mit der Anzahl je Tabelle.

    Zweimal dieselbe Datei einzusammeln bleibt folgenlos: Erkannt
    wird jede Zeile an ihrer uid.
    """

    # Auch die eigenen Zeilen brauchen eine Kennung - sonst hätte
    # eine spätere Rückgabe an das andere Gerät nichts, woran es sie
    # erkennt.
    db.uids_nachtragen()

    fremd = _oeffnen(pfad)

    uebernommen = {}

    # Tabelle -> {fremde Nummer: hiesige Nummer}. Wird beim Einfügen
    # der Kindzeilen gebraucht: Ein eingesammelter Bon muss auf das
    # HIESIGE Event zeigen, nicht auf die Nummer, die es beim anderen
    # Gerät hatte.
    zuordnungen = {}

    try:
        for tabelle in MERGE_TABELLEN:

            spalten = _spalten(fremd, tabelle)

            if "uid" not in spalten:
                continue

            # Was ist hier schon bekannt? uid -> hiesige Nummer.
            db.cursor.execute(f"SELECT id, uid FROM {tabelle}")

            bekannt = {
                zeile["uid"]: zeile["id"]
                for zeile in db.cursor.fetchall()
                if zeile["uid"]
            }

            zuordnung = {}

            verweise = VERWEISE.get(tabelle, {})

            # id wird nicht übernommen: Die vergibt die Datenbank hier
            # selbst, sonst stieße sie mit einer vorhandenen zusammen.
            zu_uebernehmen = [name for name in spalten if name != "id"]

            platzhalter = ",".join("?" for _ in zu_uebernehmen)

            neu = 0

            for zeile in fremd.execute(f"SELECT * FROM {tabelle} ORDER BY id"):

                uid = zeile["uid"]

                if not uid:
                    continue

                if uid in bekannt:
                    zuordnung[zeile["id"]] = bekannt[uid]
                    continue

                werte = []

                for name in zu_uebernehmen:

                    wert = zeile[name]

                    if name in verweise and wert is not None:
                        wert = zuordnungen.get(
                            verweise[name], {}
                        ).get(wert)

                    werte.append(wert)

                db.cursor.execute(
                    f"INSERT INTO {tabelle}"
                    f"({','.join(zu_uebernehmen)}) VALUES ({platzhalter})",
                    werte
                )

                zuordnung[zeile["id"]] = db.cursor.lastrowid
                neu += 1

            zuordnungen[tabelle] = zuordnung

            if neu:
                uebernommen[tabelle] = neu

        db.commit()

    finally:
        fremd.close()

    return uebernommen


def bericht(uebernommen):
    """Ein Satz, der sagt, was dazugekommen ist."""

    if not uebernommen:
        return "Nichts Neues - alles war schon da."

    teile = [
        f"{anzahl} {BEZEICHNUNGEN.get(tabelle, tabelle)}"
        for tabelle, anzahl in uebernommen.items()
    ]

    return "Eingesammelt: " + ", ".join(teile) + "."
