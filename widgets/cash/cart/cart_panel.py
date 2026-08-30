from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

import geldformat
import theme

from widgets.kig_label import KiGLabel
from widgets.common.kig_action_tile import KiGActionTile
from widgets.common.kig_symbol import (
    KiGSymbol, PFEIL_OBEN, PFEIL_UNTEN,
)
from widgets.common.rounded_panel import RoundedPanel
from widgets.cash.cart.cart_item_widget import CartItemWidget
from widgets.cash.cart.cart_footer import CartFooter


class _Warenkorbleiste(BoxLayout):
    """Der zugeklappte Warenkorb: eine Zeile, zwei Ziele.

    Links, antippbar: wie viele Posten und was sie kosten - ein Tipp
    holt den Warenkorb hoch. Rechts "Bezahlen", damit der übliche Weg
    nicht über das Aufklappen führt.
    """

    def __init__(self, on_auf, on_bezahlen, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.spacing = dp(theme.ROW_SPACING)
        self.size_hint_y = None
        self.height = dp(CartPanel.SCHMAL_LEISTE_HOEHE - 2 * theme.CARD_PADDING)

        self.on_auf = on_auf

        self.zusammenfassung = _LeistenZeile(on_auf)
        self.add_widget(self.zusammenfassung)

        self.btn_bezahlen = Button(
            text="Bezahlen",
            size_hint=(None, 1), width=dp(82),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="17sp", bold=True,
        )

        if callable(on_bezahlen):
            self.btn_bezahlen.bind(
                on_release=lambda *_args: on_bezahlen()
            )

        self.add_widget(self.btn_bezahlen)

    def setzen(self, anzahl, summe):

        self.zusammenfassung.setzen(anzahl, summe)


class _LeistenZeile(ButtonBehavior, BoxLayout):
    """Der antippbare Teil der Leiste."""

    def __init__(self, on_auf, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.spacing = dp(theme.SPACE_S)

        self.symbol = KiGSymbol(
            symbol=PFEIL_UNTEN,
            color=theme.PRIMARY_ORANGE,
            size_hint=(None, 1),
            width=dp(18),
        )
        self.add_widget(self.symbol)

        # Einzeilig und notfalls gekuerzt: In dieser Zeile ist kein
        # Platz fuer einen Umbruch - "Warenkorb" wurde sonst zu
        # "Warenk/orb".
        self.lbl_posten = KiGLabel()
        self.lbl_posten.set_font_size(14)
        self.lbl_posten.set_bold(True)
        self.lbl_posten.set_alignment("left")
        self.lbl_posten.set_color(theme.TEXT_SECONDARY)
        self.lbl_posten.max_lines = 1
        self.lbl_posten.shorten = True
        self.lbl_posten.shorten_from = "right"
        self.lbl_posten.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.lbl_posten)

        self.lbl_summe = KiGLabel()
        self.lbl_summe.set_font_size(19)
        self.lbl_summe.set_bold(True)
        self.lbl_summe.set_alignment("right")
        self.lbl_summe.set_color(theme.PRIMARY_ORANGE)
        self.lbl_summe.size_hint_x = None
        self.lbl_summe.width = dp(72)
        self.lbl_summe.max_lines = 1
        self.lbl_summe.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.lbl_summe)

        self.bind(
            on_release=lambda *_args: on_auf() if callable(on_auf) else None
        )

        self.setzen(0, 0.0)

    def setzen(self, anzahl, summe):

        # Kurz halten: Neben Summe und "Bezahlen" bleiben rund 98
        # Bildpunkte - genug für "3 Posten" (72), nicht für mehr.
        self.lbl_posten.set_text(
            "leer" if not anzahl else f"{anzahl:g} Posten"
        )

        self.lbl_summe.set_text(geldformat.geld(summe))


class _Zuklappzeile(ButtonBehavior, BoxLayout):
    """Ueberschrift des aufgeklappten Warenkorbs - antippbar.

    Traegt den Winkel nach oben, damit man ihm ansieht, wohin er
    fuehrt.
    """

    def __init__(self, text, on_zu, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.spacing = dp(theme.SPACE_S)

        self.symbol = KiGSymbol(
            symbol=PFEIL_OBEN,
            color=theme.PRIMARY_ORANGE,
            size_hint=(None, 1),
            width=dp(20),
        )
        self.add_widget(self.symbol)

        self.beschriftung = KiGLabel()
        self.beschriftung.set_text(text)
        self.beschriftung.set_font_size(17)
        self.beschriftung.set_bold(True)
        self.beschriftung.set_alignment("left")
        self.beschriftung.set_color(theme.PRIMARY_ORANGE)
        self.beschriftung.max_lines = 1
        self.beschriftung.bind(
            size=lambda instanz, groesse: setattr(
                instanz, "text_size", groesse
            )
        )
        self.add_widget(self.beschriftung)

        self.bind(
            on_release=lambda *_args: on_zu() if callable(on_zu) else None
        )


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

    # Telefon: Der Warenkorb belegte dort fast die halbe Hoehe - meist,
    # um "Summe 0,00" anzuzeigen. Zugeklappt bleibt eine Zeile stehen;
    # ein Tipp darauf holt ihn hoch.
    SCHMAL_LEISTE_HOEHE = 62

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

        self.padding = dp(self.PADDING)
        self.spacing = dp(self.SPACING)

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
            height=dp(self.HEADER_HEIGHT),
            spacing=dp(theme.ROW_SPACING)
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

        # Auf dem Telefon fuehrt die Ueberschrift wieder zurueck: Der
        # Warenkorb liess sich aufklappen, aber nicht mehr zuklappen -
        # es gab schlicht nichts zum Antippen.
        if theme.is_narrow():

            self.zuklapp_knopf = _Zuklappzeile(
                text="Warenkorb", on_zu=self.zuklappen
            )

            self.header.add_widget(self.zuklapp_knopf)

        else:

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
        # Auf dem Telefon noch einmal schmaler: Bei 84 dp je Schaltfläche
        # blieben der Überschrift 114 Bildpunkte - "Warenkorb" wurde zu
        # "Waren" abgeschnitten. Nachgemessen bei 339 dp Breite.
        knopfbreite = 70 if theme.is_narrow() else self.HEADER_BUTTON_WIDTH

        for schaltflaeche in (self.btn_storno, self.btn_clear):
            schaltflaeche.size_hint = (None, None)
            schaltflaeche.width = dp(knopfbreite)
            schaltflaeche.height = dp(theme.CATEGORY_TILE_HEIGHT)
            schaltflaeche.lbl_title.set_font_size(
                13 if theme.is_narrow() else 15
            )
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

        # -------------------------------------------------
        # Telefon: die zugeklappte Zeile
        # -------------------------------------------------

        self.schmal = theme.is_narrow()
        self.aufgeklappt = not self.schmal

        self.on_klapp = None

        if self.schmal:

            self._volle_kinder = list(reversed(self.children))

            self.leiste = _Warenkorbleiste(
                on_auf=self._aufklappen,
                on_bezahlen=pay_callback,
            )

            self._nur_leiste()

    # =====================================================
    # Zugeklappt / aufgeklappt (nur Telefon)
    # =====================================================

    def _nur_leiste(self):

        self.clear_widgets()
        self.add_widget(self.leiste)

        self.aufgeklappt = False

    def _volle_ansicht(self):

        self.clear_widgets()

        for kind in self._volle_kinder:
            self.add_widget(kind)

        self.aufgeklappt = True

    def _aufklappen(self):

        self._volle_ansicht()

        if callable(self.on_klapp):
            self.on_klapp(True)

    def zuklappen(self):
        """Klappt den Warenkorb wieder zur Zeile zusammen."""

        if not self.schmal or not self.aufgeklappt:
            return

        self._nur_leiste()

        if callable(self.on_klapp):
            self.on_klapp(False)

    def leiste_aktualisieren(self, anzahl, summe):
        """Traegt Postenzahl und Summe in die zugeklappte Zeile ein."""

        if self.schmal:
            self.leiste.setzen(anzahl, summe)

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

        self.lbl_storno_hint.height = dp(30) if aktiv else 0
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

        # Die zugeklappte Zeile zeigt dasselbe in klein.
        self.leiste_aktualisieren(
            sum(item.quantity for item in cart.items), cart.total()
        )
