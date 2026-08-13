"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/confirm_popup.py

Beschreibung:
    Sicherheitsabfrage vor Aktionen, die sich nicht ohne
    Weiteres rückgängig machen lassen (löschen, beenden).

    Bewusst an einer Stelle, damit alle Rückfragen der
    Anwendung gleich aussehen und sich gleich verhalten:
    Abbrechen steht links und ist die harmlose Wahl, die
    bestätigende Schaltfläche rechts und farblich betont.

Version:
    1.0.0
=========================================================
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import theme


class ConfirmPopup(Popup):

    def __init__(
            self,
            message,
            on_confirm,
            title="Bitte bestätigen",
            confirm_text="Löschen",
            confirm_color=None,
            **kwargs
    ):
        super().__init__(**kwargs)

        self.title = title
        self.on_confirm = on_confirm

        self.size_hint = (0.45, None)
        self.height = dp(200)

        # Kein Wegtippen daneben: eine Rückfrage soll bewusst
        # beantwortet werden.
        self.auto_dismiss = False

        content = BoxLayout(
            orientation="vertical",
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.CARD_SPACING),
        )

        with content.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_background, size=self._update_background)

        text_label = Label(
            text=message, color=theme.TEXT_PRIMARY, font_size="16sp",
            halign="center", valign="middle",
        )
        text_label.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        content.add_widget(text_label)

        buttons = BoxLayout(
            size_hint_y=None, height=dp(52), spacing=dp(theme.ROW_SPACING)
        )
        buttons.add_widget(self._button(
            "Abbrechen", theme.SURFACE, theme.TEXT_PRIMARY, self.dismiss
        ))
        buttons.add_widget(self._button(
            confirm_text,
            confirm_color if confirm_color else theme.ERROR,
            theme.TEXT_WHITE,
            self._confirmed,
        ))
        content.add_widget(buttons)

        self.content = content

    @staticmethod
    def _button(text, background_color, text_color, callback):

        button = Button(
            text=text, background_normal="", background_down="",
            background_color=background_color, color=text_color,
            font_size="15sp", bold=True,
        )
        button.bind(on_release=lambda *_args: callback())
        return button

    def _confirmed(self):

        # Erst schließen, dann handeln - sonst bliebe der Dialog bei
        # einer Aktion stehen, die den Bildschirm wechselt oder das
        # Programm beendet.
        self.dismiss()

        if callable(self.on_confirm):
            self.on_confirm()

    def _update_background(self, instance, _value):

        self._background.pos = instance.pos
        self._background.size = instance.size
