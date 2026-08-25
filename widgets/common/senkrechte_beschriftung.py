"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/senkrechte_beschriftung.py

Beschreibung:
    Eine um 90 Grad gedrehte Beschriftung.

    Gedacht als Beschriftung neben einer Gruppe statt über
    ihr: Waagerecht kostet eine Überschrift eine ganze
    Zeile Höhe, senkrecht nur einen schmalen Streifen
    Breite - und Höhe ist auf dem Tablet das knappere Gut.

    Gelesen wird von unten nach oben, wie auf einem
    Buchrücken.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import PopMatrix, PushMatrix, Rotate
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import theme


class SenkrechteBeschriftung(Widget):
    """Beschriftung, die hochkant neben ihrem Inhalt steht."""

    def __init__(
            self,
            text="",
            font_size=16,
            bold=True,
            color=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.label = Label(
            text=text,
            font_size=f"{font_size}sp",
            bold=bold,
            color=color if color is not None else theme.TEXT_SECONDARY,
            halign="center",
            valign="middle",
        )

        # Gedreht wird der gesamte Zeichenvorgang dieses Widgets: Das
        # Label selbst bleibt ein gewöhnliches, waagerechtes Label -
        # nur die Fläche, auf die es gezeichnet wird, ist gedreht.
        with self.canvas.before:
            PushMatrix()
            self.drehung = Rotate(angle=90, origin=self.center)

        with self.canvas.after:
            PopMatrix()

        self.add_widget(self.label)

        self.bind(pos=self._nachfuehren, size=self._nachfuehren)

        self._nachfuehren()

    # =====================================================

    def _nachfuehren(self, *_args):

        self.drehung.origin = self.center

        # Vertauscht, weil gedreht: Was für das Label Breite ist,
        # erscheint auf dem Bildschirm als Höhe.
        self.label.size = (self.height, self.width)
        self.label.text_size = self.label.size
        self.label.center = self.center

    # =====================================================

    def set_text(self, text):

        self.label.text = text

    @property
    def text(self):

        return self.label.text
