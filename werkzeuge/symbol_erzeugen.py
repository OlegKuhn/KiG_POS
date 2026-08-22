"""
=========================================================
KiG POS
=========================================================

Datei:
    werkzeuge/symbol_erzeugen.py

Beschreibung:
    Erzeugt das Programmsymbol aus assets/kig_logo.png.

    Zwei Dateien, weil zwei Stellen es anzeigen:

        kig_pos.ico   Windows: die exe, Verknüpfungen,
                      Explorer
        kig_pos.png   Kivy: Fenster und Taskleiste des
                      laufenden Programms

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

    Beides liegt auf einer weißen Kachel: Das Logo selbst
    ist schwarz auf durchsichtig und war auf einem dunklen
    Bildschirm nicht zu sehen.

Aufruf:
    .venv\\Scripts\\python.exe werkzeuge\\symbol_erzeugen.py

Version:
    1.0.0
=========================================================
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJEKT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJEKT))

QUELLE = PROJEKT / "assets" / "kig_logo.png"

# Zwei Ziele, zwei Verwendungen:
#     .ico  Windows: die exe selbst, Verknüpfungen, Explorer
#     .png  Kivy: Fenster und Taskleiste des laufenden Programms
ZIEL = PROJEKT / "assets" / "icons" / "kig_pos.ico"
ZIEL_PNG = PROJEKT / "assets" / "icons" / "kig_pos.png"

FENSTER_GROESSE = 256

# Anteil der Logobreite, in dem der Schriftzug "KiG" steht. Gemessen am
# vorhandenen Logo: Die Krone links und rechts (Dartpfeile, Billardqueues)
# ist bei 16 Bildpunkten ohnehin nur noch Rauschen.
KIG_LINKS = 0.28
KIG_RECHTS = 0.72
KIG_UNTEN = 0.52

# Rundung der Ecken, als Anteil der Kantenlaenge. 0 = eckig.
ECKEN_ANTEIL = 0.16

GROSSE_GROESSEN = (256, 128, 64)
KLEINE_GROESSEN = (48, 32, 16)


def zuschneiden(bild):
    """Schneidet den durchsichtigen Rand ab."""

    rand = bild.getbbox()

    return bild.crop(rand) if rand else bild


def weisse_flaeche(kante):
    """Weiße Kachel mit abgerundeten Ecken.

    Das Logo ist schwarz auf durchsichtig. Auf einem dunklen
    Bildschirm - dunkler Desktop, dunkle Taskleiste - stand es damit
    schwarz auf schwarz und war schlicht nicht zu sehen. Die weiße
    Fläche darunter macht es überall sichtbar.

    Die Ecken sind gerundet, wie bei Programmsymbolen üblich; ein
    hartes weißes Quadrat sieht in der Taskleiste aus wie ein
    Blatt Papier. Wer es eckig möchte, setzt ECKEN_ANTEIL auf 0.
    """

    flaeche = Image.new("RGBA", (kante, kante), (255, 255, 255, 0))

    if ECKEN_ANTEIL <= 0:
        flaeche.paste((255, 255, 255, 255), (0, 0, kante, kante))
        return flaeche

    # Vierfach gezeichnet und dann verkleinert: Sonst sind die
    # Rundungen bei 16 Bildpunkten ausgefranst.
    fein = 4
    gross = Image.new("RGBA", (kante * fein, kante * fein), (255, 255, 255, 0))

    ImageDraw.Draw(gross).rounded_rectangle(
        (0, 0, kante * fein - 1, kante * fein - 1),
        radius=int(kante * fein * ECKEN_ANTEIL),
        fill=(255, 255, 255, 255),
    )

    return gross.resize((kante, kante), Image.LANCZOS)


def ins_quadrat(bild, kante, rand_anteil=0.08):
    """Legt ein Bild mittig auf die weiße Kachel."""

    platz = int(kante * (1 - 2 * rand_anteil))

    breite, hoehe = bild.size
    faktor = min(platz / breite, platz / hoehe)

    verkleinert = bild.resize(
        (max(1, round(breite * faktor)), max(1, round(hoehe * faktor))),
        Image.LANCZOS,
    )

    flaeche = weisse_flaeche(kante)
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

    # -------------------------------------------------
    # Dasselbe Symbol als PNG - fuer Fenster und Taskleiste
    # -------------------------------------------------
    #
    # Kivy bekommt eine .ico-Datei NICHT geladen: Das Fenster behaelt
    # dann Kivys eigenes Zeichen, und genau das steht in der
    # Taskleiste. Nachgemessen am laufenden Fenster (WM_GETICON) -
    # mit .png kommt unser Symbol an, mit .ico nicht.
    #
    # Bewusst der Zuschnitt "KiG" und nicht das ganze Logo: In der
    # Taskleiste ist das Symbol rund 32 Bildpunkte gross.

    ins_quadrat(schriftzug, FENSTER_GROESSE).save(ZIEL_PNG)

    print(f"{ZIEL_PNG.relative_to(PROJEKT)} erzeugt "
          f"({FENSTER_GROESSE} fuer Fenster und Taskleiste)")


if __name__ == "__main__":
    main()
