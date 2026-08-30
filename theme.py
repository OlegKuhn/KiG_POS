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

    # Eingabefelder: Was hineingeschrieben wurde, ist fast schwarz -
    # der Platzhalter deutlich blasser, aber kraeftig genug, um ihn im
    # Halbdunkel und auf dem E-Ink-Tablet lesen zu koennen.
    "INPUT_TEXT": (0.08, 0.08, 0.08, 1.0),
    "INPUT_HINT": (0.34, 0.34, 0.34, 1.0),

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

    # Eingabefelder (siehe hellen Modus)
    "INPUT_TEXT": (0.97, 0.97, 0.98, 1.0),
    "INPUT_HINT": (0.72, 0.72, 0.75, 1.0),

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


# =========================================================
# AKZENTFARBE (normal / Demo)
# =========================================================
#
# Im Demo-Modus arbeitet die Anwendung auf einer Kopie der Datenbank
# (siehe demo.py). Damit auf einen Blick klar ist, dass gerade nichts
# Echtes passiert, wechselt die Akzentfarbe von Vereinsorange auf ein
# grelles Grün - zusammen mit dem Wort DEMO in der Kopfzeile.

_ACCENTS = {

    "normal": {
        "PRIMARY_ORANGE": (244 / 255, 70 / 255, 17 / 255, 1),
        "PRIMARY_ORANGE_LIGHT": (1.00, 0.42, 0.18, 1),
        "PRIMARY_ORANGE_DARK": (0.82, 0.22, 0.05, 1),
        "TILE_PRESS_COLOR": (1.00, 0.82, 0.68, 1),
    },

    "demo": {
        "PRIMARY_ORANGE": (0.20, 0.85, 0.10, 1),
        "PRIMARY_ORANGE_LIGHT": (0.55, 0.95, 0.35, 1),
        "PRIMARY_ORANGE_DARK": (0.12, 0.60, 0.05, 1),
        "TILE_PRESS_COLOR": (0.72, 0.98, 0.60, 1),
    },
}

CURRENT_ACCENT = "normal"


def set_accent(accent):
    """Schaltet die Akzentfarbe um ("normal" oder "demo").

    Wie beim Farbmodus gilt: Bereits gebaute Widgets behalten ihre
    Farben - die Oberfläche muss danach neu aufgebaut werden (siehe
    KiGPOS.apply_demo_mode).
    """

    global CURRENT_ACCENT

    if accent not in _ACCENTS:
        return

    CURRENT_ACCENT = accent

    _apply_accent()


def get_accent():

    return CURRENT_ACCENT


def _apply_accent():
    """Trägt die Akzentfarben ein und rechnet alles nach, was sich
    aus ihnen ableitet."""

    global PROGRESS_FOREGROUND, BUTTON_PRIMARY, BUTTON_PRIMARY_HOVER
    global BUTTON_PRIMARY_PRESSED

    globals().update(_ACCENTS[CURRENT_ACCENT])

    PROGRESS_FOREGROUND = PRIMARY_ORANGE

    BUTTON_PRIMARY = PRIMARY_ORANGE
    BUTTON_PRIMARY_HOVER = PRIMARY_ORANGE_LIGHT
    BUTTON_PRIMARY_PRESSED = PRIMARY_ORANGE_DARK


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

    # Die Palette bringt die Vereinsfarben mit; im Demo-Modus gilt
    # stattdessen der grüne Akzent.
    _apply_accent()


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
# SCHMALE BILDSCHIRME
# =========================================================
#
# Quer und hoch reichen nicht: Ein Telefon im Hochformat bekam bisher
# dieselbe Anordnung wie das 10-Zoll-Tablet im Hochformat, nur auf
# einem Drittel der Fläche. Kategorienamen brachen mitten im Wort um,
# und von neun Startkacheln waren fünf zu sehen.
#
# Deshalb eine dritte Frage neben der Ausrichtung: Ist überhaupt Platz
# nebeneinander? Sie hängt an der wirklichen Breite in dp, nicht an
# einer Geräteliste - ein schmales Fenster am Rechner ist genauso
# schmal wie ein Telefon.

# Ab hier gilt ein Bildschirm als schmal. 500 dp liegt zwischen den
# üblichen Telefonen (360-430 dp) und den kleinen Tablets (ab 600 dp).
NARROW_MAX_WIDTH = 500

CURRENT_WIDTH = None


def set_breite(breite_dp):
    """Merkt sich die kürzere Bildschirmseite in dp.

    Wird beim Start gesetzt (siehe KiGPOS.build). Bewusst die kürzere
    Seite: Sie ändert sich beim Drehen nicht, und damit bleibt ein
    Telefon auch quer ein Telefon.

    Ohne Angabe bleibt es beim Normalfall breit - ein Skript ohne
    Fenster soll nicht versehentlich die Telefonanordnung bekommen.
    """

    global CURRENT_WIDTH

    CURRENT_WIDTH = breite_dp


def is_narrow():
    """True, wenn nebeneinander kein Platz mehr ist."""

    return CURRENT_WIDTH is not None and CURRENT_WIDTH < NARROW_MAX_WIDTH


# =========================================================
# RADIUS
# =========================================================

CARD_RADIUS = 18

BUTTON_RADIUS = 14

PROGRESS_RADIUS = 10

INPUT_RADIUS = 10

# Schriftgröße in Eingabefeldern.
#
# Kivys Voreinstellung (15 sp) ist an einer Bar nicht zu gebrauchen:
# Wer im Halbdunkel einen Artikelnamen eintippt, muss lesen können,
# was dasteht - erst recht auf dem E-Ink-Tablet.
INPUT_FONT_SIZE = 19

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

# Telefon: zwei Kacheln nebeneinander. Bei 412 dp Bildschirmbreite
# bleiben innerhalb der Karte rund 364 dp - zwei mal 168 plus Abstand
# passen hinein, 165 mal zwei wären zu knapp gewesen, sobald die
# Karte einmal etwas mehr Rand bekommt.
NARROW_ARTICLE_TILE_WIDTH = 168
NARROW_ARTICLE_TILE_HEIGHT = 88

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
