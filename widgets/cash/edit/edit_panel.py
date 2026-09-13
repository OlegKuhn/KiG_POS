from kivy.graphics import (
    Color,
    Rectangle,
    Line
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from kivy.metrics import dp

import geldformat
import theme
import units

from widgets.kig_label import KiGLabel
from widgets.common.kig_action_tile import KiGActionTile
from widgets.cash.edit.quantity_editor import QuantityEditor
from widgets.common.slide_panel import SlidePanel


def _menge_text(menge):
    """4 -> "4", 2.5 -> "2,5"."""

    try:
        menge = float(menge)
    except (TypeError, ValueError):
        return str(menge)

    if menge.is_integer():
        return str(int(menge))

    return f"{menge:.2f}".rstrip("0").replace(".", ",")


class ZutatZeile(BoxLayout):
    """Eine Zutat im Bearbeiten-Dialog.

    Links Name und Menge, rechts Minus und Plus - aber nur, wenn es
    zu der Zutat einen Shot gibt. Nur dann gibt es einen Preis, zu dem
    sie verstärkt werden kann (siehe database.get_verstaerkung).

        Rum                              [ - ] [ + ]
        6 cl  (+1 Shot, +2,50 €)
    """

    HOEHE = 54
    KNOPF_BREITE = 48

    def __init__(self, zutat, anzahl=0, aendern_callback=None, **kwargs):

        super().__init__(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(self.HOEHE),
            spacing=dp(theme.SPACE_XS),
            **kwargs
        )

        self.zutat = zutat
        self.anzahl = anzahl
        self.aendern_callback = aendern_callback

        with self.canvas.before:
            Color(*theme.CART_BACKGROUND)
            self._grund = Rectangle()

        self.bind(
            pos=self._nachziehen,
            size=self._nachziehen
        )

        texte = BoxLayout(
            orientation="vertical",
            padding=(dp(theme.SPACE_S), dp(4)),
        )

        self.lbl_name = KiGLabel(text=zutat["name"])
        self.lbl_name.set_bold(True)
        self.lbl_name.set_font_size(16)
        self.lbl_name.set_color(theme.TEXT_PRIMARY)
        self.lbl_name.set_alignment("left")
        self.lbl_name.shorten = True
        self.lbl_name.shorten_from = "right"
        self.lbl_name.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.lbl_menge = KiGLabel()
        self.lbl_menge.set_font_size(14)
        self.lbl_menge.set_color(theme.TEXT_SECONDARY)
        self.lbl_menge.set_alignment("left")
        self.lbl_menge.markup = True
        self.lbl_menge.shorten = True
        self.lbl_menge.shorten_from = "right"
        self.lbl_menge.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        texte.add_widget(self.lbl_name)
        texte.add_widget(self.lbl_menge)

        self.add_widget(texte)

        self.btn_minus = None
        self.btn_plus = None

        if zutat.get("verstaerkung"):

            self.btn_minus = self._knopf("-", -1)
            self.btn_plus = self._knopf("+", +1)

            self.add_widget(self.btn_minus)
            self.add_widget(self.btn_plus)

        self.aktualisieren()

    def _knopf(self, beschriftung, schritt):

        knopf = Button(
            text=beschriftung,
            size_hint=(None, 1),
            width=dp(self.KNOPF_BREITE),
            background_normal="", background_down="",
            background_color=theme.SURFACE,
            color=theme.TEXT_PRIMARY,
            disabled_color=theme.TEXT_SECONDARY,
            font_size="26sp", bold=True,
        )

        knopf.bind(
            on_release=lambda *_args: self._geaendert(schritt)
        )

        return knopf

    def _geaendert(self, schritt):

        if callable(self.aendern_callback):
            self.aendern_callback(self.zutat, schritt)

    def _nachziehen(self, *_args):

        self._grund.pos = self.pos
        self._grund.size = self.size

    def set_anzahl(self, anzahl):

        self.anzahl = anzahl
        self.aktualisieren()

    def aktualisieren(self):

        zutat = self.zutat
        einheit = zutat.get("einheit") or ""
        menge = zutat.get("menge") or 0

        verstaerkung = zutat.get("verstaerkung")

        if verstaerkung and self.anzahl:

            # Der Shot kann in einer anderen Einheit hinterlegt sein
            # als das Rezept (2 cl gegen 20 ml).
            zusatz = units.convert(
                verstaerkung["menge"], verstaerkung["einheit"], einheit
            )

            if zusatz is not None:
                menge = menge + zusatz * self.anzahl

            aufpreis = geldformat.geld(verstaerkung["preis"] * self.anzahl)

            orange = "".join(
                f"{int(round(kanal * 255)):02x}"
                for kanal in theme.PRIMARY_ORANGE[:3]
            )

            self.lbl_menge.text = (
                f"{_menge_text(menge)} {einheit}  "
                f"[color={orange}][b](+{self.anzahl} Shot, "
                f"+{aufpreis})[/b][/color]"
            ).strip()

        else:
            self.lbl_menge.text = f"{_menge_text(menge)} {einheit}".strip()

        if self.btn_minus is not None:
            # Weniger als das Rezept gibt es nicht - Minus nimmt nur
            # zurück, was Plus dazugegeben hat.
            self.btn_minus.disabled = self.anzahl <= 0


class EditPanel(SlidePanel, BoxLayout):

    WIDTH = 350

    PADDING = theme.CARD_PADDING
    SPACING = theme.CARD_SPACING

    HEADER_HEIGHT = 60

    # Menge und Preis
    ZEILEN_HOEHE = 60

    BUTTON_SPACING = theme.ROW_SPACING
    BUTTON_WIDTH = 160
    BUTTON_HEIGHT = theme.CATEGORY_TILE_HEIGHT

    def __init__(
            self,
            price_callback=None,
            quantity_callback=None,
            apply_callback=None,
            **kwargs
    ):

        super().__init__(**kwargs)

        self.price_callback = price_callback

        self.quantity_callback = quantity_callback

        self.apply_callback = apply_callback

        self.orientation = "vertical"

        self.init_slide(dp(self.WIDTH))

        self.padding = dp(self.PADDING)
        self.spacing = dp(self.SPACING)

        self.cart_item = None

        # Was im Dialog eingestellt, aber noch nicht übernommen ist.
        # Erst "Übernehmen" schreibt es in die Warenkorbposition;
        # "Abbrechen" verwirft es.
        self.preis = 0.0
        self.zusatz = {}
        self.zutaten = []
        self.zutat_zeilen = {}

        # =====================================================
        # Hintergrund
        # =====================================================

        with self.canvas.before:

            Color(*theme.CARD)

            self.background = Rectangle()

        with self.canvas.after:

            Color(*theme.CART_SEPARATOR)

            self.separator = Line(width=1)

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas
        )

        # =====================================================
        # Header
        # =====================================================

        self.lbl_title = KiGLabel()

        self.lbl_title.text = "Artikel bearbeiten"

        self.lbl_title.set_bold(True)
        self.lbl_title.set_font_size(24)
        self.lbl_title.set_color(theme.PRIMARY_ORANGE)

        self.lbl_title.horizontal_alignment = "left"
        self.lbl_title.vertical_alignment = "middle"

        self.lbl_title.size_hint = (1, None)
        self.lbl_title.height = dp(self.HEADER_HEIGHT)

        self.lbl_title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(
            self.lbl_title
        )

        # =====================================================
        # Artikelname
        # =====================================================

        self.lbl_article = KiGLabel()

        self.lbl_article.text = ""

        self.lbl_article.set_bold(True)
        self.lbl_article.set_font_size(18)
        self.lbl_article.set_color(theme.TEXT_PRIMARY)

        self.lbl_article.horizontal_alignment = "left"
        self.lbl_article.vertical_alignment = "middle"

        self.lbl_article.size_hint = (1, None)
        self.lbl_article.height = dp(40)

        self.lbl_article.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.add_widget(
            self.lbl_article
        )

        # =====================================================
        # Menge und Preis
        # =====================================================
        #
        # Beschriftung und Wert in EINER Zeile. Übereinander kosteten
        # sie 230 dp - bei einem Mischgetränk blieb darunter kaum Platz
        # für eine einzige Zutat.

        self.quantity_container = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(self.ZEILEN_HOEHE),
            spacing=dp(theme.ROW_SPACING),
        )

        self.lbl_quantity = self._ueberschrift("Menge")
        self.lbl_quantity.size_hint_y = 1

        self.quantity_editor = QuantityEditor(
            edit_callback=self.quantity_clicked
        )

        self.quantity_container.add_widget(
            self.lbl_quantity
        )

        self.quantity_container.add_widget(
            self.quantity_editor
        )

        self.add_widget(
            self.quantity_container
        )

        self.price_container = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(self.ZEILEN_HOEHE),
            spacing=dp(theme.ROW_SPACING),
        )

        self.lbl_price = self._ueberschrift("Preis")
        self.lbl_price.size_hint_y = 1

        self.btn_price = KiGActionTile(
            text="0,00 €",
            callback=self._price_clicked
        )

        # size_hint erst nach der Konstruktion (siehe schaltflaeche).
        self.btn_price.size_hint = (None, 1)
        self.btn_price.width = self.quantity_editor.width

        self.price_container.add_widget(
            self.lbl_price
        )

        self.price_container.add_widget(
            self.btn_price
        )

        self.add_widget(
            self.price_container
        )

        # =====================================================
        # Zutaten (nur Mischgetränke)
        # =====================================================
        #
        # Früher kam die Zusammensetzung als Sprechblase, sobald man
        # eine Position antippte. Hier steht sie dort, wo man sie auch
        # ändern kann: Wer es kräftiger möchte, bekommt je Plus einen
        # Shot der Zutat dazu - zum Preis dieses Shots.

        self.zutaten_bereich = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
        )

        self.lbl_zutaten = self._ueberschrift("Zutaten")

        self.zutaten_liste = BoxLayout(
            orientation="vertical",
            spacing=dp(theme.SPACE_XS),
            size_hint_y=None,
        )

        self.zutaten_liste.bind(
            minimum_height=self.zutaten_liste.setter("height")
        )

        self.zutaten_rollbereich = ScrollView(
            do_scroll_x=False,
            bar_width=dp(6),
        )

        self.zutaten_rollbereich.add_widget(
            self.zutaten_liste
        )

        self.add_widget(
            self.zutaten_bereich
        )

        # =====================================================
        # Buttons
        # =====================================================

        # Duplizieren und Löschen gibt es hier nicht mehr: Eine
        # zweite Portion ist Plus in der Warenkorbzeile, weg ist eine
        # Position mit Minus auf null. Und ein verstärkter Drink wird
        # nicht dupliziert, sondern neu angetippt und verstärkt.
        self.button_area = BoxLayout(
            spacing=dp(self.BUTTON_SPACING),
            size_hint=(1, None),
            height=dp(self.BUTTON_HEIGHT)
        )

        # Die Breite bestimmt die Reihe, nicht die Kachel (wie in
        # cart_footer.py). size_hint erst NACH der Konstruktion setzen:
        # KiGActionTile überschreibt im Konstruktor übergebene Werte.
        def schaltflaeche(text, callback):

            kachel = KiGActionTile(
                text=text,
                height=dp(self.BUTTON_HEIGHT),
                callback=callback
            )

            kachel.size_hint = (1, None)
            kachel.height = dp(self.BUTTON_HEIGHT)

            return kachel

        self.btn_cancel = schaltflaeche("Abbrechen", self._cancel_clicked)

        self.btn_apply = schaltflaeche("Übernehmen", self._apply_clicked)

        self.button_area.add_widget(
            self.btn_cancel
        )

        self.button_area.add_widget(
            self.btn_apply
        )

        self.add_widget(
            self.button_area
        )

    # =====================================================
    # Bausteine
    # =====================================================

    @staticmethod
    def _ueberschrift(text):

        label = KiGLabel()

        label.text = text

        label.set_bold(True)
        label.set_font_size(16)
        label.set_color(theme.TEXT_PRIMARY)

        label.horizontal_alignment = "left"
        label.vertical_alignment = "middle"

        label.size_hint = (1, None)
        label.height = dp(28)

        label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        return label

    # =====================================================
    # Canvas
    # =====================================================

    def _update_canvas(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size

        # Unter der Ueberschrift, nicht durch sie hindurch: Die Hoehe
        # der Ueberschrift ist in dp gerechnet, und oben liegt noch der
        # Innenabstand. Ohne beides lag der Strich bei 125 % Skalierung
        # mitten auf "Artikel bearbeiten" - die Zeile sah durchgestrichen
        # aus.
        y = self.top - dp(self.PADDING) - dp(self.HEADER_HEIGHT)

        self.separator.points = [
            self.x,
            y,
            self.right,
            y
        ]

    # =====================================================
    # Öffnen
    # =====================================================

    def open(self, cart_item, zutaten=None):
        """Öffnet den Dialog für eine Warenkorbposition.

        zutaten: die Rezeptzeilen eines Mischgetränks, je ein
        Wörterbuch mit id, name, menge, einheit und verstaerkung
        (siehe CashScreen._zutaten_fuer). Leer bei allem anderen.
        """

        self.cart_item = cart_item

        self.lbl_article.text = cart_item.article.name

        self.quantity_editor.set_quantity(
            cart_item.quantity
        )

        self.preis = cart_item.unit_price

        self.zusatz = dict(getattr(cart_item, "zusatz", {}) or {})

        self._zutaten_zeigen(zutaten or [])

        self._preis_zeigen()

        self.slide_open()

    # -----------------------------------------------------

    def _zutaten_zeigen(self, zutaten):

        self.zutaten = list(zutaten)

        self.zutaten_bereich.clear_widgets()
        self.zutaten_liste.clear_widgets()

        self.zutat_zeilen = {}

        if not self.zutaten:
            # Kein Mischgetränk: Der Platz bleibt leer, die Knöpfe
            # stehen trotzdem unten.
            return

        self.zutaten_bereich.add_widget(self.lbl_zutaten)
        self.zutaten_bereich.add_widget(self.zutaten_rollbereich)

        # Was sich verstärken lässt, steht oben - darum geht es, wenn
        # man hier ist. Cola und Limette kommen danach.
        reihenfolge = sorted(
            self.zutaten,
            key=lambda zutat: 0 if zutat.get("verstaerkung") else 1,
        )

        for zutat in reihenfolge:

            zeile = ZutatZeile(
                zutat,
                anzahl=self.zusatz.get(zutat["id"], 0),
                aendern_callback=self._zutat_geaendert,
            )

            self.zutat_zeilen[zutat["id"]] = zeile

            self.zutaten_liste.add_widget(zeile)

        self.zutaten_rollbereich.scroll_y = 1

    # -----------------------------------------------------

    def _preis_zeigen(self):

        self.btn_price.set_title(
            geldformat.geld(self.preis)
        )

    # =====================================================
    # Schließen
    # =====================================================

    def close(self):

        self.cart_item = None

        self.slide_close(on_closed=self._closed)

    # =====================================================

    def _closed(self, *args):

        self.lbl_article.text = ""

        self.preis = 0.0
        self.zusatz = {}

        self.btn_price.set_title("0,00 €")

    # =====================================================
    # Preis
    # =====================================================

    def set_preis(self, preis):
        """Der am Nummernblock eingetippte Einzelpreis."""

        self.preis = max(0.0, float(preis))

        self._preis_zeigen()

    # -----------------------------------------------------

    def _price_clicked(self, tile, action):

        if callable(self.price_callback):

            self.price_callback(
                self.cart_item
            )

    # =====================================================
    # Zutaten
    # =====================================================

    def _zutat_geaendert(self, zutat, schritt):
        """Ein Shot mehr oder weniger von dieser Zutat.

        Der Preis wandert mit: je Shot um dessen Verkaufspreis.
        """

        verstaerkung = zutat.get("verstaerkung")

        if not verstaerkung:
            return

        alt = self.zusatz.get(zutat["id"], 0)
        neu = alt + schritt

        if neu < 0:
            return

        if neu:
            self.zusatz[zutat["id"]] = neu
        else:
            self.zusatz.pop(zutat["id"], None)

        self.preis = round(self.preis + schritt * verstaerkung["preis"], 2)

        zeile = self.zutat_zeilen.get(zutat["id"])

        if zeile is not None:
            zeile.set_anzahl(neu)

        self._preis_zeigen()

    def zusatz_text(self):
        """Kurz, was dazukommt: "+1 Bacardi, +2 Jack Daniels"."""

        teile = []

        for zutat in self.zutaten:

            anzahl = self.zusatz.get(zutat["id"], 0)
            verstaerkung = zutat.get("verstaerkung")

            if anzahl and verstaerkung:
                teile.append(f"+{anzahl} {verstaerkung['name']}")

        return ", ".join(teile)

    # =====================================================
    # Buttons
    # =====================================================

    def _cancel_clicked(self, tile, action):

        self.close()

    # -----------------------------------------------------

    def _apply_clicked(self, tile, action):

        if callable(self.apply_callback):
            self.apply_callback(
                self.cart_item,
                self.quantity_editor.quantity,
                self.preis,
                dict(self.zusatz),
            )

    def quantity_clicked(self, quantity):

        if callable(self.quantity_callback):
            self.quantity_callback(self.cart_item)
