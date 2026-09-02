"""
====================================================================
KiG POS
====================================================================

Datei:
config.py

Beschreibung:
Zentrale Konfigurationsdatei der Anwendung.

Diese Datei enthält ausschließlich Konstanten und Einstellungen,
die von der gesamten Anwendung verwendet werden.

Inhalt:
- Projektinformationen
- Versionsverwaltung
- Fensterkonfiguration
- Ordnerpfade
- Dateipfade
- Mengeneinheiten und Formate

Farben, Schriftgrößen und Abmessungen stehen ausschließlich in
theme.py.

WICHTIG:
Diese Datei enthält bewusst KEINE Programm-Logik.

--------------------------------------------------------------------

Projekt:
KiG POS

Verein:
KiG e.V. - est. 1996

Autor:
Oleg Kuhn & OpenAI ChatGPT

Version:
0.1.0

Build:
0001

Änderungsverlauf:

0.1.0
- Datei erstellt
- Grundkonfiguration definiert

====================================================================
"""

import sys

from pathlib import Path

# ==========================================================
# Projektinformationen
# ==========================================================

APP_NAME = "KiG POS"

VEREIN = "KiG e.V. - est. 1996"

VERSION = "0.1.0"


def _buildnummer():
    """Die Buildnummer - sie steigt mit jeder Revision von selbst.

    Von Hand gepflegt blieb sie jahrelang auf "0001" stehen. Gezaehlt
    wird deshalb, was das Projekt an Commits hat:

        1. buildnummer.txt neben dieser Datei. Die schreiben die
           Bauablaeufe (Windows wie Android), denn im fertigen Paket
           gibt es kein Git mehr.
        2. Auf dem Entwicklungsrechner sonst Git selbst.
        3. Bleibt beides aus: 0000 - eine Nummer, die es so nie
           gibt und die damit selbst die Auskunft ist.
    """

    orte = [Path(__file__).resolve().parent]

    # Im PyInstaller-Paket liegen die mitgelieferten Dateien im
    # Entpackordner, nicht neben dem Quelltext.
    entpackt = getattr(sys, "_MEIPASS", None)

    if entpackt:
        orte.insert(0, Path(entpackt))

    for ordner in orte:

        datei = ordner / "buildnummer.txt"

        try:
            if datei.exists():
                gelesen = datei.read_text(encoding="utf-8").strip()
                if gelesen.isdigit():
                    return f"{int(gelesen):04d}"
        except OSError:
            pass

    try:
        import subprocess

        ergebnis = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(Path(__file__).resolve().parent),
            capture_output=True, text=True, timeout=5,
        )

        if ergebnis.returncode == 0:
            gezaehlt = ergebnis.stdout.strip()
            if gezaehlt.isdigit():
                return f"{int(gezaehlt):04d}"

    except (OSError, ValueError, subprocess.SubprocessError):
        pass

    return "0000"


BUILD = _buildnummer()

# ==========================================================
# Fenster
# ==========================================================

"""
Fenstermodi

window      = normales Fenster

fullscreen  = Vollbild

borderless  = randloses Fenster
"""

WINDOW_MODE = "fullscreen"

WINDOW_WIDTH = 1200

WINDOW_HEIGHT = 700

MIN_WIDTH = 1200

MIN_HEIGHT = 700

"""
Hochformat

Maße für die hochkant aufgebaute Oberfläche (siehe
theme.set_orientation).

Einheit ist - wie bei WINDOW_WIDTH/WINDOW_HEIGHT oben - die
Fenstergröße, die an Kivy übergeben wird. Bei einer Windows-Skalierung
von z. B. 125 % ist das Fenster auf dem Bildschirm entsprechend größer
(660 -> 825 echte Bildpunkte).

Die tatsächliche Höhe wird beim Start zusätzlich an den Bildschirm
angepasst, damit die Fußzeile mit "Programm beenden" nicht unter dem
Bildschirmrand verschwindet (siehe KiG_POS.apply_window_orientation).
"""

PORTRAIT_WINDOW_WIDTH = 660

PORTRAIT_WINDOW_HEIGHT = 900

PORTRAIT_MIN_WIDTH = 560

PORTRAIT_MIN_HEIGHT = 640

# Reserve für Taskleiste und Fenstertitel, in echten Bildpunkten.
PORTRAIT_SCREEN_MARGIN = 90

# ==========================================================
# Splashscreen
# ==========================================================

SPLASH_DURATION = 2.0

# ==========================================================
# Ordnerstruktur
# ==========================================================
#
# Als fertiges Programm (.exe) gibt es zwei verschiedene Orte:
#
#     BASE_DIR      der Ordner NEBEN der exe - dorthin wird
#                   geschrieben (Datenbank, Ausgaben, Protokoll)
#     RESOURCE_DIR  die mitgelieferten Dateien im Programmpaket -
#                   von dort wird nur gelesen
#
# PyInstaller packt die Bilder und Schriften in einen eigenen Ordner
# (sys._MEIPASS), der bei jedem Start neu entsteht. Wer dort etwas
# ablegt, findet es beim nächsten Start nicht wieder - deshalb die
# Trennung. Im Projektordner sind beide gleich.

IST_PROGRAMMPAKET = getattr(sys, "frozen", False)

if IST_PROGRAMMPAKET:
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR

ASSETS_DIR = RESOURCE_DIR / "assets"

DATABASE_DIR = BASE_DIR / "database"

EXPORT_DIR = BASE_DIR / "exports"

LOG_DIR = BASE_DIR / "logs"

# ==========================================================
# Unterordner
# ==========================================================

ICON_DIR = ASSETS_DIR / "icons"

USERGUIDE_IMAGE_DIR = ASSETS_DIR / "userguide"

EXPORT_EXCEL_DIR = EXPORT_DIR / "excel"

EXPORT_PDF_DIR = EXPORT_DIR / "pdf"

EXPORT_CSV_DIR = EXPORT_DIR / "csv"

# Übergabedateien zwischen den Geräten (siehe uebergabe.py). Eigener
# Ordner, damit sie nicht zwischen Excel-Listen untergehen - man sucht
# sie gezielt, wenn die Kasse weitergereicht wird.
EXPORT_UEBERGABE_DIR = EXPORT_DIR / "uebergabe"

# ==========================================================
# Dateien
# ==========================================================

DATABASE = DATABASE_DIR / "kig.db"

LOGO = ASSETS_DIR / "kig_logo.png"


# ==========================================================
# Logo
# ==========================================================

LOGO_PATH = ASSETS_DIR / "kig_logo.png"

# Helle Logovariante für dunklen Modus (gleiche Zeichnung, invertiert,
# Transparenz unverändert) - das Original ist schwarze Linienkunst und
# auf dunklem Grund sonst kaum sichtbar.
LOGO_PATH_DARK = ASSETS_DIR / "kig_logo_dark.png"

SPLASH_LOGO_SIZE = 600

# ==========================================================
# Icons
# ==========================================================

ICON_CASH = ICON_DIR / "cash.png"

ICON_STATISTICS = ICON_DIR / "statistics.png"

ICON_EVENTS = ICON_DIR / "events.png"

ICON_CASHBOOK = ICON_DIR / "cashbook.png"

ICON_CHECKLIST = ICON_DIR / "checklist.png"

ICON_SHIFTPLAN = ICON_DIR / "time-management.png"

ICON_ARTICLES = ICON_DIR / "articles.png"

ICON_USE = ICON_DIR / "use.png"

ICON_SETTINGS = ICON_DIR / "settings.png"

# Programmsymbol, erzeugt aus dem Vereinslogo
# (siehe werkzeuge/symbol_erzeugen.py). Zwei Dateien, weil zwei
# verschiedene Stellen es anzeigen:
#
#     .ico   Windows selbst: die exe, Verknüpfungen, Explorer
#     .png   Kivy: Fenster und Taskleiste des laufenden Programms
#
# Kivy bekommt eine .ico-Datei nicht geladen und behält dann sein
# eigenes Zeichen - nachgemessen am laufenden Fenster.
ICON_APP = ICON_DIR / "kig_pos.ico"

ICON_APP_FENSTER = ICON_DIR / "kig_pos.png"

# ==========================================================
# Hinweis zu Farben, Größen und Schriftgrößen
# ==========================================================
#
# Die standen früher auch hier - und damit ein zweites Mal neben
# theme.py, das sie tatsächlich verwendet. Zwei Quellen für
# dieselbe Zahl sind eine Fehlerquelle; maßgeblich ist theme.py.

# ==========================================================
# Datenbank
# ==========================================================

DATABASE_VERSION = 1

# ==========================================================
# Mengeneinheiten
# ==========================================================

# Bestand wird für diese Einheit immer intern in ml geführt (siehe
# units.stock_dimension_unit() und products_screen.py) - beim
# Wareneingang wird nach der Flaschengröße gefragt und automatisch
# umgerechnet, da eine Flasche keinen festen ml-Wert hat.
BOTTLE_UNIT = "Flasche"

ARTICLE_UNITS = ("Stück", "ml", "g", BOTTLE_UNIT)

# ==========================================================
# Währung
# ==========================================================

CURRENCY = "€"

DECIMAL_PLACES = 2

# ==========================================================
# Debug
# ==========================================================

DEBUG = True

# ==========================================================
# Datumsformate
# ==========================================================

DATE_FORMAT = "%d.%m.%Y"

TIME_FORMAT = "%H:%M:%S"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==========================================================
# Sprache
# ==========================================================

LANGUAGE = "de"

# ==========================================================
# Screennamen
# ==========================================================

SCREEN_HOME = "home"
SCREEN_CASH = "cash"
SCREEN_EVENTS = "events"
SCREEN_CASHBOOK = "cashbook"
SCREEN_CHECKLIST = "checklist"
SCREEN_SHIFTPLAN = "shiftplan"
SCREEN_PRODUCTS = "products"
SCREEN_STATISTICS = "statistics"
SCREEN_USE = "use"
SCREEN_SETTINGS = "settings"