"""
=========================================================
KiG POS
=========================================================

Datei:
    storage.py

Beschreibung:
    Speicherorte der Anwendung - je nach Plattform.

    Auf dem Windows-Rechner liegt alles im Projektordner
    (siehe config.py). Auf Android ist dieser Ordner Teil der
    installierten App: dort lässt sich zwar schreiben, aber niemand
    käme je an die Dateien heran. Deshalb wird dort getrennt:

        • Datenbank, Sicherungen und Protokoll in den PRIVATEN
          App-Ordner. Er wird beim Deinstallieren mitgelöscht - genau
          richtig für Daten, die nur die App selbst braucht.

        • Ausgaben (PDF, Excel, CSV) in den app-eigenen Ordner auf dem
          gemeinsamen Speicher:

              Android/data/<paket>/files/exports/...

          Den erreicht man mit jedem Dateimanager und über das
          USB-Kabel, ganz ohne zusätzliche Berechtigungen.

Version:
    1.0.0
=========================================================
"""

from pathlib import Path

from kivy.app import App
from kivy.utils import platform

import config


IS_ANDROID = platform == "android"


# =========================================================
# Private Daten (Datenbank, Sicherungen, Protokoll)
# =========================================================

def data_dir() -> Path:
    """Ordner für die Daten der Anwendung.

    Läuft eine Anwendung, gilt deren user_data_dir - unter Windows
    also AppData\\Roaming\\<name>, auf Android der private App-Ordner.
    Ohne laufende Anwendung (z. B. in einem Skript) bleibt es beim
    Projektordner aus config.py.
    """

    app = App.get_running_app()

    if app is not None:
        ordner = Path(app.user_data_dir)
    else:
        ordner = config.DATABASE_DIR

    ordner.mkdir(parents=True, exist_ok=True)

    return ordner


def log_dir() -> Path:
    """Ordner für Protokolldateien."""

    if IS_ANDROID:
        ordner = data_dir() / "logs"
    else:
        ordner = config.LOG_DIR

    ordner.mkdir(parents=True, exist_ok=True)

    return ordner


# =========================================================
# Ausgaben (PDF, Excel, CSV)
# =========================================================

def export_dir(unterordner: str) -> Path:
    """Ordner für eine Ausgabe, die der Nutzer wiederfinden soll.

    unterordner: "pdf", "excel" oder "csv".
    """

    if IS_ANDROID:
        ordner = _android_export_base() / unterordner
    else:
        ordner = _windows_export_dir(unterordner)

    ordner.mkdir(parents=True, exist_ok=True)

    return ordner


def _windows_export_dir(unterordner: str) -> Path:
    """Die in config.py festgelegten Ausgabeordner.

    Bewusst erst beim Aufruf nachgeschlagen und nicht in einer Tabelle
    festgehalten: So bleiben die Konstanten aus config.py die
    maßgebliche Stelle, auch wenn sie zur Laufzeit umgebogen werden
    (Tests lenken die Ausgabe auf diesem Weg in einen eigenen Ordner).
    """

    if unterordner == "pdf":
        return config.EXPORT_PDF_DIR

    if unterordner == "excel":
        return config.EXPORT_EXCEL_DIR

    if unterordner == "csv":
        return config.EXPORT_CSV_DIR

    return config.EXPORT_DIR / unterordner


def _android_export_base() -> Path:
    """Ausgabeordner auf dem gemeinsamen Speicher.

    getExternalFilesDir() gehört zur App und braucht deshalb keine
    Berechtigung, ist aber trotzdem über Dateimanager und USB
    erreichbar. Klappt der Zugriff nicht (kein Speicher eingehängt),
    landen die Ausgaben ersatzweise im privaten Ordner - lieber dort
    als gar nicht.
    """

    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        ordner = activity.getExternalFilesDir(None)

        if ordner is not None:
            return Path(ordner.getAbsolutePath()) / "exports"

    except Exception:
        pass

    return data_dir() / "exports"
