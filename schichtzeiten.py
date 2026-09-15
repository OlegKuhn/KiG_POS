"""
=========================================================
KiG POS
=========================================================

Datei:
    schichtzeiten.py

Beschreibung:
    Rechnen mit den Zeiten des Schichtplans - ohne Oberfläche,
    damit Bildschirm, Excel und PDF dasselbe Ergebnis haben.

    Die Zeiten stehen als freier Text in der Datenbank, so wie
    sie eingetippt wurden: "18:00", "18", "18.30", "1830". Hier
    werden sie zu Minuten ab Mitternacht.

    Eine Schicht, die vor ihrem Beginn endet, geht über
    Mitternacht: 22:00 bis 02:00 sind 4 Stunden, nicht minus 20.
    "24:00" ist Mitternacht am Ende des Tages.

    Wie bei den Verkäufen wechselt der Tag um 6 Uhr: Eine Schicht
    um 02:00 gehört zur Nacht der Veranstaltung, nicht an den
    Morgen davor. Sonst stünde der Abbau um zwei Uhr in der Matrix
    vor dem Aufbau um vier Uhr nachmittags.

        zeitraum("21:00", "02:00")    -> (1260, 1560)
        ueberschneidungen(schichten)  -> wer wo doppelt steht
        passt_zu(schicht, "an")       -> Anna, Jana, Stefan ...

Version:
    1.0.0
=========================================================
"""

import re

TAG = 24 * 60

# Vor dieser Uhrzeit zählt eine Schicht zur Nacht davor (siehe oben).
TAGESWECHSEL = 6 * 60


def minuten(text):
    """ "18:30" -> 1110; None, wenn sich keine Uhrzeit lesen lässt."""

    if text is None:
        return None

    text = str(text).strip().lower().replace("uhr", "").strip()

    if not text:
        return None

    treffer = re.fullmatch(r"(\d{1,2})(?:[:.,h](\d{1,2}))?", text)

    if treffer is None:
        # "1830" ohne Trennzeichen
        treffer = re.fullmatch(r"(\d{1,2})(\d{2})", text)

    if treffer is None:
        return None

    stunde = int(treffer.group(1))
    minute = int(treffer.group(2) or 0)

    if minute >= 60 or stunde > 24 or (stunde == 24 and minute):
        return None

    return stunde * 60 + minute


def zeitraum(beginn, ende):
    """(von, bis) in Minuten - oder None, wenn eine Zeit fehlt.

    Endet die Schicht vor (oder mit) ihrem Beginn, geht sie über
    Mitternacht; "bis" liegt dann am nächsten Tag.
    """

    von = minuten(beginn)
    bis = minuten(ende)

    if von is None or bis is None:
        return None

    if von < TAGESWECHSEL:
        von += TAG

    if bis < TAGESWECHSEL:
        bis += TAG

    if bis <= von:
        bis += TAG

    return von, bis


def uhrzeit(minuten_wert):
    """1560 -> "02:00" (über Mitternacht wieder ab null)."""

    minuten_wert = int(minuten_wert) % TAG

    return f"{minuten_wert // 60:02d}:{minuten_wert % 60:02d}"


def spanne_text(beginn, ende):
    """ "18:00–21:00" in einheitlicher Schreibweise."""

    bereich = zeitraum(beginn, ende)

    if bereich is None:
        teile = [t for t in (beginn, ende) if t]
        return "–".join(teile) if teile else "ohne Uhrzeit"

    # Ein Ende genau um Mitternacht heisst "24:00" - "18:00–00:00"
    # liest sich, als ende die Schicht vor ihrem Beginn.
    ende_text = "24:00" if bereich[1] == TAG else uhrzeit(bereich[1])

    return f"{uhrzeit(bereich[0])}–{ende_text}"


def name_schluessel(name):
    """ "  anna " und "Anna" sind derselbe Helfer."""

    return " ".join((name or "").split()).casefold()


def ueberschneiden_sich(a, b):
    """Zwei Zeiträume (von, bis) teilen sich mindestens eine Minute.

    18:00–21:00 und 21:00–24:00 überschneiden sich NICHT: Wer um neun
    an der Theke aufhört, kann um neun am Grill anfangen.
    """

    return a[0] < b[1] and b[0] < a[1]


def ueberschneidungen(schichten):
    """Helfer, die zur selben Zeit in zwei Schichten stehen.

    schichten: Wörterbücher mit id, task, start_time, end_time und
    helfer (Liste der Namen).

    Liefert eine Liste aus Wörterbüchern

        name      wie er in der ersten Schicht steht
        schichten die beiden Schichten (Wörterbücher wie oben)

    - je Paar ein Eintrag. Schichten ohne lesbare Uhrzeit bleiben
    außen vor: Ob sie sich überschneiden, lässt sich nicht sagen.
    """

    je_name = {}

    for schicht in schichten:

        bereich = zeitraum(schicht.get("start_time"), schicht.get("end_time"))

        if bereich is None:
            continue

        for name in schicht.get("helfer") or ():
            je_name.setdefault(name_schluessel(name), []).append(
                (" ".join(name.split()), bereich, schicht)
            )

    gefunden = []

    for eintraege in je_name.values():

        for i, (name, bereich_a, schicht_a) in enumerate(eintraege):

            for _name_b, bereich_b, schicht_b in eintraege[i + 1:]:

                if schicht_a["id"] == schicht_b["id"]:
                    continue

                if ueberschneiden_sich(bereich_a, bereich_b):
                    gefunden.append({
                        "name": name,
                        "schichten": (schicht_a, schicht_b),
                    })

    return gefunden


def konflikte_je_schicht(schichten):
    """{schicht_id: {name_schluessel, ...}} - wer in welcher Schicht
    doppelt steht. Für die Einfärbung in der Zeile."""

    ergebnis = {}

    for treffer in ueberschneidungen(schichten):
        for schicht in treffer["schichten"]:
            ergebnis.setdefault(schicht["id"], set()).add(
                name_schluessel(treffer["name"])
            )

    return ergebnis


def konflikt_text(treffer):
    """ "Anna: Theke 18:00–21:00 und Grill 20:00–22:00"."""

    a, b = treffer["schichten"]

    return (
        f"{treffer['name']}: "
        f"{a.get('task') or 'Schicht'} {spanne_text(a.get('start_time'), a.get('end_time'))}"
        f" und "
        f"{b.get('task') or 'Schicht'} {spanne_text(b.get('start_time'), b.get('end_time'))}"
    )


def passt_zu(schicht, suchtext):
    """Steht ein Helfer in der Schicht, dessen Name den Suchtext
    enthält? Ohne Suchtext passt jede Schicht."""

    such = name_schluessel(suchtext)

    if not such:
        return True

    return any(such in name_schluessel(name) for name in schicht.get("helfer") or ())


def nach_zeit(schichten):
    """Die Schichten nach Beginn, bei gleichem Beginn nach Ende.

    Die Nacht zählt nach dem Abend (siehe TAGESWECHSEL): Abbau um
    02:00 kommt nach der Theke ab 21:00. Schichten ohne lesbare Zeit
    stehen am Ende, in ihrer bisherigen Reihenfolge.
    """

    def schluessel(eintrag):

        position, schicht = eintrag
        bereich = zeitraum(schicht.get("start_time"), schicht.get("end_time"))

        if bereich is None:
            return (1, 0, 0, position)

        return (0, bereich[0], bereich[1], position)

    return [schicht for _p, schicht in sorted(enumerate(schichten), key=schluessel)]


# =========================================================
# Matrix: Zeitachse und Bahnen
# =========================================================

def raster(schichten, schritt=None):
    """Die Zeitachse für die Matrix: (anfang, ende, schritt) in Minuten.

    Anfang und Ende liegen auf vollen Stunden; der Schritt ist 30
    Minuten, 15, wenn eine Zeit auf einer Viertelstunde liegt. None,
    wenn keine Schicht eine lesbare Zeit hat.
    """

    bereiche = [
        zeitraum(s.get("start_time"), s.get("end_time")) for s in schichten
    ]
    bereiche = [b for b in bereiche if b is not None]

    if not bereiche:
        return None

    anfang = min(b[0] for b in bereiche)
    ende = max(b[1] for b in bereiche)

    anfang = anfang // 60 * 60
    ende = -(-ende // 60) * 60

    if schritt is None:
        schritt = 30

        for von, bis in bereiche:
            if von % 30 or bis % 30:
                schritt = 15
                break

    return anfang, ende, schritt


def bahnen(schichten):
    """Ordnet die Schichten in Zeilen für die Matrix.

    Je Tätigkeit eine Zeile - in der Reihenfolge, in der die
    Tätigkeiten zum ersten Mal vorkommen; nach nach_zeit sortiert also
    die, die am frühesten beginnt, zuoberst. Liegen
    zwei Schichten derselben Tätigkeit zur selben Zeit (zwei
    Thekenschichten parallel), bekommt die zweite eine eigene Zeile
    darunter, sonst lägen die Blöcke übereinander.

    Liefert eine Liste aus (tätigkeit, [schicht, ...]); Schichten ohne
    lesbare Zeit fehlen darin (siehe ohne_zeit).
    """

    # Tätigkeit -> Liste ihrer Bahnen; die Reihenfolge der Tätigkeiten
    # ist die ihres ersten Auftretens im Plan.
    je_taetigkeit = {}
    namen = {}

    for schicht in schichten:

        bereich = zeitraum(schicht.get("start_time"), schicht.get("end_time"))

        if bereich is None:
            continue

        taetigkeit = (schicht.get("task") or "").strip() or "Schicht"
        schluessel = taetigkeit.casefold()

        namen.setdefault(schluessel, taetigkeit)
        liste_der_bahnen = je_taetigkeit.setdefault(schluessel, [])

        for bahn in liste_der_bahnen:

            frei = all(
                not ueberschneiden_sich(
                    bereich,
                    zeitraum(andere.get("start_time"), andere.get("end_time")),
                )
                for andere in bahn
            )

            if frei:
                bahn.append(schicht)
                break

        else:
            liste_der_bahnen.append([schicht])

    return [
        (namen[schluessel], bahn)
        for schluessel, liste_der_bahnen in je_taetigkeit.items()
        for bahn in liste_der_bahnen
    ]


def ohne_zeit(schichten):
    """Schichten, deren Zeit sich nicht lesen lässt."""

    return [
        s for s in schichten
        if zeitraum(s.get("start_time"), s.get("end_time")) is None
    ]
