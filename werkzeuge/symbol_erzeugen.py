"""
=========================================================
KiG POS
=========================================================

Datei:
    werkzeuge/symbol_erzeugen.py

Beschreibung:
    Erzeugt das Programmsymbol assets/icons/kig_pos.ico
    aus assets/kig_logo.png.

    Das Logo ist doppelt so breit wie hoch. In ein Quadrat
    gezwängt bleibt davon in der Taskleiste ein grauer
    Streifen übrig - lesbar ist das nicht mehr.

    Deshalb enthält die .ico-Datei zwei Zuschnitte:

        gross (256, 128, 64)   das ganze Logo
        klein (48, 32, 16)     nur der Schriftzug "KiG"

    Windows sucht sich je nach Anzeigegröße das passende
    Bild heraus. So bleibt in der Taskleiste erkennbar,
    was man vor sich hat, und in der Dateiübersicht steht
    trotzdem das vollständige Logo.

Aufruf:
    .venv\\Scripts\\python.exe werkzeuge\\symbol_erzeugen.py

Version:
    1.0.0
=========================================================
"""

import sys
from pathlib import Path

from PIL import Image

PROJEKT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJEKT))

QUELLE = PROJEKT / "assets" / "kig_logo.png"
ZIEL = PROJEKT / "assets" / "icons" / "kig_pos.ico"

# Anteil der Logobreite, in dem der Schriftzug "KiG" steht. Gemessen am
# vorhandenen Logo: Die Krone links und rechts (Dartpfeile, Billardqueues)
# ist bei 16 Bildpunkten ohnehin nur noch Rauschen.
KIG_LINKS = 0.28
KIG_RECHTS = 0.72
KIG_UNTEN = 0.52

GROSSE_GROESSEN = (256, 128, 64)
KLEINE_GROESSEN = (48, 32, 16)


def zuschneiden(bild):
    """Schneidet den durchsichtigen Rand ab."""

    rand = bild.getbbox()

    return bild.crop(rand) if rand else bild


def ins_quadrat(bild, kante, rand_anteil=0.06):
    """Legt ein Bild mittig auf eine durchsichtige quadratische Fläche."""

    platz = int(kante * (1 - 2 * rand_anteil))

    breite, hoehe = bild.size
    faktor = min(platz / breite, platz / hoehe)

    verkleinert = bild.resize(
        (max(1, round(breite * faktor)), max(1, round(hoehe * faktor))),
        Image.LANCZOS,
    )

    flaeche = Image.new("RGBA", (kante, kante), (255, 255, 255, 0))
    flaeche.paste(
        verkleinert,
        (
            (kante - verkleinert.width) // 2,
            (kante - verkleinert.height) // 2,
        ),
        verkleinert,
    )

    return flaeche


def main():

    logo = zuschneiden(Image.open(QUELLE).convert("RGBA"))

    breite, hoehe = logo.size

    schriftzug = zuschneiden(logo.crop((
        int(breite * KIG_LINKS),
        0,
        int(breite * KIG_RECHTS),
        int(hoehe * KIG_UNTEN),
    )))

    bilder = [ins_quadrat(logo, kante) for kante in GROSSE_GROESSEN]
    bilder += [ins_quadrat(schriftzug, kante) for kante in KLEINE_GROESSEN]

    ZIEL.parent.mkdir(parents=True, exist_ok=True)

    # Pillow schreibt alle uebergebenen Groessen in eine Datei; das
    # erste Bild bestimmt die Aufloesung der Vorschau.
    bilder[0].save(
        ZIEL,
        format="ICO",
        sizes=[(bild.width, bild.height) for bild in bilder],
        append_images=bilder[1:],
    )

    print(f"{ZIEL.relative_to(PROJEKT)} erzeugt "
          f"({', '.join(str(bild.width) for bild in bilder)})")


if __name__ == "__main__":
    main()
