"""
=========================================================
KiG POS
=========================================================

Datei:
    teilen.py

Beschreibung:
    Eine ausgegebene Datei weitergeben - per Mail,
    Messenger oder wohin auch immer.

    Auf Android öffnet das die gewohnte Teilen-Auswahl.
    Der Weg dorthin ist allerdings nicht der naheliegende:

        Eine Datei aus dem App-Ordner direkt zu verschicken
        verbietet Android seit Version 7 (die andere App
        dürfte sie gar nicht öffnen). Deshalb wandert sie
        zuerst in den öffentlichen Ordner "Download/KiG POS"
        und wird von dort geteilt.

        Das löst nebenbei ein zweites Ärgernis: Bis dahin
        lagen die Ausgaben unter Android/data/..., wo kein
        Dateimanager hineinkommt. Nach dem Teilen liegen sie
        im Download-Ordner und sind auch ohne Kabel
        auffindbar.

    Auf Windows gibt es kein vergleichbares Teilen. Dort
    öffnet der Knopf den Ordner mit der ausgewählten Datei -
    von da lässt sie sich in eine Mail ziehen. Das ist
    ehrlicher, als eine Teilen-Auswahl vorzutäuschen, die
    das System nicht hat.

Version:
    1.0.0
=========================================================
"""

import subprocess

from pathlib import Path

from kivy.utils import platform


IS_ANDROID = platform == "android"


# Für die Teilen-Auswahl: Woran erkennt die Gegenstelle, was sie
# bekommt? Ohne passenden Typ bieten manche Apps gar nichts an.
DATEITYPEN = {
    ".xlsx": "application/vnd.openxmlformats-officedocument."
             "spreadsheetml.sheet",
    ".csv": "text/csv",
    ".pdf": "application/pdf",
    ".kigdb": "application/octet-stream",
    ".db": "application/octet-stream",
    ".txt": "text/plain",
}

OEFFENTLICHER_ORDNER = "Download/KiG POS"


def dateityp(pfad):

    return DATEITYPEN.get(Path(pfad).suffix.lower(), "application/octet-stream")


def per_bluetooth(pfad, betreff="KiG POS"):
    """Gibt die Datei über Bluetooth weiter. Liefert (erfolg, meldung).

    Derselbe Weg wie teilen(), nur ohne Auswahl: Die Absicht geht
    direkt an die Bluetooth-Übertragung des Geräts.

    Warum kein eigener Bluetooth-Kanal? Zwei Geräte selbst zu
    verbinden hieße: koppeln, Berechtigungen ab Android 12, ein
    lauschender Dienst auf der Gegenseite und eine Anwendung, die
    dafür offen sein muss. Die Übertragung, die jedes Android schon
    mitbringt (OPP), braucht davon nichts - sie fragt am anderen
    Gerät nach und legt die Datei ab. Genau das wird hier benutzt.

    Auf der Gegenseite landet sie im Ordner "Bluetooth" bzw.
    "Download" und wird über "Datei suchen" eingespielt (siehe
    dateiwahl.py).
    """

    if not pfad:
        return False, "Erst eine Datei erzeugen, dann senden."

    pfad = Path(pfad)

    if not pfad.is_file():
        return False, f"Die Datei gibt es nicht mehr: {pfad.name}"

    if not IS_ANDROID:
        return _rechner_bluetooth(pfad)

    return _android_bluetooth(pfad, betreff)


def teilen(pfad, betreff="KiG POS"):
    """Gibt die Datei weiter. Liefert (erfolg, meldung).

    Die Meldung ist für die Hinweiszeile gedacht und sagt im
    Fehlerfall, was schiefging - ein Knopf, der wortlos nichts tut,
    ist schlimmer als keiner.
    """

    if not pfad:
        return False, "Erst exportieren, dann teilen."

    pfad = Path(pfad)

    if not pfad.is_file():
        return False, f"Die Datei gibt es nicht mehr: {pfad.name}"

    if IS_ANDROID:
        return _android_teilen(pfad, betreff)

    return _rechner_teilen(pfad)


# =========================================================
# Android
# =========================================================

def _android_teilen(pfad, betreff):

    try:
        from jnius import autoclass, cast

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        uri = _in_downloads_kopieren(pfad, activity)

        if uri is None:
            return False, (
                "Die Datei ließ sich nicht in den Download-Ordner "
                "legen - Teilen nicht möglich."
            )

        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")

        absicht = Intent()
        absicht.setAction(Intent.ACTION_SEND)
        absicht.setType(dateityp(pfad))
        absicht.putExtra(Intent.EXTRA_SUBJECT, cast("java.lang.CharSequence", String(betreff)))
        absicht.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", uri))
        absicht.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        auswahl = Intent.createChooser(
            absicht, cast("java.lang.CharSequence", String("Senden mit"))
        )
        auswahl.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

        activity.startActivity(auswahl)

        return True, f"{pfad.name} - Teilen-Auswahl geöffnet."

    except Exception as fehler:
        return False, f"Teilen nicht möglich: {fehler}"


def _android_bluetooth(pfad, betreff):
    """Schickt die Datei an die Bluetooth-Übertragung des Systems."""

    try:
        from jnius import autoclass, cast

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity

        uri = _in_downloads_kopieren(pfad, activity)

        if uri is None:
            return False, (
                "Die Datei ließ sich nicht in den Download-Ordner "
                "legen - Senden nicht möglich."
            )

        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")

        absicht = Intent()
        absicht.setAction(Intent.ACTION_SEND)
        absicht.setType(dateityp(pfad))
        absicht.putExtra(
            Intent.EXTRA_SUBJECT, cast("java.lang.CharSequence", String(betreff))
        )
        absicht.putExtra(Intent.EXTRA_STREAM, cast("android.os.Parcelable", uri))
        absicht.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        paket = _bluetooth_paket(activity, absicht)

        if paket is None:
            # Kein Bluetooth-Empfänger - dann wenigstens die gewohnte
            # Auswahl, statt gar nichts zu tun.
            return teilen(pfad, betreff)

        absicht.setPackage(paket)
        absicht.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

        activity.startActivity(absicht)

        return True, (
            f"{pfad.name} an Bluetooth übergeben - am anderen Gerät "
            f"annehmen."
        )

    except Exception as fehler:
        return False, f"Bluetooth nicht möglich: {fehler}"


def _bluetooth_paket(activity, absicht):
    """Sucht die App, die Dateien über Bluetooth verschickt.

    Nicht über einen festen Namen: Der ist je nach Hersteller
    "com.android.bluetooth", "com.mediatek.bluetooth" oder etwas
    anderes. Gefragt wird deshalb das System, wer die Absicht
    annehmen würde, und davon der Eintrag mit "bluetooth" im Namen.
    """

    from jnius import autoclass

    PackageManager = autoclass("android.content.pm.PackageManager")

    verwalter = activity.getPackageManager()

    for eintrag in verwalter.queryIntentActivities(absicht, 0).toArray():

        name = eintrag.activityInfo.packageName

        if "bluetooth" in name.lower():
            return name

    return None


def _rechner_bluetooth(pfad):
    """Auf Windows gibt es keinen Weg, eine Datei aus dem Programm
    heraus per Bluetooth zu verschicken.

    Windows hat den Assistenten, aber er nimmt keine Datei als
    Argument entgegen - der Weg führt über das Kontextmenü. Statt
    etwas vorzutäuschen, führt der Knopf genau dorthin: Ordner auf,
    Datei ausgewählt.
    """

    erfolg, _meldung = _rechner_teilen(pfad)

    if not erfolg:
        return False, "Ordner ließ sich nicht öffnen."

    return True, (
        f"{pfad.name} ist ausgewählt - Rechtsklick, \"Senden an\", "
        f"\"Bluetooth-Gerät\"."
    )


def _in_downloads_kopieren(pfad, activity):
    """Legt die Datei unter Download/KiG POS ab und liefert ihre Uri.

    Über den MediaStore, nicht über einen Dateipfad: Seit Android 10
    darf eine App nicht mehr einfach in fremde Ordner schreiben, wohl
    aber über den MediaStore eigene Dateien dort ablegen - ohne jede
    zusätzliche Berechtigung.
    """

    from jnius import autoclass

    ContentValues = autoclass("android.content.ContentValues")
    MediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
    Downloads = autoclass("android.provider.MediaStore$Downloads")

    werte = ContentValues()
    werte.put(MediaColumns.DISPLAY_NAME, pfad.name)
    werte.put(MediaColumns.MIME_TYPE, dateityp(pfad))
    werte.put(MediaColumns.RELATIVE_PATH, OEFFENTLICHER_ORDNER)

    aufloeser = activity.getContentResolver()

    uri = aufloeser.insert(Downloads.EXTERNAL_CONTENT_URI, werte)

    if uri is None:
        return None

    strom = aufloeser.openOutputStream(uri)

    try:
        # In Häppchen statt am Stück: Eine Datenbankkopie kann ein
        # paar Megabyte haben, und der Umweg über Java-Bytes ist
        # teuer.
        with open(pfad, "rb") as quelle:

            while True:

                brocken = quelle.read(64 * 1024)

                if not brocken:
                    break

                strom.write(brocken)

    finally:
        strom.close()

    return uri


# =========================================================
# Rechner
# =========================================================

def _rechner_teilen(pfad):
    """Öffnet den Ordner und wählt die Datei aus."""

    try:
        subprocess.Popen(
            ["explorer", "/select,", str(pfad)],
            shell=False,
        )

        return True, (
            f"Ordner geöffnet, {pfad.name} ist ausgewählt - von dort "
            f"lässt sie sich in eine E-Mail ziehen."
        )

    except Exception as fehler:
        return False, f"Ordner ließ sich nicht öffnen: {fehler}"
