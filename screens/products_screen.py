"""
=========================================================
KiG POS
=========================================================

Datei:
    products_screen.py

Beschreibung:
    Zusammengeführte Artikelverwaltung.

    Fasst die früher getrennten Screens Artikel, Einkauf,
    Inventar und Rezepte an einem Ort zusammen:

        • Liste: alle Artikel mit Preis, Bestand und
          Bestellmenge (Kategorie-Filter links).
        • "Bearbeiten" öffnet pro Artikel ein Dashboard mit
          Stammdaten, Bestand (inkl. Historie), Bestellmenge
          und - bei Mix-/Rezeptartikeln - der Zusammensetzung.
          Das Dashboard ersetzt dabei die Liste vollständig.

Version:
    3.0.0
=========================================================
"""

import csv
from datetime import datetime

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

import config
import storage
import theme
import units

from database import DatabaseManager

from widgets.products.category_panel import CategoryPanel
from widgets.products.category_dialog import CategoryDialog
from widgets.products.article_list_panel import ArticleListPanel
from widgets.products.article_dashboard_panel import ArticleDashboardPanel
from widgets.products.product_sort_dialog import ProductSortDialog
from widgets.products.bottle_size_popup import BottleSizePopup
from widgets.common.confirm_popup import ConfirmPopup
from widgets.common.numpad.numpad_panel import NumpadPanel
from widgets.inventory.stock_adjustment_dialog import StockAdjustmentDialog


class ProductsScreen(Screen):
    """Zentrale Steuerklasse der zusammengeführten Artikelverwaltung."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.db = DatabaseManager()

        self.mode = "list"

        self.categories = []
        self.selected_category = None
        self.selected_category_card = None

        self.selected_article = None
        self.order_amounts = {}

        self.current_price_input = None
        self.editing_ingredient_id = None
        self.editing_ingredient_unit = None
        self.editing_ingredient_row_id = None

        self.root_layout = self._build_ui()
        self.add_widget(self.root_layout)

    # =====================================================
    # Oberfläche
    # =====================================================

    def _build_ui(self):

        # Im Hochformat stehen Kategorien und Artikelliste übereinander
        # statt nebeneinander (siehe theme.set_orientation).
        self.hochformat = theme.is_portrait()

        self.root = BoxLayout(
            orientation="vertical" if self.hochformat else "horizontal",
            spacing=dp(theme.SCREEN_SPACING),
            padding=dp(theme.SCREEN_PADDING),
        )

        self.category_panel = CategoryPanel(
            on_new=self.new_category, on_edit=self.edit_category,
        )

        if self.hochformat:
            self.category_panel.size_hint = (1, 0.26)
        else:
            self.category_panel.size_hint_x = 0.22

        self.article_list_panel = ArticleListPanel(
            new_callback=self.new_article,
            amount_callback=self.open_order_amount_numpad,
            confirm_callback=self.receive_order_from_list,
            edit_callback=self.edit_article,
            delete_callback=self.delete_article_from_list,
            sort_callback=self.open_sort_dialog,
            export_callback=self.export_order_list,
        )

        if self.hochformat:
            self.article_list_panel.size_hint = (1, 0.74)
        else:
            self.article_list_panel.size_hint_x = 0.78

        self.dashboard_panel = ArticleDashboardPanel(
            on_back=self.back_to_list,
            on_save=self.save_stammdaten,
            on_numpad=self.open_price_numpad,
            on_adjust_stock=self.open_stock_adjustment,
            on_order_amount_button=self.open_dashboard_order_numpad,
            on_receive_order=self.receive_order,
            on_recipe_quantity=self.edit_ingredient_quantity,
            on_recipe_unit=self.change_ingredient_unit,
            on_recipe_remove=self.remove_recipe_ingredient,
            on_recipe_add_amount=self.open_add_ingredient_numpad,
            on_recipe_add_confirm=self.add_ingredient_clicked,
            on_recipe_add_free_text_amount=self.open_add_free_text_ingredient_numpad,
            on_recipe_add_free_text_confirm=self.add_free_text_ingredient_clicked,
        )

        self.numpad_panel = NumpadPanel()

        # Das Numpad hängt nur im Layout, wenn es geöffnet ist - sonst
        # bliebe rechts eine zusätzliche Lücke in Breite des
        # Panel-Abstands stehen, obwohl das Panel selbst 0 breit ist.
        # "disabled" wird beim Schließen erst NACH der Animation
        # gesetzt, das Panel bleibt also sichtbar, während es zuklappt.
        self.numpad_panel.bind(disabled=lambda *_args: self._render_root())

        self._render_root()

        return self.root

    def _render_root(self):

        self.root.clear_widgets()

        # Im Hochformat fehlt die Breite für den Nummernblock neben der
        # Liste - er übernimmt dort den ganzen Inhaltsbereich und gibt
        # ihn nach "Bestätigen" oder "Abbrechen" wieder frei.
        if self.hochformat and not self.numpad_panel.disabled:
            self.root.add_widget(self.numpad_panel)
            return

        nummernblock_offen = not self.numpad_panel.disabled

        if self.mode == "list":

            # Solange der Nummernblock offen ist, tritt die
            # Kategorienkarte zur Seite: Die Artikelliste braucht ihre
            # sieben Spalten, und gefiltert wird gerade ohnehin nicht -
            # es wird eine Menge eingetippt.
            if not nummernblock_offen:
                self.root.add_widget(self.category_panel)

            self.root.add_widget(self.article_list_panel)

        else:
            self.root.add_widget(self.dashboard_panel)

        if nummernblock_offen:
            self.root.add_widget(self.numpad_panel)

    # =====================================================
    # Lifecycle
    # =====================================================

    def on_pre_enter(self, *args):

        self.mode = "list"
        self.current_price_input = None
        self.numpad_panel.close()
        self.refresh()
        self._render_root()

    def refresh(self):

        self.refresh_categories()
        self.refresh_order_amounts()
        self.refresh_articles()

    def refresh_categories(self):

        self.categories = self.db.get_categories()
        self.category_panel.set_categories(self.categories, self.select_category)
        self.dashboard_panel.stammdaten_card.set_categories(self.categories)

        self.selected_category = None
        self.selected_category_card = None

    def refresh_order_amounts(self):

        self.order_amounts = {
            item["article_id"]: item["quantity"] for item in self.db.get_order_items()
        }

    def refresh_articles(self):

        # Nur aktive Artikel: gelöschte (= deaktivierte) Artikel sollen
        # aus der Liste verschwinden, damit "Löschen" tatsächlich für
        # eine spürbar aufgeräumtere Übersicht sorgt. Historische
        # Verkäufe bleiben trotzdem unangetastet (delete_article()
        # deaktiviert nur, statt zu löschen).
        if self.selected_category is None:
            rows = self.db.get_articles(active_only=True)
        else:
            rows = self.db.get_articles_by_category(
                self.selected_category["id"], active_only=True,
            )

        articles = []
        for row in rows:
            article = dict(row)
            if article["article_type"] != "MIX":
                article["stock"] = self.db.get_stock_quantity(article["id"])
            articles.append(article)

        self.article_list_panel.set_articles(articles, self.order_amounts)

        if self.selected_category is None:
            self.article_list_panel.set_title("Artikel")
        else:
            self.article_list_panel.set_title(f"Artikel · {self.selected_category['name']}")

    # =====================================================
    # Kategorien
    # =====================================================

    def select_category(self, card, category):

        if self.selected_category_card is card:
            card.unselect()
            self.selected_category_card = None
            self.selected_category = None
            self.refresh_articles()
            return

        if self.selected_category_card is not None:
            self.selected_category_card.unselect()

        self.selected_category_card = card
        card.select()
        self.selected_category = category
        self.refresh_articles()

    def new_category(self):

        CategoryDialog(on_save=self.save_category).open()

    def save_category(self, name):

        if not self.db.add_category(name):
            self.message("Fehler", "Kategorie konnte nicht angelegt werden.")
            return

        self.refresh_categories()
        self.refresh_articles()

    def edit_category(self):

        if self.selected_category is None:
            self.message("Keine Kategorie gewählt", "Bitte zuerst eine Kategorie auswählen.")
            return

        CategoryDialog(
            category=self.selected_category,
            on_save=self.update_category,
            on_delete=self.delete_category_from_dialog,
        ).open()

    def update_category(self, name):

        if self.selected_category is None:
            return

        updated = self.db.update_category(category_id=self.selected_category["id"], name=name)

        if not updated:
            self.message("Nicht gespeichert", "Die Kategorie konnte nicht geändert werden.")
            return

        self.refresh_categories()
        self.refresh_articles()
        self.message("Gespeichert", "Die Kategorie wurde erfolgreich geändert.")

    def delete_category_from_dialog(self, category):

        if category is None:
            return

        deleted = self.db.delete_category(category["id"])

        if not deleted:
            self.message(
                "Kategorie nicht gelöscht",
                "Die Kategorie enthält noch Artikel und kann deshalb nicht gelöscht werden.",
            )
            return

        self.refresh_categories()
        self.refresh_articles()
        self.message("Gelöscht", "Die Kategorie wurde erfolgreich gelöscht.")

    def open_sort_dialog(self):

        ProductSortDialog().open()

    # =====================================================
    # Einkaufsliste exportieren (CSV)
    # =====================================================

    def export_order_list(self):
        """Exportiert alle Artikel mit gesetzter Bestellmenge als
        Excel-kompatible CSV-Datei, um eine Einkaufsliste verschicken
        zu können."""

        items = self.db.get_order_items()

        if not items:
            self.article_list_panel.set_export_status(
                "Keine offenen Bestellmengen zum Exportieren."
            )
            return

        filename = datetime.now().strftime("einkaufsliste_%Y-%m-%d_%H-%M.csv")
        export_path = storage.export_dir("csv") / filename

        with export_path.open("w", newline="", encoding="utf-8-sig") as export_file:
            writer = csv.writer(export_file, delimiter=";")
            writer.writerow(["Kategorie", "Artikel", "Bestellmenge"])
            for item in items:
                writer.writerow([
                    item["category_name"] or "-",
                    item["article_name"],
                    item["quantity"],
                ])

        self.article_list_panel.set_export_status(f"Export erstellt: {export_path.name}")

    # =====================================================
    # Liste <-> Dashboard
    # =====================================================

    def new_article(self):

        self.selected_article = None
        self.mode = "dashboard"

        category_id = self.selected_category["id"] if self.selected_category else None
        self.dashboard_panel.show_for_new_article(category_id=category_id)

        self._render_root()

    def edit_article(self, article):

        self.selected_article = article
        self.mode = "dashboard"

        self._load_dashboard_sections(article)
        self.dashboard_panel.show_for_article(article)
        self._load_shot_info(article)

        self._render_root()

    def _reload_current_article(self):
        """Lädt den gerade bearbeiteten Artikel frisch aus der Datenbank
        (z. B. nachdem sich Artikeltyp oder Bestand geändert haben)."""

        if self.selected_article is None:
            return

        row = self.db.get_article(self.selected_article["id"])
        if row is None:
            self.back_to_list()
            return

        article = dict(row)
        self.selected_article = article
        self._load_dashboard_sections(article)
        self.dashboard_panel.show_for_article(article)
        self._load_shot_info(article)

    def _load_shot_info(self, article):
        """Lädt (falls vorhanden) den mit einer Flasche verknüpften
        Shot-Artikel in die Stammdaten-Karte - nur relevant für
        Einzelzutaten mit Einheit "Flasche" (siehe config.BOTTLE_UNIT)."""

        if article["article_type"] == "MIX" or article["stock_unit"] != config.BOTTLE_UNIT:
            return

        shot_article = self.db.get_linked_shot(article["id"])
        portion_ml = None

        if shot_article is not None:
            for ingredient in self.db.get_recipe_ingredients(shot_article["id"]):
                if ingredient["ingredient_article_id"] == article["id"]:
                    portion_ml = units.convert(ingredient["quantity"], ingredient["unit"], "ml")
                    break

        self.dashboard_panel.stammdaten_card.load_shot_info(shot_article, portion_ml)

    def _load_dashboard_sections(self, article):

        if article["article_type"] == "MIX":
            ingredients = self.db.get_ingredient_articles()
            self.dashboard_panel.rezept_card.set_ingredient_options(ingredients)
            self.dashboard_panel.rezept_card.set_recipe(
                {"id": article["id"], "name": "Zusammensetzung"}
            )
            self.dashboard_panel.rezept_card.set_ingredients(
                self.db.get_recipe_ingredients(article["id"])
            )
            self._refresh_recipe_summary(article["id"])
        else:
            stock = self.db.get_stock_quantity(article["id"])
            self.dashboard_panel.bestand_card.set_stock(
                stock, article["stock_unit"], article.get("bottle_size_ml")
            )
            self.dashboard_panel.bestand_card.set_history(
                self.db.get_stock_history(article["id"])
            )
            self.dashboard_panel.bestand_card.set_reicht_fuer(
                self._compute_reicht_fuer(article, stock)
            )
            self.dashboard_panel.bestellmenge_card.set_amount(
                self.order_amounts.get(article["id"], 0)
            )

    def _refresh_recipe_summary(self, recipe_article_id):
        """Zeigt für einen Mix-/Rezeptartikel die "umgekehrte" Sicht:
        wie oft reicht der aktuelle Zutatenbestand noch (limitiert
        durch die knappste Zutat) und was kostet eine Portion,
        berechnet aus den Einkaufspreisen der Zutaten - gilt generell
        für beliebig viele Zutaten (siehe database.py:
        get_recipe_available_quantity / get_recipe_cost)."""

        available = self.db.get_recipe_available_quantity(recipe_article_id)
        cost = self.db.get_recipe_cost(recipe_article_id)
        self.dashboard_panel.rezept_card.set_summary(available, cost)

    def _compute_reicht_fuer(self, ingredient_article, ingredient_stock):
        """Berechnet für jedes Rezept, das diese Zutat verwendet, wie
        viele Verkäufe der aktuelle Bestand noch hergibt. Mehrere
        Rezepte teilen sich dabei denselben Bestand."""

        base_unit = units.stock_dimension_unit(ingredient_article["stock_unit"])
        results = []

        for row in self.db.get_recipes_using_ingredient(ingredient_article["id"]):
            required = units.convert(row["quantity"], row["unit"], base_unit)
            if not required or required <= 0:
                continue
            results.append((row["recipe_name"], int(ingredient_stock // required)))

        return results

    def back_to_list(self):

        self.mode = "list"
        self.selected_article = None
        self.current_price_input = None
        self.numpad_panel.close()

        self.refresh_order_amounts()
        self.refresh_articles()

        self._render_root()

    # =====================================================
    # Stammdaten speichern
    # =====================================================

    def save_stammdaten(self):

        data = self.dashboard_panel.stammdaten_card.get_data()

        if data is None:
            self.message("Unvollständig", "Bitte Name, Preis und Kategorie prüfen.")
            return

        is_new_article = self.selected_article is None

        if is_new_article:

            # Neuanlage: Flaschengröße wird bewusst erst beim
            # Wareneingang/der Bestandskorrektur erfragt, nicht hier.
            saved = self.db.add_article(
                category_id=data["category_id"], name=data["name"], price=data["price"],
                purchase_price=data["purchase_price"], article_type=data["article_type"],
                cash_visible=data["cash_visible"], stock_unit=data["stock_unit"],
            )
            bottle_id = self.db.get_article_id_by_name(data["name"]) if saved else None

        else:

            # Eine bereits gemerkte Flaschengröße bleibt beim
            # Speichern der Stammdaten unangetastet - sie wird
            # ausschließlich über Wareneingang/Bestandskorrektur
            # gepflegt (siehe receive_order() / save_stock_adjustment()).
            saved = self.db.update_article(
                article_id=self.selected_article["id"], category_id=data["category_id"],
                name=data["name"], price=data["price"], purchase_price=data["purchase_price"],
                image=self.selected_article.get("image"), description=self.selected_article.get("description"),
                sort_order=self.selected_article.get("sort_order", 0), active=data["active"],
                article_type=data["article_type"], cash_visible=data["cash_visible"],
                stock_unit=data["stock_unit"], bottle_size_ml=self.selected_article.get("bottle_size_ml"),
            )
            bottle_id = self.selected_article["id"]

        if not saved:
            self.message("Nicht gespeichert", "Der Artikel konnte nicht gespeichert werden (Name evtl. bereits vergeben).")
            return

        # "Auch als Shot verkaufen": legt den verknüpften Mix-Artikel
        # an/pflegt ihn bzw. deaktiviert ihn wieder, wenn der Schalter
        # ausgeschaltet wurde. Schlägt das fehl (i. d. R. Namenskollision
        # des Shot-Namens), bleibt die Flasche selbst trotzdem gespeichert -
        # der Bearbeiten-Dialog bleibt aber offen, damit der Name sofort
        # korrigiert werden kann.
        if data["stock_unit"] == config.BOTTLE_UNIT and bottle_id is not None:

            shot_saved, shot_error = self._sync_linked_shot(bottle_id, data)

            if not shot_saved:
                row = self.db.get_article(bottle_id)
                if row is not None:
                    self.selected_article = dict(row)
                self.message("Shot nicht gespeichert", shot_error)
                if self.selected_article is not None:
                    self._reload_current_article()
                return

        self.current_price_input = None
        self.numpad_panel.close()

        if is_new_article:
            # Neuanlage: zurück zur Liste, da Bestand/Bestellmenge/Rezept
            # erst nach dem Speichern existieren.
            self.message("Gespeichert", "Der Artikel wurde erfolgreich angelegt.")
            self.back_to_list()
        else:
            self.message("Gespeichert", "Der Artikel wurde erfolgreich geändert.")
            self.refresh_order_amounts()
            self._reload_current_article()

    def _sync_linked_shot(self, bottle_id, data):
        """Legt den mit einer Flasche verknüpften Shot-Mix-Artikel an,
        aktualisiert ihn oder deaktiviert ihn wieder - je nachdem, ob
        "Auch als Shot verkaufen" (ein-)aktiviert ist.

        Der Shot bekommt einen eigenen, vom Flaschennamen verschiedenen
        Namen (siehe StammdatenCard._on_shot_switch_changed) - so lassen
        sich z. B. "Flasche Jack Daniels" (Zutat, an der Kasse
        unsichtbar) und "Jack Daniels" (Shot, an der Kasse verkäuflich)
        ohne Namenskollision gleichzeitig führen. Der Einkaufspreis des
        Shots ist immer 0, da der Einkauf bereits auf die Flasche
        gebucht wird; das Rezept des Shots besteht aus genau einer
        Zutat (der Flasche) in der angegebenen ml-Portion.

        Gibt (True, None) bei Erfolg zurück, sonst (False, Fehlermeldung).
        """

        existing_shot = self.db.get_linked_shot(bottle_id)
        existing_shot = dict(existing_shot) if existing_shot is not None else None

        if not data.get("shot_enabled"):
            if existing_shot is not None:
                self.db.delete_article(existing_shot["id"])
                self.db.set_linked_shot(bottle_id, None)
            return True, None

        shot_name = data["shot_name"]
        shot_price = data["shot_price"]
        shot_category_id = data["shot_category_id"]
        portion_ml = data["shot_portion_ml"]

        if existing_shot is not None:
            saved = self.db.update_article(
                article_id=existing_shot["id"], category_id=shot_category_id,
                name=shot_name, price=shot_price, purchase_price=0.0,
                image=existing_shot.get("image"), description=existing_shot.get("description"),
                sort_order=existing_shot.get("sort_order", 0), active=True,
                article_type="MIX", cash_visible=True, stock_unit="Stück",
            )
            shot_id = existing_shot["id"]
        else:
            # Kein verknüpfter Shot (mehr) vorhanden - aber möglicherweise
            # existiert unter demselben Namen noch ein zuvor deaktivierter
            # Shot (z. B. weil der Schalter einmal aus- und wieder
            # eingeschaltet wurde): article_exists() ignoriert active=0
            # nicht, add_article() würde also fälschlich an genau dem
            # Namen scheitern, den wir gerade wieder anlegen wollen.
            # Ein solcher inaktiver Artikel wird deshalb reaktiviert statt
            # dupliziert. Ist der gefundene Artikel dagegen noch AKTIV,
            # handelt es sich um eine echte Namenskollision mit einem
            # fremden Artikel - dann wird ganz normal abgelehnt.
            candidate_id = self.db.get_article_id_by_name(shot_name)
            candidate = self.db.get_article(candidate_id) if candidate_id is not None else None

            if candidate is not None and candidate["active"] == 0:
                saved = self.db.update_article(
                    article_id=candidate["id"], category_id=shot_category_id,
                    name=shot_name, price=shot_price, purchase_price=0.0,
                    image=candidate["image"], description=candidate["description"],
                    sort_order=candidate["sort_order"], active=True,
                    article_type="MIX", cash_visible=True, stock_unit="Stück",
                )
                shot_id = candidate["id"] if saved else None
            elif candidate is not None:
                # Aktiver, fremder Artikel mit exakt diesem Namen.
                saved = False
                shot_id = None
            else:
                saved = self.db.add_article(
                    category_id=shot_category_id, name=shot_name, price=shot_price,
                    purchase_price=0.0, article_type="MIX", cash_visible=True,
                    stock_unit="Stück",
                )
                shot_id = self.db.get_article_id_by_name(shot_name) if saved else None

        if not saved or shot_id is None:
            return False, (
                f"Der Shot-Artikel \"{shot_name}\" konnte nicht gespeichert werden "
                "(der Name ist evtl. bereits vergeben - bitte einen anderen Namen wählen)."
            )

        self.db.set_linked_shot(bottle_id, shot_id)
        self.db.set_recipe_ingredient(shot_id, bottle_id, portion_ml, "ml")

        return True, None

    # =====================================================
    # Numpad (Preisfelder)
    # =====================================================

    def open_price_numpad(self, input_widget):

        if input_widget.disabled or input_widget.locked:
            return

        self.current_price_input = input_widget

        text = input_widget.text.strip().replace(",", ".")
        try:
            value = float(text)
        except (ValueError, TypeError):
            value = 0.0

        cent_value = int(round(value * 100))

        self.numpad_panel.open(
            value=cent_value, mode="price",
            confirm_callback=self.price_numpad_confirmed,
            cancel_callback=self.price_numpad_cancelled,
        )

    def price_numpad_confirmed(self, value):

        if self.current_price_input is None:
            return

        price = value / 100
        self.current_price_input.text = f"{price:.2f}".replace(".", ",")
        self.current_price_input = None

    def price_numpad_cancelled(self):

        self.current_price_input = None

    # =====================================================
    # Bestand
    # =====================================================

    def open_stock_adjustment(self):

        if self.selected_article is None:
            return

        current_stock = self.db.get_stock_quantity(self.selected_article["id"])

        StockAdjustmentDialog(
            article=self.selected_article, current_stock=current_stock,
            on_save=self.save_stock_adjustment,
        ).open()

    def save_stock_adjustment(self, new_quantity, reason, changed_by, timestamp, bottle_size_ml=None):

        if self.selected_article is None:
            return

        article_id = self.selected_article["id"]
        old_quantity = self.db.get_stock_quantity(article_id)

        self.db.update_stock(article_id, new_quantity)
        self.db.add_stock_history(
            article_id=article_id, old_quantity=old_quantity, new_quantity=new_quantity,
            reason=reason, changed_by=changed_by, changed_at=timestamp,
        )

        # Wurde der Flaschenrechner im Korrektur-Dialog benutzt, die
        # verwendete Flaschengröße als neuen Vorgabewert merken.
        if bottle_size_ml:
            self.db.set_bottle_size(article_id, bottle_size_ml)
            self.selected_article["bottle_size_ml"] = bottle_size_ml

        self.dashboard_panel.bestand_card.set_stock(
            new_quantity, self.selected_article["stock_unit"], self.selected_article.get("bottle_size_ml")
        )
        self.dashboard_panel.bestand_card.set_history(self.db.get_stock_history(article_id))
        self.dashboard_panel.bestand_card.set_reicht_fuer(
            self._compute_reicht_fuer(self.selected_article, new_quantity)
        )

    # =====================================================
    # Bestellmenge (Liste - Schnelleingabe)
    # =====================================================

    def open_order_amount_numpad(self, article):

        self._order_amount_article = article

        self.numpad_panel.open(
            value=self.order_amounts.get(article["id"], 0), mode="integer",
            confirm_callback=self.order_amount_list_confirmed,
            cancel_callback=self.numpad_cancelled,
        )

    def order_amount_list_confirmed(self, value):

        article = getattr(self, "_order_amount_article", None)
        if article is None:
            return

        article_id = article["id"]

        if value > 0:
            self.order_amounts[article_id] = value
        else:
            self.order_amounts.pop(article_id, None)

        self.db.set_order_quantity(article_id, value)
        self.article_list_panel.update_row_amount(article_id, value)
        self._order_amount_article = None

    def receive_order_from_list(self, article):
        """Bucht den Wareneingang direkt aus der Liste heraus - ganz
        ohne den Bearbeiten-Dialog zu öffnen.

        Bei Einheit "Flasche" wird vorher die Flaschengröße erfragt,
        da der Bestand intern immer in ml geführt wird.
        """

        article_id = article["id"]
        amount = self.order_amounts.get(article_id, 0)

        if amount <= 0:
            return

        if article["stock_unit"] == config.BOTTLE_UNIT:
            BottleSizePopup(
                article_name=article["name"], bottle_count=amount,
                default_size_ml=article.get("bottle_size_ml"),
                on_confirm=lambda bottle_size_ml: self._receive_bottle_from_list(
                    article, amount, bottle_size_ml
                ),
            ).open()
            return

        self._finish_receive_order_from_list(article_id, amount)

    def _receive_bottle_from_list(self, article, bottle_count, bottle_size_ml):

        self.db.set_bottle_size(article["id"], bottle_size_ml)
        self._finish_receive_order_from_list(article["id"], bottle_count * bottle_size_ml)

    def _finish_receive_order_from_list(self, article_id, amount_to_add):

        self._credit_stock(article_id, amount_to_add)

        self.order_amounts.pop(article_id, None)
        self.db.clear_order_item(article_id)

        self.refresh_articles()

    def _credit_stock(self, article_id, amount_to_add):
        """Bucht `amount_to_add` (bereits in der internen Lagereinheit
        des Artikels, z. B. ml) dem Bestand gut und protokolliert die
        Änderung in der Historie."""

        old_stock = self.db.get_stock_quantity(article_id)
        new_stock = old_stock + amount_to_add
        self.db.update_stock(article_id, new_stock)
        self.db.add_stock_history(
            article_id=article_id, old_quantity=old_stock, new_quantity=new_stock,
            reason="Wareneingang", changed_by="Einkauf", changed_at=self.db.timestamp(),
        )
        return new_stock

    # =====================================================
    # Artikel löschen (Liste)
    # =====================================================

    def delete_article_from_list(self, article):

        self.confirm(
            f"\"{article['name']}\" wirklich löschen?",
            lambda: self._delete_article_confirmed(article),
        )

    def _delete_article_confirmed(self, article):

        self.db.delete_article(article["id"])
        self.refresh_articles()

    # =====================================================
    # Bestellmenge (Dashboard)
    # =====================================================

    def open_dashboard_order_numpad(self):

        if self.selected_article is None:
            return

        self.numpad_panel.open(
            value=self.dashboard_panel.bestellmenge_card.get_amount(), mode="integer",
            confirm_callback=self.dashboard_order_amount_confirmed,
            cancel_callback=self.numpad_cancelled,
        )

    def dashboard_order_amount_confirmed(self, value):

        if self.selected_article is None:
            return

        article_id = self.selected_article["id"]
        self.dashboard_panel.bestellmenge_card.set_amount(value)

        if value > 0:
            self.order_amounts[article_id] = value
        else:
            self.order_amounts.pop(article_id, None)

        self.db.set_order_quantity(article_id, value)

    def receive_order(self):
        """Bucht den Wareneingang im Dashboard. Bei Einheit "Flasche"
        wird vorher die Flaschengröße erfragt, da der Bestand intern
        immer in ml geführt wird."""

        if self.selected_article is None:
            return

        article = self.selected_article
        amount = self.dashboard_panel.bestellmenge_card.get_amount()

        if amount <= 0:
            return

        if article["stock_unit"] == config.BOTTLE_UNIT:
            BottleSizePopup(
                article_name=article["name"], bottle_count=amount,
                default_size_ml=article.get("bottle_size_ml"),
                on_confirm=lambda bottle_size_ml: self._receive_bottle_dashboard(
                    amount, bottle_size_ml
                ),
            ).open()
            return

        self._finish_receive_order_dashboard(amount, f"Bestand wurde um {amount} erhöht.")

    def _receive_bottle_dashboard(self, bottle_count, bottle_size_ml):

        if self.selected_article is None:
            return

        article_id = self.selected_article["id"]
        self.db.set_bottle_size(article_id, bottle_size_ml)
        self.selected_article["bottle_size_ml"] = bottle_size_ml

        total_ml = bottle_count * bottle_size_ml
        message = (
            f"Bestand wurde um {total_ml:g} ml erhöht "
            f"({bottle_count} Flasche(n) à {bottle_size_ml:g} ml)."
        )
        self._finish_receive_order_dashboard(total_ml, message)

    def _finish_receive_order_dashboard(self, amount_to_add, message):

        article_id = self.selected_article["id"]
        new_stock = self._credit_stock(article_id, amount_to_add)

        self.order_amounts.pop(article_id, None)
        self.db.clear_order_item(article_id)

        self.dashboard_panel.bestellmenge_card.set_amount(0)
        self.dashboard_panel.bestand_card.set_stock(
            new_stock, self.selected_article["stock_unit"], self.selected_article.get("bottle_size_ml")
        )
        self.dashboard_panel.bestand_card.set_history(self.db.get_stock_history(article_id))
        self.dashboard_panel.bestand_card.set_reicht_fuer(
            self._compute_reicht_fuer(self.selected_article, new_stock)
        )

        self.message("Wareneingang gebucht", message)

    def numpad_cancelled(self):

        self._order_amount_article = None
        self.editing_ingredient_id = None
        self.editing_ingredient_unit = None
        self.editing_ingredient_row_id = None

    # =====================================================
    # Rezept (nur Mix-Artikel)
    # =====================================================

    def open_add_ingredient_numpad(self):

        self.numpad_panel.open(
            value=self.dashboard_panel.rezept_card.get_add_amount(), mode="integer",
            confirm_callback=self.add_ingredient_amount_confirmed,
            cancel_callback=self.numpad_cancelled,
        )

    def add_ingredient_amount_confirmed(self, value):

        self.dashboard_panel.rezept_card.set_add_amount(value)

    def add_ingredient_clicked(self):

        if self.selected_article is None:
            return

        rezept_card = self.dashboard_panel.rezept_card
        ingredient_id = rezept_card.get_selected_ingredient_id()
        amount = rezept_card.get_add_amount()
        unit = rezept_card.get_selected_unit()

        if ingredient_id is None or amount <= 0:
            return

        self.db.set_recipe_ingredient(self.selected_article["id"], ingredient_id, amount, unit)
        self._refresh_recipe_ingredients()

    def edit_ingredient_quantity(self, ingredient):

        if self.selected_article is None:
            return

        # editing_ingredient_row_id ist der eigentliche Marker "eine
        # Bearbeitung läuft" - editing_ingredient_id ist bei
        # Freitext-Zutaten (ohne Artikel) selbst legitim None und
        # taugt daher NICHT als alleiniges Unterscheidungsmerkmal
        # zwischen "keine Bearbeitung" und "Freitext wird bearbeitet".
        self.editing_ingredient_row_id = ingredient.get("id")
        self.editing_ingredient_id = ingredient["ingredient_article_id"]
        self.editing_ingredient_unit = ingredient.get("unit")

        self.numpad_panel.open(
            value=int(ingredient.get("quantity", 0)), mode="integer",
            confirm_callback=self.ingredient_quantity_confirmed,
            cancel_callback=self.numpad_cancelled,
        )

    def ingredient_quantity_confirmed(self, value):

        if self.editing_ingredient_row_id is None or self.selected_article is None:
            self.editing_ingredient_id = None
            self.editing_ingredient_unit = None
            self.editing_ingredient_row_id = None
            return

        if self.editing_ingredient_id is not None:
            # Echte Artikel-Zutat.
            if value > 0:
                self.db.set_recipe_ingredient(
                    self.selected_article["id"], self.editing_ingredient_id,
                    value, self.editing_ingredient_unit,
                )
            else:
                self.db.delete_recipe_ingredient(self.selected_article["id"], self.editing_ingredient_id)
        else:
            # Freitext-Zutat ohne Artikel - über die eigene Zeilen-id
            # adressiert (siehe database.py:
            # update_recipe_ingredient_quantity_by_id).
            if value > 0:
                self.db.update_recipe_ingredient_quantity_by_id(self.editing_ingredient_row_id, value)
            else:
                self.db.delete_recipe_ingredient_by_id(self.editing_ingredient_row_id)

        self.editing_ingredient_id = None
        self.editing_ingredient_unit = None
        self.editing_ingredient_row_id = None
        self._refresh_recipe_ingredients()

    def change_ingredient_unit(self, ingredient, unit):

        if self.selected_article is None:
            return

        self.db.set_recipe_ingredient(
            self.selected_article["id"], ingredient["ingredient_article_id"],
            ingredient.get("quantity", 0), unit,
        )
        self._refresh_recipe_ingredients()

    def remove_recipe_ingredient(self, ingredient):

        if self.selected_article is None:
            return

        if ingredient.get("ingredient_article_id") is not None:
            self.db.delete_recipe_ingredient(
                self.selected_article["id"], ingredient["ingredient_article_id"]
            )
        else:
            # Freitext-Zutat: ingredient_article_id ist NULL, ein
            # Löschen darüber würde in SQL nie zutreffen (siehe
            # database.py:delete_recipe_ingredient_by_id) - daher über
            # die eigene Zeilen-id.
            self.db.delete_recipe_ingredient_by_id(ingredient["id"])

        self._refresh_recipe_ingredients()

    # -----------------------------------------------------
    # Zutat OHNE eigenen Artikelstamm (Freitext, z. B. Minze)
    # -----------------------------------------------------

    def open_add_free_text_ingredient_numpad(self):

        self.numpad_panel.open(
            value=self.dashboard_panel.rezept_card.get_add_free_text_amount(), mode="integer",
            confirm_callback=self.add_free_text_amount_confirmed,
            cancel_callback=self.numpad_cancelled,
        )

    def add_free_text_amount_confirmed(self, value):

        self.dashboard_panel.rezept_card.set_add_free_text_amount(value)

    def add_free_text_ingredient_clicked(self):

        if self.selected_article is None:
            return

        rezept_card = self.dashboard_panel.rezept_card
        name = rezept_card.get_free_text_name()
        amount = rezept_card.get_add_free_text_amount()
        unit = rezept_card.get_free_text_unit()

        if not name or amount <= 0:
            self.message(
                "Unvollständig",
                "Bitte einen Namen und eine Menge größer 0 für die Zutat angeben.",
            )
            return

        added = self.db.add_recipe_free_text_ingredient(
            self.selected_article["id"], name, amount, unit
        )

        if not added:
            self.message("Nicht gespeichert", "Die Zutat konnte nicht hinzugefügt werden.")
            return

        rezept_card.clear_free_text_inputs()
        self._refresh_recipe_ingredients()

    def _refresh_recipe_ingredients(self):

        if self.selected_article is None:
            return

        self.dashboard_panel.rezept_card.set_ingredient_options(self.db.get_ingredient_articles())
        self.dashboard_panel.rezept_card.set_ingredients(
            self.db.get_recipe_ingredients(self.selected_article["id"])
        )
        self._refresh_recipe_summary(self.selected_article["id"])

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
        content.add_widget(Label(text=text, color=theme.TEXT_PRIMARY))

        Popup(
            title=title, content=content, size_hint=(0.7, None), height=dp(180), auto_dismiss=True,
        ).open()

    @staticmethod
    def confirm(message_text, on_confirm):
        """Sicherheitsabfrage vor unumkehrbaren Aktionen (z. B. Löschen).

        Nutzt den gemeinsamen Dialog aus widgets/common, damit alle
        Rückfragen der Anwendung gleich aussehen.
        """

        ConfirmPopup(message=message_text, on_confirm=on_confirm).open()
