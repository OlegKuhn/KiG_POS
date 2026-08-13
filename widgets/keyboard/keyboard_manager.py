"""
=========================================================
KiG POS
=========================================================

Datei:
    keyboard_manager.py

Beschreibung:
    Globale Verwaltung der Bildschirmtastatur.

    Es existiert immer nur eine Instanz der Tastatur.

=========================================================
"""

from kivy.core.window import Window

from widgets.keyboard.bottom_keyboard import BottomKeyboard


class KeyboardManager:
    """
    Globale Verwaltung der KiG-Bildschirmtastatur.
    """

    _keyboard = None

    # =====================================================
    # Tastaturinstanz
    # =====================================================

    @classmethod
    def keyboard(cls):
        """
        Liefert die globale Tastaturinstanz.

        Falls noch keine Tastatur existiert,
        wird sie einmalig erzeugt.
        """

        if cls._keyboard is None:

            cls._keyboard = BottomKeyboard()

        return cls._keyboard

    # =====================================================
    # Tastatur anzeigen
    # =====================================================

    @classmethod
    def show(
            cls,
            target
    ):
        """
        Öffnet die Bildschirmtastatur für das
        übergebene Eingabefeld.
        """

        if target is None:
            return

        keyboard = cls.keyboard()

        # -------------------------------------------------
        # Tastatur zum Window hinzufügen
        # -------------------------------------------------

        if keyboard.parent is None:

            Window.add_widget(
                keyboard
            )

        # -------------------------------------------------
        # Position und Größe sicherstellen
        # -------------------------------------------------

        keyboard.x = 0
        keyboard.y = 0

        keyboard.width = Window.width

        # -------------------------------------------------
        # Ziel-Eingabefeld setzen und Tastatur anzeigen
        # -------------------------------------------------

        keyboard.show(
            target
        )

    # =====================================================
    # Tastatur ausblenden
    # =====================================================

    @classmethod
    def hide(cls):
        """
        Blendet die Bildschirmtastatur aus und entfernt
        sie anschließend aus dem Window.
        """

        keyboard = cls.keyboard()

        keyboard.hide()

        # -------------------------------------------------
        # Aus Window entfernen
        # -------------------------------------------------

        if keyboard.parent is not None:

            Window.remove_widget(
                keyboard
            )

    # =====================================================
    # Sichtbarkeit
    # =====================================================

    @classmethod
    def visible(cls):
        """
        Gibt True zurück, wenn die Tastatur aktuell
        angezeigt wird.
        """

        keyboard = cls.keyboard()

        return (
            keyboard.parent is not None
        )

    # =====================================================
    # Aktuelles Eingabefeld
    # =====================================================

    @classmethod
    def target(cls):
        """
        Liefert das aktuell von der Tastatur verwendete
        Eingabefeld.
        """

        keyboard = cls.keyboard()

        return keyboard.target

    # =====================================================
    # Tastatur auf anderes Feld umschalten
    # =====================================================

    @classmethod
    def set_target(
            cls,
            target
    ):
        """
        Wechselt das aktive Eingabefeld, ohne eine zweite
        Tastaturinstanz zu erzeugen.
        """

        if target is None:
            return

        keyboard = cls.keyboard()

        keyboard.target = target

        if keyboard.parent is None:

            cls.show(
                target
            )