[app]

# =========================================================
# KiG POS - Androidpaket
# =========================================================
#
# Gebaut wird mit Buildozer, das ausschliesslich unter Linux
# laeuft (WSL, Docker oder GitHub Actions - siehe
# ANDROID_BAUEN.md im Projektordner).
#
#   buildozer android debug     -> bin/kigpos-*-debug.apk
#   buildozer android release   -> signierte Fassung (Play Store)
#
# =========================================================

title = KiG POS

package.name = kigpos
package.domain = de.kigev

source.dir = .

# Startdatei ist main.py (siehe dort) - Buildozer erwartet diesen
# Namen; die Anwendung selbst steht weiterhin in KiG_POS.py.

# Welche Dateitypen ins Paket wandern. png deckt Logo, Symbole und
# die Screenshots des Benutzerhandbuchs ab.
source.include_exts = py,png,jpg,jpeg,ttf,otf,json,txt,md

# Nicht mitnehmen:
#
#   database  - die Datenbank bleibt bewusst aussen vor. Auf dem
#               Telefon wird beim ersten Start eine leere angelegt
#               (Kategorien und Grundeinstellungen kommen
#               automatisch, Getraenke/Rezepte/Events legst du dort
#               neu an).
#   exports   - Ausgaben des Windows-Rechners
#   logs      - Protokolldateien
#   vorlagen  - die Excel-Arbeitsmappe, auf dem Telefon nutzlos
#   bin/.buildozer - Ergebnisse frueherer Baulaeufe
source.exclude_dirs = database, exports, logs, vorlagen, tests, bin, .buildozer, .venv, venv, .git, .github, .idea, __pycache__

# Zur Sicherheit auch ueber die Dateiendung: eine Datenbank wandert
# unter keinen Umstaenden mit ins Paket.
source.exclude_patterns = *.db, *.db-shm, *.db-wal, *.xlsm, *.bas, *.log

version = 0.1.0

# reportlab fehlt hier bewusst.
#
# Das Rezept von python-for-android holt einen reportlab-Stand von
# 2019, dessen C-Erweiterung noch direkt in PyFrameObject hineingreift
# ("error: incomplete definition of type 'struct _frame'"). Seit
# Python 3.11 ist diese Struktur undurchsichtig - das laesst sich von
# aussen nicht reparieren.
#
# Folge: Auf dem Telefon ist der PDF-Export des Handbuchs nicht
# verfuegbar; der Knopf sperrt sich dort selbst (siehe
# screens/userguide_screen.py). Alles andere - auch der Excel-Export,
# denn openpyxl ist reines Python - funktioniert unveraendert. Auf dem
# Windows-Rechner bleibt der PDF-Export ohnehin erhalten.
requirements = python3,kivy==2.3.1,pillow,pyjnius,openpyxl,et-xmlfile

# Das Telefon wird hochkant benutzt - die Oberflaeche baut sich auf
# Android immer im Hochformat auf (siehe KiG_POS.py).
orientation = portrait

# Statusleiste sichtbar lassen: Uhrzeit und Akkustand sind am
# Veranstaltungsabend durchaus von Interesse.
fullscreen = 0

icon.filename = %(source.dir)s/assets/android/icon.png

presplash.filename = %(source.dir)s/assets/android/presplash.png
android.presplash_color = #FFFFFF

# Bildschirm nicht abschalten, solange die Kasse laeuft.
android.wakelock = True

# Keine Berechtigungen noetig: Die Datenbank liegt im privaten
# App-Ordner, Ausgaben (PDF/Excel/CSV) im app-eigenen Ordner unter
# Android/data/de.kigev.kigpos/files/exports - beides ohne
# Berechtigung erlaubt (siehe storage.py).
android.permissions =

# Werkzeugkette bewusst festgenagelt.
#
# Ohne Angabe holt Buildozer python-for-android vom Zweig "master".
# Der baute im ersten Versuch Python 3.14 fuer das Telefon - dafuer
# gibt es weder ein passendes Kivy 2.3.1 noch ein passendes Cython
# 0.29. Diese Fassung baut Python 3.11 und ist mit Kivy 2.3.1
# erprobt.
p4a.branch = v2024.01.21

android.api = 33
android.minapi = 21
android.ndk_api = 21

# Zur p4a-Fassung oben passendes NDK (der Standard waere inzwischen
# r28c und damit deutlich neuer als alles, was diese Rezepte kennen).
android.ndk = 25b

android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

# Lizenzen unbeaufsichtigt bestaetigen (noetig fuer GitHub Actions).
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
