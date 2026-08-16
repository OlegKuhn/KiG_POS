from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.textinput import TextInput
from kivy.properties import BooleanProperty, ObjectProperty

import theme


class RoundedInput(TextInput):
    """
    Großes Eingabefeld mit abgerundeter Umrandung
    für Touchbedienung.

    kig_keyboard_mode:
        "numpad" -> öffnet den Nummernblock der Anwendung
        alles andere -> Tastatur des Systems

    Eine eigene Buchstabentastatur gibt es nicht mehr: Windows und
    Android bringen beide eine mit, und auf dem Telefon erschienen
    sonst zwei Tastaturen übereinander.
    """

    numpad_callback = ObjectProperty(
        None,
        allownone=True
    )

    # Eigener Lesemodus. Anders als ``disabled`` oder ``readonly``
    # dämpft er die Textfarbe nicht.
    locked = BooleanProperty(False)

    def __init__(
            self,
            kig_keyboard_mode="text",
            **kwargs
    ):

        super().__init__(**kwargs)

        # -------------------------------------------------
        # KiG Tastaturmodus
        # -------------------------------------------------

        self.kig_keyboard_mode = kig_keyboard_mode

        # -------------------------------------------------
        # Standard TextInput Hintergrund deaktivieren
        # -------------------------------------------------

        self.background_normal = ""
        self.background_active = ""

        self.background_color = (
            0,
            0,
            0,
            0
        )

        # -------------------------------------------------
        # Textfarben
        # -------------------------------------------------

        self.foreground_color = (
            theme.TEXT_PRIMARY
        )

        self.hint_text_color = (
            theme.TEXT_SECONDARY
        )

        # Wichtig:
        # Kivy verwendet bei disabled=True eine eigene
        # Schriftfarbe. Ohne diese Einstellung erscheint
        # der Text im gesperrten Zustand ausgegraut.

        
        self.disabled_foreground_color = (
            theme.TEXT_PRIMARY
        )

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

            self.field_border_color = Color(
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
            size=self._update_canvas,
            focus=self._update_focus
        )

    # =====================================================
    # Darstellung
    # =====================================================

    def _update_canvas(
            self,
            *_args
    ):

        self.field_background.pos = (
            self.pos
        )

        self.field_background.size = (
            self.size
        )

        self.field_border.rounded_rectangle = (
            *self.pos,
            *self.size,
            theme.INPUT_RADIUS
        )

    # =====================================================
    # Fokusdarstellung
    # =====================================================

    def _update_focus(
            self,
            _instance,
            focused
    ):
        """
        Ändert ausschließlich die Farbe des Rahmens.

        Die Tastatur wird hier ausdrücklich NICHT
        geöffnet.
        """

        self.field_border_color.rgba = (
            theme.PRIMARY_ORANGE
            if focused
            else theme.BORDER_COLOR
        )

    # =====================================================
    # Touch
    # =====================================================

    def on_touch_down(
            self,
            touch
    ):
        """
        Öffnet abhängig vom Eingabemodus entweder
        die Bildschirmtastatur oder das Numpad.

        Wichtig:
        Deaktivierte Felder reagieren überhaupt nicht.
        """

        # -------------------------------------------------
        # Deaktiviertes Feld
        # -------------------------------------------------

        if self.disabled:
            return super().on_touch_down(touch)

        if self.locked and self.collide_point(*touch.pos):
            return True

        # -------------------------------------------------
        # Touch liegt nicht auf diesem Feld
        # -------------------------------------------------

        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        # -------------------------------------------------
        # TextInput verarbeitet Touch
        # -------------------------------------------------

        result = super().on_touch_down(touch)

        # -------------------------------------------------
        # Nummernblock
        # -------------------------------------------------
        #
        # Für Buchstaben gibt es nichts zu tun: Die Tastatur des
        # Systems öffnet sich von selbst, sobald das Feld den Fokus
        # bekommt.

        if self.kig_keyboard_mode == "numpad":

            if callable(self.numpad_callback):
                self.numpad_callback(
                    self
                )

        return result
