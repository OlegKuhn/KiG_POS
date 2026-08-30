"""
=========================================================
KiG POS

Category Panel
=========================================================

Datei:
    widgets/products/category_panel.py
=========================================================
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

import theme

from widgets.common import schreibschutz
from widgets.common.rounded_panel import RoundedPanel
from widgets.common.kig_action_tile import KiGActionTile
from widgets.kig_label import KiGLabel
from widgets.products.category_card import CategoryCard


class CategoryPanel(RoundedPanel):
    """
    Linkes Panel zur Verwaltung der Kategorien.
    """

    # Ab dieser Breite je Kachel dürfen "Neu" und "Bearbeiten"
    # nebeneinander stehen - darunter werden sie untereinander
    # angeordnet (siehe _update_actions_orientation).
    ACTION_TILE_MIN_WIDTH = 110

    # Hochformat: Breite von "Neu"/"Bearbeiten" in der Kopfzeile und
    # Anzahl der Kategorien nebeneinander.
    PORTRAIT_ACTION_WIDTH = 130
    PORTRAIT_COLUMNS = 3

    # Telefon: zwei statt drei Kategorien nebeneinander, und die
    # Schaltflaechen daneben schmaler - sonst blieben fuer die
    # Ueberschrift "Kategorien" keine 90 dp mehr uebrig, und sie brach
    # mitten im Wort um.
    NARROW_ACTION_WIDTH = 96
    NARROW_COLUMNS = 2

    def __init__(
            self,
            on_new,
            on_edit,
            show_actions=True,
            als_liste=None,
            **kwargs
    ):
        """als_liste bestimmt den Aufbau der Karte:

            True    schmale Spalte, Kategorien untereinander
            False   flaches Band, Kategorien nebeneinander
            None    nach Ausrichtung (Hochformat = Band)

        Maßgeblich ist die Form der Karte, nicht die des Bildschirms:
        An der Kasse steht sie auch im Hochformat als Spalte neben den
        Artikeln (siehe widgets/cash/left_panel.py) und braucht dort
        eine Liste - drei Kacheln nebeneinander wären in einer 150 dp
        schmalen Spalte nicht mehr zu lesen.
        """

        super().__init__(**kwargs)

        self.on_new = on_new
        self.on_edit = on_edit
        self.show_actions = show_actions

        self.orientation = "vertical"
        self.padding = dp(theme.CARD_PADDING)
        self.spacing = dp(theme.CARD_SPACING)

        # -------------------------------------------------
        # Überschrift
        # -------------------------------------------------
        #
        # Als flaches Band (Hochformat der Artikelverwaltung) steht die
        # Karte quer über dem Inhalt. Überschrift und Schaltflächen
        # teilen sich dort eine Zeile - untereinander bliebe für die
        # Kategorien selbst nichts mehr übrig.

        if als_liste is None:
            als_liste = not theme.is_portrait()

        self.als_liste = als_liste

        # Der bisherige Name für "flaches Band" - hing früher allein an
        # der Ausrichtung.
        self.hochformat = not als_liste

        title = KiGLabel(
            text="Kategorien"
        )

        title.set_font_size(18 if theme.is_narrow() else 26)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)

        title.size_hint_y = None
        title.height = dp(42)

        if self.hochformat:

            self.header = BoxLayout(
                orientation="horizontal",
                spacing=dp(theme.ROW_SPACING),
                size_hint_y=None,
                height=dp(theme.CATEGORY_TILE_HEIGHT)
            )

            title.size_hint_y = 1
            self.header.add_widget(title)

            self.add_widget(self.header)

        else:
            self.add_widget(title)

        # -------------------------------------------------
        # Aktionsleiste
        # -------------------------------------------------

        if self.show_actions and self.hochformat:

            for text, callback in (
                ("Neu", lambda *_: self.on_new()),
                ("Bearbeiten", lambda *_: self.on_edit()),
            ):
                button = KiGActionTile(text=text, callback=callback)

                # Breite und Höhe erst NACH der Konstruktion setzen -
                # KiGActionTile überschreibt übergebene Werte.
                button.size_hint = (None, None)
                button.width = dp(
                    self.NARROW_ACTION_WIDTH if theme.is_narrow()
                    else self.PORTRAIT_ACTION_WIDTH
                )
                button.height = dp(theme.CATEGORY_TILE_HEIGHT)

                self.header.add_widget(button)

                if text == "Neu":
                    self.new_button = button
                else:
                    self.edit_button = button

        elif self.show_actions:
            self.actions = BoxLayout(
                orientation="horizontal",
                spacing=dp(theme.ROW_SPACING),
                size_hint_y=None,
                height=dp(theme.CATEGORY_TILE_HEIGHT)
            )

            self.new_button = KiGActionTile(
                text="Neu",
                callback=lambda *_: self.on_new()
            )

            self.edit_button = KiGActionTile(
                text="Bearbeiten",
                callback=lambda *_: self.on_edit()
            )

            # KiGActionTile bringt von Haus aus eine feste Breite mit
            # (theme.CATEGORY_TILE_WIDTH). Zwei davon nebeneinander
            # passen in ein schmales Panel nicht hinein und ragten
            # deshalb über den Kartenrand hinaus. Hier bestimmt statt-
            # dessen das Layout die Breite - siehe auch
            # _update_actions_orientation().
            for button in (self.new_button, self.edit_button):
                button.size_hint_x = 1
                button.size_hint_y = None
                button.height = dp(theme.CATEGORY_TILE_HEIGHT)
                self.actions.add_widget(button)

            self.actions.bind(width=self._update_actions_orientation)

            self.add_widget(self.actions)

        # Ohne Aktionsleiste (Hochformat oder show_actions=False) gibt
        # es nichts umzusortieren.
        if not hasattr(self, "actions"):
            self.actions = None

        # Kategorien gehoeren zu den Stammdaten - ein Nebengeraet darf
        # sie ansehen, aber nicht anlegen oder umbenennen.
        if self.show_actions and schreibschutz.nur_ansicht():
            schreibschutz.sperren(
                getattr(self, "new_button", None),
                getattr(self, "edit_button", None),
            )

        # -------------------------------------------------
        # Scrollbereich
        # -------------------------------------------------

        self.scroll = ScrollView(
            bar_width=dp(12)
        )

        # -------------------------------------------------
        # Kategorienliste
        # -------------------------------------------------

        self.category_grid = GridLayout(
            cols=self._spalten(),
            spacing=dp(theme.ROW_SPACING),
            size_hint_y=None
        )

        self.category_grid.bind(
            minimum_height=self.category_grid.setter("height")
        )

        self.scroll.add_widget(
            self.category_grid
        )

        self.add_widget(
            self.scroll
        )

    def _spalten(self):
        """Wie viele Kategorien nebeneinander?"""

        if not self.hochformat:
            return 1

        return (
            self.NARROW_COLUMNS if theme.is_narrow()
            else self.PORTRAIT_COLUMNS
        )

    # =====================================================
    # Aktionsleiste (reagiert auf die Panelbreite)
    # =====================================================

    def _update_actions_orientation(self, *_args):
        """Stellt die beiden Aktions-Kacheln untereinander, sobald sie
        nebeneinander zu schmal würden.

        So bleiben sie auch bei kleinem Fenster immer vollständig
        innerhalb der Karte, statt über deren rechten Rand
        hinauszuragen.
        """

        tile_height = dp(theme.CATEGORY_TILE_HEIGHT)
        spacing = dp(theme.ROW_SPACING)

        fits_side_by_side = (
            self.actions.width >= 2 * dp(self.ACTION_TILE_MIN_WIDTH) + spacing
        )

        self.actions.orientation = "horizontal" if fits_side_by_side else "vertical"
        self.actions.height = (
            tile_height if fits_side_by_side else tile_height * 2 + spacing
        )

    # =====================================================
    # Öffentliche Methoden
    # =====================================================

    def clear(self):
        """
        Entfernt alle Kategorien aus der Anzeige.
        """

        self.category_grid.clear_widgets()

    def set_categories(
            self,
            categories,
            callback
    ):
        """
        Zeigt die übergebenen Kategorien an.
        """

        self.clear()

        for category in categories:

            card = CategoryCard(
                category=category,
                callback=callback
            )

            self.category_grid.add_widget(
                card
            )

    def refresh(
            self,
            categories,
            callback
    ):
        """
        Aktualisiert die Kategorienliste.
        """

        self.set_categories(
            categories,
            callback
        )

    def count(self):
        """
        Anzahl der aktuell angezeigten Kategorien.
        """

        return len(
            self.category_grid.children
        )