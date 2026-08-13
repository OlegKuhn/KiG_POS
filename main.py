"""
=========================================================
KiG POS
=========================================================

Datei:
    main.py

Beschreibung:
    Einstiegspunkt für Android.

    Buildozer startet auf dem Gerät immer die Datei "main.py" -
    ein anderer Name ist nicht vorgesehen. Die eigentliche
    Anwendung steht unverändert in KiG_POS.py; hier wird sie nur
    gestartet.

    Auf dem Windows-Rechner ändert sich dadurch nichts: Dort kann
    weiterhin KiG_POS.py gestartet werden (oder ebenso gut diese
    Datei).

Version:
    1.0.0
=========================================================
"""

from KiG_POS import KiGPOS


if __name__ == "__main__":

    KiGPOS().run()
