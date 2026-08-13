"""
=========================================================
KiG POS
=========================================================

Modul:
    M006.0

Datei:
    kig_footerbar.py

Beschreibung:
    FooterBar der Anwendung.

Die FooterBar wird auf allen Screens
am unteren Fensterrand dargestellt.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from kivy.graphics import (
    Color,
    Line,
    Rectangle
)

from kivy.properties import (
    ObjectProperty,
    StringProperty
)

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout

import theme

from widgets.kig_widget import KiGWidget
from widgets.kig_label import KiGLabel


class KiGFooterBar(KiGWidget):
    """
    FooterBar der Anwendung.
    """

    # =====================================================
    # Eigenschaften
    # =====================================================

    version = StringProperty("1.0.0")

    build = StringProperty("0001")

    exit_callback = ObjectProperty(
        None,
        allownone=True
    )

    # =====================================================
    # Layout
    # =====================================================

    HEIGHT = 60

    PADDING = 18

    SPACING = 20

    LEFT_WIDTH = 320

    RIGHT_WIDTH = 260

    # =====================================================
    # Konstruktor
    # =====================================================

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        #
        # Größe
        #

        self.size_hint_y = None
        self.height = theme.FOOTER_HEIGHT

        #
        # Hintergrund
        #

        with self.canvas.before:

            Color(*theme.HEADER_BACKGROUND)

            self.background = Rectangle()

        #
        # Obere Trennlinie
        #

        with self.canvas.after:

            Color(*theme.HEADER_SEPARATOR)

            self.top_line = Line(
                width=1
            )

        #
        # Hauptlayout
        #

        self.content = BoxLayout(

            orientation="horizontal",

            padding=(
                15,
                0,
                15,
                0
            ),

            spacing=self.SPACING
        )

        self.add_widget(
            self.content
        )

        #
        # Linker Bereich
        #

        self.left_container = BoxLayout(

            orientation="vertical",

            size_hint=(None, 1),

            width=self.LEFT_WIDTH,

            padding=(0, 8, 0, 8),

            spacing=2
        )

        #
        # Mittlerer Bereich
        #

        self.center_container = AnchorLayout(

            anchor_x="center",

            anchor_y="center"

        )

        #
        # Rechter Bereich
        #

        self.right_container = AnchorLayout(

            anchor_x="right",

            anchor_y="center",

            size_hint=(None, 1),

            width=self.RIGHT_WIDTH

        )

        #
        # Bereiche hinzufügen
        #

        self.content.add_widget(
            self.left_container
        )

        self.content.add_widget(
            self.center_container
        )

        self.content.add_widget(
            self.right_container
        )

        #
        # Layout aktualisieren
        #

        self.bind(

            pos=self._update_layout,

            size=self._update_layout

        )

        # =====================================================
        # Linker Bereich
        # =====================================================

        self.left_layout = BoxLayout(
            orientation="vertical",
            spacing=2,
            size_hint=(None, None),
            width=220,
            height=40
        )

        #
        # Programmname
        #

        self.lbl_program = KiGLabel()

        self.lbl_program.text = "KiG POS"

        self.lbl_program.font_size = 18

        self.lbl_program.bold = True

        self.lbl_program.halign = "left"

        self.lbl_program.valign = "middle"

        self.lbl_program.text_size = self.lbl_program.size

        self.lbl_program.bind(
            size=lambda i, v: setattr(i, "text_size", v)
        )

        #
        # Version
        #

        self.lbl_version = KiGLabel()

        self.lbl_version.text = (
            f"Version {self.version} | "
            f"Build {self.build}"
        )

        self.lbl_version.font_size = 13

        self.lbl_version.color = (
            0.35,
            0.35,
            0.35,
            1
        )

        self.lbl_version.halign = "left"

        self.lbl_version.valign = "middle"

        self.lbl_version.text_size = self.lbl_version.size

        self.lbl_version.bind(
            size=lambda i, v: setattr(i, "text_size", v)
        )

        self.left_container.add_widget(self.lbl_program)
        self.left_container.add_widget(self.lbl_version)

        # =====================================================
        # Rechter Bereich
        # =====================================================

        self.lbl_exit = KiGLabel()

        self.lbl_exit.text = "Programm beenden"

        self.lbl_exit.font_size = 22

        self.lbl_exit.bold = True

        self.lbl_exit.color = theme.PRIMARY_ORANGE

        self.lbl_exit.halign = "right"

        self.lbl_exit.valign = "middle"

        self.lbl_exit.text_size = (
            self.RIGHT_WIDTH,
            None
        )

        self.right_container.add_widget(
            self.lbl_exit
        )

        #
        # Aktualisieren
        #

        self.bind(

            version=self._update_labels,

            build=self._update_labels

        )

    # =====================================================
    # Layout aktualisieren
    # =====================================================

    def _update_layout(self, *args):
        """
        Aktualisiert Position und Größe.
        """

        #
        # Hintergrund
        #

        self.background.pos = self.pos
        self.background.size = self.size

        #
        # Trennlinie oben
        #

        self.top_line.points = (

            self.x,
            self.top,

            self.right,
            self.top

        )

        #
        # Hauptlayout
        #

        self.content.pos = self.pos
        self.content.size = self.size


    # =====================================================
    # Labels aktualisieren
    # =====================================================

    def _update_labels(self, *args):
        """
        Aktualisiert die Versionsinformationen.
        """

        self.lbl_version.text = (
            f"Version {self.version} | "
            f"Build {self.build}"
        )


    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def set_version(self, version: str):

        self.version = version

        self._update_labels()


    # -----------------------------------------------------

    def set_build(self, build: str):

        self.build = build

        self._update_labels()


    # -----------------------------------------------------

    def set_exit_callback(self, callback):

        self.exit_callback = callback


    # =====================================================
    # Klick auf Footer
    # =====================================================

    def on_touch_down(self, touch):

        if self.lbl_exit.collide_point(*touch.pos):

            #
            # Kurzes visuelles Feedback
            #

            self.lbl_exit.color = (
                0.85,
                0.45,
                0.00,
                1
            )

            return True

        return super().on_touch_down(touch)


    # -----------------------------------------------------

    def on_touch_up(self, touch):

        if self.lbl_exit.collide_point(*touch.pos):

            #
            # Originalfarbe wiederherstellen
            #

            self.lbl_exit.color = theme.PRIMARY_ORANGE

            #
            # Callback ausführen
            #

            if callable(self.exit_callback):

                self.exit_callback()

            return True

        return super().on_touch_up(touch)


    # =====================================================
    # String
    # =====================================================

    def __repr__(self):

        return (
            "KiGFooterBar()"
        )