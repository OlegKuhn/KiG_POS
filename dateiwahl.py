"""
=========================================================
KiG POS
=========================================================

Datei:
    dateiwahl.py

Beschreibung:
    Eine Datei von irgendwoher auf dem Gerät holen.

    Das Gegenstück zu teilen.py: Der Teilen-Knopf bringt eine
    Datei aus der App heraus, diese Auswahl bringt eine
    wieder herein.

    Warum es sie braucht: Die App sucht Übergabedateien in
    ihrem eigenen Ordner

        Android/data/de.kigev.kigpos/files/exports/uebergabe

    An den kommt auf Android kein Dateimanager heran - und
    schon gar nicht Mail oder WhatsApp, die ihre Anhänge in
    "Download" ablegen. Eine per Mail geschickte Übergabe war
    damit auf dem Tablet nicht einzuspielen: Die App durfte
    nicht dorthin sehen, wo die Datei lag.

    Seit Android 10 darf sie das auch nicht einfach so - der
    Download-Ordner gehört ihr nicht. Der vorgesehene Weg ist
    Androids eigene Dateiauswahl (ACTION_OPEN_DOCUMENT): Der
    Nutzer zeigt auf die Datei, und nur für diese eine bekommt
    die App ein Leserecht. Keine Berechtigung, kein
    Blankoscheck auf fremde Ordner.

    Die gewählte Datei wird in den Übergabeordner der App
    kopiert und von dort weiterverarbeitet. Der Rest des
    Programms sieht damit weiterhin nur gewöhnliche Pfade.

    Auf dem Rechner gibt es das nicht: Dort liegt der Ordner
    offen im Explorer, dorthin kopiert man die Datei mit zwei
    Klicks selbst.

Version:
    1.0.0
=========================================================
"""

import os
import shutil

from pathlib import Path

from kivy.clock import Clock
from kivy.utils import platform


IS_ANDROID = platform == "android"


# Eine beliebige, nur hier verwendete Zahl: Android reicht sie beim
# Ergebnis wieder herein, damit eine App mehrere offene Anfragen
# auseinanderhalten kann.
ANFRAGE = 0x4B49

# Was zur Auswahl steht. "*/*" plus die genauen Typen: Manche
# Dateiauswahlen graunen alles aus, was nicht im Typ steht, und eine
# .kigdb-Datei kennt kein Android der Welt.
TYPEN = ["application/octet-stream", "application/x-sqlite3", "*/*"]


def verfuegbar() -> bool:
    """Gibt es hier eine Systemauswahl?"""

    return IS_ANDROID


# Wo auf dem Rechner ankommt, was von außen kommt. Eine per Bluetooth
# empfangene Datei landet in dem Ordner, den Windows beim Empfangen
# vorschlägt - das ist der Download-Ordner oder der Desktop, nie der
# App-Ordner. Ohne diese Liste müsste man sie von Hand umkopieren.
EMPFANGSORDNER = ("Downloads", "Desktop", "Bluetooth")


def uebergabedateien(ordner, endung=".kigdb", anzahl=12):
    """Alle Dateien, die zum Einspielen in Frage kommen.

    Zuerst der eigene Ausgabeordner, danach - nur auf dem Rechner -
    die Orte, an denen Empfangenes liegt. Neueste zuerst.

    Liefert Paare (pfad, herkunft); herkunft ist leer für den eigenen
    Ordner und sonst der Ordnername ("Downloads").
    """

    ordner = Path(ordner)

    gefunden = []
    gesehen = set()

    def einsammeln(quelle, herkunft):

        try:
            dateien = sorted(
                quelle.glob(f"*{endung}"),
                key=lambda pfad: pfad.stat().st_mtime,
                reverse=True,
            )

        except OSError:
            return

        for pfad in dateien:

            schluessel = str(pfad).lower()

            if schluessel in gesehen:
                continue

            gesehen.add(schluessel)
            gefunden.append((pfad, herkunft))

    einsammeln(ordner, "")

    if not IS_ANDROID:

        heimat = Path.home()

        for name in EMPFANGSORDNER:
            einsammeln(heimat / name, name)

    return gefunden[:anzahl]


def auswaehlen(zielordner, fertig, fehler=None):
    """Öffnet die Dateiauswahl des Systems.

    zielordner: wohin die gewählte Datei kopiert wird
    fertig:     wird mit dem Pfad der Kopie aufgerufen
    fehler:     wird mit einem Text aufgerufen, wenn es nicht klappt

    Liefert True, wenn die Auswahl geöffnet wurde. Der Rest passiert
    später - Android meldet sich mit dem Ergebnis zurück.
    """

    if not IS_ANDROID:

        _melden(fehler, "Auf diesem Gerät gibt es keine Systemauswahl.")

        return False

    try:
        from jnius import autoclass
        from android import activity as android_aktivitaet

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")

        absicht = Intent(Intent.ACTION_OPEN_DOCUMENT)
        absicht.addCategory(Intent.CATEGORY_OPENABLE)
        absicht.setType("*/*")
        absicht.putExtra(Intent.EXTRA_MIME_TYPES, TYPEN)

        def ergebnis(anfrage, ergebnis_code, daten):

            if anfrage != ANFRAGE:
                return

            # Nur einmal zuhören: Ohne das Abmelden liefe der nächste
            # Aufruf doppelt.
            android_aktivitaet.unbind(on_activity_result=ergebnis)

            if daten is None or ergebnis_code == 0:
                # 0 ist RESULT_CANCELED - der Nutzer hat abgebrochen.
                # Das ist kein Fehler und braucht keine Meldung.
                return

            uri = daten.getData()

            if uri is None:
                _melden(fehler, "Es wurde keine Datei zurückgegeben.")
                return

            # Zurück in den Kivy-Takt: Die Antwort kommt aus Androids
            # eigenem Faden, und dort hat die Oberfläche nichts
            # verloren.
            Clock.schedule_once(
                lambda _dt: _uebernehmen(uri, zielordner, fertig, fehler), 0
            )

        android_aktivitaet.bind(on_activity_result=ergebnis)

        PythonActivity.mActivity.startActivityForResult(absicht, ANFRAGE)

        return True

    except Exception as ausnahme:

        _melden(fehler, f"Dateiauswahl nicht möglich: {ausnahme}")

        return False


# =========================================================
# Die gewählte Datei hereinholen
# =========================================================

def _uebernehmen(uri, zielordner, fertig, fehler):

    try:
        ziel = _kopieren(uri, Path(zielordner))

    except Exception as ausnahme:
        _melden(fehler, f"Datei konnte nicht gelesen werden: {ausnahme}")
        return

    if callable(fertig):
        fertig(ziel)


def _kopieren(uri, zielordner: Path) -> Path:
    """Kopiert die Datei hinter der Uri in den Zielordner."""

    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    aufloeser = PythonActivity.mActivity.getContentResolver()

    zielordner.mkdir(parents=True, exist_ok=True)

    ziel = _freier_name(zielordner, _anzeigename(uri, aufloeser))

    # Über den Dateideskriptor statt über einen Java-Datenstrom: So
    # liest Python die Datei mit seinen eigenen Mitteln, ohne jedes
    # Byte durch die Java-Brücke zu tragen.
    beschreibung = aufloeser.openFileDescriptor(uri, "r")

    try:
        with os.fdopen(os.dup(beschreibung.getFd()), "rb") as quelle:
            with open(ziel, "wb") as senke:
                shutil.copyfileobj(quelle, senke, 1024 * 1024)

    finally:
        beschreibung.close()

    return ziel


def _anzeigename(uri, aufloeser) -> str:
    """Wie die Datei heißt - so, wie der Nutzer sie gesehen hat."""

    from jnius import autoclass

    OpenableColumns = autoclass("android.provider.OpenableColumns")

    zeiger = None

    try:
        zeiger = aufloeser.query(uri, None, None, None, None)

        if zeiger is not None and zeiger.moveToFirst():

            spalte = zeiger.getColumnIndex(OpenableColumns.DISPLAY_NAME)

            if spalte >= 0:

                name = zeiger.getString(spalte)

                if name:
                    return _saeubern(name)

    except Exception:
        # Der Name ist Kür - notfalls tut es der aus der Uri.
        pass

    finally:
        if zeiger is not None:
            zeiger.close()

    letzter = uri.getLastPathSegment() or "uebergabe.kigdb"

    return _saeubern(letzter.split("/")[-1])


def _saeubern(name: str) -> str:
    """Macht aus dem Namen einen, den jedes Dateisystem verträgt."""

    erlaubt = [
        zeichen if zeichen.isalnum() or zeichen in "._- " else "_"
        for zeichen in name
    ]

    sauber = "".join(erlaubt).strip()

    # Ohne einen einzigen Buchstaben oder eine Ziffer bleibt kein
    # Name uebrig, auf den man zeigen koennte - "..", "." oder "___"
    # sind Verzeichnisse oder gar nichts.
    if not any(zeichen.isalnum() for zeichen in sauber):
        return "uebergabe.kigdb"

    return sauber[-120:]


def _freier_name(ordner: Path, name: str) -> Path:
    """Verhindert, dass eine gleichnamige Datei überschrieben wird.

    Zweimal dieselbe Übergabe zu holen ist ein Versehen, kein Grund,
    die erste zu verlieren.
    """

    ziel = ordner / name

    if not ziel.exists():
        return ziel

    stamm = ziel.stem
    endung = ziel.suffix

    for nummer in range(1, 100):

        versuch = ordner / f"{stamm}_{nummer}{endung}"

        if not versuch.exists():
            return versuch

    return ordner / f"{stamm}_neu{endung}"


def _melden(fehler, text):

    if callable(fehler):
        fehler(text)
