from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import BooleanProperty, ColorProperty
from kivy.uix.spinner import Spinner, SpinnerOption

import theme

from widgets.common.feldausrichtung import links_ausrichten


class RoundedSpinnerOption(SpinnerOption):
    """
    Eintrag innerhalb der aufgeklappten Spinner-Liste.
    """

    # Wird von __init__() bei jeder neuen Instanz aktuell gesetzt -
    # als Klassenattribut eingefroren würde dieser Default spätere
    # theme.set_mode()-Wechsel nicht mehr mitbekommen.
    option_text_color = ColorProperty(
        theme.TEXT_PRIMARY
    )

    def __init__(self, **kwargs):

        kwargs.setdefault("option_text_color", theme.TEXT_PRIMARY)

        super().__init__(**kwargs)

        self.color = self.option_text_color

        self.background_normal = ""
        self.background_down = ""

        self.background_color = theme.SURFACE

        # Auch die Eintraege im aufgeklappten Menue stehen links -
        # sonst springt der Text beim Aufklappen an eine andere Stelle.
        links_ausrichten(self)

        self.bind(
            option_text_color=self._update_text_color
        )

    def _update_text_color(self, instance, color):
        self.color = color


class RoundedSpinner(Spinner):
    """
    Kategorieauswahl im selben Feldstil
    wie die Texteingaben.
    """

    # Wird von __init__() bei jeder neuen Instanz aktuell gesetzt -
    # als Klassenattribut eingefroren würde dieser Default spätere
    # theme.set_mode()-Wechsel nicht mehr mitbekommen.
    text_color = ColorProperty(
        theme.TEXT_PRIMARY
    )

    locked = BooleanProperty(False)

    def __init__(self, **kwargs):

        kwargs.setdefault("text_color", theme.TEXT_PRIMARY)

        super().__init__(**kwargs)

        # -------------------------------------------------
        # Standard-Hintergrund deaktivieren
        # -------------------------------------------------

        self.background_normal = ""
        self.background_down = ""

        self.background_color = (
            0,
            0,
            0,
            0
        )

        # -------------------------------------------------
        # Schrift
        # -------------------------------------------------

        self.color = self.text_color

        links_ausrichten(self)

        self.bind(
            text_color=self._update_text_color
        )

        # -------------------------------------------------
        # Dropdown-Klasse
        # -------------------------------------------------

        self.option_cls = RoundedSpinnerOption

        # -------------------------------------------------
        # Eigener Hintergrund
        # -------------------------------------------------

        with self.canvas.before:

            Color(
                *theme.SURFACE
            )

            self.field_background = RoundedRectangle(
                radius=[
                    theme.INPUT_RADIUS
                ]
            )

            Color(
                *theme.BORDER_COLOR
            )

            self.field_border = Line(
                width=theme.BORDER_WIDTH
            )

        # -------------------------------------------------
        # Bindings
        # -------------------------------------------------

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

    # =====================================================
    # Darstellung
    # =====================================================

    def _update_canvas(self, *_args):

        self.field_background.pos = self.pos
        self.field_background.size = self.size

        self.field_border.rounded_rectangle = (
            *self.pos,
            *self.size,
            theme.INPUT_RADIUS
        )

    # =====================================================
    # Textfarbe
    # =====================================================

    def _update_text_color(
            self,
            instance,
            color
    ):

        self.color = color

    def on_touch_down(self, touch):
        if self.locked and self.collide_point(*touch.pos):
            return True
        return super().on_touch_down(touch)

    # =====================================================
    # Dropdown
    # =====================================================

    def _update_dropdown(self, *args):
        """
        Baut das Dropdown auf und überträgt dabei
        die Textfarbe auf alle Kategorieeinträge.
        """

        super()._update_dropdown(*args)

        if self._dropdown is None:
            return

        for option in self._dropdown.container.children:

            if isinstance(
                    option,
                    RoundedSpinnerOption
            ):

                option.option_text_color = (
                    self.text_color
                )
