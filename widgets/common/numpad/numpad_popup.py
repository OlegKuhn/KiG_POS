"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/numpad/numpad_popup.py

Beschreibung:
    Der Nummernblock als eigenständiger Dialog.

    In der Kasse und in der Artikelverwaltung schiebt sich
    der Nummernblock als Panel in die Oberfläche. Wo dafür
    kein Platz vorgesehen ist - etwa im Kassenbuch, das
    seine Beträge in einem schmalen Eingabefeld sammelt -,
    tut es ein Dialog.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.common.kig_popup import KiGPopup
from widgets.common.numpad.numpad_panel import NumpadPanel


class NumpadPopup(KiGPopup):

    def __init__(
            self,
            on_confirm,
            title="Betrag",
            value=0,
            mode="price",
            **kwargs
    ):
        super().__init__(**kwargs)

        self.on_confirm = on_confirm

        self.title = title
        self.size_hint = (None, None)
        self.size = (dp(theme.NUMPAD_PANEL_WIDTH + 50), dp(560))
        self.auto_dismiss = False

        root = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
        )

        with root.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_background, size=self._update_background)

        self.numpad = NumpadPanel()
        root.add_widget(self.numpad)

        self.content = root

        self.numpad.open(
            value=value,
            mode=mode,
            confirm_callback=self._confirmed,
            cancel_callback=self.dismiss,
        )

    def _update_background(self, instance, _value):
        self._background.pos = instance.pos
        self._background.size = instance.size

    def _confirmed(self, wert):

        self.dismiss()

        if callable(self.on_confirm):
            self.on_confirm(wert)
