"""Dashboard-Karte: Stammdaten eines Artikels (Name, Einheit, Preise, Kategorie, Typ).

Aufbau: je Angabe eine Zeile mit der Bezeichnung links und dem
editierbaren Feld rechts. Das ist auch in einer schmalen Spalte noch
lesbar - vorher trugen die Felder ihre Bezeichnung nur als Platzhalter
im Feld selbst, der bei wenig Platz abgeschnitten wurde.

Reihenfolge bewusst Name -> Einheit: Bei Einheit "Flasche" handelt es
sich immer um eine reine Lagerzutat (siehe config.BOTTLE_UNIT) - dafür
sind Kategorie, Artikeltyp, Verkaufspreis und der Verkauf-Schalter
irrelevant und werden automatisch passend gesetzt statt abgefragt:

    Kategorie     -> immer "Zutat" (der Einfachheit halber)
    Artikeltyp    -> immer "Einzelartikel"
    Verkaufspreis -> immer 0 (wird nie direkt verkauft)
    Verkauf       -> immer aus (taucht nie an der Kasse auf)

Die Flaschengröße wird hier bewusst NICHT abgefragt - das passiert
erst beim Wareneingang bzw. bei der Bestandskorrektur, wo sie
tatsächlich gebraucht wird (siehe products_screen.py /
stock_adjustment_dialog.py).

Bei Mix-/Rezeptartikeln entfällt zusätzlich der Einkaufspreis - der
gilt bereits auf den zugrunde liegenden Zutaten (z. B. der Flasche).

"Auch als Shot verkaufen" (nur bei Einheit "Flasche"): legt automatisch
einen verknüpften Mix-Artikel an/pflegt ihn, der die Flasche als
20-ml-Portion o. ä. verkauft - ohne dass man dafür manuell einen
zweiten Artikel mit anderem Namen anlegen muss (Namenskollision, da
z. B. "Jack Daniels" sonst doppelt existieren müsste).
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch

import config
import theme

from widgets.common.rounded_panel import RoundedPanel
from widgets.common.rounded_input import RoundedInput
from widgets.common.rounded_spinner import RoundedSpinner
from widgets.kig_label import KiGLabel


class StammdatenCard(RoundedPanel):
    """Bearbeitbare Stammdaten. Speichert erst auf Tastendruck (Speichern)."""

    ARTICLE_TYPE_LABELS = {"SINGLE": "Einzelartikel", "MIX": "Mix / Rezept"}
    BOTTLE_CATEGORY_NAME = "Zutat"

    # Höhe einer Angabe-Zeile und Breitenaufteilung Bezeichnung/Feld.
    ROW_HEIGHT = 54
    CAPTION_WIDTH = 0.40
    FIELD_WIDTH = 0.60

    # Zusatzangaben zum Shot rücken etwas ein, damit erkennbar bleibt,
    # dass sie zum Schalter darüber gehören.
    INDENT = 14

    def __init__(
            self,
            on_save,
            on_numpad,
            **kwargs
    ):
        super().__init__(
            orientation="vertical",
            spacing=dp(theme.CARD_SPACING),
            padding=dp(theme.CARD_PADDING),
            **kwargs
        )

        self.on_save = on_save
        self.categories = []
        self.category_names_by_id = {}

        # Alle Angabe-Zeilen in Anzeigereihenfolge, plus die aktuell
        # ausgeblendeten. Ausgeblendete Zeilen werden aus dem Layout
        # ENTFERNT statt nur auf Höhe 0 gesetzt: eine Zeile mit Höhe 0
        # bekommt von der BoxLayout trotzdem ihren Abstand zugeteilt,
        # wodurch zwischen zwei sichtbaren Angaben eine unnatürlich
        # große Lücke entstünde (siehe _relayout_rows).
        self._row_order = []
        self._hidden_rows = set()

        title = KiGLabel(text="Stammdaten")
        title.set_font_size(20)
        title.set_bold(True)
        title.set_alignment("left")
        title.set_color(theme.PRIMARY_ORANGE)
        title.size_hint_y = None
        title.height = dp(30)
        self.add_widget(title)

        # -------------------------------------------------
        # Formularfelder: bei Flasche + Shot kommen einige Zeilen
        # hinzu, wodurch die Gesamthöhe die Karte sprengen kann (die
        # Karte füllt bei Nebeneinander-Anordnung immer nur die feste
        # verfügbare Höhe). Statt über den Rand zu zeichnen, bleiben
        # die Zeilen im Rahmen und sind per ScrollView erreichbar -
        # nur der Speichern-Button bleibt immer sichtbar.
        # -------------------------------------------------

        self.fields = BoxLayout(
            orientation="vertical", spacing=dp(theme.ROW_SPACING), size_hint_y=None
        )
        self.fields.bind(minimum_height=self.fields.setter("height"))

        fields_scroll = ScrollView(bar_width=dp(10), do_scroll_x=False)
        fields_scroll.add_widget(self.fields)
        self.add_widget(fields_scroll)

        # -------------------------------------------------
        # Allgemeine Angaben
        # -------------------------------------------------

        self.name_input = self._input(
            hint_text="Artikelname",
        )
        self.name_row = self._add_row("Name", self.name_input)

        # Reihenfolge: Name, Einheit, Artikeltyp, Kategorie,
        # Einkaufspreis, Verkaufspreis.
        #
        # Sie folgt dem Weg, den man beim Anlegen ohnehin geht: erst
        # was es ist, dann wohin es gehört, dann was es kostet. Die
        # Einheit steht dabei bewusst weit vorne - bei "Flasche" hängt
        # alles Weitere automatisch daran.

        self.unit_spinner = RoundedSpinner(
            text=config.ARTICLE_UNITS[0], values=config.ARTICLE_UNITS,
        )
        self.unit_row = self._add_row("Einheit", self.unit_spinner)

        self.article_type_spinner = RoundedSpinner(
            text="Einzelartikel", values=tuple(self.ARTICLE_TYPE_LABELS.values()),
        )
        self.article_type_row = self._add_row("Artikeltyp", self.article_type_spinner)

        self.category_spinner = RoundedSpinner(text="bitte wählen")
        self.category_row = self._add_row("Kategorie", self.category_spinner)

        self.purchase_price_input = self._input(
            hint_text="0,00", keyboard="numpad", on_keyboard=on_numpad,
        )
        self.purchase_price_row = self._add_row("Einkaufspreis", self.purchase_price_input)

        self.price_input = self._input(
            hint_text="0,00", keyboard="numpad", on_keyboard=on_numpad,
        )
        self.price_row = self._add_row("Verkaufspreis", self.price_input)

        self.cash_visible_switch = Switch(active=True)
        self.cash_visible_row = self._add_row(
            "Verkauf an Kasse", self.cash_visible_switch, is_switch=True
        )

        self.active_switch = Switch(active=True)
        self.active_row = self._add_row("Aktiv", self.active_switch, is_switch=True)

        # -------------------------------------------------
        # "Auch als Shot verkaufen" (nur Einheit "Flasche")
        # -------------------------------------------------

        self.shot_switch = Switch(active=False)
        self.shot_switch_row = self._add_row(
            "Auch als Shot verkaufen", self.shot_switch, is_switch=True
        )
        self.shot_switch.bind(active=self._on_shot_switch_changed)
        # Zu Beginn ist die Einheit "Stück" (nicht "Flasche") - der
        # Schalter ist daher initial irrelevant und muss hier einmalig
        # explizit versteckt werden: unit_spinner.text wird erst unten
        # gebunden, und ein Property-Wechsel auf denselben Startwert
        # löst in Kivy ohnehin kein on_text-Event aus.
        self._set_row_visible(self.shot_switch_row, False)

        self.shot_name_input = self._input(
            hint_text="z. B. Jack Daniels",
        )
        self.shot_name_row = self._add_row(
            "Name an der Kasse", self.shot_name_input, indented=True
        )

        self.shot_portion_input = self._input(
            hint_text="z. B. 20", keyboard="numpad", on_keyboard=on_numpad,
        )
        self.shot_portion_row = self._add_row(
            "Portion (ml)", self.shot_portion_input, indented=True
        )

        self.shot_price_input = self._input(
            hint_text="0,00", keyboard="numpad", on_keyboard=on_numpad,
        )
        self.shot_price_row = self._add_row(
            "Preis je Shot", self.shot_price_input, indented=True
        )

        self.shot_category_spinner = RoundedSpinner(text="bitte wählen")
        self.shot_category_row = self._add_row(
            "Kategorie", self.shot_category_spinner, indented=True
        )

        for row in self._shot_detail_rows():
            self._set_row_visible(row, False)

        self.unit_spinner.bind(text=self._on_unit_changed)
        self.article_type_spinner.bind(text=self._on_article_type_changed)

        # Speichern-Button bewusst AUSSERHALB des ScrollView, direkt
        # auf der Karte - bleibt so unabhängig von der Scroll-Position
        # immer erreichbar.
        self.add_widget(self._save_button())

    # =====================================================
    # Zeilenaufbau
    # =====================================================

    def _input(self, hint_text, keyboard=None, on_keyboard=None):
        """Eingabefeld. keyboard="numpad" öffnet den Nummernblock der
        Anwendung; ohne Angabe erscheint die Tastatur des Systems."""

        field = RoundedInput(
            hint_text=hint_text, multiline=False,
            kig_keyboard_mode=keyboard or "text",
        )
        field.foreground_color = theme.TEXT_PRIMARY
        field.hint_text_color = theme.TEXT_SECONDARY

        if keyboard == "numpad":
            field.numpad_callback = on_keyboard

        return field

    def _add_row(self, caption, widget, is_switch=False, indented=False):
        """Eine Angabe: Bezeichnung links, Feld rechts."""

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(self.ROW_HEIGHT),
            spacing=dp(theme.ROW_SPACING),
            padding=(dp(self.INDENT) if indented else 0, 0, 0, 0),
        )

        label = Label(
            text=caption, color=theme.TEXT_SECONDARY,
            font_size="14sp", halign="left", valign="middle",
            size_hint_x=self.CAPTION_WIDTH,
        )
        label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        row.add_widget(label)

        if is_switch:
            # Ein Switch bringt eine feste Eigengröße mit - er wird
            # deshalb links in seinem Bereich ausgerichtet, damit alle
            # Schalter untereinander auf einer Linie stehen.
            holder = BoxLayout(size_hint_x=self.FIELD_WIDTH)
            widget.size_hint_x = None
            widget.width = dp(70)
            holder.add_widget(widget)
            holder.add_widget(BoxLayout())
            row.add_widget(holder)
        else:
            widget.size_hint_x = self.FIELD_WIDTH
            row.add_widget(widget)

        self._row_order.append(row)
        self.fields.add_widget(row)
        return row

    def _relayout_rows(self):
        """Baut die Zeilenliste neu auf und lässt ausgeblendete Zeilen
        dabei ganz weg - so entsteht zwischen zwei sichtbaren Angaben
        immer genau ein Zeilenabstand, egal wie viele Zeilen dazwischen
        gerade verborgen sind."""

        self.fields.clear_widgets()

        for row in self._row_order:
            if row not in self._hidden_rows:
                self.fields.add_widget(row)

    def _shot_detail_rows(self):

        return (
            self.shot_name_row,
            self.shot_portion_row,
            self.shot_price_row,
            self.shot_category_row,
        )

    def _set_row_visible(self, row, visible):

        row.opacity = 1 if visible else 0
        row.disabled = not visible

        if visible:
            self._hidden_rows.discard(row)
        else:
            self._hidden_rows.add(row)

        self._relayout_rows()

    # =====================================================
    # Abhängigkeiten zwischen den Feldern
    # =====================================================

    def _on_unit_changed(self, _instance, value):
        """Bei "Flasche" sind Verkaufspreis, Kategorie, Artikeltyp und
        der Verkauf-Schalter irrelevant - sie werden automatisch auf
        die einzig sinnvollen Werte gesetzt und ausgeblendet, statt sie
        abzufragen. Nur bei "Flasche" ergibt "Auch als Shot verkaufen"
        überhaupt einen Sinn."""

        is_bottle = value == config.BOTTLE_UNIT

        self._set_row_visible(self.price_row, not is_bottle)
        self._set_row_visible(self.category_row, not is_bottle)
        self._set_row_visible(self.article_type_row, not is_bottle)
        self._set_row_visible(self.cash_visible_row, not is_bottle)
        self._set_row_visible(self.shot_switch_row, is_bottle)

        if is_bottle:
            self.price_input.text = "0,00"
            self.article_type_spinner.text = "Einzelartikel"
            self.cash_visible_switch.active = False

            zutat_id = self._get_category_id(self.BOTTLE_CATEGORY_NAME)
            if zutat_id is not None:
                self.set_category_by_id(zutat_id)
        else:
            self.shot_switch.active = False

    def _on_article_type_changed(self, _instance, value):
        """Mix-/Rezeptartikel haben keinen eigenen Einkaufspreis - der
        gilt bereits auf den verwendeten Zutaten."""

        is_mix = value == "Mix / Rezept"

        self._set_row_visible(self.purchase_price_row, not is_mix)

        if is_mix:
            self.purchase_price_input.text = "0,00"

    def _on_shot_switch_changed(self, _instance, active):

        for row in self._shot_detail_rows():
            self._set_row_visible(row, active)

        if active and not self.shot_name_input.text.strip():
            # Vorschlag für den Kassennamen des Shots: NICHT einfach
            # den Flaschennamen übernehmen, sonst kollidiert der neue
            # Shot-Artikel beim Speichern sofort mit der Flasche selbst
            # (gleicher Name). Üblich ist ein "Flasche "-Präfix im
            # Flaschennamen (z. B. "Flasche Jack Daniels") - das wird
            # abgeschnitten, sonst bleibt das Feld bewusst leer und der
            # Nutzer vergibt selbst einen eindeutigen Namen.
            base_name = self.name_input.text.strip()
            lowered = base_name.lower()
            if lowered.startswith("flasche "):
                suggestion = base_name[len("flasche "):].strip()
            elif lowered.startswith("flasche"):
                suggestion = base_name[len("flasche"):].strip()
            else:
                suggestion = ""

            if suggestion and suggestion.lower() != base_name.lower():
                self.shot_name_input.text = suggestion

    def _save_button(self):
        button = Button(
            text="Speichern", size_hint_y=None, height=dp(54),
            background_normal="", background_down="",
            background_color=theme.PRIMARY_ORANGE, color=theme.TEXT_WHITE,
            font_size="16sp", bold=True,
        )
        button.bind(on_release=lambda *_args: self.on_save())
        return button

    # =====================================================
    # Kategorien
    # =====================================================

    def set_categories(self, categories):
        self.categories = categories
        self.category_names_by_id = {c["id"]: c["name"] for c in categories}
        self.category_spinner.values = tuple(c["name"] for c in categories)
        self.shot_category_spinner.values = tuple(c["name"] for c in categories)

    def set_category_by_id(self, category_id):
        name = self.category_names_by_id.get(category_id)
        if name:
            self.category_spinner.text = name

    def _get_category_id(self, name):
        for category in self.categories:
            if category["name"] == name:
                return category["id"]
        return None

    # =====================================================
    # Artikel laden / leeren
    # =====================================================

    def load_article(self, article):

        self.name_input.text = article["name"]
        # Cursor an den Anfang: sonst zeigt das Feld bei langen Namen
        # nur das Ende des Textes ("...Orangenscheibe").
        self.name_input.cursor = (0, 0)

        # Einheit zuerst setzen: löst _on_unit_changed() aus, das bei
        # "Flasche" Preis/Kategorie/Typ/Verkauf auf die Vorgabewerte
        # setzt - die folgenden Zeilen überschreiben das anschließend
        # mit den tatsächlich gespeicherten Werten dieses Artikels.
        self.unit_spinner.text = article["stock_unit"] if "stock_unit" in article.keys() else config.ARTICLE_UNITS[0]

        self.price_input.text = f"{article['price']:.2f}".replace(".", ",")
        self.purchase_price_input.text = f"{article['purchase_price']:.2f}".replace(".", ",")

        self.set_category_by_id(article["category_id"])

        article_type = article["article_type"] if "article_type" in article.keys() else "SINGLE"
        self.article_type_spinner.text = self.ARTICLE_TYPE_LABELS.get(article_type, "Einzelartikel")

        self.cash_visible_switch.active = bool(
            article["cash_visible"] if "cash_visible" in article.keys() else True
        )
        self.active_switch.active = bool(article["active"]) if "active" in article.keys() else True

        # Shot-Verknüpfung wird separat über load_shot_info() geladen,
        # da sie eine zusätzliche Datenbankabfrage benötigt (welcher
        # Mix-Artikel ist verknüpft, welche Portionsgröße hat er).
        self.shot_switch.active = False

    def load_shot_info(self, shot_article, portion_ml):
        """shot_article: der verknüpfte Mix-Artikel (dict/Row) oder
        None, falls (noch) keiner existiert. portion_ml: die für
        diese Flasche im Rezept hinterlegte Menge."""

        if shot_article is None:
            self.shot_switch.active = False
            self.shot_name_input.text = ""
            self.shot_portion_input.text = ""
            self.shot_price_input.text = ""
            return

        self.shot_name_input.text = shot_article["name"]
        self.shot_price_input.text = f"{shot_article['price']:.2f}".replace(".", ",")
        self.shot_portion_input.text = (
            str(int(portion_ml)) if portion_ml and float(portion_ml).is_integer()
            else (f"{portion_ml:.2f}".replace(".", ",") if portion_ml else "")
        )
        if shot_article["category_id"] in self.category_names_by_id:
            self.shot_category_spinner.text = self.category_names_by_id[shot_article["category_id"]]

        self.shot_switch.active = True

    def clear(self, category_id=None):

        self.name_input.text = ""
        self.unit_spinner.text = config.ARTICLE_UNITS[0]
        self.price_input.text = ""
        self.purchase_price_input.text = ""
        self.category_spinner.text = "bitte wählen"
        self.article_type_spinner.text = "Einzelartikel"
        self.cash_visible_switch.active = True
        self.active_switch.active = True

        self.shot_switch.active = False
        self.shot_name_input.text = ""
        self.shot_portion_input.text = ""
        self.shot_price_input.text = ""
        self.shot_category_spinner.text = "bitte wählen"

        if category_id is not None:
            self.set_category_by_id(category_id)

    # =====================================================
    # Daten auslesen
    # =====================================================

    def get_data(self):

        name = self.name_input.text.strip()
        if not name:
            return None

        try:
            price = float(self.price_input.text.strip().replace(",", "."))
            purchase_price = float(self.purchase_price_input.text.strip().replace(",", ".") or 0)
        except ValueError:
            return None

        category_id = self._get_category_id(self.category_spinner.text)
        if category_id is None:
            return None

        article_type = "MIX" if self.article_type_spinner.text == "Mix / Rezept" else "SINGLE"

        data = {
            "name": name,
            "price": price,
            "purchase_price": purchase_price,
            "category_id": category_id,
            "category_name": self.category_spinner.text,
            "article_type": article_type,
            "cash_visible": self.cash_visible_switch.active,
            "active": self.active_switch.active,
            "stock_unit": self.unit_spinner.text,
            "shot_enabled": False,
            "shot_name": None,
            "shot_price": None,
            "shot_portion_ml": None,
            "shot_category_id": None,
        }

        if self.unit_spinner.text == config.BOTTLE_UNIT and self.shot_switch.active:

            shot_name = self.shot_name_input.text.strip()
            shot_category_id = self._get_category_id(self.shot_category_spinner.text)

            try:
                shot_price = float(self.shot_price_input.text.strip().replace(",", "."))
                shot_portion_ml = float(self.shot_portion_input.text.strip().replace(",", "."))
            except ValueError:
                return None

            if not shot_name or shot_category_id is None or shot_price < 0 or shot_portion_ml <= 0:
                return None

            data.update({
                "shot_enabled": True,
                "shot_name": shot_name,
                "shot_price": shot_price,
                "shot_portion_ml": shot_portion_ml,
                "shot_category_id": shot_category_id,
            })

        return data
