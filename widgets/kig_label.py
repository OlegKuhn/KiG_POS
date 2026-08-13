"""
=========================================================
KiG POS
=========================================================

Datei:
    kig_label.py

Beschreibung:
    Einheitliches Label-Widget für KiG POS.

Version:
    2.0.0
=========================================================
"""

from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    OptionProperty,
)
from kivy.uix.label import Label

import theme


class KiGLabel(Label):
    """
    Einheitliches Label für die gesamte Anwendung.
    """

    # Nur als Fallback für Kivys eigenes Introspektions-Tooling
    # relevant. Da Kivy Property-Defaults einmalig beim Laden dieser
    # Klasse auswertet, würde ein hier direkt eingetragenes
    # theme.TEXT_PRIMARY spätere set_mode()-Wechsel NICHT mehr
    # mitbekommen ("eingefroren"). Deshalb setzt __init__() unten
    # den tatsächlich verwendeten Wert bei jeder neuen Instanz aktuell
    # neu, sofern er nicht explizit übergeben wurde.
    text_color = ColorProperty((0.12, 0.12, 0.12, 1))
    text_size_sp = NumericProperty(18)
    is_bold = BooleanProperty(False)

    horizontal_alignment = OptionProperty(
        "center",
        options=("left", "center", "right")
    )

    vertical_alignment = OptionProperty(
        "middle",
        options=("top", "middle", "bottom")
    )

    def __init__(self, **kwargs):

        kwargs.setdefault("text_color", theme.TEXT_PRIMARY)

        super().__init__(**kwargs)

        self.color = self.text_color
        self.bold = self.is_bold
        self.font_size = f"{self.text_size_sp}sp"

        self.bind(
            size=self._refresh,
            text=self._refresh,
            font_size=self._refresh
        )

        self._apply_alignment()
        self._refresh()

    # -------------------------------------------------

    def _apply_alignment(self):

        self.halign = self.horizontal_alignment
        self.valign = self.vertical_alignment

    # -------------------------------------------------

    def _refresh(self, *args):

        self._apply_alignment()

        self.text_size = self.size

        self.texture_update()

    # -------------------------------------------------

    def set_font_size(self, size: int):

        self.text_size_sp = size
        self.font_size = f"{size}sp"
        self._refresh()

    # -------------------------------------------------

    def set_color(self, color):

        self.text_color = color
        self.color = color

    # -------------------------------------------------

    def set_bold(self, value=True):

        self.is_bold = value
        self.bold = value

    # -------------------------------------------------

    def set_alignment(self, alignment: str):
        """
        left | center | right
        """
        if alignment not in ("left", "center", "right"):
            raise ValueError("alignment must be left, center or right")

        self.horizontal_alignment = alignment
        self._refresh()

    # -------------------------------------------------

    def set_vertical_alignment(self, alignment: str):
        """
        top | middle | bottom
        """
        if alignment not in ("top", "middle", "bottom"):
            raise ValueError(
                "vertical alignment must be top, middle or bottom"
            )

        self.vertical_alignment = alignment
        self._refresh()

    # -------------------------------------------------

    def set_text(self, text: str):

        self.text = text
        self._refresh()
