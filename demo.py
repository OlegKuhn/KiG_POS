"""
=========================================================
KiG POS
=========================================================

Datei:
    demo.py

Beschreibung:
    Demo-Modus: eine Spielwiese auf einer Kopie der
    Datenbank.

    Beim Starten wird der aktuelle Stand der Datenbank
    eingefroren - kopiert - und die Anwendung arbeitet ab
    da auf dieser Kopie. Alles funktioniert wie sonst,
    Änderungen werden auch gespeichert, aber eben nur in
    der Kopie. Beim Verlassen verschwindet sie samt allem,
    was darin angestellt wurde; es gilt wieder der Stand
    von vorher.

    Gedacht zum Zeigen und Ausprobieren: neue Helfer
    einweisen, eine Rezeptkalkulation durchspielen, den
    Ablauf eines Abends üben - ohne die echten Bestände zu
    verändern.

    Der Modus wird bewusst NICHT gespeichert: Nach jedem
    Programmstart läuft die Anwendung im normalen Modus.
    Eine Kopie, die von einem Absturz übrig geblieben ist,
    wird beim Start weggeräumt (siehe aufraeumen).

Version:
    1.0.0
=========================================================
"""

import shutil

# Nur im Arbeitsspeicher: Ein Neustart beginnt immer im normalen
# Modus, egal wie die Anwendung beendet wurde.
_aktiv = False

# Unterordner neben der echten Datenbank. Eigener Ordner, damit auch
# die automatischen Sicherungen der Demo dort landen und nicht
# zwischen den echten liegen.
ORDNER_NAME = "demo"
DATEI_NAME = "kig_demo.db"


def ist_aktiv():
    """Läuft die Anwendung gerade im Demo-Modus?"""

    return _aktiv


def ordner(daten_ordner):
    """Ordner der Demo-Datenbank."""

    return daten_ordner / ORDNER_NAME


def database_path(daten_ordner):
    """Welche Datenbank gilt gerade?

    Im Demo-Modus die Kopie, sonst die echte. Der
    DatabaseManager fragt hier nach (siehe
    database.py:get_database_path).
    """

    if _aktiv:
        return ordner(daten_ordner) / DATEI_NAME

    return daten_ordner / "kig.db"


def aufraeumen(daten_ordner):
    """Räumt eine übrig gebliebene Demo-Kopie weg.

    Wird beim Programmstart aufgerufen: Endete die letzte Sitzung
    im Demo-Modus (Absturz, Akku leer), soll davon nichts
    übrigbleiben - weder Daten noch Speicherplatz.
    """

    global _aktiv

    _aktiv = False

    _loeschen(daten_ordner)


def starten(daten_ordner):
    """Friert den aktuellen Stand ein und schaltet um.

    Die Kopie wird jedes Mal neu angelegt: Der Demo-Modus beginnt
    immer mit dem, was gerade wirklich in der Datenbank steht.

    Die Datenbank muss vorher geschlossen sein - sonst stünden
    Änderungen noch im WAL-Journal und fehlten in der Kopie (siehe
    KiGPOS.apply_demo_mode).
    """

    global _aktiv

    _loeschen(daten_ordner)

    ziel_ordner = ordner(daten_ordner)
    ziel_ordner.mkdir(parents=True, exist_ok=True)

    quelle = daten_ordner / "kig.db"

    if quelle.exists():
        shutil.copy2(quelle, ziel_ordner / DATEI_NAME)

    _aktiv = True

    return ziel_ordner / DATEI_NAME


def beenden(daten_ordner):
    """Verlässt den Demo-Modus und verwirft die Kopie."""

    global _aktiv

    _aktiv = False

    _loeschen(daten_ordner)


def _loeschen(daten_ordner):

    ziel = ordner(daten_ordner)

    if not ziel.exists():
        return

    # Ein fehlgeschlagenes Aufräumen darf die Anwendung nicht
    # aufhalten - beim nächsten Start wird es erneut versucht.
    shutil.rmtree(ziel, ignore_errors=True)
