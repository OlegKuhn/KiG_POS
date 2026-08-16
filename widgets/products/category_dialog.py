"""
=========================================================
KiG POS
=========================================================

Datei:
    category_dialog.py

Beschreibung:
    Dialog zum Anlegen und Bearbeiten einer Kategorie.

    Optimiert für Touchbedienung und die
    KiG-Bildschirmtastatur.

=========================================================
"""

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from widgets.common.kig_popup import KiGPopup

import theme

from widgets.common.rounded_input import RoundedInput


class CategoryDialog(KiGPopup):
    """
    Dialog zum Anlegen oder Bearbeiten einer Kategorie.

    Der Dialog wird bewusst im oberen Bildschirmbereich
    positioniert, damit die Bildschirmtastatur darunter
    eingeblendet werden kann.
    """

    # =====================================================
    # Initialisierung
    # =====================================================

    def __init__(
            self,
            on_save,
            on_delete=None,
            category=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        # -------------------------------------------------
        # Callbacks
        # -------------------------------------------------

        self.on_save_callback = on_save
        self.on_delete_callback = on_delete

        # -------------------------------------------------
        # Kategorie
        # -------------------------------------------------

        self.category = category

        # -------------------------------------------------
        # Titel
        # -------------------------------------------------

        self.title = (
            "Kategorie bearbeiten"
            if category is not None
            else "Neue Kategorie"
        )

        # -------------------------------------------------
        # Popup-Größe
        # -------------------------------------------------

        self.size_hint = (
            0.55,
            None
        )

        self.height = dp(350)

        # -------------------------------------------------
        # Popup-Position
        #
        # Das Popup sitzt bewusst deutlich weiter oben.
        # Dadurch bleibt unterhalb Platz für die Tastatur.
        # -------------------------------------------------

        self.pos_hint = {
            "center_x": 0.5,
            "top": 0.96
        }

        # -------------------------------------------------
        # Popup-Verhalten
        # -------------------------------------------------

        self.auto_dismiss = False

        # -------------------------------------------------
        # Oberfläche
        # -------------------------------------------------

        self.content = self._build_ui()

        # -------------------------------------------------
        # Bestehende Kategorie laden
        # -------------------------------------------------

        if self.category is not None:

            self.set_category(
                self.category
            )

    # =====================================================
    # Oberfläche
    # =====================================================

    def _build_ui(self):
        """
        Erstellt den vollständigen Inhalt des Dialogs.
        """

        root = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=(
                dp(24),
                dp(18),
                dp(24),
                dp(20)
            )
        )

        # Eigener, themefähiger Hintergrund statt des Kivy-eigenen
        # Popup-Standardskins - so ist der Kontrast zu den Labels in
        # jedem Modus garantiert.
        with root.canvas.before:
            Color(*theme.CARD)
            self._background = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=self._update_background,
            size=self._update_background
        )

        # =================================================
        # Name
        # =================================================

        name_label = Label(
            text="Name",
            color=theme.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(30),
            font_size="18sp",
            halign="left",
            valign="middle"
        )

        name_label.bind(
            size=self._update_label_text_size
        )

        root.add_widget(
            name_label
        )

        # =================================================
        # Eingabefeld
        # =================================================

        self.name_input = RoundedInput(
            hint_text="Kategoriename",


            size_hint_y=None,

            height=dp(76),

            font_size="22sp",

            padding=(
                dp(16),
                dp(20)
            ),

            multiline=False
        )

        root.add_widget(
            self.name_input
        )

        # =================================================
        # Flexibler Leerraum
        # =================================================

        spacer = Label()

        root.add_widget(
            spacer
        )

        # =================================================
        # Aktionsbuttons
        # =================================================

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=dp(theme.ROW_SPACING),
            size_hint_y=None,
            height=dp(58)
        )

        # -------------------------------------------------
        # Löschen
        # -------------------------------------------------

        if self.category is not None:

            delete_button = Button(
                text="Löschen",
                font_size="18sp",
                background_normal="",
                background_down="",
                background_color=theme.ERROR,
                color=theme.TEXT_WHITE
            )

            delete_button.bind(
                on_release=self._delete
            )

            buttons.add_widget(
                delete_button
            )

        # -------------------------------------------------
        # Abbrechen
        # -------------------------------------------------

        cancel_button = Button(
            text="Abbrechen",
            font_size="18sp",
            background_normal="",
            background_down="",
            background_color=theme.SURFACE,
            color=theme.TEXT_PRIMARY
        )

        cancel_button.bind(
            on_release=self._cancel
        )

        buttons.add_widget(
            cancel_button
        )

        # -------------------------------------------------
        # Speichern
        # -------------------------------------------------

        save_button = Button(
            text="Speichern",
            font_size="18sp",
            background_normal="",
            background_down="",
            background_color=theme.PRIMARY_ORANGE,
            color=theme.TEXT_WHITE
        )

        save_button.bind(
            on_release=self._save
        )

        buttons.add_widget(
            save_button
        )

        # -------------------------------------------------

        root.add_widget(
            buttons
        )

        return root

    # =====================================================
    # Hintergrund
    # =====================================================

    def _update_background(self, instance, _value):

        self._background.pos = instance.pos
        self._background.size = instance.size

    # =====================================================
    # Label-Ausrichtung
    # =====================================================

    @staticmethod
    def _update_label_text_size(
            instance,
            _size
    ):
        """
        Sorgt dafür, dass die linke Ausrichtung des
        Labels korrekt funktioniert.
        """

        instance.text_size = (
            instance.width,
            instance.height
        )

    # =====================================================
    # Kategorie setzen
    # =====================================================

    def set_category(
            self,
            category
    ):
        """
        Lädt eine vorhandene Kategorie in den Dialog.
        """

        self.category = category

        self.name_input.text = (
            category["name"]
        )

    # =====================================================
    # Kategoriename abrufen
    # =====================================================

    def get_name(self):
        """
        Liefert den bereinigten Kategorienamen.
        """

        return (
            self.name_input.text.strip()
        )

    # =====================================================
    # Speichern
    # =====================================================

    def _save(
            self,
            *_args
    ):
        """
        Speichert die Eingabe.
        """

        name = self.get_name()

        # -------------------------------------------------
        # Leerer Name
        # -------------------------------------------------

        if not name:

            # Fokus setzen ist erlaubt.
            #
            # RoundedInput öffnet die Tastatur dadurch
            # NICHT automatisch.
            self.name_input.focus = True

            return

        # -------------------------------------------------
        # Callback
        # -------------------------------------------------

        if callable(
                self.on_save_callback
        ):

            self.on_save_callback(
                name
            )

        # -------------------------------------------------
        # Dialog schließen
        # -------------------------------------------------

        self.dismiss()

    # =====================================================
    # Abbrechen
    # =====================================================

    def _cancel(
            self,
            *_args
    ):
        """
        Bricht die Bearbeitung ab.
        """

        # -------------------------------------------------
        # Dialog schließen
        # -------------------------------------------------

        self.dismiss()

    # =====================================================
    # Löschen
    # =====================================================

    def _delete(
            self,
            *_args
    ):
        """
        Löscht die aktuell bearbeitete Kategorie.
        """

        # -------------------------------------------------
        # Callback
        # -------------------------------------------------

        if callable(
                self.on_delete_callback
        ):

            self.on_delete_callback(
                self.category
            )

        # -------------------------------------------------
        # Dialog schließen
        # -------------------------------------------------

        self.dismiss()

    # =====================================================
    # Popup geschlossen
    # =====================================================

    def on_dismiss(
            self
    ):
        """
        Sicherheitsmechanismus:

        Das Eingabefeld gibt beim Schließen den Fokus ab - sonst
        bliebe die Tastatur des Systems offen stehen.
        """

        self.name_input.focus = False