"""Eine nummerierte Anleitungs-Schritt-Karte (Überschrift, Text, optionales Bild)."""

import os

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

import config
import theme


class UserguideStepCard(BoxLayout):

    def __init__(self, number, step, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.ROW_SPACING),
            **kwargs
        )

        with self.canvas.before:
            Color(*theme.CARD)
            self._background = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(12)]
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # -------------------------------------------------
        # Überschrift mit Schrittnummer
        # -------------------------------------------------

        heading = Label(
            text=f"{number}. {step['heading']}",
            color=theme.PRIMARY_ORANGE,
            bold=True,
            font_size="19sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
        )
        heading.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.add_widget(heading)

        # -------------------------------------------------
        # Beschreibungstext
        # -------------------------------------------------

        text_label = Label(
            text=step["text"],
            color=theme.TEXT_PRIMARY,
            font_size="15sp",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        text_label.bind(
            width=lambda instance, value: setattr(
                instance, "text_size", (value, None)
            ),
            texture_size=lambda instance, value: setattr(
                instance, "height", value[1]
            ),
        )
        self.add_widget(text_label)

        # -------------------------------------------------
        # Screenshot (optional)
        # -------------------------------------------------

        image_path = step.get("image")

        if image_path:

            full_path = str(config.USERGUIDE_IMAGE_DIR / image_path)

            if os.path.isfile(full_path):

                image = Image(
                    source=full_path,
                    size_hint_y=None,
                    fit_mode="contain",
                )
                image.bind(
                    texture_size=self._update_image_height,
                    width=self._update_image_height,
                )
                self.add_widget(image)

        self.bind(minimum_height=self.setter("height"))

    def _update_canvas(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    @staticmethod
    def _update_image_height(instance, _value):
        """Skaliert den Screenshot proportional zur aktuellen Breite."""

        if not instance.texture_size[0] or not instance.width:
            return

        ratio = instance.texture_size[1] / instance.texture_size[0]
        instance.height = instance.width * ratio
