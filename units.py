"""
=========================================================
KiG POS
=========================================================

Datei:
    units.py

Beschreibung:
    Zentrale Mengeneinheiten-Logik.

    Definiert, welche Einheiten es gibt, zu welcher
    physikalischen Größe (Dimension) sie gehören, und wie
    sich Einheiten exakt ineinander umrechnen lassen.

    WICHTIG:
    Nur Einheiten derselben Dimension lassen sich umrechnen
    (z. B. ml -> l, g -> kg). Eine Umrechnung zwischen
    unterschiedlichen Dimensionen (z. B. g -> ml oder
    Stück -> g) ist ohne zusätzliche, hier nicht vorhandene
    Angaben (Dichte, Stückgewicht) grundsätzlich nicht
    eindeutig möglich und wird daher bewusst NICHT
    unterstützt - convert() liefert in diesem Fall None,
    niemals einen geratenen Wert.

Version:
    1.0.0
=========================================================
"""

import config

# Jede Einheit gehört zu genau einer Dimension und hat einen
# Umrechnungsfaktor zur "Basiseinheit" ihrer Dimension
# (ml für Volumen, g für Masse, Stück für Anzahl).

_UNIT_INFO = {

    "Stück": ("count", 1),

    "ml": ("volume", 1),
    "cl": ("volume", 10),
    "l": ("volume", 1000),

    "g": ("mass", 1),
    "kg": ("mass", 1000),

}

ALL_UNITS = tuple(_UNIT_INFO)

# "Flasche" ist bewusst NICHT Teil von _UNIT_INFO: Anders als l/ml
# oder g/kg hat eine Flasche keinen festen Umrechnungsfaktor (700 ml,
# 750 ml, 1000 ml, ...). Artikel mit dieser Einheit führen ihren
# tatsächlichen Bestand deshalb intern immer in ml (siehe
# database.py: bottle_size_ml + Umrechnung beim Wareneingang).
BOTTLE_UNIT = config.BOTTLE_UNIT


def stock_dimension_unit(article_stock_unit):
    """Liefert die für Mengenrechnung tatsächlich relevante Einheit
    eines Artikelbestands.

    Für BOTTLE_UNIT ("Flasche") ist das immer "ml", da der Bestand
    intern in ml geführt wird - jede andere Einheit wird unverändert
    durchgereicht. Damit lassen sich Flaschen-Artikel z. B. ganz
    normal als Rezeptzutat in ml/cl/l verknüpfen.
    """

    if article_stock_unit == BOTTLE_UNIT:
        return "ml"

    return article_stock_unit


def dimension(unit):
    """Liefert die physikalische Größe einer Einheit oder None,
    falls die Einheit unbekannt ist."""

    info = _UNIT_INFO.get(unit)

    return info[0] if info else None


def compatible_units(unit):
    """Liefert alle Einheiten, die sich verlustfrei in `unit`
    umrechnen lassen (inklusive `unit` selbst).

    Für eine unbekannte Einheit wird nur die Einheit selbst
    zurückgegeben, damit ein Auswahlfeld nie leer bleibt.
    """

    dim = dimension(unit)

    if dim is None:
        return (unit,) if unit else ()

    return tuple(
        candidate
        for candidate, (candidate_dim, _factor) in _UNIT_INFO.items()
        if candidate_dim == dim
    )


def convert(value, from_unit, to_unit):
    """Rechnet `value` von `from_unit` nach `to_unit` um.

    Liefert None, wenn beide Einheiten unterschiedlichen
    Dimensionen angehören oder unbekannt sind. Der Aufrufer MUSS
    diesen Fall behandeln - es darf NIEMALS stillschweigend von
    einem Umrechnungsfaktor 1 ausgegangen werden, sobald sich die
    Einheiten unterscheiden.
    """

    if from_unit == to_unit:
        return value

    from_info = _UNIT_INFO.get(from_unit)
    to_info = _UNIT_INFO.get(to_unit)

    if from_info is None or to_info is None:
        return None

    from_dimension, from_factor = from_info
    to_dimension, to_factor = to_info

    if from_dimension != to_dimension:
        return None

    base_value = value * from_factor

    return base_value / to_factor
