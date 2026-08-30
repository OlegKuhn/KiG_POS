"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/schreibschutz.py

Beschreibung:
    Was ein Nebengerät nicht darf - schon in der Bedienung.

    Der eigentliche Schutz sitzt tiefer, am Datenbankcursor
    (database.NurAnsichtCursor). Der ist verlässlich, aber
    er meldet sich erst, wenn es zu spät ist: Man hat den
    Preis schon eingetippt und auf "Speichern" gedrückt.
    Genau so ist es passiert - und weil die Ausnahme aus
    einem Tastendruck heraus flog, blieb die Anwendung
    stehen.

    Hier wird deshalb vorher gesperrt: Wer die Kasse nicht
    hat, sieht die betroffenen Schaltflächen ausgegraut und
    daneben den Grund. Kein Weg führt mehr in eine Meldung,
    die nichts mehr retten kann.

    Gesperrt gehört genau das, was die Datenbank ablehnt -
    nachgemessen, nicht geraten:

        Artikel anlegen, ändern, löschen
        Wareneingang buchen (er schreibt den Einkaufspreis)
        Kategorien anlegen und umbenennen
        Sortierung ändern

    Erlaubt bleibt, was zusammengeführt werden kann:
    verkaufen, Bestand korrigieren, Bestellmengen notieren,
    Kassenbuch, Checklisten, Schichten.

Version:
    1.0.0
=========================================================
"""

import theme


HINWEIS = (
    "Nur Ansicht: Artikel, Preise und Kategorien gehören dem "
    "Hauptgerät."
)


def nur_ansicht() -> bool:
    """True, wenn die Kasse gerade einem anderen Gerät gehört."""

    try:
        from database import DatabaseManager

        return bool(DatabaseManager().nur_ansicht)

    except Exception:
        # Ohne Datenbank (Werkzeuge, Tests) gibt es nichts zu schützen.
        return False


def sperren(*widgets):
    """Schaltet Bedienelemente ab und nimmt ihnen die Signalfarbe.

    Ein oranger Knopf, der nichts tut, sieht aus wie ein Fehler.
    """

    for widget in widgets:

        if widget is None:
            continue

        widget.disabled = True

        if hasattr(widget, "background_color"):
            widget.background_color = theme.SURFACE

        if hasattr(widget, "color"):
            widget.color = theme.TEXT_SECONDARY


def sperren_wenn_noetig(*widgets):
    """Sperrt nur auf einem Nebengerät. Liefert, ob gesperrt wurde."""

    if not nur_ansicht():
        return False

    sperren(*widgets)

    return True
