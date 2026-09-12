"""
=========================================================
KiG POS
=========================================================

Datei:
    werkzeuge/symbolbilder_hell.py

Beschreibung:
    Erzeugt helle Fassungen der Symbolbilder.

    Die Bilder in assets/icons sind schwarze Striche auf
    durchsichtigem Grund. Im Dunkelmodus verschwinden sie
    damit fast vollständig - und einfärben hilft nicht:
    Kivy multipliziert die Farbe auf die Bildpunkte, und
    Schwarz bleibt dabei schwarz.

    Dieses Werkzeug legt deshalb neben jedes Bild eine
    helle Fassung ("<name>_hell.png"), in der die Striche
    weiß sind. Die Durchsichtigkeit bleibt unverändert -
    nur die Farbe wird getauscht.

    Aufruf:

        .venv\\Scripts\\python.exe werkzeuge/symbolbilder_hell.py

    Läuft nur beim Entwickeln; im Programm werden allein
    die fertigen Dateien gelesen.

Version:
    1.0.0
=========================================================
"""

import sys

from pathlib import Path

from PIL import Image


PROJEKT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJEKT))

import config


# Nur die drei Handgriffe, die als Schaltfläche erscheinen - die
# Kacheln der Startseite stehen auf hellen Karten und bleiben, wie
# sie sind.
BILDER = ("recycle-bin", "edit", "plus")


def hell(quelle, ziel):
    """Tauscht Schwarz gegen Weiß, lässt die Durchsichtigkeit."""

    bild = Image.open(quelle).convert("RGBA")

    punkte = bild.load()

    breite, hoehe = bild.size

    for x in range(breite):
        for y in range(hoehe):

            _r, _g, _b, a = punkte[x, y]

            punkte[x, y] = (255, 255, 255, a)

    bild.save(ziel)

    return ziel


def main():

    for name in BILDER:

        quelle = config.ICON_DIR / f"{name}.png"

        if not quelle.exists():
            print(f"   fehlt: {quelle.name}")
            continue

        ziel = hell(quelle, config.ICON_DIR / f"{name}_hell.png")

        print(f"   {ziel.name}")


if __name__ == "__main__":
    main()
