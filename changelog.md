# Changelog

Alle wichtigen Änderungen an **KiG POS** werden in dieser Datei dokumentiert.

Das Projekt orientiert sich an den Empfehlungen von
**Keep a Changelog** und verwendet eine interne Buildverwaltung.

---

# Version 0.2.0
Build 0002

Status:
✔ Freigegeben

Veröffentlichung:
04.07.2026

---

## Hinzugefügt

### Projektstruktur

- Grundstruktur des Projektes erstellt
- Modulstruktur vorbereitet
- Trennung in Screens, Widgets, Datenbank und Tests

---

### Datenbank

- SQLite-Datenbank integriert
- Automatische Datenbankerstellung
- Kategorien werden automatisch angelegt
- Pfandarten werden automatisch angelegt
- Grundeinstellungen werden automatisch angelegt
- Datenbanktest erstellt

---

### Theme

- Zentrales Theme-System eingeführt
- Vereinsfarbe RAL 2004 (Reinorange)
- Farbdefinitionen zentral verwaltet
- Schriftgrößen zentral definiert
- SplashScreen-Konstanten ergänzt

---

### Eigene Widgets

#### KiGWidget

- Basisklasse für alle zukünftigen Widgets erstellt

#### KiGLogo

- Eigenes Logo-Widget entwickelt
- Automatische Größenanpassung

#### KiGLabel

- Eigenes Label-Widget
- Unterstützung für Schriftgröße
- Unterstützung für Farben
- Unterstützung für Fettschrift

#### KiGProgressBar

Version 1.0 abgeschlossen

Enthält:

- Animierte ProgressBar
- Weiche Fortschrittsanimation
- RAL 2004 Reinorange
- Hellgrauer Hintergrund
- Schatten
- Abgerundete Ecken
- Wandernder Glanzstreifen
- Reset-Funktion
- Complete-Funktion
- Stop-Funktion

Eigenständiger Test erfolgreich abgeschlossen.

---

### Splash Screen

Version 1.0 abgeschlossen

Enthält:

- Vereinslogo
- Programmtitel
- Untertitel
- Doppelte Trennlinie
- Slogan
- Premium ProgressBar
- Statusanzeige
- Versionsanzeige
- Initialisierungslogik
- Callback-System
- Eigenständiger Test erfolgreich abgeschlossen

---

### Tests

Erstellt:

- test_database.py
- test_progressbar.py
- test_splash_screen.py

---

## Geändert

- Projektstruktur vereinheitlicht
- Theme zentralisiert
- Einheitliche Widgets eingeführt

---

## Behoben

- Fehler bei der Datenbankinitialisierung
- Fehler beim Anlegen der Standarddaten
- Fehler in der ProgressBar-Animation
- Fehler beim SplashScreen-Start
- Fehler bei der Widget-Initialisierung

---

## Bekannte Einschränkungen

Der HomeScreen befindet sich derzeit in Entwicklung.

---

# Nächste Version

Version 0.3.0

Geplant:

- HomeScreen
- Navigation
- Veranstaltungsverwaltung
- Einstellungen
- Benutzerverwaltung

KiG POS – Changelog

Datum: 05.07.2026

Version: Development Build 0001

Allgemein
Beginn der Entwicklung der neuen KiGHeaderBar Version 1.0.
Die HeaderBar wird künftig auf allen Screens der Anwendung verwendet.
Entscheidung getroffen, die Architektur nicht mehr grundlegend zu verändern, sondern nur noch optisch zu verfeinern.
HeaderBar
Architektur

Neu aufgebaut:

Header als eigenes Widget (KiGHeaderBar)
Drei feste Bereiche:
Logo
Veranstaltung
Statusbereich

Verwendete Widgets:

KiGLogoButton
KiGLabel
KiGWidget
Layout

Festgelegt:

Headerhöhe: 90 px
Hintergrund: hellgrau (theme.HEADER_BACKGROUND)
untere Trennlinie
leichter Schatten unter dem Header
BoxLayout mit drei Bereichen
Logo

Änderungen:

Logo links positioniert
Logo als Home-Button
Logo verwendet nun wieder das Original-PNG (identisch zum SplashScreen)
Fehler durch falsche Logo-Datei behoben

Offen:

Logo noch etwas größer darstellen
Logo exakt mittig innerhalb des linken Bereichs ausrichten
Veranstaltungsbereich

Umgesetzt:

Veranstaltungsname mittig
Zusatzinformation mittig
schwarze Schrift
größere Schrift für Veranstaltungsnamen

Status:

✔ nahezu abgeschlossen

Statusbereich

Umgesetzt:

Datum
Uhrzeit
Tagesumsatz
Umsatz in Reinorange
Aktualisierung der Uhr im Sekundentakt

Geplante Änderungen:

Datum fett darstellen
Tagesumsatz in Sekundärfarbe (theme.TEXT_SECONDARY)
feine horizontale Trennlinie zwischen Datum und Umsatzbereich
Vertikale Trennlinien

Erster Entwurf implementiert.

Festgestellt:

Linien werden derzeit noch falsch positioniert.
Teilweise reichen sie in den Arbeitsbereich hinein.

Entscheidung:

Die Linien dürfen ausschließlich innerhalb des Headers dargestellt werden.

Zu prüfen:

Berechnung im Canvas oder
Einführung eines eigenen KiGDivider-Widgets
SplashScreen

Fehler behoben:

Import von kig_label_old auf kig_label geändert
SplashScreen funktioniert wieder vollständig
Logo

Assets bereinigt:

doppelte Logo-Dateien entdeckt
richtige PNG-Datei verwendet
Header und SplashScreen greifen wieder auf dieselbe Originaldatei zu
Designentscheidungen

Endgültig beschlossen:

Header über gesamte Fensterbreite
Hintergrund hellgrau
schwarzer Text für optimale Lesbarkeit im Sonnenlicht
Reinorange ausschließlich als Akzentfarbe
Umsatz wird orange dargestellt
Logo bleibt unverändert
keine KI-generierte Logo-Version
ausschließlich Original-Logo mit transparentem Hintergrund
Teststatus
Erfolgreich getestet
SplashScreen
KiGLogo
KiGLogoButton
KiGLabel
KiGHeaderBar (Grundfunktion)
Bekannte offene Punkte
Logo etwas größer darstellen
Logo exakt vertikal zentrieren
Vertikale Trennlinien korrekt positionieren
Horizontale Trennlinie im Statusbereich ergänzen
Datum fett darstellen
Tagesumsatz grau darstellen
Feinabstimmung der Abstände
Nächster Entwicklungsschritt

Bei der nächsten Sitzung:

HeaderBar fertigstellen
Optisches Feintuning abschließen
HeaderBar Version 1.0 Final freigeben
Entwicklung des HomeScreens beginnen