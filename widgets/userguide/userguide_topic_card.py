"""Ein Thema in der Themenliste des Handbuchs - als Register.

Bis hierher war es eine flache Schaltflaeche in Kartenfarbe: ohne
Rand, ohne Rundung, gewaehlt einfach ganz orange. Neben den Reitern
der Ertraege ("Kassenbuch" / "Statistik") sah dieselbe Auswahl damit
aus wie zwei verschiedene Programme.

Jetzt dasselbe Register wie dort (widgets/cash/design.SectionButton):
abgerundet, mit leicht getoenter Flaeche und Rand, gewaehlt in der
Bereichsfarbe. Das Handbuch traegt Blau - dieselbe Farbe, die auch
seine Kachel in der Kopfzeile unterstreicht (siehe
widgets/common/design_navigation.py).
"""

from kivy.metrics import dp

import theme

from widgets.cash.design import SectionButton


class UserguideTopicCard(SectionButton):

    # Bereichsfarbe des Handbuchs
    TONE = "blue"

    HOEHE = 56

    def __init__(self, topic, callback=None, **kwargs):

        self.topic = topic
        self.callback = callback

        super().__init__(
            tone=self.TONE,
            text=topic["title"],
            font_size="18sp",
            bold=True,
            **kwargs
        )

        self.size_hint = (1, None)
        self.height = dp(self.HOEHE)

        # Linksbuendig wie eine Zeile in einer Liste - die Reiter der
        # Ertraege stehen mittig, weil dort nur zwei nebeneinander
        # liegen; hier sind es zehn untereinander.
        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(theme.CARD_PADDING), 0)

        self.bind(size=self._update_text_size)
        self._update_text_size()

    def _update_text_size(self, *_args):

        self.text_size = (
            self.width - 2 * dp(theme.CARD_PADDING),
            self.height
        )

    # Die Themenliste schaltet mit select()/unselect() um; das
    # Register selbst kennt nur select(aktiv).
    def select(self, active=True):
        super().select(active)

    def unselect(self):
        super().select(False)

    def on_release(self):

        if callable(self.callback):
            self.callback(self, self.topic)
