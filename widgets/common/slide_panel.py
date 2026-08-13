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

import theme


class SlidePanel:
    """Mischklasse für Panels, die sich bei Bedarf einblenden.

    Querformat:
        Das Panel schiebt sich seitlich zwischen Artikelbereich und
        Warenkorb; seine Breite wächst von 0 auf SLIDE_WIDTH.

    Hochformat:
        Dafür fehlt schlicht die Breite - ein 350 px breites Panel
        neben Artikeln und Warenkorb ließe von beidem nichts übrig.
        Das Panel übernimmt dort stattdessen den kompletten
        Inhaltsbereich (siehe _render_layout der Screens) und wird
        nur ein- und ausgeblendet; eine Breitenanimation gäbe es
        dabei ohnehin nicht zu sehen.

    Die Screens hängen die Panels nur ins Layout, solange sie
    geöffnet sind, und erkennen das an "disabled". Deshalb wird
    "disabled" beim Schließen erst NACH der Animation gesetzt - das
    Panel bleibt sichtbar, während es zuklappt.
    """

    SLIDE_DURATION = 0.18

    # =====================================================
    # Aufbau
    # =====================================================

    def init_slide(self, width):
        """Bringt das Panel in den geschlossenen Ausgangszustand."""

        self.slide_width = width

        if theme.is_portrait():
            self.size_hint = (1, 1)
        else:
            self.size_hint = (None, 1)
            self.width = 0

        self.opacity = 0
        self.disabled = True

    # =====================================================
    # Öffnen
    # =====================================================

    def slide_open(self):

        Animation.cancel_all(self)

        self.disabled = False

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
