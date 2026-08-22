# KiG POS als Windows-Programm (.exe) bauen

Anders als beim Android-Paket braucht es dafür nichts Fremdes: Der Bau
läuft auf demselben Rechner, auf dem auch entwickelt wird.

---

## Kurzfassung

```bash
.venv\Scripts\pyinstaller.exe KiG_POS.spec --noconfirm
```

Fertig liegt das Programm danach in:

```
dist\KiG POS\KiG POS.exe
```

Der ganze Ordner `dist\KiG POS` gehört zusammen — nur die .exe allein
läuft nicht. Zum Weitergeben also den **Ordner** kopieren (oder als ZIP
verschicken).

---

## Was wo landet

| Was | Wo |
|---|---|
| Programm und mitgelieferte Bilder | `KiG POS\_internal` |
| Datenbank und Sicherungen | `KiG POS\daten` |
| Ausgaben (Excel, CSV, PDF) | `KiG POS\exports` |
| Protokoll | `KiG POS\logs` |

Diese Ordner entstehen beim **ersten Start**. Solange sie fehlen, legt
das Programm eine leere Datenbank an: sechs Kategorien, keine Artikel,
keine Verkäufe.

Das ist der Unterschied zur Entwicklungsfassung, die ihre Datenbank
unter `AppData\Roaming\kigpos` führt (siehe `storage.py:data_dir`). Das
fertige Programm bleibt bewusst bei sich: Wer den Ordner kopiert, nimmt
alles mit — und wer es zum ersten Mal startet, fängt bei null an statt
mit den Daten eines fremden Rechners.

**Zum Zurücksetzen** genügt es, den Ordner `daten` zu löschen. Beim
nächsten Start ist die Kasse wieder leer. (Eine Sicherung liegt jeweils
in `daten\backups`.)

---

## Das Programmsymbol

Beide Symboldateien entstehen aus dem Vereinslogo:

```bash
.venv\Scripts\python.exe werkzeuge\symbol_erzeugen.py
```

| Datei | Wer zeigt sie |
|---|---|
| `assets\icons\kig_pos.ico` | Windows: die exe, Verknüpfungen, Explorer |
| `assets\icons\kig_pos.png` | Kivy: Fenster und Taskleiste des laufenden Programms |

**Zwei Dateien sind nötig, keine Bequemlichkeit:** Kivy nimmt eine
.ico-Datei zwar widerspruchslos an, lädt sie aber nicht — das Fenster
behält dann Kivys eigenes Zeichen, und genau das steht in der
Taskleiste. Nachgemessen am laufenden Fenster (`WM_GETICON`).

Die .ico enthält zwei Zuschnitte: das ganze Logo für große
Darstellungen, nur den Schriftzug "KiG" für kleine. In der Taskleiste
wäre das vollständige Logo sonst ein grauer Streifen. Beides liegt auf
einer weißen Kachel, sonst ist das schwarze Logo auf dunklem
Bildschirm unsichtbar.

Neu erzeugen muss man die Dateien nur, wenn sich das Logo ändert.

**Wenn Windows trotzdem das alte Symbol zeigt:** Das ist der
Symbolzwischenspeicher, nicht die Datei. Auffrischen mit

```bash
ie4uinit.exe -show
```

---

## Fenster oder Vollbild?

`config.py` legt mit `WINDOW_MODE` fest, wie das Programm startet
(`window`, `fullscreen`, `maximized`, `borderless`). Diese Einstellung
wird **fest eingebaut** — in der fertigen .exe lässt sie sich nicht
mehr ändern. Für einen anderen Modus also `config.py` anpassen und neu
bauen.

---

## Wenn etwas nicht startet

Die .exe läuft ohne Konsolenfenster; Fehlermeldungen sind damit
unsichtbar. Zum Nachsehen eine Fassung **mit** Konsole bauen: in
`KiG_POS.spec` `console=False` auf `console=True` setzen, neu bauen,
aus der Eingabeaufforderung starten — dort steht dann, woran es liegt.

---

## Warum ein Ordner und keine einzelne Datei

PyInstaller kann alles in eine einzige .exe packen. Die entpackt sich
dann aber bei **jedem** Start neu in einen temporären Ordner: rund
90 MB Kivy und SDL2, also mehrere Sekunden Warten, bevor die Kasse
aufgeht. Am Vereinsabend ist das die falsche Reihenfolge.
