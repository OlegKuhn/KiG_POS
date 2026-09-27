"""
=========================================================
KiG POS
=========================================================

Datei:
    werkzeuge/pruefkatalog.py

Beschreibung:
    Erzeugt eine Excel-Mappe zum Durchtesten der Anwendung -
    Funktion für Funktion, Gerät für Gerät.

    Aufruf:
        .venv\\Scripts\\python.exe werkzeuge\\pruefkatalog.py
        .venv\\Scripts\\python.exe werkzeuge\\pruefkatalog.py <zieldatei>

    Aufbau der Mappe:

        Anleitung    wie die Liste zu benutzen ist
        Übersicht    zählt je Bereich zusammen, was geprüft ist
        je Bereich   ein Blatt mit den Funktionen darin

    Je Zeile eine Funktion, je Gerät eine Spalte. Wo eine
    Funktion auf einem Gerät nicht vorkommt, steht ein
    Strich - dort ist nichts zu prüfen, und niemand soll
    suchen (den PDF-Export gibt es nur am Rechner, die
    Dateiauswahl des Systems nur auf Android).

    Die Liste ist aus dem Programm abgeleitet: Sie folgt
    den Themen des Handbuchs (widgets/userguide/content.py)
    und ergänzt, was dort noch nicht steht - Übertragung
    zwischen Geräten und das Sperren auf dem Nebengerät.

Version:
    1.0.0
=========================================================
"""

import sys

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


PROJEKT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJEKT))

import config


# =========================================================
# Geräte und Zustände
# =========================================================

GERAETE = ("Rechner", "Tablet")

ZUSTAENDE = ("offen", "OK", "Fehler", "Teilweise", "entfällt")

# Kürzel für die Spalten je Gerät: Wo eine Funktion nicht vorkommt,
# steht von vornherein "entfällt".
NICHT = "entfällt"


# =========================================================
# Was beim Neuerzeugen erhalten bleibt
# =========================================================
#
# Der Katalog waechst mit dem Programm - eingetragene Ergebnisse und
# Kommentare duerfen dabei nicht verlorengehen. Beim Erzeugen wird
# eine vorhandene Mappe deshalb gelesen und ihr Stand uebernommen.
#
# Zwei Sonderfaelle:
#
#   UMBENANNT   Die Funktion heisst jetzt anders. Der Kommentar zieht
#               mit, das Ergebnis nicht - die Funktion ist eine
#               andere geworden.
#
#   GEAENDERT   Die Funktion heisst gleich, verhaelt sich aber
#               anders. Auch hier bleibt der Kommentar, das Ergebnis
#               geht auf "offen": Was sich geaendert hat, will neu
#               angesehen werden.

UMBENANNT = {
    ("Grundlagen", "Fußzeile: Version und Beenden"):
        ("Grundlagen", "Version, Build und Beenden in den Einstellungen"),

    ("Grundlagen", "Kopfzeile: Datum, Uhrzeit, Tagesumsatz"):
        ("Grundlagen", "Kopfzeile: Tagesumsatz"),

    ("Darstellung", "Kopf- und Fußzeile schlank"):
        ("Darstellung", "Kopfzeile schlank"),
}

GEAENDERT = {
    ("Grundlagen", "Kopfzeile: Veranstaltung des Tages"),
    ("Kasse", "Warenkorb als Zeile"),
    ("Kasse", "Warenkorb aufklappen"),
    ("Artikelverwaltung", "Übersicht"),
    ("Artikelverwaltung", "Kategorie anlegen"),
    ("Artikelverwaltung", "Kategorie ändern und löschen"),
    ("Kassenbuch", "Zeitraum wählen"),
    ("Statistik", "Nach Event filtern"),
    ("Statistik", "Nach Zeitraum filtern"),
}


FARBEN = {
    "kopf": "F44611",
    "bereich": "FDE8E1",
    "ok": "C6EFCE",
    "fehler": "FFC7CE",
    "teilweise": "FFEB9C",
    "entfaellt": "E7E7E7",
}


# =========================================================
# Der Katalog
# =========================================================
#
# (Funktion, Wo zu finden, Erwartetes Verhalten, Geräte)
#
# Geräte: Zeichenkette aus R (Rechner) und T (Tablet).
# Was fehlt, entfällt dort.

KATALOG = [

    ("Grundlagen", [

        ("Programm startet",
         "Programmsymbol / Startseite",
         "Startbild erscheint, danach die Startseite mit den Kacheln.",
         "RT"),

        ("Leere Datenbank beim ersten Start",
         "Erster Start auf einem neuen Gerät",
         "Sechs Kategorien, keine Artikel, keine Verkäufe.",
         "RT"),

        ("Automatische Sicherung",
         "Ordner daten/backups",
         "Bei jedem Start entsteht eine Sicherung; die letzten 15 "
         "bleiben liegen.",
         "RT"),

        ("Kaputte Datenbank",
         "daten/kig.db unlesbar machen (Sicherung vorher!)",
         "Verständlicher Hinweis mit Speicherort und Beenden-Knopf "
         "statt Absturz.",
         "R"),

        ("Kopfzeile: Logo führt heim",
         "Kopfzeile links",
         "Ein Tipp auf das Logo öffnet die Startseite.",
         "RT"),

        ("Kopfzeile: Tagesumsatz",
         "Kopfzeile rechts",
         "Der Tagesumsatz ändert sich nach einem Verkauf sofort.",
         "RT"),

        ("Kopfzeile: Datum und Uhrzeit nur am Rechner",
         "Kopfzeile rechts",
         "Am Rechner läuft die Uhr mit. Auf dem Tablet steht dort "
         "nichts dergleichen - das zeigt das Gerät selbst.",
         "RT"),

        ("Kopfzeile: Veranstaltung des Tages",
         "Kopfzeile Mitte (Event im Kalender anlegen)",
         "Der Name der heutigen Veranstaltung steht dort, sonst "
         "\"KiG POS\". Ein neu angelegtes Event erscheint nach dem "
         "nächsten Bildschirmwechsel.",
         "RT"),

        ("Keine Fußzeile mehr",
         "Alle Bildschirme, unterer Rand",
         "Unten steht nur noch, was zum Bildschirm gehört - Warenkorb "
         "oder Filter. Kein Streifen mit Version und Beenden.",
         "RT"),

        ("Version, Build und Beenden in den Einstellungen",
         "Einstellungen, Abschnitt \"Programm\"",
         "Version und Buildnummer stehen dort; \"Programm beenden\" "
         "fragt vorher nach und beendet erst dann.",
         "RT"),

        ("Buildnummer steigt mit jeder Fassung",
         "Einstellungen, Abschnitt \"Programm\"",
         "Nicht mehr fest 0001: Die Nummer ist bei jedem neuen Stand "
         "höher als beim vorigen.",
         "RT"),

        ("Startbild sitzt richtig",
         "Beim Start, vor der Startseite",
         "Das Logo ist ganz zu sehen und nicht abgeschnitten; Titel, "
         "Untertitel und Wahlspruch überlappen einander nicht.",
         "RT"),

        ("Startseite: drei Gruppen",
         "Startseite",
         "Operativ, Administrativ, Support - alle neun Kacheln "
         "erreichbar.",
         "RT"),

        ("Jede Kachel öffnet ihren Bereich",
         "Startseite, alle neun Kacheln",
         "Jeder Bereich öffnet sich und lässt sich wieder verlassen.",
         "RT"),

    ]),

    ("Kasse", [

        ("Aufbau",
         "Kasse",
         "Kategorien, Artikel und Warenkorb sind zu sehen.",
         "RT"),

        ("Nach Kategorie filtern",
         "Kasse, Kategorie antippen",
         "Nur deren Artikel; zweiter Tipp hebt den Filter auf.",
         "RT"),

        ("Artikel suchen",
         "Kasse, Suchfeld",
         "Treffer erscheinen beim Tippen; das Kreuz setzt zurück.",
         "RT"),

        ("Bestand auf der Kachel",
         "Kasse, Artikelkacheln",
         "\"Bestand\" bei normalen Artikeln, \"Verfügbar\" bei "
         "Rezepten; ausverkauft ist grau.",
         "RT"),

        ("Artikel in den Warenkorb",
         "Kasse, Kachel antippen",
         "Position erscheint im Warenkorb, Summe stimmt.",
         "RT"),

        ("Lange Namen auf der Kachel",
         "Kasse, Artikel mit langem Namen (z. B. \"Apfelschorle naturtrüb\")",
         "Name in zwei Zeilen, nicht abgeschnitten; Bestand darunter "
         "vollständig lesbar, Preis unten.",
         "RT"),

        ("Menge direkt ändern",
         "Warenkorb, Plus/Minus an der Position",
         "Menge und Summe ändern sich sofort.",
         "RT"),

        ("Position bearbeiten",
         "Warenkorb, Position antippen, \"Bearbeiten\"",
         "Preis und Menge lassen sich ändern; kein Löschen, kein "
         "Duplizieren. \"Abbrechen\" verwirft auch einen geänderten Preis.",
         "RT"),

        ("Mix antippen: keine Sprechblase",
         "Kasse, Mix-Artikel im Warenkorb antippen",
         "Die Position wird nur ausgewählt, es geht nichts auf.",
         "RT"),

        ("Mischgetränk verstärken",
         "Mix-Position, \"Bearbeiten\", Zutatenliste",
         "Zutaten mit Menge stehen da; \"+\" nur bei Zutaten mit Shot, "
         "je Tipp ein Shot mehr und Preis + Shotpreis; \"-\" nicht unter "
         "das Rezept.",
         "RT"),

        ("Verstärkter Drink im Warenkorb",
         "Nach \"Übernehmen\"",
         "Zeile heißt z. B. \"Jacky Cola  +1 Jack Daniels\"; derselbe "
         "Drink neu angetippt wird eine eigene Position zum Normalpreis.",
         "RT"),

        ("Extra-Shot im Bestand",
         "Verstärkten Drink bezahlen, Flasche ansehen",
         "Der Bestand der Flasche sinkt um Rezept plus Extra-Shot.",
         "RT"),

        ("Warenkorb leeren",
         "Warenkorb, \"Leeren\"",
         "Nach Rückfrage ist der Warenkorb leer.",
         "RT"),

        ("Warenkorb als Zeile",
         "Kasse im Hochformat, unten",
         "Zugeklappt eine Zeile: Postenzahl, Summe, \"Bezahlen\".",
         "RT"),

        ("Warenkorb aufklappen",
         "Kasse im Hochformat, auf die Zeile tippen",
         "Er klappt hoch und nimmt den ganzen Bildschirm ein; die "
         "Artikel treten so lange beiseite.",
         "RT"),

        ("Warenkorb wieder zuklappen",
         "Aufgeklappter Warenkorb, auf \"Warenkorb\" oben tippen",
         "Der Winkel zeigt nach oben; ein Tipp klappt zu, die Artikel "
         "sind wieder da.",
         "RT"),

        ("Bezahlen aus der zugeklappten Zeile",
         "Kasse im Hochformat, \"Bezahlen\" in der Zeile",
         "Das Zahlungsfenster geht mit der richtigen Summe auf - ohne "
         "vorher aufzuklappen.",
         "RT"),

        ("Leerer Warenkorb klappt selbst zu",
         "Bezahlen oder Leeren, während er aufgeklappt ist",
         "Er klappt von allein zur Zeile zusammen, statt leer den "
         "Bildschirm zu belegen.",
         "RT"),

        ("Bezahlen: Dialog geht auf",
         "Kasse, \"Bezahlen\"",
         "Ein Fenster über der Kasse: links Schnellwahl und Beträge, "
         "rechts das Zahlenfeld, unten Abbrechen und Zahlung "
         "abschließen. \"Zu zahlen\" steht hervorgehoben.",
         "RT"),

        ("Bezahlen: Schnellwahl 5/10/20/50/100",
         "Bezahlen, Schnellwahlfelder",
         "Jeder Tipp legt einen Schein dazu (2x20 = 40); darunter "
         "steht die Aufstellung.",
         "RT"),

        ("Bezahlen: Rückgeld",
         "Bezahlen",
         "Gegeben und Rückgeld stimmen; Rückgeld wird erst grün, wenn "
         "es reicht.",
         "RT"),

        ("Bezahlen: KiG Karte",
         "Bezahlen, \"KiG Karte\", Betrag, OK",
         "Überschrift wird \"Bezahlen · KiG Karte\", der Betrag steht im "
         "Knopf und geht von \"Zu zahlen\" ab; \"Bestätigen\" führt "
         "zurück zum Bargeld.",
         "RT"),

        ("Bezahlen: Gutschein",
         "Bezahlen, \"Gutschein\", Betrag, OK",
         "Wie KiG Karte; mehr als der offene Betrag wird nicht "
         "angerechnet, ganz entwertet geht OK ohne Bargeld.",
         "RT"),

        ("Entwertet in der Statistik",
         "Statistik nach Verkauf mit KiG Karte/Gutschein",
         "Einnahmen mit vollem Preis; darunter \"Entwertet: KiG Karte | "
         "Gutschein | bar\". Auch im Excel-Export.",
         "RT"),

        ("Verkauf abschließen",
         "Bezahlen, bestätigen",
         "Bon wird gebucht, Warenkorb leer, Bestand sinkt, Tagesumsatz "
         "steigt.",
         "RT"),

        ("Stornieren",
         "Kasse, \"Storno\"",
         "Artikel antippen, bestätigen: Gegenbuchung mit negativer "
         "Menge, Bestand steigt wieder.",
         "RT"),

        ("Beträge mit Komma",
         "Überall in der Kasse",
         "2,50 € statt 2.50 - im Warenkorb, auf den Kacheln und beim "
         "Bezahlen.",
         "RT"),

    ]),

    ("Artikelverwaltung", [

        ("Übersicht",
         "Artikel",
         "Die Artikelliste hat den ganzen Bildschirm; die Kategorien "
         "stehen unten in der Leiste. Zeilen abwechselnd weiß und "
         "leicht grau.",
         "RT"),

        ("Kategorien in der Leiste",
         "Artikel, Leiste unten \"Kategorie\"",
         "Zugeklappt steht dort die gewählte Kategorie (sonst \"Alle "
         "Kategorien\"); ein Tipp klappt die Kategorien hoch.",
         "RT"),

        ("Nach Kategorie filtern",
         "Artikel, Kategorie in der Leiste antippen",
         "Die Liste zeigt nur deren Artikel, die Leiste nennt sie; "
         "ein zweiter Tipp hebt den Filter auf.",
         "RT"),

        ("Kategorie anlegen",
         "Artikel, Leiste aufklappen, \"Neu\"",
         "Neue Kategorie erscheint in der Liste und in der Kasse.",
         "RT"),

        ("Kategorie ändern und löschen",
         "Artikel, Leiste aufklappen, \"Bearbeiten\"",
         "Umbenennen wirkt überall; Löschen fragt nach.",
         "RT"),

        ("Neuen Artikel anlegen",
         "Artikel, \"+ Neuer Artikel\"",
         "Name, Preis, Kategorie reichen; der Artikel erscheint in der "
         "Kasse.",
         "RT"),

        ("Stammdaten ändern",
         "Artikel, \"Bearbeiten\"",
         "Preis, Einkaufspreis, Kategorie, Sichtbarkeit lassen sich "
         "speichern.",
         "RT"),

        ("Artikel löschen",
         "Artikel, Mülleimer in der Zeile",
         "Nach Rückfrage verschwindet der Artikel; die Zahl am Regler "
         "\"Inaktive\" zählt eins hoch.",
         "RT"),

        ("Inaktive Artikel",
         "Artikel, Regler \"Inaktive\"",
         "Umgelegt stehen die gelöschten Artikel mit Preis und Bestand "
         "in der Liste; die Zahl am Regler stimmt.",
         "RT"),

        ("Wieder aktivieren",
         "Artikel, Regler \"Inaktive\", \"Wieder aktivieren\"",
         "Der Artikel verschwindet aus der Inaktivliste, steht wieder in "
         "der Liste und an der Kasse.",
         "RT"),

        ("Bestellmenge erfassen",
         "Artikel, Mengenfeld",
         "Nummernblock öffnet sich, Menge wird übernommen.",
         "RT"),

        ("Wareneingang buchen",
         "Artikel, \"Buchen\"",
         "Bestand steigt um die Menge, Einkaufspreis wird verrechnet.",
         "RT"),

        ("Bestand korrigieren",
         "Artikel, Bearbeiten, Bestandskorrektur",
         "Der Bestand wird auf den gezählten Wert gesetzt, die "
         "Bewegung steht in der Historie.",
         "RT"),

        ("Bestandshistorie",
         "Artikel, Bearbeiten",
         "Zugänge, Abgänge und Korrekturen mit Grund und Gerät.",
         "RT"),

        ("Bearbeiter im Bestandsverlauf",
         "Artikel, Bearbeiten, Bestand anpassen mit Namen",
         "Die Korrektur zeigt den Namen in \"Bearbeiter\"; bei Verkauf "
         "und Wareneingang bleibt die Spalte leer.",
         "RT"),

        ("Reihenfolge festlegen",
         "Artikel, \"Sortierung\"",
         "Die gewählte Reihenfolge gilt auch in der Kasse.",
         "RT"),

        ("Rezept anlegen",
         "Artikel, Mix-Artikel bearbeiten",
         "Zutaten zuordnen, Mengen und Einheiten ändern, entfernen.",
         "RT"),

        ("Zutat ohne eigenen Artikel",
         "Rezept, Freitextzutat",
         "Lässt sich mit Menge eintragen und wieder entfernen.",
         "RT"),

        ("Verfügbarkeit und Kosten je Portion",
         "Artikel, Mix-Artikel",
         "\"Verfügbar\" richtet sich nach der knappsten Zutat; Kosten "
         "stimmen.",
         "RT"),

        ("Flasche als Spirituose führen",
         "Artikel, Einheit \"Flasche\"",
         "Flaschengröße wird erfragt, Bestand läuft in ml.",
         "RT"),

        ("Shot zur Flasche",
         "Artikel, Flasche bearbeiten",
         "Der Shot verkauft aus derselben Flasche; Bestand sinkt "
         "anteilig.",
         "RT"),

        ("Einkaufsliste exportieren",
         "Artikel, \"Einkaufsliste exportieren\"",
         "Excel-Datei mit Logo, nach Kategorien gegliedert, mit "
         "Abhakkästchen; darunter stehen Dateiname und Ordner.",
         "RT"),

    ]),

    ("Kalender", [

        ("Monatsübersicht",
         "Events",
         "Der Monat wird angezeigt; Blättern vor und zurück geht.",
         "RT"),

        ("Tag öffnen",
         "Events, Tag antippen",
         "Die Einträge des Tages erscheinen.",
         "RT"),

        ("Eintrag anlegen",
         "Events, Tag, Neu",
         "Veranstaltung, Mitarbeiter oder Termin lassen sich anlegen.",
         "RT"),

        ("Checkliste und Schichtplan mit anlegen",
         "Events, Veranstaltung anlegen",
         "Die beiden Häkchen legen Liste und Plan mit demselben Namen "
         "an.",
         "RT"),

        ("Eintrag ändern und löschen",
         "Events, Eintrag antippen",
         "Änderungen werden gespeichert; Löschen fragt nach.",
         "RT"),

        ("Zusammenspiel mit Kasse und Statistik",
         "Events / Kasse / Statistik",
         "Die Veranstaltung des Tages steht in der Kopfzeile und "
         "filtert die Statistik.",
         "RT"),

    ]),

    ("Kassenbuch", [

        ("Zeitraum wählen",
         "Kassenbuch, Leiste unten \"Zeitraum\"",
         "Zugeklappt steht dort Monat und Jahr; aufgeklappt lassen "
         "sich beide wählen, die Tabelle zieht nach.",
         "RT"),

        ("Zeile erfassen",
         "Kassenbuch, Formular",
         "Datum über den Kalender, Beträge über den Nummernblock; "
         "Speichern legt die Zeile an.",
         "RT"),

        ("Startbestand wird vorbelegt",
         "Kassenbuch, neue Zeile",
         "Der Endbestand des Vortags steht als Startbestand.",
         "RT"),

        ("Endbestand rechnet mit",
         "Kassenbuch, Beträge eintippen",
         "Der Endbestand ergibt sich, solange man ihn nicht selbst "
         "überschreibt.",
         "RT"),

        ("Auffällige Zeilen",
         "Kassenbuch, Zeile mit falscher Rechnung",
         "Die Zeile wird als \"Prüfen\" hervorgehoben, mit Grund.",
         "RT"),

        ("Zeile ändern und löschen",
         "Kassenbuch, Zeile antippen",
         "Änderungen werden übernommen; Löschen fragt nach.",
         "RT"),

        ("Exportieren",
         "Kassenbuch, \"Excel exportieren\"",
         "Datei mit Logo, Übersicht und Einträgen; zum Ausdrucken "
         "eingerichtet, auffällige Zeilen rot mit Hinweis.",
         "RT"),

    ]),

    ("Checkliste", [

        ("Liste anlegen und löschen",
         "Checkliste, \"Neue Liste\" / \"Löschen\"",
         "Liste erscheint; Löschen nimmt ihre Aufgaben mit.",
         "RT"),

        ("Aufgabe eintragen",
         "Checkliste, Feld unten",
         "Die Aufgabe erscheint in der Liste.",
         "RT"),

        ("Aufgabe abhaken",
         "Checkliste, Häkchen",
         "Der Fortschritt oben ändert sich mit.",
         "RT"),

        ("Frist, Verantwortlich, Infos",
         "Checkliste, Felder der Zeile",
         "Alle Angaben werden gespeichert.",
         "RT"),

        ("Aufgabe entfernen",
         "Checkliste, \"Entfernen\"",
         "Die Zeile verschwindet.",
         "RT"),

        ("Exportieren",
         "Checkliste, \"Excel exportieren\"",
         "Datei mit Logo und Haken/Kästchen entsteht; leere Liste gibt "
         "einen Hinweis statt einer leeren Datei.",
         "RT"),

    ]),

    ("Schichtplan", [

        ("Plan anlegen und löschen",
         "Schichtplan, \"Plan anlegen\"",
         "Plan erscheint in der Liste.",
         "RT"),

        ("Schicht eintragen",
         "Schichtplan, Feld unten",
         "Tätigkeit, Zeiten und Bedarf lassen sich eintragen.",
         "RT"),

        ("Helfer eintragen",
         "Schichtplan, Helferfeld",
         "Die Zahl \"eingetragen\" steigt.",
         "RT"),

        ("Farben stimmen",
         "Schichtplan",
         "Grün besetzt, orange teilweise, rot niemand.",
         "RT"),

        ("Schichten übernehmen",
         "Schichtplan, \"Schichten übernehmen\"",
         "Die Schichten eines anderen Plans werden kopiert.",
         "RT"),

        ("Nach Helfer suchen",
         "Schichtplan, Feld \"Helfer suchen\"",
         "Nur Schichten mit diesem Namen; darüber Anzahl und Zeiten; "
         "Kreuz leert die Suche.",
         "RT"),

        ("Überschneidung",
         "Schichtplan, denselben Namen in zwei gleichzeitige Schichten",
         "Warnung im Helfer-Dialog; beide Zeilen rot mit \"!\"; darüber "
         "steht, wo es sich überschneidet. Anschluss 21:00/21:00 ist "
         "keine.",
         "RT"),

        ("Matrix als Excel",
         "Schichtplan, \"Excel\"",
         "Blatt \"Plan\": Zeit nach rechts, Tätigkeiten nach unten, "
         "Blöcke mit Namen in Ampelfarben; Blatt \"Liste\"; Name und "
         "Ordner darunter.",
         "RT"),

        ("Ausdruck nach Uhrzeit",
         "Schichtplan mit Schichten in beliebiger Reihenfolge, \"PDF\"",
         "Matrix und Liste nach Beginn sortiert; was zuerst dran ist, "
         "steht oben, Schichten nach Mitternacht unten.",
         "RT"),

        ("Matrix als PDF",
         "Schichtplan, \"PDF\"",
         "Dieselbe Matrix im Querformat, auch auf dem Tablet; Abbau "
         "nach Mitternacht steht am Ende der Zeitleiste.",
         "RT"),

        ("Plan eines Helfers ausgeben",
         "Schichtplan, Suche aktiv, \"PDF\" oder \"Excel\"",
         "Nur dessen Schichten; der Name steht im Titel und im "
         "Dateinamen.",
         "RT"),

    ]),

    ("Statistik", [

        ("Verkaufsliste",
         "Statistik",
         "Verkäufe des Zeitraums stehen in der Tabelle.",
         "RT"),

        ("Viele Verkäufe laden schnell",
         "Statistik nach einem langen Abend (tausende Verkäufe)",
         "Der Bildschirm ist in wenigen Sekunden da; die Tabelle rollt "
         "flüssig; Auswahl bleibt beim Rollen an der richtigen Zeile.",
         "RT"),

        ("Nach Event filtern",
         "Statistik, Leiste unten \"Auswahl\"",
         "Nur Verkäufe dieser Veranstaltung; die zugeklappte Leiste "
         "nennt das gewählte Event.",
         "RT"),

        ("Nach Kategorie filtern",
         "Statistik, Leiste unten \"Auswahl\", Kategorie",
         "Balken, Kreis, Kennzahlen und Tabelle zeigen nur diese "
         "Kategorie; die zugeklappte Leiste nennt sie.",
         "RT"),

        ("Nach Zeitraum filtern",
         "Statistik, Leiste unten, Von / Bis",
         "Kalender öffnet sich, Filter wirkt, Kreuz setzt zurück; die "
         "Leiste nennt den Zeitraum.",
         "RT"),

        ("Einzelne Position löschen",
         "Statistik, Zeile wählen, \"Ausgewählte löschen\"",
         "Nach Rückfrage weg; Tagesumsatz und Bestand ziehen nach.",
         "RT"),

        ("Ganzen Zeitraum löschen",
         "Statistik, \"Zeitraum löschen\"",
         "Nach deutlicher Rückfrage sind die Verkäufe des Zeitraums "
         "weg.",
         "RT"),

        ("Gesamtverkaufszahlen",
         "Statistik, Karte unten",
         "Einnahmen, Ausgaben, Gewinn passen zum Filter.",
         "RT"),

        ("Top-Artikel",
         "Statistik, Karte unten",
         "Rangliste passt zum Filter.",
         "RT"),

        ("Verteilung nach Kategorie",
         "Statistik, Tortendiagramm",
         "Diagramm und Legende passen zum Filter.",
         "RT"),

        ("Einkaufspreise nachtragen",
         "Statistik, Hinweiszeile",
         "Fehlende Rezeptpreise lassen sich nachtragen; Gewinn "
         "stimmt danach.",
         "RT"),

        ("Excel ausgeben",
         "Statistik, \"Excel\"",
         "Mappe mit Logo: Zusammenfassung mit Kreis- und "
         "Balkendiagramm, Blatt Einzelverkäufe; folgt der Auswahl.",
         "RT"),

        ("PDF ausgeben",
         "Statistik, \"PDF\"",
         "Seite 1 Dashboard (Kennzahlen, Kreis, Topseller je Kategorie), "
         "Seite 2 Verkäufe nach Kategorie, danach die Artikel als "
         "Tabelle nach Kategorien, Zeilen weiß/grau; auch auf dem "
         "Tablet; folgt der Auswahl.",
         "RT"),

    ]),

    ("Einstellungen", [

        ("Farbmodus hell / dunkel",
         "Einstellungen, Farbmodus",
         "Die Oberfläche wechselt vollständig; nach Neustart bleibt "
         "die Wahl.",
         "RT"),

        ("Hoch- oder Querformat",
         "Einstellungen, Bildschirmausrichtung",
         "Die Anordnung wechselt; nach Neustart bleibt die Wahl.",
         "RT"),

        ("Demo-Modus starten",
         "Einstellungen, \"Demo starten\"",
         "Akzentfarbe wird grün, oben steht DEMO; alles lässt sich "
         "ausprobieren.",
         "RT"),

        ("Demo-Modus beenden",
         "Einstellungen, \"Demo beenden\"",
         "Alles Ausprobierte ist verworfen, der Stand von vorher gilt "
         "wieder.",
         "RT"),

        ("Gerät umbenennen",
         "Einstellungen, \"Gerät umbenennen\"",
         "Der neue Name steht in der Kopfzeile und in den Übergaben.",
         "RT"),

        ("Übergaben anzeigen",
         "Einstellungen, \"Übergaben anzeigen\"",
         "Das Protokoll zeigt, wer wann an wen übergeben hat.",
         "RT"),

    ]),

    ("Mehrere Geräte", [

        ("Daten empfangen: warten",
         "Einstellungen, \"Daten empfangen\"",
         "Das Gerät wartet und zeigt Name und Adresse.",
         "RT"),

        ("Daten senden: suchen",
         "Einstellungen, \"Daten senden\"",
         "Das wartende Gerät steht in der Liste.",
         "RT"),

        ("Gegenseite wird gefragt",
         "Senden, Gerät antippen",
         "Auf dem anderen Gerät erscheint \"möchte Daten senden - "
         "annehmen?\".",
         "RT"),

        ("Ablehnen",
         "Empfangen, \"Ablehnen\"",
         "Der Sender meldet die Ablehnung, nichts wird übertragen.",
         "RT"),

        ("Datenbank übertragen",
         "Senden, \"Datenbank\"",
         "Das andere Gerät hat danach alle Artikel und ist "
         "Nebengerät.",
         "RT"),

        ("Kasse übertragen",
         "Senden, \"Kasse\"",
         "Das Schreibrecht wandert; dieses Gerät ist danach nur noch "
         "Ansicht.",
         "RT"),

        ("Buchungen übertragen",
         "Senden, \"Buchungen\"",
         "Nur Zugänge; zweimal gesendet ändert nichts.",
         "RT"),

        ("Kasse steht auf dem Nebengerät nicht zur Wahl",
         "Senden auf einem Nebengerät",
         "Nur Datenbank und Buchungen werden angeboten, mit Begründung.",
         "RT"),

        ("Ohne WLAN: Datei schreiben",
         "Senden, \"Stattdessen als Datei\"",
         "Datei entsteht; danach lässt sie sich teilen.",
         "RT"),

        ("Ohne WLAN: Datei einlesen",
         "Empfangen, \"Kein Netz? Datei suchen\"",
         "Die Datei wird gefunden und nach Rückfrage eingespielt.",
         "RT"),

        ("Empfangene Datei wird gefunden",
         "Empfangen, Dateiliste",
         "Auch Dateien aus Downloads, Desktop oder Bluetooth stehen "
         "dort, mit Herkunft.",
         "R"),

        ("Dateiauswahl des Geräts",
         "Empfangen, \"Datei suchen\"",
         "Androids Dateiauswahl öffnet sich; die gewählte Datei wird "
         "übernommen.",
         "T"),

        ("Per Bluetooth senden",
         "Senden, Datei, \"Per Bluetooth senden\"",
         "Die Bluetooth-Übertragung öffnet sich; die Gegenseite nimmt "
         "an.",
         "T"),

        ("Nebengerät: Sperren sichtbar",
         "Artikel auf einem Nebengerät",
         "Neu, Sortierung, Buchen, Bearbeiten und Löschen sind grau, "
         "darüber steht der Grund.",
         "RT"),

        ("Nebengerät: kein Absturz",
         "Nebengerät, gesperrte Knöpfe antippen",
         "Nichts passiert bzw. ein wegtippbarer Hinweis - das Programm "
         "läuft weiter.",
         "RT"),

        ("Nebengerät: buchen bleibt erlaubt",
         "Nebengerät, Kasse und Listen",
         "Verkaufen, Kassenbuch, Checklisten und Schichten gehen.",
         "RT"),

        ("Bonnummern je Gerät",
         "Zwei Geräte verkaufen",
         "Keine doppelten Bonnummern nach dem Einsammeln.",
         "RT"),

        ("Bestand über mehrere Geräte",
         "Zwei Geräte verkaufen, dann einsammeln",
         "Die Abgänge beider Geräte sind zusammengerechnet.",
         "RT"),

    ]),

    ("Ausgabe und Teilen", [

        ("Ordner steht beim Export dabei",
         "Nach jedem Export",
         "Dateiname und Ordner stehen unter dem Knopf.",
         "RT"),

        ("Teilen: Statistik",
         "Statistik, \"Teilen\"",
         "Teilen-Auswahl (Android) bzw. Ordner mit ausgewählter Datei "
         "(Rechner).",
         "RT"),

        ("Teilen: Kassenbuch",
         "Kassenbuch, \"Teilen\"",
         "wie oben",
         "RT"),

        ("Teilen: Checkliste",
         "Checkliste, \"Teilen\"",
         "wie oben",
         "RT"),

        ("Teilen: Schichtplan",
         "Schichtplan, \"Teilen\"",
         "wie oben",
         "RT"),

        ("Teilen: Einkaufsliste",
         "Artikel, \"Teilen\"",
         "wie oben",
         "RT"),

        ("Teilen ohne Export",
         "Teilen antippen, bevor exportiert wurde",
         "Hinweis \"Erst exportieren, dann teilen.\"",
         "RT"),

        ("Geteilte Datei ist auffindbar",
         "Android, nach dem Teilen",
         "Die Datei liegt in Download/KiG POS und ist im Dateimanager "
         "zu sehen.",
         "T"),

        ("Handbuch als PDF",
         "Handbuch, \"Als PDF exportieren\"",
         "PDF mit allen Bildern entsteht.",
         "R"),

        ("PDF-Export gesperrt",
         "Handbuch auf Android",
         "Der Knopf ist gesperrt und sagt, warum.",
         "T"),

    ]),

    ("Handbuch", [

        ("Themen und Anleitung",
         "Userguide",
         "Links das Thema wählen, rechts erscheint der Text mit Bild.",
         "RT"),

        ("Alle Themen öffnen sich",
         "Userguide, jedes Thema",
         "Kein Thema bleibt leer oder bricht ab.",
         "RT"),

        ("Bilder passen zum Text",
         "Userguide",
         "Die Screenshots zeigen den beschriebenen Bildschirm.",
         "RT"),

    ]),

    ("Darstellung", [

        ("Nichts ragt über den Rand",
         "Alle Bildschirme",
         "Keine Schaltfläche und keine Beschriftung läuft aus dem Bild.",
         "RT"),

        ("Keine abgeschnittenen Wörter",
         "Alle Bildschirme",
         "Nichts bricht mitten im Wort um.",
         "RT"),

        ("Filterleiste sagt, was gilt",
         "Artikel, Kassenbuch, Statistik",
         "Zugeklappt steht dort der eingestellte Stand - ohne dass man "
         "sie öffnen muss.",
         "RT"),

        ("Filterleiste klappt auf und zu",
         "Artikel, Kassenbuch, Statistik",
         "Ein Tipp öffnet sie, ein zweiter schließt sie; beim Wechsel "
         "des Bildschirms ist sie wieder zu.",
         "RT"),

        ("Bildschirmtastatur schiebt das Feld hoch",
         "Listen, neues Feld beschreiben",
         "Das beschriebene Feld bleibt sichtbar.",
         "T"),

        ("Nummernblock ohne Systemtastatur",
         "Zahlenfelder antippen",
         "Nur der Nummernblock geht auf, nicht zusätzlich die "
         "Tastatur.",
         "T"),

        ("Dunkelmodus überall",
         "Alle Bildschirme im Dunkelmodus",
         "Kein weißer Kasten, keine unlesbare Schrift.",
         "RT"),

        ("Lesbarkeit auf E-Ink",
         "Alle Bildschirme auf dem Tablet",
         "Kontraste reichen, nichts verschwimmt.",
         "T"),

    ]),

]


# =========================================================
# Mappe bauen
# =========================================================

def _kopfzeile(blatt, spalten, zeile=1):

    for nummer, (titel, breite) in enumerate(spalten, start=1):

        zelle = blatt.cell(row=zeile, column=nummer, value=titel)

        zelle.font = Font(bold=True, color="FFFFFF", size=11)
        zelle.fill = PatternFill("solid", fgColor=FARBEN["kopf"])
        zelle.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )

        blatt.column_dimensions[get_column_letter(nummer)].width = breite

    blatt.row_dimensions[zeile].height = 28


def _rahmen():

    duenn = Side(style="thin", color="D0D0D0")

    return Border(left=duenn, right=duenn, top=duenn, bottom=duenn)


def _anleitung(mappe):

    blatt = mappe.create_sheet("Anleitung")

    blatt.column_dimensions["A"].width = 26
    blatt.column_dimensions["B"].width = 92

    zeilen = [
        ("KiG POS - Prüfkatalog", ""),
        ("", ""),
        ("Wozu", "Jede Funktion einmal bewusst ausprobieren und "
                 "festhalten, was dabei herauskam."),
        ("Aufbau", "Ein Blatt je Bereich. Je Zeile eine Funktion, je "
                   "Gerät eine Spalte."),
        ("", ""),
        ("Geräte", "Rechner = Windows, Tablet = Boox Go 10.3."),
        ("Strich (entfällt)", "Die Funktion gibt es auf diesem Gerät "
                              "nicht - dort ist nichts zu prüfen."),
        ("", ""),
        ("Zustände", "offen - noch nicht geprüft"),
        ("", "OK - tut, was danebensteht"),
        ("", "Fehler - tut es nicht"),
        ("", "Teilweise - tut es, aber nicht ganz"),
        ("", "entfällt - kommt auf diesem Gerät nicht vor"),
        ("", ""),
        ("Kommentar", "Was aufgefallen ist. Bei \"Fehler\" bitte so "
                      "genau wie möglich: Was hast du getan, was "
                      "passierte, was hattest du erwartet?"),
        ("", ""),
        ("Übersicht", "Das zweite Blatt zählt automatisch zusammen, "
                      "wie weit du bist."),
        ("", ""),
        ("Neu erzeugen", "werkzeuge/pruefkatalog.py - erzeugt diese "
                         "Mappe neu, wenn Funktionen dazukommen. "
                         "Achtung: Kommentare gehen dabei verloren, "
                         "also vorher sichern."),
    ]

    for nummer, (links, rechts) in enumerate(zeilen, start=1):

        a = blatt.cell(row=nummer, column=1, value=links)
        b = blatt.cell(row=nummer, column=2, value=rechts)

        a.font = Font(bold=True, size=14 if nummer == 1 else 11,
                      color=FARBEN["kopf"] if nummer == 1 else "000000")
        b.alignment = Alignment(vertical="top", wrap_text=True)

    return blatt


def _altbestand(ziel):
    """Liest Ergebnisse und Kommentare aus einer vorhandenen Mappe.

    Ergebnis: {(Bereich, Funktion): ([Rechner, Tablet],
    Kommentar)}. Fehlt die Datei oder laesst sie sich nicht lesen,
    bleibt das Ergebnis leer - dann entsteht eben eine frische Mappe.
    """

    ziel = Path(ziel)

    if not ziel.exists():
        return {}

    try:
        from openpyxl import load_workbook

        mappe = load_workbook(ziel, data_only=True)

    except Exception as fehler:                      # pragma: no cover
        print(f"   (vorhandene Mappe nicht lesbar: {fehler})")
        return {}

    bestand = {}

    for name in mappe.sheetnames:

        if name in ("Anleitung", "Übersicht"):
            continue

        blatt = mappe[name]

        for zeile in blatt.iter_rows(min_row=2):

            werte = [zelle.value for zelle in zeile]

            if len(werte) < 8 or not werte[1]:
                continue

            funktion = str(werte[1]).strip()

            zustaende = [
                str(wert).strip() if wert else ""
                for wert in werte[4:7]
            ]

            kommentar = str(werte[7]).strip() if werte[7] else ""

            bestand[(name, funktion)] = (zustaende, kommentar)

    mappe.close()

    return bestand


def _uebernehmen(bestand, bereich, funktion):
    """Was fuer diese Funktion schon eingetragen war.

    Liefert (Zustaende, Kommentar). Zustaende ist None, wenn die
    Funktion sich geaendert hat und deshalb neu angesehen werden will.
    """

    schluessel = (bereich, funktion)

    # Alte Namen mitnehmen
    for alt, neu in UMBENANNT.items():

        if neu == schluessel and alt in bestand:

            _zustaende, kommentar = bestand[alt]

            return None, kommentar

    if schluessel not in bestand:
        return None, ""

    zustaende, kommentar = bestand[schluessel]

    if schluessel in GEAENDERT:
        return None, kommentar

    return zustaende, kommentar


def _bereichsblatt(mappe, bereich, eintraege, pruefliste, bestand):

    blatt = mappe.create_sheet(bereich[:31])

    spalten = [
        ("Nr", 5),
        ("Funktion", 34),
        ("Wo zu finden", 34),
        ("Erwartetes Verhalten", 52),
    ]

    spalten += [(geraet, 12) for geraet in GERAETE]
    spalten += [("Kommentar", 46)]

    _kopfzeile(blatt, spalten)

    rahmen = _rahmen()

    for nummer, (funktion, wo, erwartet, geraete) in enumerate(
            eintraege, start=1
    ):

        zeile = nummer + 1

        werte = [nummer, funktion, wo, erwartet]

        alte_zustaende, alter_kommentar = _uebernehmen(
            bestand, bereich, funktion
        )

        for stelle, (kuerzel, geraet) in enumerate(zip("RTH", GERAETE)):

            if kuerzel not in geraete:
                werte.append(NICHT)
                continue

            frueher = (
                alte_zustaende[stelle] if alte_zustaende else ""
            )

            # "entfällt" von frueher gilt nicht mehr, wenn es die
            # Funktion auf dem Geraet inzwischen gibt.
            if frueher in ("", NICHT):
                werte.append("offen")
            else:
                werte.append(frueher)

        werte.append(alter_kommentar)

        for spalte, wert in enumerate(werte, start=1):

            zelle = blatt.cell(row=zeile, column=spalte, value=wert)

            zelle.border = rahmen
            zelle.alignment = Alignment(
                vertical="top",
                wrap_text=spalte in (2, 3, 4, 8),
                horizontal="center" if spalte in (1, 5, 6, 7) else "left",
            )

        blatt.row_dimensions[zeile].height = 30

        pruefliste.append((bereich, funktion, geraete))

    letzte = len(eintraege) + 1

    # Auswahlliste in den Gerätespalten
    pruefung = DataValidation(
        type="list",
        formula1='"' + ",".join(ZUSTAENDE) + '"',
        allow_blank=True,
        showDropDown=False,
    )
    blatt.add_data_validation(pruefung)

    for spalte in range(5, 5 + len(GERAETE)):

        buchstabe = get_column_letter(spalte)

        pruefung.add(f"{buchstabe}2:{buchstabe}{letzte}")

        bereich_text = f"{buchstabe}2:{buchstabe}{letzte}"

        for zustand, farbe in (
            ("OK", FARBEN["ok"]),
            ("Fehler", FARBEN["fehler"]),
            ("Teilweise", FARBEN["teilweise"]),
            (NICHT, FARBEN["entfaellt"]),
        ):
            blatt.conditional_formatting.add(
                bereich_text,
                CellIsRule(
                    operator="equal",
                    formula=[f'"{zustand}"'],
                    fill=PatternFill("solid", fgColor=farbe),
                ),
            )

    blatt.freeze_panes = "B2"
    blatt.auto_filter.ref = f"A1:H{letzte}"

    return blatt


def _uebersicht(mappe, bereiche):
    """Zählt je Bereich und Gerät zusammen - mit Formeln, damit sich
    die Zahlen beim Ausfüllen mitbewegen."""

    blatt = mappe.create_sheet("Übersicht", 1)

    spalten = [("Bereich", 26), ("Funktionen", 12)]

    for geraet in GERAETE:
        spalten += [
            (f"{geraet}: OK", 13),
            (f"{geraet}: Fehler", 14),
            (f"{geraet}: offen", 13),
        ]

    _kopfzeile(blatt, spalten)

    rahmen = _rahmen()

    for nummer, (bereich, anzahl) in enumerate(bereiche, start=1):

        zeile = nummer + 1

        blattname = f"'{bereich[:31]}'"

        werte = [bereich, anzahl]

        for spalte in ("E", "F", "G"):

            bezug = f"{blattname}!{spalte}2:{spalte}{anzahl + 1}"

            werte += [
                f'=COUNTIF({bezug},"OK")',
                f'=COUNTIF({bezug},"Fehler")',
                f'=COUNTIF({bezug},"offen")',
            ]

        for spalte, wert in enumerate(werte, start=1):

            zelle = blatt.cell(row=zeile, column=spalte, value=wert)
            zelle.border = rahmen
            zelle.alignment = Alignment(
                horizontal="left" if spalte == 1 else "center"
            )

    # Summenzeile
    summe = len(bereiche) + 2

    blatt.cell(row=summe, column=1, value="Zusammen").font = Font(bold=True)

    for spalte in range(2, 2 + 1 + 3 * len(GERAETE)):

        buchstabe = get_column_letter(spalte)

        zelle = blatt.cell(
            row=summe, column=spalte,
            value=f"=SUM({buchstabe}2:{buchstabe}{len(bereiche) + 1})",
        )
        zelle.font = Font(bold=True)
        zelle.fill = PatternFill("solid", fgColor=FARBEN["bereich"])
        zelle.alignment = Alignment(horizontal="center")

    blatt.freeze_panes = "B2"

    return blatt


def erzeugen(ziel):

    # Was schon geprueft und kommentiert wurde, bleibt erhalten.
    bestand = _altbestand(ziel)

    mappe = Workbook()
    mappe.remove(mappe.active)

    _anleitung(mappe)

    pruefliste = []
    bereiche = []

    for bereich, eintraege in KATALOG:

        _bereichsblatt(mappe, bereich, eintraege, pruefliste, bestand)

        bereiche.append((bereich, len(eintraege)))

    _uebersicht(mappe, bereiche)

    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)

    try:
        mappe.save(ziel)

    except PermissionError:

        # Excel haelt die Datei offen. Statt die Arbeit wegzuwerfen,
        # daneben ablegen - der Name sagt, was zu tun ist.
        ausweich = ziel.with_name(f"{ziel.stem}_NEU{ziel.suffix}")

        mappe.save(ausweich)

        print(f"   {ziel.name} ist geöffnet - neu geschrieben nach "
              f"{ausweich.name}")

        ziel = ausweich

    return ziel, pruefliste, bestand


def main():

    if len(sys.argv) > 1:
        ziel = Path(sys.argv[1])
    else:
        ziel = config.EXPORT_EXCEL_DIR / "KiG_POS_Pruefkatalog.xlsx"

    ziel, pruefliste, bestand = erzeugen(ziel)

    gesamt = len(pruefliste)

    einzelpruefungen = sum(len(g) for _b, _f, g in pruefliste)

    print(f"{ziel}")
    print(f"{len(KATALOG)} Bereiche, {gesamt} Funktionen, "
          f"{einzelpruefungen} Einzelprüfungen")

    if bestand:

        namen = {(b, f) for b, f, _g in pruefliste}

        wieder = len(namen & set(bestand))
        neu = len(namen - set(bestand))
        weg = len(set(bestand) - namen)

        print(f"Aus der bisherigen Mappe übernommen: {wieder} Funktionen, "
              f"{neu} neu, {weg} entfallen")

    for bereich, eintraege in KATALOG:
        print(f"   {bereich:22s} {len(eintraege):3d}")


if __name__ == "__main__":
    main()
