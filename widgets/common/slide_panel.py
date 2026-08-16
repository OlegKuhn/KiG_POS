"""
=========================================================
KiG POS
=========================================================

Datei:
    widgets/common/slide_panel.py

Beschreibung:
    Gemeinsames Ein- und Ausblenden der einklappbaren Panels
    (Nummernblock, Position bearbeiten, Bezahlen).

Version:
    1.0.0
=========================================================
"""

from kivy.animation import Animation
from kivy.graphics import Color, Line

import theme


class SlidePanel:
    """Mischklasse für Panels, die sich bei Bedarf einblenden.

    Querformat:
        Das Panel schiebt sich seitlich auf; seine Breite wächst von
        0 auf SLIDE_WIDTH.

    Hochformat:
        Dafür fehlt schlicht die Breite - ein 350 px breites Panel
        neben Artikeln und Warenkorb ließe von beidem nichts übrig.
        Das Panel deckt dort stattdessen eine ganze Fläche ab und
        wird nur ein- und ausgeblendet; eine Breitenanimation gäbe es
        dabei ohnehin nicht zu sehen.

    Wohin das Panel geht, entscheidet der Screen:

        overlay=False   Das Panel hängt als Spalte im Layout, alles
                        daneben rückt zusammen (Artikelverwaltung).

        overlay=True    Das Panel liegt über der Oberfläche, nichts
                        daneben bewegt sich (Kasse).

    "disabled" meldet den Zustand nach außen und wird beim Schließen
    erst NACH der Animation gesetzt - das Panel bleibt sichtbar,
    während es zuklappt.
    """

    SLIDE_DURATION = 0.18

    # =====================================================
    # Aufbau
    # =====================================================

    def init_slide(self, width, overlay=False):
        """Bringt das Panel in den geschlossenen Ausgangszustand.

        overlay=True: Das Panel hängt nicht in einer Layoutspalte,
        sondern liegt über der Oberfläche - Position und Höhe bestimmt
        dann der Screen (siehe CashScreen._position_panels). So muss
        daneben nichts zusammenrücken, wenn es aufgeht.
        """

        self.slide_width = width
        self.slide_overlay = overlay

        if overlay:
            self.size_hint = (None, None)
            self.width = 0
            self._add_overlay_border()

        elif theme.is_portrait():
            self.size_hint = (1, 1)

        else:
            self.size_hint = (None, 1)
            self.width = 0

        self.opacity = 0
        self.disabled = True

    # =====================================================
    # Umrandung
    # =====================================================

    def _add_overlay_border(self):
        """Feine Linie um das Panel.

        Ein überlagerndes Panel liegt auf der weißen Artikelkarte auf -
        ohne Kante wäre nicht zu erkennen, wo das eine aufhört und das
        andere anfängt.

        Der Screen ruft init_slide() unter Umständen ein zweites Mal
        auf (um auf Überlagerung umzustellen); die Linie darf es
        deshalb nur einmal geben.
        """

        if getattr(self, "_overlay_border", None) is not None:
            return

        with self.canvas.after:
            Color(*theme.CARD_BORDER)
            self._overlay_border = Line(width=theme.BORDER_WIDTH)

        self.bind(
            pos=self._update_overlay_border,
            size=self._update_overlay_border,
        )

    def _update_overlay_border(self, *_args):

        if self.width <= 0:
            self._overlay_border.points = []
            return

        self._overlay_border.rectangle = (*self.pos, self.width, self.height)

    # =====================================================
    # Öffnen
    # =====================================================

    def slide_open(self):

        Animation.cancel_all(self)

        self.disabled = False

        # Im Hochformat deckt das Panel eine feste Fläche ab (die des
        # Artikelbereichs) - dort gibt es nichts zu schieben.
        if theme.is_portrait():
            self.opacity = 1
            return

        Animation(
            width=self.slide_width,
            opacity=1,
            duration=self.SLIDE_DURATION,
            t="out_quad"
        ).start(self)

    # =====================================================
    # Schließen
    # =====================================================

    def slide_close(self, on_closed=None):

        Animation.cancel_all(self)

        if theme.is_portrait():

            self.opacity = 0
            self.disabled = True

            if callable(on_closed):
                on_closed()

            return

        animation = Animation(
            width=0,
            opacity=0,
            duration=self.SLIDE_DURATION,
            t="out_quad"
        )

        def fertig(*_args):

            self.disabled = True

            if callable(on_closed):
                on_closed()

        animation.bind(on_complete=fertig)

        animation.start(self)
