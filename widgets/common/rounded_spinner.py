from kivy.properties import BooleanProperty, ColorProperty
from kivy.uix.spinner import Spinner, SpinnerOption

import theme

from widgets.common.feld import Feldflaeche, schrift_setzen
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
        theme.INPUT_TEXT
    )

    locked = BooleanProperty(False)

    def __init__(self, **kwargs):

        kwargs.setdefault("text_color", theme.INPUT_TEXT)

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

        # Gewicht und Farbe wie in jedem anderen Feld, die Groesse aus
        # dem Thema - es sei denn, der Aufrufer nennt eine eigene.
        schrift_setzen(self)

        if "font_size" in kwargs:
            self.font_size = kwargs["font_size"]

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

        self.flaeche = Feldflaeche(self)

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
