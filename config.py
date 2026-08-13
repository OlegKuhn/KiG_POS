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
- Farben
- Schriftgrößen
- Größen
- Ordnerpfade
- Dateipfade
- Splashscreen

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

from pathlib import Path

# ==========================================================
# Projektinformationen
# ==========================================================

APP_NAME = "KiG POS"

VEREIN = "KiG e.V. - est. 1996"

VERSION = "0.1.0"

BUILD = "0001"

# ==========================================================
# Fenster
# ==========================================================

"""
Fenstermodi

window      = normales Fenster

fullscreen  = Vollbild

borderless  = randloses Fenster
"""

WINDOW_MODE = "window"

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

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"

DATABASE_DIR = BASE_DIR / "database"

EXPORT_DIR = BASE_DIR / "exports"

LOG_DIR = BASE_DIR / "logs"

TEST_DIR = BASE_DIR / "tests"

# ==========================================================
# Unterordner
# ==========================================================

ICON_DIR = ASSETS_DIR / "icons"

ARTICLE_IMAGE_DIR = ASSETS_DIR / "artikelbilder"

USERGUIDE_IMAGE_DIR = ASSETS_DIR / "userguide"

EXPORT_EXCEL_DIR = EXPORT_DIR / "excel"

EXPORT_PDF_DIR = EXPORT_DIR / "pdf"

EXPORT_CSV_DIR = EXPORT_DIR / "csv"

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

ICON_ARTICLES = ICON_DIR / "articles.png"

ICON_USE = ICON_DIR / "use.png"

ICON_SETTINGS = ICON_DIR / "settings.png"

# ==========================================================
# Farben
# ==========================================================

BACKGROUND = "#F5F5F5"

CARD = "#FFFFFF"

HEADER = "#202124"

TEXT = "#202124"

TEXT_LIGHT = "#FFFFFF"

PRIMARY = "#1976D2"

SECONDARY = "#607D8B"

SUCCESS = "#2E7D32"

WARNING = "#F57C00"

ERROR = "#C62828"

# Kategorien

COLOR_ALKOHOLFREI = "#1976D2"

COLOR_ALKOHOL = "#F57C00"

COLOR_COCKTAIL = "#D32F2F"

COLOR_ESSEN = "#43A047"

COLOR_SONSTIGES = "#7B1FA2"

# ==========================================================
# Größen
# ==========================================================

HEADER_HEIGHT = 100

LOGO_WIDTH = 180

LOGO_HEIGHT = 90

BUTTON_WIDTH = 220

BUTTON_HEIGHT = 110

BUTTON_RADIUS = 18

CARD_RADIUS = 18

PADDING = 12

SPACING = 10

# ==========================================================
# Schriftgrößen
# ==========================================================

FONT_TITLE = 30

FONT_SUBTITLE = 22

FONT_BUTTON = 22

FONT_NORMAL = 20

FONT_SMALL = 16

FONT_CLOCK = 22

FONT_TOTAL = 28

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
SCREEN_PRODUCTS = "products"
SCREEN_STATISTICS = "statistics"
SCREEN_USE = "use"
SCREEN_SETTINGS = "settings"