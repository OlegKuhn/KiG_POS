from kivy.animation import Animation
from kivy.graphics import (
    Color,
    RoundedRectangle,
    Line
)
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ObjectProperty
)
from kivy.uix.behaviors import ButtonBehavior

from kivy.metrics import dp

import theme

from widgets.kig_widget import KiGWidget


class KiGTile(ButtonBehavior, KiGWidget):
    """
    Basisklasse für alle KiG-Kacheln.
    """

    callback = ObjectProperty(
        None,
        allownone=True
    )

    selected = BooleanProperty(False)

    # Wird von __init__() bei jeder neuen Instanz aktuell gesetzt -
    # als Klassenattribut eingefroren würde dieser Default spätere
    # theme.set_mode()-Wechsel nicht mehr mitbekommen (die Kachel
    # bliebe in jedem Modus weiß, während ihr Text korrekt der
    # aktuellen Textfarbe folgt - im Dunkelmodus dann helle Schrift
    # auf weißem Grund).
    background_color = ColorProperty(
        (1, 1, 1, 1)
    )

    WIDTH = 260
    HEIGHT = 180

    RADIUS = 15
    BORDER_WIDTH = 1

    def __init__(self, **kwargs):

        kwargs.setdefault("background_color", theme.CARD)

        super().__init__(**kwargs)

        # Farbe, zu der die Kachel nach einem Tipp zurückkehrt und die
        # beim Abwählen wieder gilt. Normalerweise die Kartenfarbe -
        # abweichend z. B. bei ausverkauften Artikeln, die grau
        # bleiben sollen (siehe widgets/cash/article_tile.py).
        self.normal_color = kwargs["background_color"]

        # =====================================================
        # WICHTIG:
        # Ursprüngliches Größenverhalten beibehalten
        # =====================================================

        self.size_hint = (None, None)

        # dp: Die Kachel soll auf jedem Geraet gleich GROSS sein, nicht
        # gleich viele Bildpunkte breit. Ohne diese Umrechnung waere sie
        # auf einem 300-dpi-Geraet halb so gross wie am Rechner (siehe
        # theme.py, Abschnitt GROESSEN).
        self.size = (
            dp(self.WIDTH),
            dp(self.HEIGHT)
        )

        # ButtonBehavior
        self.always_release = False

        # =====================================================
        # Canvas
        # =====================================================

        with self.canvas.before:

            self.bg_color = Color(
                *self.background_color
            )

            self.bg = RoundedRectangle(
                radius=[self.RADIUS]
            )

            Color(
                *theme.HEADER_SEPARATOR
            )

            self.border = Line(
                width=self.BORDER_WIDTH
            )

        self.bind(
            pos=self._update_graphics,
            size=self._update_graphics
        )

        self.bind(
            background_color=
            self._update_background_color
        )

    # =====================================================
    # Animation
    # =====================================================

    def animate_press(self):

        Animation.cancel_all(
            self,
            "background_color"
        )

        normal_color = (
            theme.PRIMARY_ORANGE
            if self.selected
            else self.normal_color
        )

        (
            Animation(
                background_color=
                theme.TILE_PRESS_COLOR,
                duration=0.06
            )
            +
            Animation(
                background_color=
                normal_color,
                duration=0.08
            )
        ).start(self)

    # =====================================================
    # Darstellung
    # =====================================================

    def _update_background_color(
            self,
            instance,
            value
    ):

        self.bg_color.rgba = value

    def _update_graphics(self, *args):

        self.bg.pos = self.pos
        self.bg.size = self.size

        self.border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.RADIUS
        )

    # =====================================================
    # Callback
    # =====================================================

    def set_callback(self, callback):

        self.callback = callback

    def _dispatch_callback(self):

        if callable(self.callback):

            data = getattr(
                self,
                "data",
                None
            )

            self.callback(
                self,
                data
            )

    # =====================================================
    # Auswahl
    # =====================================================

    def select(self):

        Animation.cancel_all(
            self,
            "background_color"
        )

        self.selected = True

        self.background_color = (
            theme.PRIMARY_ORANGE
        )

    def unselect(self):

        Animation.cancel_all(
            self,
            "background_color"
        )

        self.selected = False

        self.background_color = self.normal_color

    # =====================================================
    # Sichtbarkeit
    # =====================================================

    def show(self):

        self.opacity = 1
        self.disabled = False

    def hide(self):

        self.opacity = 0
        self.disabled = True

    # =====================================================
    # Aktivieren / Deaktivieren
    # =====================================================

    def enable(self):

        self.disabled = False
        self.opacity = 1

    def disable(self):

        self.disabled = True
        self.opacity = 0.45

    # =====================================================
    # Button
    # =====================================================

    def on_press(self):

        self.animate_press()

    def on_release(self):

        pass

    # =====================================================
    # String
    # =====================================================

    def __repr__(self):

        return (
            f"{self.__class__.__name__}()"
        )