from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
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
        # Schriftgröße
        # -------------------------------------------------
        #
        # Ohne diese Zeile gilt Kivys Voreinstellung von 15 sp - in
        # einem 52 dp hohen Feld ein schmaler Streifen, den an der Bar
        # niemand lesen kann. Wer eine eigene Größe braucht, kann sie
        # weiterhin übergeben.
        if "font_size" not in kwargs:
            self.font_size = f"{theme.INPUT_FONT_SIZE}sp"

        # Ausdruecklich, auch wenn Kivy hier ohnehin links schreibt:
        # So steht die Regel an derselben Stelle wie bei den
        # Auswahlfeldern (siehe feldausrichtung.py).
        self.halign = "left"

        # Text mittig statt oben klebend: Kivy setzt einzeilige
        # Eingaben sonst an den oberen Rand, was in hohen Feldern
        # unruhig aussieht.
        self.bind(
            size=self._update_padding,
            font_size=self._update_padding,
            line_height=self._update_padding,
        )

        # -------------------------------------------------
        # Textfarben
        # -------------------------------------------------

        self.foreground_color = (
            theme.INPUT_TEXT
        )

        self.hint_text_color = (
            theme.INPUT_HINT
        )

        # Wichtig:
        # Kivy verwendet bei disabled=True eine eigene
        # Schriftfarbe. Ohne diese Einstellung erscheint
        # der Text im gesperrten Zustand ausgegraut.

        
        self.disabled_foreground_color = (
            theme.INPUT_TEXT
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

            # Textfarbe ZULETZT setzen.
            #
            # Kivy legt die Farbe des Textes ganz am Anfang von
            # canvas.before fest und zeichnet den Text danach in
            # canvas - also im Farbzustand, den die letzte Anweisung
            # hier hinterlässt. Hintergrund und Rahmen von oben haben
            # diesen Zustand bisher überschrieben, weshalb alles
            # Geschriebene in Rahmengrau (0,88) erschien statt in der
            # eingestellten Farbe: blass und kaum lesbar.
            self.text_color_instruction = Color(*theme.INPUT_TEXT)

        self.bind(
            text=self._update_text_color,
            foreground_color=self._update_text_color,
            hint_text_color=self._update_text_color,
            disabled=self._update_text_color,
        )

        self._update_text_color()

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

    def _update_text_color(self, *_args):
        """Hält die zuletzt gesetzte Farbe passend zum Zustand -
        genauso, wie Kivy es in seiner eigenen Vorlage tut
        (kivy/data/style.kv, Abschnitt TextInput)."""

        if self.disabled:
            farbe = self.disabled_foreground_color
        elif not self.text:
            farbe = self.hint_text_color
        else:
            farbe = self.foreground_color

        self.text_color_instruction.rgba = farbe

    def _update_padding(self, *_args):
        """Hält einzeiligen Text senkrecht in der Mitte.

        line_height steht erst fest, wenn die Schrift geladen ist -
        vorher meldet Kivy 1. Wer damit rechnet, drückt den Text auf
        einen Pixel zusammen: Er sieht dann blass und angeschnitten
        aus, weil nur ein Streifen davon übrig bleibt. Solange der
        Wert unbrauchbar ist, wird deshalb aus der Schriftgröße
        geschätzt.
        """

        if self.multiline:
            return

        zeile = self.line_height if self.line_height > 1 else self.font_size * 1.3

        rand = max(dp(4), (self.height - zeile) / 2)

        self.padding = [dp(12), rand, dp(12), rand]

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
