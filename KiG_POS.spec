# -*- mode: python ; coding: utf-8 -*-
#
# =========================================================
# KiG POS - Bauanleitung fuer das Windows-Programmpaket
# =========================================================
#
# Aufruf:
#     .venv\Scripts\pyinstaller.exe KiG_POS.spec --noconfirm
#
# Ergebnis:
#     dist\KiG POS\KiG POS.exe
#
# Bewusst ein Ordner und keine einzelne Datei: Eine
# Ein-Datei-exe packt sich bei JEDEM Start neu in einen
# temporaeren Ordner aus (Kivy, SDL2, ~90 MB) - auf dem
# Vereinsrechner sind das mehrere Sekunden Wartezeit vor
# jedem Kassenstart. Der Ordner startet sofort.
#
# Die Daten liegen daneben in "daten" (siehe storage.py):
# Wer den Ordner kopiert, nimmt Datenbank, Sicherungen und
# Ausgaben mit.

from pathlib import Path

from kivy_deps import sdl2, glew

from kivy.tools.packaging.pyinstaller_hooks import (
    get_deps_minimal, hookspath, runtime_hooks,
)


PROJEKT = Path(SPECPATH)

# Die Buildnummer zaehlt Commits (siehe config._buildnummer). Im
# fertigen Paket gibt es kein Git mehr - sie wird deshalb hier
# festgehalten und mit eingepackt.
import subprocess

try:
    _gezaehlt = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=str(PROJEKT), capture_output=True, text=True, timeout=10,
    )

    if _gezaehlt.returncode == 0 and _gezaehlt.stdout.strip().isdigit():
        (PROJEKT / "buildnummer.txt").write_text(
            _gezaehlt.stdout.strip(), encoding="utf-8"
        )
        print(f"Buildnummer: {_gezaehlt.stdout.strip()}")

except Exception as fehler:                      # pragma: no cover
    print(f"Buildnummer nicht ermittelbar: {fehler}")

# Kivy laedt seine Anbieter (Fenster, Bild, Text) erst zur Laufzeit -
# PyInstaller findet sie deshalb nicht von selbst. get_deps_minimal()
# nennt genau die, die tatsaechlich gebraucht werden.
abhaengigkeiten = get_deps_minimal(video=None, audio=None, camera=None)

# Zusaetzlich: Was ueber Zeichenketten geladen wird oder erst in einem
# selten benutzten Zweig auftaucht.
abhaengigkeiten["hiddenimports"] += [
    "openpyxl",
    "openpyxl.chart",
    "reportlab.graphics.barcode",
    "reportlab.pdfbase._fontdata_enc_winansi",
    "reportlab.pdfbase._fontdata_widths_helvetica",
]

# get_deps_minimal() bringt seine eigene Ausschlussliste mit (die
# nicht benutzten Kivy-Anbieter). Entwicklungswerkzeuge kommen dazu -
# ersetzen darf man die Liste nicht.
abhaengigkeiten["excludes"] += [
    "tkinter",
    "unittest",
    "pydoc",
    "doctest",
]


a = Analysis(
    ["main.py"],
    pathex=[str(PROJEKT)],
    datas=[
        # Bilder, Symbole und die Bilder des Handbuchs
        (str(PROJEKT / "assets"), "assets"),
        # Die Buildnummer (siehe oben)
        (str(PROJEKT / "buildnummer.txt"), "."),
    ],
    hookspath=hookspath(),
    runtime_hooks=runtime_hooks(),
    noarchive=False,
    **abhaengigkeiten,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="KiG POS",
    debug=False,
    strip=False,
    upx=False,
    # Kein Konsolenfenster: Die Kasse startet als Programm, nicht als
    # schwarzes Fenster mit Protokolltext dahinter.
    console=False,
    icon=str(PROJEKT / "assets" / "icons" / "kig_pos.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=False,
    name="KiG POS",
)
