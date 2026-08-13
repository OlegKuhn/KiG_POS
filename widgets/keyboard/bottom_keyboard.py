"""
=========================================================
KiG POS
=========================================================

Modul:
    Bildschirmtastatur

Datei:
    bottom_keyboard.py

Beschreibung:
    Bildschirmtastatur für Texteingaben.

    Enthält:
        • deutsches QWERTZ-Layout
        • Zahlenreihe
        • Shift
        • Sonderzeichen
        • Backspace
        • Leerzeichen
        • OK
        • automatische Größenanpassung

=========================================================
"""

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.keyboard.keyboard_key import KeyboardKey
from widgets.keyboard.keyboard_layout import KeyboardLayout


class BottomKeyboard(RoundedPanel):
    """
    Bildschirmtastatur für KiG POS.

    Die Tastatur schreibt immer in das aktuell übergebene
    TextInput-Widget.

    Die Darstellung der Tastatur wird vollständig aus
    KeyboardLayout erzeugt.
    """

    HEIGHT = dp(360)

    # =====================================================
    # Initialisierung
    # =====================================================

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # -------------------------------------------------
        # Ziel-Eingabefeld
        # -------------------------------------------------

        self.target = None

        # -------------------------------------------------
        # Tastaturstatus
        # -------------------------------------------------

        self.shift_active = False
        self.symbol_mode = False

        # -------------------------------------------------
        # Layout
        # -------------------------------------------------

        self.orientation = "vertical"

        self.spacing = dp(theme.ROW_SPACING)

        self.padding = (
            dp(12),
            dp(12),
            dp(12),
            dp(12)
        )

        self.size_hint = (None, None)

        self.width = Window.width
        self.height = self.HEIGHT

        self.x = 0
        self.y = 0

        # -------------------------------------------------
        # Fensteränderungen
        # -------------------------------------------------

        Window.bind(
            size=self._update_window_size
        )

        # -------------------------------------------------
        # Tastatur aufbauen
        # -------------------------------------------------

        self.build_keyboard()

    # =====================================================
    # Fenstergröße
    # =====================================================

    def _update_window_size(self, *_args):
        """
        Passt die Tastaturbreite an die Fensterbreite an.
        """

        self.width = Window.width

        self.x = 0

    # =====================================================
    # Tastatur anzeigen
    # =====================================================

    def show(self, target):
        """
        Öffnet die Tastatur für das übergebene Eingabefeld.
        """

        if target is None:
            return

        self.target = target

        # -------------------------------------------------
        # Bei jedem neuen Öffnen normales Textlayout
        # -------------------------------------------------

        self.symbol_mode = False
        self.shift_active = False

        self.build_keyboard()

        # -------------------------------------------------
        # Tastatur unten positionieren
        # -------------------------------------------------

        self.width = Window.width
        self.x = 0

        # -------------------------------------------------
        # Einblendanimation
        # -------------------------------------------------

        Animation.cancel_all(self)

        self.opacity = 0

        animation = Animation(
            opacity=1,
            duration=0.15
        )

        animation.start(self)

    # =====================================================
    # Tastatur ausblenden
    # =====================================================

    def hide(self):
        """
        Blendet die Tastatur aus.

        Das eigentliche Entfernen aus dem Window übernimmt
        der KeyboardManager.
        """

        Animation.cancel_all(self)

        animation = Animation(
            opacity=0,
            duration=0.12
        )

        animation.start(self)

    # =====================================================
    # Tastatur aufbauen
    # =====================================================

    def build_keyboard(self):
        """
        Baut die komplette Tastatur anhand des aktuell
        ausgewählten Layouts neu auf.
        """

        self.clear_widgets()

        # -------------------------------------------------
        # Aktuelles Layout bestimmen
        # -------------------------------------------------

        if self.symbol_mode:

            layout = KeyboardLayout.get_symbol_layout()

        else:

            layout = KeyboardLayout.get_text_layout(
                shift=self.shift_active
            )

        # -------------------------------------------------
        # Reihen erzeugen
        # -------------------------------------------------

        for row_definition in layout:

            self._add_row(
                row_definition
            )

    # =====================================================
    # Tastaturreihe erzeugen
    # =====================================================

    def _add_row(self, row_definition):
        """
        Erzeugt eine einzelne Tastaturreihe.

        key_value:
            Interner Wert.

        display_text:
            Sichtbare Beschriftung.
        """

        row = BoxLayout(
            orientation="horizontal",
            spacing=dp(theme.ROW_SPACING),
            size_hint=(1, 1)
        )

        for definition in row_definition:

            # ---------------------------------------------
            # Standardwerte
            # ---------------------------------------------

            key_value = definition
            width_factor = 1.0

            # ---------------------------------------------
            # Sonderbreite
            #
            # Beispiel:
            #
            # ("BACKSPACE", 1.5)
            # ---------------------------------------------

            if isinstance(definition, tuple):
                key_value = definition[0]
                width_factor = definition[1]

            # ---------------------------------------------
            # Sichtbare Beschriftung bestimmen
            # ---------------------------------------------

            display_text = self._get_display_text(
                key_value
            )

            # ---------------------------------------------
            # Taste erzeugen
            # ---------------------------------------------

            button = KeyboardKey(

                display_text=display_text,

                key_value=key_value,

                callback=self.key_pressed,

                width_factor=width_factor
            )

            row.add_widget(
                button
            )

        self.add_widget(
            row
        )

    # =====================================================
    # Sichtbare Tastenbeschriftung
    # =====================================================

    @staticmethod
    def _get_display_text(key):
        """
        Übersetzt interne Tastennamen in sichtbare
        Beschriftungen.
        """

        if key == "SPACE":
            return "Leerzeichen"

        if key == "SHIFT":
            return "Shift"

        if key == "BACKSPACE":
            return "<-"

        return key

    # =====================================================
    # Tastendruck
    # =====================================================

    def key_pressed(self, key):
        """
        Zentrale Verarbeitung aller Tastendrücke.
        """

        if self.target is None:
            return

        # -------------------------------------------------
        # Shift
        # -------------------------------------------------

        if key == "SHIFT":
            self._toggle_shift()
            return

        # -------------------------------------------------
        # Sonderzeichen
        # -------------------------------------------------

        if key == "123#+":
            self._show_symbols()
            return

        # -------------------------------------------------
        # Zurück zu Buchstaben
        # -------------------------------------------------

        if key == "ABC":
            self._show_letters()
            return

        # -------------------------------------------------
        # Backspace
        # -------------------------------------------------

        if key == "BACKSPACE":
            self._backspace()
            return

        # -------------------------------------------------
        # Leerzeichen
        # -------------------------------------------------

        if key == "SPACE":
            self._insert_text(" ")
            return

        # -------------------------------------------------
        # OK
        # -------------------------------------------------

        if key == "OK":
            self._confirm()
            return

        # -------------------------------------------------
        # Normales Zeichen
        # -------------------------------------------------

        self._insert_text(key)

        # -------------------------------------------------
        # Shift nach einem Zeichen automatisch deaktivieren
        # -------------------------------------------------

        if self.shift_active:
            self.shift_active = False
            self.build_keyboard()

    # =====================================================
    # Text einfügen
    # =====================================================

    def _insert_text(self, text):
        """
        Fügt Text an der aktuellen Cursorposition ein.

        insert_text() wird bewusst verwendet, damit
        Cursorposition und vorhandene Markierungen durch
        Kivys TextInput verarbeitet werden.
        """

        if self.target is None:
            return

        if not hasattr(
                self.target,
                "insert_text"
        ):
            return

        self.target.insert_text(
            text
        )

    # =====================================================
    # Backspace
    # =====================================================

    def _backspace(self):
        """
        Löscht das Zeichen links vom Cursor.

        Falls Text markiert ist, wird die Markierung
        gelöscht.
        """

        if self.target is None:
            return

        # -------------------------------------------------
        # Markierten Text löschen
        # -------------------------------------------------

        if getattr(
                self.target,
                "selection_text",
                ""
        ):

            try:

                self.target.delete_selection()

            except Exception:

                pass

            return

        # -------------------------------------------------
        # Cursorposition
        # -------------------------------------------------

        cursor_index = self.target.cursor_index()

        if cursor_index <= 0:
            return

        # -------------------------------------------------
        # Zeichen links vom Cursor entfernen
        # -------------------------------------------------

        text = self.target.text

        new_text = (
            text[:cursor_index - 1]
            + text[cursor_index:]
        )

        self.target.text = new_text

        # -------------------------------------------------
        # Cursor wieder korrekt setzen
        # -------------------------------------------------

        self.target.cursor = (
            self.target.get_cursor_from_index(
                cursor_index - 1
            )
        )

    # =====================================================
    # Shift
    # =====================================================

    def _toggle_shift(self):
        """
        Schaltet zwischen Groß- und Kleinschreibung um.
        """

        if self.symbol_mode:
            return

        self.shift_active = (
            not self.shift_active
        )

        self.build_keyboard()

    # =====================================================
    # Sonderzeichen anzeigen
    # =====================================================

    def _show_symbols(self):
        """
        Schaltet auf die Sonderzeichenebene.
        """

        self.symbol_mode = True
        self.shift_active = False

        self.build_keyboard()

    # =====================================================
    # Buchstaben anzeigen
    # =====================================================

    def _show_letters(self):
        """
        Schaltet zurück zum normalen QWERTZ-Layout.
        """

        self.symbol_mode = False
        self.shift_active = False

        self.build_keyboard()

    # =====================================================
    # Eingabe bestätigen
    # =====================================================

    def _confirm(self):
        """
        Bestätigt die Eingabe und schließt die Tastatur.
        """

        target = self.target

        # -------------------------------------------------
        # Ziel zuerst freigeben
        # -------------------------------------------------

        self.target = None

        # -------------------------------------------------
        # Fokus entfernen
        # -------------------------------------------------

        if target is not None:

            try:

                target.focus = False

            except Exception:

                pass

        # -------------------------------------------------
        # KeyboardManager erst hier importieren.
        #
        # Dadurch vermeiden wir einen zirkulären Import:
        #
        # KeyboardManager -> BottomKeyboard
        # BottomKeyboard -> KeyboardManager
        # -------------------------------------------------

        from widgets.keyboard.keyboard_manager import (
            KeyboardManager
        )

        KeyboardManager.hide()