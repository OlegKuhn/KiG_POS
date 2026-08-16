# Werkzeuge

Hilfsmittel für die Entwicklung. Sie gehören **nicht** zur Anwendung
und wandern nicht ins Androidpaket (siehe `buildozer.spec`,
`source.exclude_dirs`).

## geraete_pruefen.py

Baut die komplette Oberfläche für mehrere Geräte auf und meldet jede
Stelle, an der etwas über seinen Rahmen hinausragt.

```bash
.venv\Scripts\python.exe werkzeuge\geraete_pruefen.py
```

Geprüft werden derzeit:

| Gerät | Bildpunkte | Dichte |
|---|---|---|
| Windows-Rechner (quer) | 1500 × 875 | 1,25 |
| Windows-Rechner (hoch) | 825 × 990 | 1,25 |
| Onyx Boox Go 10.3 (hoch) | 1860 × 2480 | 1,875 |
| Onyx Boox Go 10.3 (quer) | 2480 × 1860 | 1,875 |
| Galaxy S24 Ultra | 1440 × 3120 | 3,5 |
| Kleines Telefon (HD+) | 720 × 1600 | 2,0 |

**Warum kein Emulator?** Für das Layout zählen nur zwei Zahlen:
Bildschirmgröße und Bildschirmdichte. Beide lassen sich hier direkt
setzen. Die Oberfläche wird dabei nicht angezeigt, sondern nur
vermessen - deshalb sind auch Bildschirme prüfbar, die größer sind als
der Monitor des Rechners. Ein Durchlauf dauert rund eine Minute statt
der Viertelstunde, die Bau, Installation und Klickerei im Emulator
kosten.

**Neues Gerät aufnehmen:** In der Liste `GERAETE` ergänzen. Die Werte
liefert ein angeschlossenes Gerät:

```bash
adb shell wm size
```

```bash
adb shell wm density
```

Dichte = gemeldeter Wert / 160.

**Rückgabewert:** 0 wenn alles passt, sonst 1 - damit lässt sich die
Prüfung auch automatisch auswerten.

Die Prüfung läuft in einer eigenen Anwendung mit eigenem Datenordner;
die echte Datenbank wird nicht angefasst.
