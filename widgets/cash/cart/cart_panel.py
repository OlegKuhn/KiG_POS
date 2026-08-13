from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

import theme

from widgets.kig_label import KiGLabel
from widgets.common.kig_action_tile import KiGActionTile
from widgets.common.rounded_panel import RoundedPanel
from widgets.cash.cart.cart_item_widget import CartItemWidget
from widgets.cash.cart.cart_footer import CartFooter


class CartPanel(RoundedPanel):
    """
    Rechter Bereich der Kasse.

    Optisch an die weißen Karten der Artikelverwaltung angeglichen
    (siehe widgets/common/rounded_panel.py) statt des früheren eigenen
    cremefarbenen Hintergrunds.
    """

    HEADER_HEIGHT = 60

    # Schmaler als die Standardkachel (theme.CATEGORY_TILE_WIDTH = 160),
    # damit neben "Storno" und "Leeren" noch Platz für die Überschrift
    # bleibt.
    # Nachgemessen: "Warenkorb" braucht bei Schriftgröße 26 rund
    # 156 px. Bei 84 px je Schaltfläche bleiben 164 px übrig - genug,
    # ohne dass die Überschrift umbricht.
    HEADER_BUTTON_WIDTH = 84

    PADDING = theme.CARD_PADDING
    SPACING = theme.CARD_SPACING

    def __init__(
            self,
            edit_callback=None,
            pay_callback=None,
            clear_callback=None,
            tap_callback=None,
            quantity_callback=None,
            storno_callback=None,
            storno_confirm_callback=None,
            storno_cancel_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.clear_callback = clear_callback
        self.tap_callback = tap_callback
        self.quantity_callback = quantity_callback
        self.storno_callback = storno_callback

        self.orientation = "vertical"

        self.padding = self.PADDING
        self.spacing = self.SPACING

        # -------------------------------------------------
        # Auswahl
        # -------------------------------------------------

        self._selected_widget = None
        self._selected_item = None

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        self.header = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=self.HEADER_HEIGHT,
            spacing=theme.ROW_SPACING
        )

        self.lbl_title = KiGLabel()

        self.lbl_title.text = "Warenkorb"
        self.lbl_title.set_bold(True)
        self.lbl_title.set_font_size(26)
        self.lbl_title.set_color(theme.PRIMARY_ORANGE)

        self.lbl_title.horizontal_alignment = "left"
        self.lbl_title.vertical_alignment = "middle"

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.header.add_widget(
            self.lbl_title
        )

        # -------------------------------------------------
        # Schaltflächen "Storno" und "Leeren"
        # -------------------------------------------------
        #
        # Beide etwas schmaler als die Standardkachel, damit neben der
        # Überschrift "Warenkorb" genug Platz bleibt.

        self.btn_storno = KiGActionTile(
            text="Storno",
            callback=self._storno_clicked
        )

        self.btn_clear = KiGActionTile(
            text="Leeren",
            callback=self._clear_clicked
        )

        # KiGActionTile setzt sich im Konstruktor auf eine feste Breite
        # (theme.CATEGORY_TILE_WIDTH = 160) und überschreibt dabei ein
        # übergebenes width. Zwei solche Kacheln würden vom Kopfbereich
        # nichts mehr für die Überschrift übrig lassen - deshalb hier
        # NACH der Konstruktion schmaler setzen.
        for schaltflaeche in (self.btn_storno, self.btn_clear):
            schaltflaeche.size_hint = (None, None)
            schaltflaeche.width = self.HEADER_BUTTON_WIDTH
            schaltflaeche.height = theme.CATEGORY_TILE_HEIGHT
            schaltflaeche.lbl_title.set_font_size(15)
            self.header.add_widget(schaltflaeche)

        self.add_widget(
            self.header
        )

        # -------------------------------------------------
        # Hinweiszeile für den Storno-Modus
        # -------------------------------------------------
        #
        # Bleibt im Normalbetrieb auf Höhe 0 und damit unsichtbar.
        # Zusammen mit dem roten Titel macht sie unmissverständlich,
        # dass gerade keine Ware verkauft, sondern zurückgenommen wird.

        # Kurz genug, damit die Zeile in der Breite des Warenkorbs
        # sicher einzeilig bleibt - ein umbrechender Hinweis würde am
        # unteren Rand abgeschnitten.
        self.lbl_storno_hint = KiGLabel()
        self.lbl_storno_hint.text = "Zu stornierende Artikel antippen"
        self.lbl_storno_hint.set_font_size(15)
        self.lbl_storno_hint.set_bold(True)
        self.lbl_storno_hint.set_color(theme.ERROR)
        self.lbl_storno_hint.horizontal_alignment = "left"
        self.lbl_storno_hint.vertical_alignment = "middle"
        self.lbl_storno_hint.size_hint_y = None
        self.lbl_storno_hint.height = 0
        self.lbl_storno_hint.opacity = 0
        self.lbl_storno_hint.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        # Die Zeile hängt nur im Storno-Modus im Layout. Ein Widget der
        # Höhe 0 würde trotzdem seinen Abstand nach oben und unten
        # beanspruchen - der Warenkorb verlöre also dauerhaft eine
        # Lücke an eine unsichtbare Zeile (siehe set_storno_mode).

        # -------------------------------------------------
        # Artikelbereich
        # -------------------------------------------------
        #
        # Scrollbar: Jede Position ist 60 px hoch, ein voller Warenkorb
        # hätte sonst mehr Zeilen, als die Karte hoch ist - sie würden
        # über deren Rand hinausgezeichnet. Im Hochformat, wo der
        # Warenkorb sich die Höhe mit dem Artikelbereich teilt, tritt
        # das schon bei wenigen Positionen ein.

        self.items_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None
        )

        self.items_container.bind(
            minimum_height=self.items_container.setter("height")
        )

        self.items_scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(8)
        )

        self.items_scroll.add_widget(
            self.items_container
        )

        self.add_widget(
            self.items_scroll
        )

        # -------------------------------------------------
        # Footer
        # -------------------------------------------------

        self.footer = CartFooter(
            edit_callback=edit_callback,
            pay_callback=pay_callback,
            storno_confirm_callback=storno_confirm_callback,
            storno_cancel_callback=storno_cancel_callback
        )

        self.add_widget(
            self.footer
        )

    # =====================================================
    # Eigenschaften
    # =====================================================

    @property
    def selected_item(self):
        """
        Gibt den aktuell ausgewählten CartItem zurück.
        """

        return self._selected_item

    # =====================================================
    # Header
    # =====================================================

    def _clear_clicked(self, tile, action):

        if callable(self.clear_callback):
            self.clear_callback()

    def _storno_clicked(self, tile, action):

        if callable(self.storno_callback):
            self.storno_callback()

    # =====================================================
    # Storno-Modus
    # =====================================================

    def set_storno_mode(self, aktiv):
        """Stellt den Warenkorb sichtbar auf Rücknahme um.

        Titel, Farbe und Hinweiszeile ändern sich gemeinsam - eine
        einzelne Umfärbung wäre im Betrieb leicht zu übersehen, und ein
        versehentlich gebuchter Storno kostet doppelt Arbeit.
        """

        self.lbl_title.text = "Storno" if aktiv else "Warenkorb"
        self.lbl_title.set_color(theme.ERROR if aktiv else theme.PRIMARY_ORANGE)

        self.lbl_storno_hint.height = 30 if aktiv else 0
        self.lbl_storno_hint.opacity = 1 if aktiv else 0

        # Hinweiszeile nur im Storno-Modus einhängen - sonst bliebe
        # eine leere Lücke in Höhe des Abstands stehen.
        if aktiv and self.lbl_storno_hint.parent is None:
            self.add_widget(self.lbl_storno_hint, index=len(self.children) - 1)
        elif not aktiv and self.lbl_storno_hint.parent is not None:
            self.remove_widget(self.lbl_storno_hint)

        # "Storno" und "Leeren" haben im Storno-Modus keine sinnvolle
        # Bedeutung - dafür gibt es unten "Abbrechen".
        for schaltflaeche in (self.btn_storno, self.btn_clear):
            schaltflaeche.opacity = 0 if aktiv else 1
            schaltflaeche.disabled = aktiv

        self.footer.set_storno_mode(aktiv)

    # =====================================================
    # Auswahl
    # =====================================================

    def clear_selection(self):
        """
        Hebt die aktuelle Auswahl auf.
        """

        if self._selected_widget is not None:
            self._selected_widget.unselect()

        self._selected_widget = None
        self._selected_item = None

    # -----------------------------------------------------

    def item_selected(self, widget, cart_item):
        """
        Wird vom CartItemWidget beim Anklicken aufgerufen.
        """

        if self._selected_widget is not None:
            self._selected_widget.unselect()

        self._selected_widget = widget
        self._selected_item = cart_item

        widget.select()

        # Bei Mix-/Rezeptartikeln zusätzlich die Zusammensetzung als
        # Hilfe für die Bar einblenden (siehe cash_screen.py:
        # show_recipe_tooltip / recipe_tooltip.py).
        if callable(self.tap_callback):
            self.tap_callback(widget, cart_item)

    # =====================================================
    # Warenkorb aktualisieren
    # =====================================================

    def refresh(self, cart):

        self.items_container.clear_widgets()

        self.clear_selection()

        for item in cart.items:

            widget = CartItemWidget(
                cart_item=item,
                callback=self.item_selected,
                quantity_callback=self.quantity_callback
            )

            self.items_container.add_widget(widget)

        self.footer.update(total=cart.total())
