"""
=========================================================
KiG POS
=========================================================

Modul:
    M004.0

Datei:
    cash_screen.py

Beschreibung:
    Kassenscreen der Anwendung.

Version:
    1.0.0

Build:
    0001
=========================================================
"""

from datetime import datetime, timedelta

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

import theme
import units

from models.cart import Cart
from models.cart_item import CartItem
from models.article import Article

from database import DatabaseManager

from widgets.cash.left_panel import CashLeftPanel
from widgets.cash.cart.cart_panel import CartPanel
from widgets.cash.cart.recipe_tooltip import RecipeTooltip
from widgets.cash.edit.edit_panel import EditPanel
from widgets.common.kig_popup import KiGPopup
from widgets.common.confirm_popup import ConfirmPopup
from widgets.common.numpad.numpad_panel import NumpadPanel
from widgets.cash.payment.payment_panel import PaymentPanel


class CashScreen(Screen):

    # Warenkorb im Hochformat (siehe _update_cart_height)
    PORTRAIT_CART_MIN_HEIGHT = 300
    PORTRAIT_CART_SHARE = 0.42

    def __init__(self, revenue_changed_callback=None, **kwargs):

        super().__init__(**kwargs)

        self.cart = Cart()

        self.database = DatabaseManager()

        self.revenue_changed_callback = revenue_changed_callback

        # Aktuell bearbeitete Position
        self.current_cart_item = None

        # Läuft gerade ein Tipp aus der Schnellwahl? Siehe
        # payment_shortcut - der Nummernblock meldet die Änderung
        # zurück, und die Rückmeldung muss unterscheiden können,
        # woher der Betrag kam.
        self._schnellwahl_laeuft = False

        # Im Storno-Modus sammelt derselbe Warenkorb die Artikel, die
        # zurückgenommen werden sollen. Gebucht wird daraus dann eine
        # Gegenbuchung mit negativen Mengen (siehe book_storno).
        self.storno_mode = False

        # Im Hochformat stehen Artikel und Warenkorb übereinander
        # statt nebeneinander (siehe theme.set_orientation).
        self.hochformat = theme.is_portrait()

        # =====================================================
        # Hauptlayout
        # =====================================================

        self.layout = BoxLayout(
            orientation="vertical" if self.hochformat else "horizontal",
            spacing=dp(theme.SCREEN_SPACING),
            padding=dp(theme.SCREEN_PADDING)
        )

        # =====================================================
        # Linkes Panel
        # =====================================================

        categories = self.database.get_categories()

        # Hochformat: Artikelbereich oben, Warenkorb unten. Der
        # Artikelbereich nimmt dabei den Platz, den der Warenkorb übrig
        # lässt (siehe _update_cart_height) - auf einem hohen Bildschirm
        # kommt der gewonnene Raum so den Artikeln zugute.
        self.left_panel = CashLeftPanel(
            categories=categories,
            size_hint=(1, 1),
            article_callback=self.article_selected,
            category_articles_callback=self.get_category_articles
        )

        # =====================================================
        # Edit Panel
        # =====================================================

        self.edit_panel = EditPanel(
            price_callback=self.edit_price_clicked,
            quantity_callback=self.edit_quantity_clicked,
            apply_callback=self.edit_confirmed,
            delete_callback=self.delete_clicked,
            duplicate_callback=self.duplicate_clicked
        )

        # =====================================================
        # Payment Panel
        # =====================================================

        self.payment_panel = PaymentPanel(
            cancel_callback=self.payment_cancelled,
            ok_callback=self.payment_confirmed,
            shortcut_callback=self.payment_shortcut,
        )

        # =====================================================
        # Numpad Panel
        # =====================================================

        self.numpad_panel = NumpadPanel()

        # =====================================================
        # Rechtes Panel
        # =====================================================

        self.right_panel = CartPanel(
            size_hint=(1, None) if self.hochformat else (None, 1),
            width=dp(theme.CART_PANEL_WIDTH),
            edit_callback=self.edit_clicked,
            pay_callback=self.pay_clicked,
            clear_callback=self.clear_cart_clicked,
            tap_callback=self.show_recipe_tooltip,
            quantity_callback=self.change_cart_quantity,
            storno_callback=lambda *_args: self.start_storno(),
            storno_confirm_callback=lambda *_args: self.confirm_storno(),
            storno_cancel_callback=lambda *_args: self.cancel_storno()
        )

        # =====================================================
        # Layout
        # =====================================================

        # Die drei einklappbaren Panels liegen ÜBER der Oberfläche,
        # nicht als eigene Spalte darin. Beim Aufgehen rückt deshalb
        # nichts zusammen: Kategorien, Artikel und Warenkorb behalten
        # ihren Platz, das Panel legt sich darüber.
        self.root_layout = FloatLayout()

        self.layout.size_hint = (1, 1)
        self.root_layout.add_widget(self.layout)

        for panel in self.overlay_panels:

            panel.init_slide(panel.slide_width, overlay=True)

            # "disabled" meldet, dass ein Panel zu ist - dann kommt es
            # aus der Oberfläche heraus (siehe _render_overlays). Die
            # Breite ändert sich während der Animation; das Panel
            # wächst nach links aus seinem rechten Rand heraus und muss
            # dabei laufend neu gesetzt werden.
            panel.bind(
                disabled=lambda *_args: self._render_overlays(),
                width=lambda *_args: self._position_panels(),
            )

        self.layout.bind(
            pos=lambda *_args: self._position_panels(),
            size=lambda *_args: self._position_panels(),
        )

        if self.hochformat:
            self.layout.bind(height=lambda *_args: self._update_cart_height())
            self._update_cart_height()

        self._render_layout()

        self.add_widget(self.root_layout)

    # =====================================================
    # Überlagernde Panels
    # =====================================================

    @property
    def overlay_panels(self):
        """Die einklappbaren Panels - vorne das, was gewinnt, wenn
        mehrere offen sind (der Nummernblock liegt über dem
        Bearbeiten-Panel: Er ist das, worauf gerade getippt wird)."""

        return (self.numpad_panel, self.payment_panel, self.edit_panel)

    def _render_overlays(self, *_args):
        """Hängt die offenen Panels über die Oberfläche - und nimmt die
        geschlossenen wieder heraus.

        Ein geschlossenes Panel bleibt bewusst NICHT unsichtbar liegen.
        Kivy lässt ein abgeschaltetes Widget jede Berührung
        verschlucken, die auf seine Fläche fällt (widget.py:
        "if self.disabled and self.collide_point ..."), und zwar auch
        dann, wenn nur noch einzelne Kinder dort stehen: Ein Panel auf
        Größe 0 zu setzen genügt nicht, denn seine Kinder behalten ihre
        Maße und erben das "disabled". Genau das hat die Kasse im
        Hochformat lahmgelegt - die Oberfläche sah normal aus, aber der
        Mengenwähler des geschlossenen Bearbeiten-Panels lag unsichtbar
        über den Kategorien.

        Was nicht im Baum hängt, kann nichts verschlucken.
        """

        for panel in self.overlay_panels:
            if panel.parent is not None:
                self.root_layout.remove_widget(panel)

        # Rückwärts hinzufügen: Kivy zeichnet später hinzugefügte
        # Widgets oben. So liegt der Nummernblock über dem
        # Bearbeiten-Panel und nicht darunter.
        for panel in reversed(self.overlay_panels):
            if not panel.disabled:
                self.root_layout.add_widget(panel)

        self._position_panels()

    def _position_panels(self, *_args):
        """Legt die offenen Panels an ihren Platz über der Oberfläche.

        Querformat: rechtsbündig am Warenkorb, über dem Artikelbereich.
        Hochformat: deckungsgleich mit dem Artikelbereich - der
        Warenkorb darunter bleibt sichtbar und bedienbar.
        """

        rand = dp(theme.SCREEN_PADDING)
        abstand = dp(theme.SCREEN_SPACING)

        # Geschlossene Panels hängen nicht in der Oberfläche und haben
        # dort auch keinen Platz zu beanspruchen.
        offene = [p for p in self.overlay_panels if p.parent is not None]

        if self.hochformat:

            # Hochformat: über den ganzen Inhaltsbereich. Nur über den
            # Artikelbereich zu legen, wäre zu wenig - der Inhalt des
            # Bearbeiten-Panels (Menge, Preis, vier Schaltflächen)
            # braucht mehr Höhe, als dort zur Verfügung steht.
            for panel in offene:
                panel.width = self.layout.width - 2 * rand
                panel.height = self.layout.height - 2 * rand
                panel.pos = (self.layout.x + rand, self.layout.y + rand)

            return

        # Querformat: von rechts nach links aufreihen, beginnend am
        # Warenkorb. Sind Nummernblock UND Bearbeiten-Panel offen,
        # stehen sie wie bisher nebeneinander - nur dass jetzt nichts
        # dafür zusammenrücken muss.
        rechter_rand = self.right_panel.x - abstand

        for panel in offene:

            panel.height = self.layout.height - 2 * rand
            panel.y = self.layout.y + rand

            panel.right = rechter_rand

            # Ein zuklappendes Panel ist noch nicht abgeschaltet, aber
            # schon schmal - der Rand rückt entsprechend mit.
            if panel.width > 0:
                rechter_rand -= panel.width + abstand

    def _update_cart_height(self):
        """Bestimmt die Höhe des Warenkorbs im Hochformat.

        Anteilig, aber mit Untergrenze: Kopfzeile, Summe und die beiden
        Schaltflächen belegen bereits rund 280 px. Ein reiner Anteil
        ließe auf kleinen Bildschirmen keine einzige Position mehr
        übrig, eine feste Höhe würde auf großen Bildschirmen den
        gewonnenen Platz verschenken.
        """

        verfuegbar = (
            self.layout.height
            - dp(theme.SCREEN_PADDING) * 2
            - dp(theme.SCREEN_SPACING)
        )

        self.right_panel.height = max(
            dp(self.PORTRAIT_CART_MIN_HEIGHT),
            verfuegbar * self.PORTRAIT_CART_SHARE
        )

    def _render_layout(self):
        """Der Grundaufbau ändert sich nie - die einklappbaren Panels
        liegen darüber (siehe _position_panels)."""

        self.layout.clear_widgets()

        self.layout.add_widget(self.left_panel)
        self.layout.add_widget(self.right_panel)

        self._position_panels()

    # =====================================================
    # Screen wird geöffnet
    # =====================================================

    def on_pre_enter(self, *args):

        # Nie im Storno-Modus landen, nur weil der Screen beim letzten
        # Mal so verlassen wurde - sonst würde ein Verkauf versehentlich
        # als Rücknahme erfasst.
        if self.storno_mode:
            self.cancel_storno()

        self.refresh_categories()
        self.left_panel.clear_selection()

        # Beim Betreten immer mit freiem Blick auf alle Artikel starten -
        # ein Suchbegriff vom letzten Mal wuerde sonst verwirren.
        self.left_panel.article_panel_widget.search_input.text = ""

        self.left_panel.article_panel_widget.set_articles(
            self.get_all_articles()
        )

    # =====================================================
    # Kategorien aktualisieren
    # =====================================================

    def refresh_categories(self):

        # Nur Kategorien mit mindestens einem an der Kasse
        # verkäuflichen Artikel anzeigen (z. B. keine reine
        # Zutat-Kategorie).
        categories = self.database.get_categories(cash_only=True)

        self.left_panel.set_categories(
            categories
        )

    # =====================================================
    # Artikel gewählt
    # =====================================================

    def article_selected(self, tile, article):

        self.cart.add(article)

        self.right_panel.refresh(self.cart)

    # =====================================================
    # Footer
    # =====================================================

    # =====================================================
    # Meldungen
    # =====================================================

    @staticmethod
    def message(title, text):

        content = BoxLayout(padding=dp(theme.CARD_PADDING))

        with content.canvas.before:
            Color(*theme.CARD)
            background = Rectangle(pos=content.pos, size=content.size)

        def update_background(instance, _value):
            background.pos = instance.pos
            background.size = instance.size

        content.bind(pos=update_background, size=update_background)

        label = Label(
            text=text, color=theme.TEXT_PRIMARY, font_size="16sp",
            halign="center", valign="middle",
        )
        label.bind(size=lambda i, v: setattr(i, "text_size", v))
        content.add_widget(label)

        KiGPopup(
            title=title, content=content, size_hint=(0.6, None),
            height=dp(220), auto_dismiss=True,
        ).open()

    # =====================================================
    # Storno
    # =====================================================

    def start_storno(self):
        """Schaltet in den Storno-Modus.

        Danach werden - genau wie beim Verkauf - die betroffenen
        Artikel angetippt; gebucht wird erst nach ausdrücklicher
        Bestätigung.
        """

        if self.storno_mode:
            return

        # Ein noch gefüllter Warenkorb und eine Rücknahme im selben
        # Behälter wären nicht auseinanderzuhalten.
        if self.cart.items:
            self.message(
                "Warenkorb nicht leer",
                "Bitte den laufenden Verkauf erst abschließen oder über "
                "\"Leeren\" verwerfen, bevor storniert wird.",
            )
            return

        self.storno_mode = True

        self.edit_panel.close()
        self.payment_panel.close()
        self.numpad_panel.close()

        self.right_panel.set_storno_mode(True)

    # -----------------------------------------------------

    def cancel_storno(self):

        self.storno_mode = False

        self.cart.clear()
        self.right_panel.set_storno_mode(False)
        self.right_panel.refresh(self.cart)

    # -----------------------------------------------------

    def confirm_storno(self):

        if not self.cart.items:
            self.message(
                "Nichts ausgewählt",
                "Bitte zuerst die Artikel antippen, die storniert werden sollen.",
            )
            return

        positionen = sum(item.quantity for item in self.cart.items)
        summe = self.cart.total()

        ConfirmPopup(
            message=(
                f"{positionen} Artikel im Wert von "
                f"{summe:.2f} EUR".replace(".", ",") + " stornieren?"
            ),
            title="Storno bestätigen",
            confirm_text="Stornieren",
            on_confirm=self.book_storno,
        ).open()

    # -----------------------------------------------------

    def book_storno(self):
        """Bucht die Gegenbuchung.

        Der Verkauf bleibt unangetastet - stattdessen entsteht ein
        zweiter Eintrag mit negativen Mengen. Umsatz und Gewinn der
        Statistik verrechnen sich dadurch von selbst.

        Beim Einkaufspreis wird unterschieden:

            Einzelartikel  verschlossen zurück ins Lager, der Einkauf
                           wird also gegengerechnet (Gewinn geht auf 0)
            Mix / Rezept   eingeschenkt und damit verbraucht - der
                           Einkauf bleibt als Verlust stehen
        """

        now = datetime.now()
        business_day = now.date()
        if now.hour < 6:
            business_day -= timedelta(days=1)

        event = self.database.get_event_for_date(business_day.isoformat())

        items = []

        for cart_item in self.cart.items:

            article = cart_item.article

            if article.article_type == "MIX":
                einkaufspreis = 0.0
            else:
                einkaufspreis = article.purchase_price

            items.append({
                "article_id": article.id,
                "name": article.name,
                "quantity": -cart_item.quantity,
                "price": cart_item.unit_price,
                "purchase_price": einkaufspreis,
                "line_total": -cart_item.total_price,
            })

        summe = -self.cart.total()

        self.database.save_sale(
            event_id=event["id"] if event is not None else None,
            payment_type="STORNO",
            subtotal=summe,
            deposit_total=0,
            total=summe,
            received=0,
            change=0,
            items=items,
        )

        self.restore_stock_for_storno()

        self.cart.clear()
        self.storno_mode = False
        self.right_panel.set_storno_mode(False)
        self.right_panel.refresh(self.cart)

        self.refresh_article_stock_display()

        if callable(self.revenue_changed_callback):
            self.revenue_changed_callback()

        self.message(
            "Storno gebucht",
            "Der Vorgang wurde als Gegenbuchung erfasst und erscheint "
            "in der Statistik.",
        )

    # -----------------------------------------------------

    def restore_stock_for_storno(self):
        """Bucht zurückgenommene Ware wieder ein.

        Nur Einzelartikel: Die kommen verschlossen zurück ins Regal.
        Ein eingeschenkter Mix-Artikel ist verbraucht - dessen Zutaten
        wieder gutzuschreiben würde den Bestand zu hoch ausweisen.
        """

        for cart_item in self.cart.items:

            article = cart_item.article

            if article.article_type == "MIX":
                continue

            alter_bestand = self.database.get_stock_quantity(article.id)
            neuer_bestand = alter_bestand + cart_item.quantity

            self.database.update_stock(article.id, neuer_bestand)
            self.database.add_stock_history(
                article_id=article.id,
                old_quantity=alter_bestand,
                new_quantity=neuer_bestand,
                reason="Storno",
                changed_by="Kasse",
                changed_at=self.database.timestamp(),
            )

    # -----------------------------------------------------

    def change_cart_quantity(self, cart_item, veraenderung):
        """Erhöht oder verringert die Menge einer Warenkorbposition.

        Bei 0 verschwindet die Position ganz - das ist der schnellste
        Weg, einen versehentlich angetippten Artikel wieder loszuwerden.
        """

        neue_menge = cart_item.quantity + veraenderung

        if neue_menge <= 0:
            self.cart.remove(cart_item)
        else:
            cart_item.quantity = neue_menge

        self.right_panel.refresh(self.cart)

        # Das Bearbeiten-Panel zeigte sonst weiter die alte Menge einer
        # Position, die es womöglich gar nicht mehr gibt.
        self.edit_panel.close()
        self.current_cart_item = None

    # -----------------------------------------------------

    def show_recipe_tooltip(self, widget, cart_item):
        """Zeigt bei Mix-/Rezeptartikeln die Zusammensetzung als
        Sprechblasen-Hinweis - eine Gedächtnisstütze für die Bar, was
        genau in den Warenkorb-Artikel hineingehört. Schließt sich
        automatisch, sobald irgendwo anders hingetippt wird (siehe
        RecipeTooltip.auto_dismiss)."""

        article = cart_item.article

        if article.article_type != "MIX":
            return

        ingredients = self.database.get_recipe_ingredients(article.id)

        lines = []
        for ingredient in ingredients:
            quantity = ingredient["quantity"]
            quantity_text = (
                str(int(quantity)) if float(quantity).is_integer()
                else f"{quantity:.2f}".replace(".", ",")
            )
            unit = ingredient["unit"] or ""
            lines.append(f"{quantity_text} {unit}  {ingredient['name']}".strip())

        RecipeTooltip(article_name=article.name, ingredient_lines=lines).open()

    # -----------------------------------------------------

    def edit_clicked(self, tile, action):

        cart_item = self.right_panel.selected_item

        if cart_item is None:
            return

        self.edit_panel.open(cart_item)

    # -----------------------------------------------------

    def pay_clicked(self, tile, action):

        if len(self.cart.items) == 0:
            return

        total = self.cart.total()

        self.payment_panel.open(total)

        self.open_numpad(
            value=0,
            mode="price",
            confirm_callback=None,
            cancel_callback=self.payment_cancelled,
            change_callback=self.payment_amount_changed
        )

    # =====================================================
    # Edit Panel
    # =====================================================

    def edit_price_clicked(self, cart_item):

        if cart_item is None:
            return

        self.current_cart_item = cart_item

        price = int(cart_item.unit_price * 100)

        self.open_numpad(
            value=price,
            mode="price",
            confirm_callback=self.numpad_confirmed,
            cancel_callback=self.numpad_cancelled
        )

    # -----------------------------------------------------

    def cart_item_changed(self):

        self.right_panel.refresh(self.cart)

    # =====================================================
    # Numpad
    # =====================================================

    def open_numpad(
            self,
            value=0,
            mode="price",
            confirm_callback=None,
            cancel_callback=None,
            change_callback=None
    ):

        self.numpad_panel.open(
            value=value,
            mode=mode,
            confirm_callback=confirm_callback,
            cancel_callback=cancel_callback,
            change_callback=change_callback
        )

    # =====================================================
    # Numpad Callback
    # =====================================================

    def numpad_confirmed(self, value):

        print("Numpad bestätigt:", value)

        if self.current_cart_item is None:
            print("Kein current_cart_item")
            return

        print("Alt:", self.current_cart_item.unit_price)

        self.current_cart_item.unit_price = value / 100

        print("Neu:", self.current_cart_item.unit_price)

        self.right_panel.refresh(self.cart)

        self.edit_panel.open(self.current_cart_item)

        self.current_cart_item = None

    # -----------------------------------------------------

    def numpad_cancelled(self):

        self.current_cart_item = None

    def edit_confirmed(
            self,
            cart_item,
            quantity
    ):

        cart_item.quantity = quantity

        self.right_panel.refresh(self.cart)

        self.edit_panel.close()

        self.current_cart_item = None

    def edit_quantity_clicked(self, cart_item):

        if cart_item is None:
            return

        self.current_cart_item = cart_item

        self.open_numpad(
            value=cart_item.quantity,
            mode="integer",
            confirm_callback=self.quantity_confirmed,
            cancel_callback=self.numpad_cancelled
        )

    def quantity_confirmed(self, value):

        self.edit_panel.quantity_editor.set_quantity(value)

        self.numpad_panel.close()

    def delete_clicked(self, cart_item):

        if cart_item is None:
            return

        self.cart.remove(cart_item)

        self.right_panel.refresh(self.cart)

        self.edit_panel.close()

        self.current_cart_item = None

    def duplicate_clicked(self, cart_item):
        if cart_item is None:
            return

        new_item = CartItem(cart_item.article)

        new_item.quantity = 1
        new_item.unit_price = cart_item.unit_price

        self.cart.add_item(new_item)

        self.right_panel.refresh(self.cart)

        self.edit_panel.close()

        self.current_cart_item = None

    def clear_cart_clicked(self):

        self.cart.clear()

        self.right_panel.refresh(self.cart)

        self.edit_panel.close()

        self.current_cart_item = None

    def payment_amount_changed(self, value):

        amount = value / 100

        self.payment_panel.set_paid_amount(amount)

        # Kommt der Betrag NICHT aus der Schnellwahl, sondern vom
        # Nummernblock, stimmt die Aufstellung der gelegten Scheine
        # nicht mehr - dann lieber keine als eine falsche.
        if not self._schnellwahl_laeuft:
            self.payment_panel.scheine_zuruecksetzen()

    def payment_shortcut(self, betrag):
        """Ein Tipp auf einen Schein in der Schnellwahl.

        Der Schein wird DAZUGELEGT, nicht ersetzt: Wer 40 Euro
        bekommt, tippt zweimal auf 20 - so, wie das Geld auch auf den
        Tresen wandert.

        Gesetzt wird die Summe im Nummernblock, nicht direkt in der
        Anzeige: Von dort kommt sie auf demselben Weg zurück wie ein
        getippter Betrag (change_callback). So gibt es nur einen Weg,
        auf dem sich der gegebene Betrag ändert - und der
        Nummernblock zeigt danach dieselbe Zahl, statt weiter auf
        seinem alten Stand zu stehen.
        """

        neuer_wert = (
            self.numpad_panel.get_value() + int(round(betrag * 100))
        )

        # Der Nummernblock meldet die Änderung sofort zurück; ohne
        # diese Klammer hielte payment_amount_changed sie für eine
        # Eingabe von Hand und würfe die Aufstellung weg.
        self._schnellwahl_laeuft = True

        try:
            self.numpad_panel.set_value(neuer_wert)
        finally:
            self._schnellwahl_laeuft = False

        self.payment_panel.schein_gelegt(betrag)

    def payment_cancelled(self):

        self.payment_panel.close()

        self.numpad_panel.close()

    def payment_confirmed(self):

        if self.payment_panel.paid < self.payment_panel.total:
            return

        # Der Bestand wird ausschließlich nach erfolgreicher Zahlung
        # angepasst. Das bloße Leeren des Warenkorbs bleibt folgenlos.
        self.save_paid_sale()
        self.reduce_stock_for_paid_cart()

        self.cart.clear()

        self.right_panel.refresh(self.cart)

        self.payment_panel.close()

        self.numpad_panel.close()

        self.current_cart_item = None

        self.refresh_article_stock_display()

        if callable(self.revenue_changed_callback):
            self.revenue_changed_callback()

    def reduce_stock_for_paid_cart(self):
        """Zieht die im bezahlten Warenkorb enthaltenen Mengen ab.

        Rezeptmengen können in einer anderen (aber umrechenbaren)
        Einheit hinterlegt sein als die Zutat selbst gelagert wird
        (z. B. Rezept "0,02 l", Lagerbestand in "ml"). Der Abzug
        erfolgt daher immer in der aktuellen Lagereinheit des
        Artikels - dafür wird die Rezeptmenge zunächst exakt
        umgerechnet.
        """

        quantities = {}

        for cart_item in self.cart.items:
            article = cart_item.article
            if article.article_type == "MIX":
                for ingredient in self.database.get_recipe_ingredients(article.id):
                    ingredient_id = ingredient["ingredient_article_id"]

                    # "Flasche" hat keinen festen ml-Wert - der
                    # tatsächliche Bestand einer Flasche-Zutat wird
                    # immer in ml geführt (siehe config.BOTTLE_UNIT),
                    # daher gilt sie hier wie ml.
                    stock_dimension_unit = units.stock_dimension_unit(
                        ingredient["article_stock_unit"]
                    )

                    converted = units.convert(
                        ingredient["quantity"],
                        ingredient["unit"],
                        stock_dimension_unit
                    )

                    if converted is None:
                        # Sollte dank der Absicherung in
                        # set_recipe_ingredient() nicht mehr vorkommen
                        # (z. B. nur bei nachträglich von Hand
                        # geänderter Lagereinheit der Zutat). Lieber
                        # den Abzug für diese Zutat auslassen, als
                        # mit falschem Faktor zu rechnen.
                        self.database.logger.warning(
                            "Lagerabzug übersprungen: Einheit '%s' der "
                            "Rezeptzutat %s passt nicht zur Lagereinheit "
                            "'%s'.",
                            ingredient["unit"], ingredient_id,
                            stock_dimension_unit
                        )
                        continue

                    quantities[ingredient_id] = (
                        quantities.get(ingredient_id, 0)
                        + converted * cart_item.quantity
                    )
            else:
                quantities[article.id] = (
                    quantities.get(article.id, 0) + cart_item.quantity
                )

        for article_id, quantity in quantities.items():
            current_stock = self.database.get_stock_quantity(article_id)
            new_stock = current_stock - quantity
            self.database.update_stock(article_id, new_stock)
            self.database.add_stock_history(
                article_id=article_id,
                old_quantity=current_stock,
                new_quantity=new_stock,
                reason="Verkauf",
                changed_by="Kasse",
                changed_at=self.database.timestamp(),
            )

    def save_paid_sale(self):
        """Speichert den Abschluss für die spätere Statistik.

        Verkäufe werden dem Event des Geschäftstags zugeordnet. Ein
        Geschäftstag läuft jeweils von 06:00 Uhr bis 05:59 Uhr des Folgetags.
        """

        now = datetime.now()
        business_day = now.date()
        if now.hour < 6:
            business_day -= timedelta(days=1)

        event = self.database.get_event_for_date(business_day.isoformat())

        items = [
            {
                "article_id": item.article.id,
                "name": item.article.name,
                "quantity": item.quantity,
                "price": item.unit_price,
                "purchase_price": self._purchase_price_for_sale(item.article),
                "line_total": item.total_price,
            }
            for item in self.cart.items
        ]

        total = self.cart.total()
        self.database.save_sale(
            event_id=event["id"] if event is not None else None,
            payment_type="BAR",
            subtotal=total,
            deposit_total=0,
            total=total,
            received=self.payment_panel.paid,
            change=self.payment_panel.change,
            items=items,
        )

    def _purchase_price_for_sale(self, article):
        """Einkaufspreis für die Statistik: bei Mix-/Rezeptartikeln
        (deren eigener purchase_price immer 0 ist - der Preis steckt
        ja in den Zutaten, siehe dashboard_stammdaten_card.py) wird er
        aus den aktuellen Zutatenpreisen berechnet (siehe
        database.py:get_recipe_cost). Bei Einzelartikeln gilt weiter
        direkt der hinterlegte Einkaufspreis."""

        if article.article_type != "MIX":
            return article.purchase_price

        cost = self.database.get_recipe_cost(article.id)

        return cost if cost is not None else article.purchase_price

    def refresh_article_stock_display(self):
        """Aktualisiert die sichtbaren Kacheln mit den neuen Beständen."""

        self.left_panel.article_panel_widget.set_articles(
            self.get_category_articles(self.left_panel.selected_category)
        )

    def get_category_articles(self, category):

        if category is None:
            return self.get_all_articles()

        category_id = category["id"]

        rows = self.database.get_articles_by_category(
            category_id,
            cash_only=True
        )

        articles = []

        for row in rows:
            article = Article(
                id=row["id"],
                category_id=category_id,
                name=row["name"],
                price=row["price"],
                stock=self._article_stock(row),
                purchase_price=row["purchase_price"],
                article_type=row["article_type"],
                stock_unit=row["stock_unit"]
            )

            articles.append(article)

        return articles

    def get_all_articles(self):
        """Lädt alle aktiven Artikel für die ungefilterte Kassenansicht."""

        rows = self.database.get_articles(active_only=True, cash_only=True)

        return [
            Article(
                id=row["id"],
                category_id=row["category_id"],
                name=row["name"],
                price=row["price"],
                stock=self._article_stock(row),
                purchase_price=row["purchase_price"],
                article_type=row["article_type"],
                stock_unit=row["stock_unit"]
            )
            for row in rows
        ]

    def _article_stock(self, row):
        """Verfügbare Menge für die Kachel-Anzeige.

        Mix-/Rezeptartikel führen keinen eigenen Bestand - verkäuflich
        ist, was die knappste Zutat noch hergibt (siehe
        database.py:get_recipe_available_quantity). Bislang stand hier
        immer 0, da nur der Bestand des Artikels selbst abgefragt
        wurde."""

        if row["article_type"] == "MIX":
            return self.database.get_recipe_available_quantity(row["id"]) or 0

        return self.database.get_stock_quantity(row["id"])

