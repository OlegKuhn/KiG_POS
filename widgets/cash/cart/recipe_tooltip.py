"""Kurzer Hinweis-Popup mit der Zusammensetzung eines Mix-/
Rezeptartikels - als Gedächtnisstütze für die Bar beim Kassieren.

Öffnet sich, wenn eine Warenkorb-Position mit Rezept angetippt wird,
und schließt sich automatisch wieder, sobald irgendwo anders
hingetippt wird (Popup.auto_dismiss, wie auch bei den übrigen Dialogen
der App, z. B. DatePickerPopup).
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

import theme


class RecipeTooltip(Popup):

    # Entwurfsgroessen; die Umrechnung in Bildpunkte passiert bei der
    # Verwendung, nicht hier (siehe adaptive_grid.py).
    MIN_HEIGHT = 160
    MAX_HEIGHT = 480

    def __init__(self, article_name, ingredient_lines, **kwargs):
        super().__init__(**kwargs)

        self.title = article_name
        self.title_size = "20sp"
        self.title_color = theme.PRIMARY_ORANGE
        self.title_align = "left"
        self.separator_color = theme.PRIMARY_ORANGE

        self.auto_dismiss = True

        self.size_hint = (None, None)
        self.width = dp(360)

        outer = BoxLayout(orientation="vertical")

        with outer.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=outer.pos, size=outer.size)
        outer.bind(pos=self._update_background, size=self._update_background)

        # Zutatenzeilen können (Menge + Einheit + Name) durchaus
        # umbrechen - sie stecken deshalb in einem scrollbaren Bereich
        # mit dynamischer Höhe statt einer festen Zeilenhöhe, damit
        # längere Zutaten nicht über den Rand der Sprechblase
        # hinausgezeichnet werden (siehe auch die anderen Karten/
        # Dialoge dieser App, die aus demselben Grund scrollen).
        lines_container = BoxLayout(
            orientation="vertical", padding=dp(theme.CARD_PADDING),
            spacing=dp(theme.ROW_SPACING), size_hint_y=None,
        )
        lines_container.bind(minimum_height=lines_container.setter("height"))

        if not ingredient_lines:
            lines_container.add_widget(self._line("Kein Rezept hinterlegt."))
        else:
            for line in ingredient_lines:
                lines_container.add_widget(self._line(line))

        scroll = ScrollView(bar_width=dp(8))
        scroll.add_widget(lines_container)
        outer.add_widget(scroll)

        self.content = outer

        # Nur eine grobe Schätzung nötig - reicht sie nicht, fängt der
        # ScrollView oben den Rest ab, statt dass etwas überläuft.
        line_count = max(1, len(ingredient_lines))
        estimated = dp(90) + line_count * dp(30)
        self.height = min(dp(self.MAX_HEIGHT), max(dp(self.MIN_HEIGHT), estimated))

    @staticmethod
    def _line(text):
        label = Label(
            text=text, color=theme.TEXT_PRIMARY, font_size="16sp",
            size_hint_y=None, halign="left", valign="middle",
        )
        label.bind(
            width=lambda instance, value: setattr(instance, "text_size", (value, None))
        )
        label.bind(
            texture_size=lambda instance, value: setattr(instance, "height", value[1] + dp(6))
        )
        return label

    def _update_background(self, instance, _value):
        self._background.pos = instance.pos
        self._background.size = instance.size
