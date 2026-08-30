"""
=========================================================
KiG POS
=========================================================

Datei:
    datenpaket.py

Beschreibung:
    Was von Gerät zu Gerät geht - und was es dort auslöst.

    Drei Arten, mehr gibt es nicht:

        datenbank   Alles: Artikel, Preise, Rezepte, bisherige
                    Buchungen. Das andere Gerät wird damit
                    Nebengerät und darf mitverkaufen, die
                    Stammdaten bleiben hier.

        kasse       Das Schreibrecht selbst. Danach darf das
                    andere Gerät Preise ändern und dieses
                    hier nur noch zusehen.

        buchungen   Nur, was dazugekommen ist: Verkäufe,
                    Kassenbuch, Listen, Schichten. Zum
                    Einsammeln auf dem anderen Gerät.

    Diese Datei ist die einzige Stelle, an der die drei
    Begriffe in Aufrufe übersetzt werden - der
    Übertragungsweg (funk.py, Datei, Bluetooth) weiß davon
    nichts und trägt nur die Datei.

Version:
    1.0.0
=========================================================
"""

import uebergabe
import zusammenfuehren


DATENBANK = "datenbank"
KASSE = "kasse"
BUCHUNGEN = "buchungen"

ARTEN = (DATENBANK, KASSE, BUCHUNGEN)


BESCHRIFTUNG = {
    DATENBANK: "Datenbank",
    KASSE: "Kasse",
    BUCHUNGEN: "Buchungen",
}


ERKLAERUNG = {
    DATENBANK: (
        "Artikel, Preise und alles Bisherige. Das andere Gerät darf "
        "danach mitverkaufen, die Stammdaten bleiben hier."
    ),
    KASSE: (
        "Das Schreibrecht wandert mit. Dieses Gerät darf danach nur "
        "noch zusehen."
    ),
    BUCHUNGEN: (
        "Nur was dazugekommen ist: Verkäufe, Kassenbuch, Listen, "
        "Schichten."
    ),
}


def erzeugen(db, art, ordner, an_id=None, an_name=None):
    """Schreibt die Datei für diese Art. Liefert (pfad, meldung).

    an_id/an_name werden nur für die Kasse gebraucht - sie muss
    wissen, an wen sie geht. Über eine Verbindung ist das kein
    Nachfragen mehr wert: Die Gegenseite hat sich beim Anklopfen
    vorgestellt.
    """

    if art == DATENBANK:

        pfad, stand = uebergabe.ausstatten(db, ordner)

        return pfad, f"Datenbank bereit (Stand {stand})"

    if art == KASSE:

        if not an_id:
            raise ValueError(
                "Für die Kasse muss feststehen, wer sie bekommt."
            )

        # Zweite Sicherung hinter der Bedienung: Der Dialog bietet die
        # Kasse auf einem Nebengerät gar nicht erst an - aber weggeben,
        # was einem nicht gehört, darf auch kein anderer Weg.
        if db.nur_ansicht:
            raise ValueError(
                "Die Kasse liegt bei einem anderen Gerät - abgeben "
                "kann nur, wer sie hat."
            )

        pfad, stand = uebergabe.abgeben(db, an_id, an_name or an_id, ordner)

        return pfad, f"Kasse an {an_name or an_id} (Stand {stand})"

    if art == BUCHUNGEN:

        pfad, verkaeufe = zusammenfuehren.bereitstellen(db, ordner)

        return pfad, f"Buchungen bereit ({verkaeufe} Verkäufe)"

    raise ValueError(f"Unbekannte Art: {art}")


def einspielen(db, art, pfad):
    """Nimmt die empfangene Datei an. Liefert eine Meldung."""

    if art == DATENBANK:

        _sicherung, nur_ansicht = uebergabe.einrichten(db, pfad)

        return (
            "Datenbank übernommen - dieses Gerät ist Nebengerät."
            if nur_ansicht else
            "Datenbank übernommen - dieses Gerät hat die Kasse."
        )

    if art == KASSE:

        besitz = db.get_besitz()

        befund = uebergabe.pruefen(
            pfad, db.geraet["id"], besitz["stand"] if besitz else 0
        )

        if not befund["lesbar"]:
            return befund["grund"]

        # Erzwingen ist hier nie nötig: Die Datei ist über eine
        # Verbindung gekommen, in der sich dieses Gerät vorgestellt
        # hat - sie ist an genau diese Kennung gerichtet.
        uebergabe.uebernehmen(
            db, pfad, erzwingen=not befund["fuer_mich"]
        )

        return "Kasse übernommen - dieses Gerät darf jetzt ändern."

    if art == BUCHUNGEN:

        uebernommen = zusammenfuehren.einsammeln(db, pfad)

        return zusammenfuehren.bericht(uebernommen)

    raise ValueError(f"Unbekannte Art: {art}")
