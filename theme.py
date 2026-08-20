"""
=========================================================
KiG POS
=========================================================

Datei:
    theme.py

Beschreibung:
    Zentrale Designeinstellungen für KiG POS.

    Alle Farben, Rundungen, Abstände und
    Animationsgeschwindigkeiten werden ausschließlich
    über diese Datei verwaltet.

    Hell-/Dunkelmodus:
        Alle FARB-Konstanten existieren zweimal (_LIGHT_COLORS /
        _DARK_COLORS). set_mode("light"|"dark") schreibt den
        gewählten Satz als Modulattribute (theme.CARD, theme.
        BACKGROUND, ...) - alle Widgets lesen diese Attribute wie
        gewohnt zur Konstruktionszeit. Ein Moduswechsel wird daher
        erst sichtbar, wenn die Oberfläche neu aufgebaut wird (siehe
        KiGPOS.apply_theme_mode() in KiG_POS.py).

        Alle übrigen Konstanten (Radien, Abstände, Schriftgrößen,
        Größen, Dauern) sind modusunabhängig und bleiben unverändert.

Corporate Design
---------------------------------------------------------

Primärfarbe:
    RAL 2004 Reinorange

Sekundärfarben:
    Weiß
    Dunkelgrau

Windows ✔
Android ✔

Version : 0.3.0
Build   : 0003
=========================================================
"""

# =========================================================
# FARBPALETTEN (hell / dunkel)
# =========================================================

_LIGHT_COLORS = {

    # Hintergründe
    "BACKGROUND": (0.95, 0.95, 0.95, 1),
    "SURFACE": (0.97, 0.97, 0.97, 1.0),
    "CARD": (1.0, 1.0, 1.0, 1.0),
    "CONTENT_BACKGROUND": (0.985, 0.985, 0.985, 1),
    "CARD_BORDER": (0.84, 0.84, 0.84, 1),

    # Text
    "TEXT_PRIMARY": (0.12, 0.12, 0.12, 1.0),
    "TEXT_SECONDARY": (0.42, 0.42, 0.42, 1.0),
    "TEXT_LIGHT": (0.70, 0.70, 0.70, 1.0),
    "TEXT_WHITE": (1.0, 1.0, 1.0, 1.0),

    # KiG Vereinsfarben (RAL 2004 Reinorange) - in beiden Modi
    # identisch, da Teil der Markenidentität.
    "PRIMARY_ORANGE": (244 / 255, 70 / 255, 17 / 255, 1),
    "PRIMARY_ORANGE_LIGHT": (1.00, 0.42, 0.18, 1),
    "PRIMARY_ORANGE_DARK": (0.82, 0.22, 0.05, 1),

    # Statusfarben
    "SUCCESS": (0.26, 0.67, 0.30, 1),
    "WARNING": (1.00, 0.60, 0.00, 1),
    "ERROR": (0.83, 0.18, 0.18, 1),
    "INFO": (0.12, 0.47, 0.82, 1),

    # Progressbar
    "PROGRESS_BACKGROUND": (0.90, 0.90, 0.90, 1),

    # Buttons
    "BUTTON_DISABLED": (0.82, 0.82, 0.82, 1),

    # Rahmen / Schatten
    "BORDER_COLOR": (0.88, 0.88, 0.88, 1),
    "SHADOW_COLOR": (0, 0, 0, 0.10),

    # Header
    "HEADER_BACKGROUND": (0.96, 0.96, 0.96, 1),
    "HEADER_SEPARATOR": (0.82, 0.82, 0.82, 1),

    # Warenkorb
    "CART_BACKGROUND": (1.00, 0.975, 0.965, 1),
    "CART_FOOTER_BACKGROUND": (0.985, 0.955, 0.940, 1),
    "STORNO_ROW": (1.00, 0.93, 0.93, 1),
    "CART_SEPARATOR": (0.93, 0.88, 0.84, 1),

    # Artikelkachel ohne Bestand: leicht grau abgesetzt. Verkaufen
    # lässt sie sich weiter (an der Bar wird nachgeschenkt, bevor
    # jemand bucht) - sie soll nur auffallen.
    "TILE_SOLD_OUT": (0.90, 0.90, 0.90, 1),

    # Buttonpress
    "TILE_PRESS_COLOR": (1.00, 0.82, 0.68, 1),

}

_DARK_COLORS = {

    # Hintergründe
    "BACKGROUND": (0.09, 0.09, 0.10, 1),
    "SURFACE": (0.15, 0.15, 0.16, 1.0),
    "CARD": (0.17, 0.17, 0.18, 1.0),
    "CONTENT_BACKGROUND": (0.10, 0.10, 0.11, 1),
    "CARD_BORDER": (0.28, 0.28, 0.30, 1),

    # Text
    "TEXT_PRIMARY": (0.93, 0.93, 0.94, 1.0),
    "TEXT_SECONDARY": (0.66, 0.66, 0.69, 1.0),
    "TEXT_LIGHT": (0.50, 0.50, 0.53, 1.0),
    "TEXT_WHITE": (1.0, 1.0, 1.0, 1.0),

    # KiG Vereinsfarben - identisch zu hell (Markenidentität).
    "PRIMARY_ORANGE": (244 / 255, 70 / 255, 17 / 255, 1),
    "PRIMARY_ORANGE_LIGHT": (1.00, 0.42, 0.18, 1),
    "PRIMARY_ORANGE_DARK": (0.82, 0.22, 0.05, 1),

    # Statusfarben, für ausreichend Kontrast auf dunklem Grund
    # etwas angehoben.
    "SUCCESS": (0.33, 0.75, 0.40, 1),
    "WARNING": (1.00, 0.66, 0.20, 1),
    "ERROR": (0.92, 0.35, 0.35, 1),
    "INFO": (0.35, 0.62, 0.95, 1),

    # Progressbar
    "PROGRESS_BACKGROUND": (0.26, 0.26, 0.28, 1),

    # Buttons
    "BUTTON_DISABLED": (0.30, 0.30, 0.32, 1),

    # Rahmen / Schatten
    "BORDER_COLOR": (0.30, 0.30, 0.32, 1),
    "SHADOW_COLOR": (0, 0, 0, 0.35),

    # Header/Footer - bewusst deutlich heller als BACKGROUND/CARD,
    # damit sich die "Chrome"-Leisten klar vom Inhalt abheben und
    # das (dunkle Linienkunst-)Vereinslogo darauf gut lesbar bleibt.
    "HEADER_BACKGROUND": (0.26, 0.26, 0.28, 1),
    "HEADER_SEPARATOR": (0.38, 0.38, 0.41, 1),

    # Warenkorb (warmer Unterton bleibt erhalten, nur abgedunkelt)
    "CART_BACKGROUND": (0.15, 0.12, 0.11, 1),
    "CART_FOOTER_BACKGROUND": (0.18, 0.14, 0.12, 1),
    "STORNO_ROW": (0.26, 0.13, 0.13, 1),
    "CART_SEPARATOR": (0.32, 0.25, 0.21, 1),

    # Artikelkachel ohne Bestand (siehe hellen Modus)
    "TILE_SOLD_OUT": (0.13, 0.13, 0.14, 1),

    # Buttonpress
    "TILE_PRESS_COLOR": (0.60, 0.32, 0.20, 1),

}

_MODES = {
    "light": _LIGHT_COLORS,
    "dark": _DARK_COLORS,
}

CURRENT_MODE = "light"


def set_mode(mode):
    """Wendet die Farbpalette des gewünschten Modus an ("light"
    oder "dark"). Unbekannte Werte werden ignoriert.

    WICHTIG: Bereits konstruierte Widgets haben ihre Farben schon
    in ihre canvas-Instructions übernommen und ändern sich hier
    NICHT automatisch mit. Für eine sichtbare Umschaltung muss die
    Oberfläche nach dem Aufruf neu aufgebaut werden (siehe
    KiGPOS.apply_theme_mode()).
    """

    global CURRENT_MODE
    global PROGRESS_FOREGROUND, BUTTON_PRIMARY, BUTTON_PRIMARY_HOVER
    global BUTTON_PRIMARY_PRESSED, BUTTON_TEXT, CARD_BACKGROUND

    palette = _MODES.get(mode)

    if palette is None:
        return

    globals().update(palette)

    CURRENT_MODE = mode

    # Konstanten, die sich aus anderen Farbkonstanten ableiten -
    # nach jedem Wechsel neu berechnen, damit sie zum neuen Modus
    # passen.
    PROGRESS_FOREGROUND = PRIMARY_ORANGE

    BUTTON_PRIMARY = PRIMARY_ORANGE
    BUTTON_PRIMARY_HOVER = PRIMARY_ORANGE_LIGHT
    BUTTON_PRIMARY_PRESSED = PRIMARY_ORANGE_DARK
    BUTTON_TEXT = TEXT_WHITE

    CARD_BACKGROUND = CARD


def get_mode():

    return CURRENT_MODE


# Startzustand: heller Modus (wird von KiGPOS.build() anhand der
# gespeicherten Einstellung ggf. sofort überschrieben, bevor die
# erste Oberfläche entsteht).
set_mode("light")


# =========================================================
# BILDSCHIRMAUSRICHTUNG (Quer- / Hochformat)
# =========================================================
#
# Querformat ("landscape"): breites Fenster, zusammengehörige Bereiche
#     stehen NEBENeinander (Artikel | Warenkorb, Kategorien | Liste).
#
# Hochformat ("portrait"): schmales, hohes Fenster - dieselben Bereiche
#     stehen UNTEReinander. Gedacht für hochkant montierte Bildschirme
#     und Tablets an der Bar.
#
# Hier steht ausschließlich, welche Ausrichtung gerade gilt; WIE sich
# ein Screen jeweils anordnet, entscheidet er selbst beim Aufbau
# (siehe screens/*.py und widgets/common/slide_panel.py). Die Werte
# stehen dort bewusst nebeneinander im Code - so ist an einer Stelle
# ablesbar, was sich zwischen beiden Ausrichtungen unterscheidet.
#
# Wie beim Farbmodus lesen die Widgets diesen Zustand zur
# Konstruktionszeit. Ein Wechsel wird deshalb erst nach einem
# Neuaufbau der Oberfläche sichtbar (siehe KiGPOS.apply_orientation()).

ORIENTATION_LANDSCAPE = "landscape"

ORIENTATION_PORTRAIT = "portrait"

CURRENT_ORIENTATION = ORIENTATION_LANDSCAPE


def set_orientation(orientation):
    """Legt die Bildschirmausrichtung fest ("landscape" oder
    "portrait"). Unbekannte Werte werden ignoriert.
    """

    global CURRENT_ORIENTATION

    if orientation not in (ORIENTATION_LANDSCAPE, ORIENTATION_PORTRAIT):
        return

    CURRENT_ORIENTATION = orientation


def get_orientation():

    return CURRENT_ORIENTATION


def is_portrait():
    """True, wenn die Oberfläche im Hochformat aufgebaut werden soll."""

    return CURRENT_ORIENTATION == ORIENTATION_PORTRAIT


# =========================================================
# RADIUS
# =========================================================

CARD_RADIUS = 18

BUTTON_RADIUS = 14

PROGRESS_RADIUS = 10

INPUT_RADIUS = 10

DIALOG_RADIUS = 18

# =========================================================
# RAHMEN
# =========================================================

BORDER_WIDTH = 1.5

# =========================================================
# ABSTÄNDE
# =========================================================
#
# Ein einziges Raster für die gesamte Anwendung, damit Kacheln,
# Karten und Beschriftungen auf allen Screens dieselben Abstände
# haben. Alle Werte sind Vielfache von 4 und werden an der
# Verwendungsstelle in dp() gewickelt (z. B. padding=dp(theme.CARD_PADDING)),
# genau wie die übrigen Maße dieser Datei.
#
# Vier Stufen, mit klarer Bedeutung:
#
#   SPACE_XS (4)  eng Zusammengehöriges innerhalb eines Elements
#                 (z. B. Name + Kategorie einer Listenzeile)
#   SPACE_S  (8)  gleichartige Elemente einer Gruppe
#                 (Listenzeilen, Buttons einer Reihe, Tasten eines Feldes)
#   SPACE_M  (12) Abschnitte innerhalb einer Karte
#                 (Formularfelder untereinander, Kacheln im Raster)
#   SPACE_L  (16) zwischen Karten/Panels und zum Screen-Rand hin
#
# Daraus ergibt sich die sichtbare Hierarchie: je weiter zwei Dinge
# inhaltlich auseinanderliegen, desto größer ihr Abstand.

SPACE_XS = 4

SPACE_S = 8

SPACE_M = 12

SPACE_L = 16

SPACE_XL = 24

# ---------------------------------------------------------
# Benannte Rollen (bevorzugt verwenden - sie sagen, WOFÜR der
# Abstand steht, nicht nur wie groß er ist)
# ---------------------------------------------------------

# Rand eines Screens und Abstand zwischen seinen Panels
SCREEN_PADDING = SPACE_L
SCREEN_SPACING = SPACE_L

# Innenabstand einer Karte / eines Panels / eines Dialogs und
# Abstand zwischen dessen Abschnitten
CARD_PADDING = SPACE_L
CARD_SPACING = SPACE_M

# Elemente nebeneinander in einer Zeile (Buttons, Eingabefelder)
# sowie aufeinanderfolgende Zeilen einer Liste
ROW_SPACING = SPACE_S

# Kacheln im Raster und deren Innenabstand
TILE_SPACING = SPACE_M
TILE_PADDING = SPACE_S

# Eng zusammengehörige Beschriftungen (Titel + Untertitel)
LABEL_SPACING = SPACE_XS

# =========================================================
# ANIMATIONEN
# =========================================================

FADE_DURATION = 0.30

BUTTON_ANIMATION = 0.12

SPLASH_FADE = 0.80

WINDOW_ANIMATION = 0.25

# =========================================================
# SCHRIFTGRÖSSEN
# =========================================================

FONT_TITLE = 36

FONT_SUBTITLE = 20

FONT_NORMAL = 18

FONT_SMALL = 15

FONT_STATUS = 16

FONT_VERSION = 13

# =========================================================
# SPLASH SCREEN
# =========================================================

SPLASH_LOGO_WIDTH = 600

SPLASH_LOGO_CENTER_Y = 0.70

SPLASH_TITLE_CENTER_Y = 0.37

SPLASH_SUBTITLE_CENTER_Y = 0.325

SPLASH_SEPARATOR_CENTER_Y = 0.255

SPLASH_SLOGAN_CENTER_Y = 0.215

SPLASH_PROGRESS_CENTER_Y = 0.145

SPLASH_STATUS_CENTER_Y = 0.095

SPLASH_VERSION_CENTER_Y = 0.045

# ----------------------------------------------------
# Header
# ----------------------------------------------------

HEADER_HEIGHT = 90

# ----------------------------------------------------
# Footer
# ----------------------------------------------------

FOOTER_HEIGHT = 60


# ----------------------------------------------------
# Startseite
# ----------------------------------------------------
#
# Die Kachelgröße steht in widgets/kig_tile.py (KiGTile.WIDTH /
# HEIGHT) - dort, wo die Kachel sie auch verwendet. Hier stand sie
# früher ein zweites Mal, ohne dass jemand sie las.


# ----------------------------------------------------
# Kasse
# ----------------------------------------------------

CATEGORY_TILE_WIDTH = 160
CATEGORY_TILE_HEIGHT = 60

# Flach gehalten: Auf einer Artikelkachel stehen nur Name, Bestand
# und Preis. Höhere Kacheln kosten nur Reihen, ohne mehr zu zeigen.
#
# Die Breite ist so bemessen, dass neben der Kategorienliste drei
# Kacheln nebeneinander passen - auch im kleinstmöglichen Fenster
# (1500 x 875 Bildpunkte): Dort bleiben dem Raster 539 dp, drei
# Kacheln brauchen 3 x 165 + 2 x 12 = 519 dp.
ARTICLE_TILE_WIDTH = 165
ARTICLE_TILE_HEIGHT = 120

# Hochformat: gleiche Breite, aber flacher - dort teilt sich der
# Artikelbereich die Höhe mit dem Warenkorb darunter.
PORTRAIT_ARTICLE_TILE_WIDTH = 165
PORTRAIT_ARTICLE_TILE_HEIGHT = 100

# ----------------------------------------------------
# Warenkorb
# ----------------------------------------------------

CART_ACTION_TILE_HEIGHT = CATEGORY_TILE_HEIGHT

# -------------------------------------------------
# Kassenscreen
# -------------------------------------------------

CART_PANEL_WIDTH = 380

# -------------------------------------------------
# Buttonpress
# -------------------------------------------------

TILE_PRESS_DURATION = 0.08

# ==========================================================
# Numpad
# ==========================================================

NUMPAD_BUTTON_SIZE = 90
NUMPAD_PANEL_WIDTH = 350
NUMPAD_RADIUS = 8
