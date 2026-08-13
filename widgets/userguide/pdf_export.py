"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/userguide/pdf_export.py

Beschreibung:
    Exportiert das komplette Benutzerhandbuch als PDF.

    Die Inhalte stammen unverändert aus
    widgets/userguide/content.py - neue Themen oder Schritte
    landen also automatisch mit im Export, ohne dass hier
    etwas angepasst werden muss.

    Aufbau des PDFs:

        • Titelseite mit Vereinslogo, Version und Datum
        • Inhaltsverzeichnis
        • je Thema eine neue Seite mit allen Schritten
          (Überschrift, Text, Screenshot)
        • Seitenzahlen in der Fußzeile

Version:
    1.0.0
=========================================================
"""

from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

import config
import storage


# Die eingebauten PDF-Schriften kennen nur WinAnsi. Ein paar Zeichen
# aus der Oberfläche kommen darin nicht vor und würden sonst als
# schwarzes Kästchen erscheinen - sie werden hier durch eine
# gleichwertige Schreibweise ersetzt.
CHARACTER_REPLACEMENTS = {
    "←": "<-",     # Pfeil links (z. B. "← Zurück")
    "→": "->",
    "≈": "ca. ",   # ungefähr
    "…": "...",    # Auslassungspunkte
    "✕": "x",      # Kreuz (Löschen-Schaltfläche)
    "×": "x",      # Multiplikationszeichen
}

PAGE_MARGIN = 20 * mm

# Orange der Anwendung, hier bewusst fest verdrahtet: theme.py liefert
# je nach Farbmodus unterschiedliche Werte, das PDF soll aber immer
# gleich aussehen - unabhängig davon, ob gerade hell oder dunkel
# eingestellt ist.
BRAND_COLOR = colors.HexColor("#F4511E")
TEXT_COLOR = colors.HexColor("#202124")
MUTED_COLOR = colors.HexColor("#5F6368")


def export_userguide_pdf(topics, target_path=None):
    """Schreibt das Handbuch als PDF und liefert den Pfad zurück.

    topics: Liste wie in content.TOPICS.
    target_path: Zielpfad; ohne Angabe wird eine Datei mit Zeitstempel
    im Ordner exports/pdf angelegt.
    """

    if target_path is None:
        filename = datetime.now().strftime("benutzerhandbuch_%Y-%m-%d_%H-%M.pdf")
        target_path = storage.export_dir("pdf") / filename

    styles = _build_styles()

    document = SimpleDocTemplate(
        str(target_path),
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN + 8 * mm,
        title=f"{config.APP_NAME} - Benutzerhandbuch",
        author=config.VEREIN,
    )

    story = []
    story.extend(_title_page(styles))
    story.extend(_table_of_contents(topics, styles))

    for topic in topics:
        story.extend(_topic_section(topic, styles, document.width))

    document.build(story, onLaterPages=_draw_footer, onFirstPage=_draw_nothing)

    return target_path


# =========================================================
# Bausteine
# =========================================================

def _build_styles():

    base = getSampleStyleSheet()

    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontSize=30, leading=36,
            textColor=BRAND_COLOR, spaceAfter=6 * mm,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", parent=base["Normal"], fontSize=14, leading=20,
            textColor=MUTED_COLOR, alignment=1,
        ),
        "topic": ParagraphStyle(
            "TopicHeading", parent=base["Heading1"], fontSize=22, leading=27,
            textColor=BRAND_COLOR, spaceAfter=5 * mm,
        ),
        "step": ParagraphStyle(
            "StepHeading", parent=base["Heading2"], fontSize=13, leading=17,
            textColor=TEXT_COLOR, spaceBefore=4 * mm, spaceAfter=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], fontSize=10.5, leading=15,
            textColor=TEXT_COLOR, alignment=TA_LEFT, spaceAfter=2 * mm,
        ),
        "toc": ParagraphStyle(
            "Toc", parent=base["Normal"], fontSize=12, leading=20,
            textColor=TEXT_COLOR, leftIndent=6 * mm,
        ),
    }


def _title_page(styles):

    story = []

    logo = _logo_image(width=70 * mm)
    if logo is not None:
        story.append(Spacer(1, 35 * mm))
        story.append(logo)

    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph("Benutzerhandbuch", styles["cover_title"]))
    story.append(Paragraph(_clean(config.APP_NAME), styles["cover_subtitle"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(_clean(config.VEREIN), styles["cover_subtitle"]))
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph(
        f"Version {config.VERSION} &#183; Build {config.BUILD}",
        styles["cover_subtitle"],
    ))
    story.append(Paragraph(
        f"Stand: {datetime.now().strftime('%d.%m.%Y')}",
        styles["cover_subtitle"],
    ))
    story.append(PageBreak())

    return story


def _table_of_contents(topics, styles):

    story = [Paragraph("Inhalt", styles["topic"])]

    for number, topic in enumerate(topics, start=1):
        step_count = len(topic.get("steps") or [])
        suffix = "Schritt" if step_count == 1 else "Schritte"
        story.append(Paragraph(
            f"{number}. {_clean(topic['title'])} "
            f"<font color='#5F6368'>({step_count} {suffix})</font>",
            styles["toc"],
        ))

    story.append(PageBreak())

    return story


def _topic_section(topic, styles, available_width):

    story = [Paragraph(_clean(topic["title"]), styles["topic"])]

    steps = topic.get("steps") or []

    if not steps:
        story.append(Paragraph(
            "Für dieses Thema wird die Anleitung noch ergänzt.",
            styles["body"],
        ))
        story.append(PageBreak())
        return story

    for number, step in enumerate(steps, start=1):

        # Überschrift und der zugehörige Text sollen nie durch einen
        # Seitenumbruch getrennt werden.
        block = [
            Paragraph(f"{number}. {_clean(step['heading'])}", styles["step"]),
            Paragraph(_clean(step["text"]), styles["body"]),
        ]
        story.append(KeepTogether(block))

        image = _step_image(step, available_width)
        if image is not None:
            story.append(Spacer(1, 2 * mm))
            story.append(image)
            story.append(Spacer(1, 3 * mm))

    story.append(PageBreak())

    return story


# =========================================================
# Bilder
# =========================================================

def _logo_image(width):

    path = config.LOGO_PATH

    if not path.is_file():
        return None

    logo = _scaled_image(path, width)

    if logo is not None:
        # Auf der Titelseite steht das Logo mittig, im Fließtext
        # richten sich Screenshots dagegen links aus.
        logo.hAlign = "CENTER"

    return logo


def _step_image(step, available_width):

    relative = step.get("image")

    if not relative:
        return None

    path = config.USERGUIDE_IMAGE_DIR / relative

    if not path.is_file():
        # Fehlender Screenshot darf den Export nicht abbrechen - der
        # Text des Schritts steht ja trotzdem im PDF.
        return None

    return _scaled_image(path, available_width)


def _scaled_image(path, width):
    """Skaliert ein Bild proportional auf die gewünschte Breite."""

    try:
        original_width, original_height = ImageReader(str(path)).getSize()
    except Exception:
        return None

    if not original_width:
        return None

    ratio = original_height / original_width

    image = Image(str(path), width=width, height=width * ratio)
    image.hAlign = "LEFT"

    return image


# =========================================================
# Fußzeile
# =========================================================

def _draw_nothing(canvas, document):
    """Die Titelseite bleibt bewusst ohne Seitenzahl."""


def _draw_footer(canvas, document):

    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED_COLOR)

    canvas.drawString(
        PAGE_MARGIN,
        PAGE_MARGIN * 0.6,
        f"{config.APP_NAME} - Benutzerhandbuch",
    )
    canvas.drawRightString(
        A4[0] - PAGE_MARGIN,
        PAGE_MARGIN * 0.6,
        f"Seite {canvas.getPageNumber()}",
    )

    canvas.restoreState()


# =========================================================
# Text
# =========================================================

def _clean(text):
    """Macht Text für reportlab sicher: Sonderzeichen ersetzen und
    XML-Zeichen maskieren (Paragraph interpretiert Markup)."""

    text = str(text)

    for original, replacement in CHARACTER_REPLACEMENTS.items():
        text = text.replace(original, replacement)

    return escape(text)
