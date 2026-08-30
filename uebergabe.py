"""
=========================================================
KiG POS
=========================================================

Datei:
    uebergabe.py

Beschreibung:
    Die Kasse von einem Gerät ans nächste weiterreichen.

    Gedacht für den Fall: Zu Hause am Rechner werden Artikel
    und Preise gepflegt, am Stand kassiert das Tablet.
    Beide gleichzeitig ginge nur mit einem Abgleich, der
    Änderungen zusammenführt - hier wandert stattdessen das
    Schreibrecht als Marke mit der Datenbank.

    Ablauf:

        1. Abgeben     Das Gerät trägt den Empfänger als
                       Besitzer ein, zählt den Stand hoch
                       und schreibt die Übergabedatei.
                       Danach ist es selbst nur noch Ansicht.

        2. Übernehmen  Das andere Gerät liest die Datei,
                       zeigt an, was drinsteht, und ersetzt
                       nach Rückfrage seine Datenbank.

    Die Übergabedatei IST die Datenbank - erzeugt über die
    Sicherungsschnittstelle von SQLite, damit auch das
    WAL-Journal darin steckt.

    Zwei Sicherungen gegen den häufigsten Fehler, eine alte
    Datei einzuspielen:

        * Der Stand muss mindestens so hoch sein wie der
          eigene. Eine ältere Datei wird abgelehnt, ihr
          Inhalt ginge sonst verloren.

        * Wer nicht als Empfänger eingetragen ist, bekommt
          eine Warnung - übernehmen kann er trotzdem, aber
          erst nach ausdrücklicher Bestätigung (sonst käme
          man an eine Kasse nicht mehr heran, deren
          Empfängergerät im Bodensee liegt).

    Daneben steht ein zweites Paar für den Fall mehrerer
    Stände, die GLEICHZEITIG verkaufen:

        3. Ausstatten  Schreibt dieselbe Kopie, lässt den
                       Besitz aber, wo er ist. Das Tablet
                       bekommt Artikel und Preise, das
                       Hauptgerät bleibt Hauptgerät.

        4. Einrichten  Spielt so eine Kopie ein, ohne die
                       Kasse an sich zu nehmen. Wer sie
                       einspielt, wird Nebengerät: buchen ja,
                       Preise ändern nein.

    Der Unterschied in einem Satz: Übergeben wechselt den
    Besitzer, Ausstatten vervielfältigt die Daten. Was die
    Nebengeräte buchen, holt zusammenfuehren.py später ein.

Version:
    1.0.0
=========================================================
"""

import sqlite3

from datetime import datetime
from pathlib import Path


ENDUNG = ".kigdb"


def dateiname(geraet_name, stand, art="uebergabe"):
    """Sprechender Name: Wer gibt ab, welcher Stand, wann."""

    sicher = "".join(
        zeichen if zeichen.isalnum() or zeichen in " -_" else "_"
        for zeichen in (geraet_name or "geraet")
    ).strip().replace(" ", "_")

    return (
        f"kigpos_{art}_{sicher or 'geraet'}_"
        f"stand{stand:03d}_{datetime.now():%Y-%m-%d_%H-%M}{ENDUNG}"
    )


def abgeben(db, an_id, an_name, ziel_ordner):
    """Überträgt das Schreibrecht und schreibt die Übergabedatei.

    Liefert (pfad, stand).

    Reihenfolge ist wichtig: erst eintragen, dann kopieren. Die Datei
    enthält damit bereits den neuen Besitzer - wer sie einspielt,
    findet sich selbst darin.
    """

    stand = db.besitz_uebernehmen(an_id, an_name)

    ziel_ordner = Path(ziel_ordner)
    ziel_ordner.mkdir(parents=True, exist_ok=True)

    ziel = ziel_ordner / dateiname(db.geraet["name"], stand)

    # Über die Sicherungsschnittstelle statt einfachem Kopieren:
    # Nur so ist die Datei in sich stimmig, auch wenn noch Daten im
    # WAL-Journal stehen (siehe DatabaseManager.create_backup).
    kopie = sqlite3.connect(ziel)

    try:
        db.connection.backup(kopie)
    finally:
        kopie.close()

    # Ab jetzt gehört die Kasse dem anderen Gerät.
    db.nur_ansicht = True

    return ziel, stand


def ausstatten(db, ziel_ordner):
    """Schreibt eine vollständige Kopie, OHNE die Kasse abzugeben.

    Für den zweiten, dritten, vierten Stand: Jedes Tablet braucht die
    Artikel, Preise und Rezepte, um verkaufen zu können - aber nur
    EIN Gerät darf sie ändern. Diese Kopie bringt die Daten mit und
    lässt den Besitz, wo er ist:

        Das ausstattende Gerät bleibt Hauptgerät und ändert weiter
        Preise. Wer die Kopie einspielt, wird Nebengerät: buchen,
        Listen führen und Schichten eintragen ja, Stammdaten nein.

    Deshalb zählt der Stand hier NICHT hoch. Der Stand gehört zur
    Kasse, und die wechselt gerade nicht den Besitzer - zwei Kopien
    für zwei Stände sind keine zwei Übergaben.

    Liefert (pfad, stand).
    """

    besitz = db.get_besitz()

    stand = besitz["stand"] if besitz else 0

    ziel_ordner = Path(ziel_ordner)
    ziel_ordner.mkdir(parents=True, exist_ok=True)

    ziel = ziel_ordner / dateiname(
        db.geraet["name"], stand, art="ausstattung"
    )

    kopie = sqlite3.connect(ziel)

    try:
        db.connection.backup(kopie)
    finally:
        kopie.close()

    return ziel, stand


def einrichten(db, pfad):
    """Spielt eine Kopie ein, ohne die Kasse an sich zu nehmen.

    Der Unterschied zu uebernehmen(): Dort wird dieses Gerät zum
    Hauptgerät. Hier bleibt der Besitzer der, der in der Datei steht -
    dieses Gerät richtet sich nur mit denselben Daten ein.

    Wessen Name in der Datei steht, entscheidet also, was dieses Gerät
    danach darf. Steht es selbst darin (weil es doch eine Übergabe
    war), bekommt es die Kasse; sonst wird es Nebengerät.

    Liefert (sicherung, nur_ansicht).
    """

    pfad = Path(pfad)

    sicherungs_ordner = db.database_path.parent / "backups"
    sicherungs_ordner.mkdir(parents=True, exist_ok=True)

    sicherung = sicherungs_ordner / (
        f"vor_ausstattung_{datetime.now():%Y-%m-%d_%H-%M-%S}.db"
    )

    kopie = sqlite3.connect(sicherung)

    try:
        db.connection.backup(kopie)
    finally:
        kopie.close()

    quelle = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)

    try:
        # Wie beim Einspielen einer Übergabe: Genau dieser Vorgang
        # darf schreiben, auch wenn das Gerät sonst nur zusehen darf.
        vorher = db.nur_ansicht
        db.nur_ansicht = False

        try:
            quelle.backup(db.connection)

            db.schema_sicherstellen()

            # Kein besitz_uebernehmen: Der Besitzer steht in der Datei
            # und bleibt, wer er ist. besitz_sicherstellen setzt daraus
            # den Schreibschutz für dieses Gerät.
            nur_ansicht = db.besitz_sicherstellen()

        except Exception:
            db.nur_ansicht = vorher
            raise

    finally:
        quelle.close()

    return sicherung, nur_ansicht


def pruefen(pfad, eigene_id, eigener_stand):
    """Was steht in dieser Datei - und darf sie eingespielt werden?

    Liefert ein Wörterbuch mit allem, was der Rückfragedialog
    braucht. Wirft nichts: Ein kaputter oder falscher Pfad ist keine
    Ausnahme, sondern eine Antwort ("lesbar": False).
    """

    ergebnis = {
        "lesbar": False,
        "grund": "",
        "besitzer_id": None,
        "besitzer_name": "",
        "stand": 0,
        "fuer_mich": False,
        "zu_alt": False,
        "verkaeufe": 0,
        "artikel": 0,
        "letzter_verkauf": "",
    }

    pfad = Path(pfad)

    if not pfad.is_file():
        ergebnis["grund"] = "Datei nicht gefunden."
        return ergebnis

    try:
        verbindung = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
        verbindung.row_factory = sqlite3.Row

    except sqlite3.Error as fehler:
        ergebnis["grund"] = f"Datei nicht lesbar ({fehler})."
        return ergebnis

    try:
        zeiger = verbindung.cursor()

        zeiger.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='besitz'"
        )

        if zeiger.fetchone() is None:
            ergebnis["grund"] = (
                "Das ist keine Übergabedatei von KiG POS."
            )
            return ergebnis

        zeiger.execute("SELECT * FROM besitz WHERE id = 1")
        besitz = zeiger.fetchone()

        if besitz is None:
            ergebnis["grund"] = "In der Datei steht kein Besitzer."
            return ergebnis

        ergebnis["besitzer_id"] = besitz["geraet_id"]
        ergebnis["besitzer_name"] = besitz["geraet_name"]
        ergebnis["stand"] = besitz["stand"]

        ergebnis["fuer_mich"] = besitz["geraet_id"] == eigene_id
        ergebnis["zu_alt"] = besitz["stand"] < eigener_stand

        zeiger.execute("SELECT COUNT(*) FROM sales")
        ergebnis["verkaeufe"] = zeiger.fetchone()[0]

        zeiger.execute("SELECT COUNT(*) FROM articles")
        ergebnis["artikel"] = zeiger.fetchone()[0]

        zeiger.execute(
            "SELECT sale_date FROM sales ORDER BY id DESC LIMIT 1"
        )
        letzter = zeiger.fetchone()

        ergebnis["letzter_verkauf"] = letzter["sale_date"] if letzter else ""

        ergebnis["lesbar"] = True

    except sqlite3.Error as fehler:
        ergebnis["grund"] = f"Datei unvollständig ({fehler})."

    finally:
        verbindung.close()

    return ergebnis


def uebernehmen(db, pfad, erzwingen=False):
    """Ersetzt die eigene Datenbank durch die Übergabedatei.

    Vorher wird die bisherige gesichert - wer sich vertut, hat sie
    noch.

    erzwingen: Die Datei ist an ein anderes Gerät gerichtet, dieses
    hier nimmt sie trotzdem. Für den Fall, dass das Empfängergerät
    nicht mehr da ist. Der Übergabestand zählt dabei hoch, damit im
    Protokoll steht, was geschehen ist.

    Liefert den Pfad der Sicherung.
    """

    pfad = Path(pfad)

    # Sicherung des bisherigen Standes, unabhängig von der
    # Startsicherung: Diese hier ist die letzte Fassung VOR der
    # Übernahme und trägt es im Namen.
    sicherungs_ordner = db.database_path.parent / "backups"
    sicherungs_ordner.mkdir(parents=True, exist_ok=True)

    sicherung = sicherungs_ordner / (
        f"vor_uebernahme_{datetime.now():%Y-%m-%d_%H-%M-%S}.db"
    )

    kopie = sqlite3.connect(sicherung)

    try:
        db.connection.backup(kopie)
    finally:
        kopie.close()

    # Die eingespielte Datenbank in die eigene Datei übertragen -
    # wieder über die Sicherungsschnittstelle, damit die laufende
    # Verbindung bestehen bleibt und kein WAL-Rest zurückbleibt.
    quelle = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)

    try:
        # nur_ansicht kurz aussetzen: Das Einspielen ist genau der
        # Vorgang, der den Schutz aufhebt.
        vorher = db.nur_ansicht
        db.nur_ansicht = False

        try:
            quelle.backup(db.connection)

            # Nach dem Ersetzen die Tabellen dieser Programmfassung
            # sicherstellen - die Datei kann von einem Gerät mit
            # älterer Fassung kommen.
            db.schema_sicherstellen()

            if erzwingen and not db.ist_besitzer():
                db.besitz_uebernehmen(
                    db.geraet["id"], db.geraet["name"]
                )

            db.besitz_sicherstellen()

        except Exception:
            db.nur_ansicht = vorher
            raise

    finally:
        quelle.close()

    return sicherung
