"""
=========================================================
KiG POS
=========================================================

Datei:
    geraet.py

Beschreibung:
    Wer bin ich? Kennung und Name dieses Geräts.

    Sobald KiG POS auf mehreren Geräten läuft, muss jedes
    von ihnen sagen können, wer es ist: Der Schichtplan-
    rechner zu Hause ist ein anderer als das Kassentablet
    am Stand.

    Die Kennung liegt bewusst NEBEN der Datenbank in einer
    eigenen Datei und nicht darin:

        Die Datenbank wandert zwischen den Geräten. Stünde
        die Kennung in ihr, hieße plötzlich das Tablet wie
        der Rechner - und keines wüsste mehr, wer es ist.

    Aufbau der Datei (geraet.json):

        {
            "id":   "PC-3f9a2c",
            "name": "Computer"
        }

    Die Kennung entsteht einmalig beim ersten Start und
    ändert sich nie wieder. Der Name ist frei wählbar und
    dient nur der Anzeige ("Kasse liegt bei Tablet").

Version:
    1.0.0
=========================================================
"""

import json
import uuid

from kivy.utils import platform


DATEI_NAME = "geraet.json"

# Ohne Namen ist eine Übergabe nicht zu lesen ("Kasse liegt bei
# 3f9a2c"), deshalb ein sinnvoller Vorschlag je nach Gerät.
STANDARD_NAMEN = {
    "android": "Tablet",
    "ios": "Tablet",
}

STANDARD_NAME_RECHNER = "Computer"


def _standard_name():

    return STANDARD_NAMEN.get(platform, STANDARD_NAME_RECHNER)


def _pfad(daten_ordner):

    return daten_ordner / DATEI_NAME


def _neue_kennung():
    """Kurze, eindeutige Kennung.

    Sechs Stellen aus einer Zufalls-UUID: kurz genug, um sie
    vorzulesen, und weit genug entfernt von einer Verwechslung.
    Das Kürzel davor sagt auf einen Blick, um welche Art Gerät es
    sich handelt.
    """

    kuerzel = "TAB" if platform in STANDARD_NAMEN else "PC"

    return f"{kuerzel}-{uuid.uuid4().hex[:6]}"


def laden(daten_ordner):
    """Kennung und Name dieses Geräts; legt beides beim ersten
    Aufruf an."""

    pfad = _pfad(daten_ordner)

    if pfad.is_file():

        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))

            if daten.get("id"):
                return {
                    "id": daten["id"],
                    "name": daten.get("name") or _standard_name(),
                }

        except (ValueError, OSError):
            # Kaputte Datei: Lieber eine neue Kennung als gar keine.
            # Der Verlust ist verschmerzbar - die Datenbank hängt
            # nicht daran, nur die Zuordnung "wer bin ich".
            pass

    daten = {"id": _neue_kennung(), "name": _standard_name()}

    speichern(daten_ordner, daten)

    return daten


def speichern(daten_ordner, daten):

    daten_ordner.mkdir(parents=True, exist_ok=True)

    _pfad(daten_ordner).write_text(
        json.dumps(daten, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def umbenennen(daten_ordner, name):
    """Ändert nur den angezeigten Namen - die Kennung bleibt."""

    name = (name or "").strip()

    if not name:
        return None

    daten = laden(daten_ordner)
    daten["name"] = name

    speichern(daten_ordner, daten)

    return daten
