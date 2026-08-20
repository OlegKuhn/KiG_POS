"""
====================================================================
KiG POS
====================================================================

Modul:
M002

Datei:
database.py

Beschreibung:
Verwaltet die komplette SQLite-Datenbank von KiG POS.

Diese Datei stellt die einzige Schnittstelle zwischen der Anwendung
und der SQLite-Datenbank dar.

Außerhalb dieser Datei dürfen keinerlei SQL-Befehle verwendet werden.

Unterstützte Plattformen

    ✓ Windows
    ✓ Android

--------------------------------------------------------------------

Projekt:
KiG POS

Verein:
KiG e.V. - est. 1996

Version:
0.1.0

Autor:
Oleg Kuhn
OpenAI ChatGPT

====================================================================
"""

from __future__ import annotations

import logging
import sqlite3

from datetime import datetime
from pathlib import Path

from kivy.app import App

import config
import storage
import units


# So viele Sicherungen bleiben erhalten - eine je Programmstart.
# Bei täglichem Betrieb deckt das gut zwei Wochen ab, ohne dass der
# Ordner nennenswert Platz braucht (die Datenbank ist klein).
BACKUP_ANZAHL = 15


class DatabaseManager:
    """
    Zentraler Datenbankmanager.

    Alle Datenbankzugriffe erfolgen ausschließlich über diese Klasse.

    Singleton:
        Jeder Screen ruft bislang eigenständig DatabaseManager() auf.
        Damit dabei nicht mehrere parallele SQLite-Verbindungen
        entstehen (und Tabellen/Standarddaten mehrfach angelegt
        werden), liefert DatabaseManager() ab jetzt immer dieselbe
        Instanz zurück.
    """

    _instance = None

    #################################################################
    # Initialisierung
    #################################################################

    def __new__(cls, *args, **kwargs):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance._initialized = False

        return cls._instance

    def __init__(self):

        if self._initialized:
            return

        self._initialized = True

        self.connection = None
        self.cursor = None

        self.database_path = self.get_database_path()

        self.setup_logging()

        self.connect()

        self.create_tables()

        self._migrate_database()

        self.create_default_data()

        self.create_backup()

        self.logger.info("DatabaseManager erfolgreich gestartet.")

    #################################################################
    # Datensicherung
    #################################################################

    def create_backup(self):
        """Legt beim Start eine Sicherungskopie der Datenbank an.

        Verwendet die Backup-Schnittstelle von SQLite statt eines
        einfachen Dateikopierens: Nur so ist die Kopie garantiert in
        sich stimmig, auch wenn noch Daten im WAL-Journal stehen, die
        die eigentliche Datei noch nicht erreicht haben.

        Eine fehlgeschlagene Sicherung darf den Programmstart NIE
        verhindern - sie wird deshalb nur protokolliert. Lieber ohne
        Sicherung kassieren als gar nicht.
        """

        try:
            backup_dir = self.database_path.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            stempel = datetime.now().strftime("kig_%Y-%m-%d_%H-%M-%S")
            ziel = backup_dir / f"{stempel}.db"

            # Der Zeitstempel geht nur bis auf die Sekunde. Im
            # Normalfall (eine Sicherung je Programmstart) genügt das,
            # zwei Sicherungen in derselben Sekunde würden sich sonst
            # aber gegenseitig überschreiben.
            nummer = 2
            while ziel.exists():
                ziel = backup_dir / f"{stempel}_{nummer}.db"
                nummer += 1

            sicherung = sqlite3.connect(ziel)
            try:
                self.connection.backup(sicherung)
            finally:
                sicherung.close()

            self._cleanup_backups(backup_dir)

            self.logger.info("Sicherung erstellt: %s", ziel.name)

        except Exception as error:
            self.logger.warning("Sicherung fehlgeschlagen: %s", error)

    def _cleanup_backups(self, backup_dir, behalten=BACKUP_ANZAHL):
        """Löscht die ältesten Sicherungen, damit der Ordner nicht
        unbegrenzt wächst."""

        sicherungen = sorted(
            backup_dir.glob("kig_*.db"),
            key=lambda pfad: pfad.stat().st_mtime,
            reverse=True,
        )

        for veraltet in sicherungen[behalten:]:
            try:
                veraltet.unlink()
            except OSError as error:
                self.logger.warning(
                    "Alte Sicherung %s nicht gelöscht: %s", veraltet.name, error
                )

    #################################################################
    # Logging
    #################################################################

    def setup_logging(self):

        logfile = storage.log_dir() / "database.log"

        logging.basicConfig(

            filename=logfile,

            level=logging.INFO,

            format="%(asctime)s | %(levelname)s | %(message)s"

        )

        self.logger = logging.getLogger("KiGPOS")

    #################################################################
    # Datenbankpfad
    #################################################################

    def get_database_path(self) -> Path:

        # Wo die Daten liegen, entscheidet die Plattform - siehe
        # storage.py (Windows: AppData, Android: privater App-Ordner).
        return storage.data_dir() / "kig.db"

    #################################################################
    # Verbindung
    #################################################################

    def connect(self):

        self.connection = sqlite3.connect(

            self.database_path

        )

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

        self.cursor.execute("PRAGMA foreign_keys = ON;")

        self.cursor.execute("PRAGMA journal_mode = WAL;")

        self.cursor.execute("PRAGMA busy_timeout = 5000;")

        self.logger.info("SQLite-Verbindung hergestellt.")

    #################################################################
    # Commit
    #################################################################

    def commit(self):

        if self.connection:

            self.connection.commit()

    #################################################################
    # Verbindung schließen
    #################################################################

    def close(self):

        if self.connection is not None:
            self.connection.close()

            self.connection = None
            self.cursor = None

            self.logger.info("SQLite-Verbindung geschlossen.")

    #################################################################
    # Zeitstempel
    #################################################################

    @staticmethod
    def timestamp():

        return datetime.now().strftime(

            config.TIMESTAMP_FORMAT

        )

    #################################################################
    # Tabellen erstellen
    #################################################################

    def create_tables(self):

        self._create_categories_table()

        self._create_articles_table()

        self._create_article_stock_table()

        self._create_article_stock_history_table()

        self._create_order_items_table()

        self._create_recipe_ingredients_table()

        self._create_deposits_table()

        self._create_article_deposits_table()

        self._create_events_table()

        self._create_sales_table()

        self._create_sale_items_table()

        self._create_settings_table()

        self._create_cash_book_table()

        self.commit()

        self.logger.info("Alle Tabellen erfolgreich erstellt.")

    #################################################################
    # Tabelle Kategorien
    #################################################################

    def _create_categories_table(self):

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS categories(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    color TEXT,

    icon TEXT,

    sort_order INTEGER NOT NULL DEFAULT 0,

    active INTEGER DEFAULT 1,

    created_at TEXT,

    updated_at TEXT

)

        """)

    #################################################################
    # Tabelle Artikel
    #################################################################

    def _create_articles_table(self):

        self.cursor.execute("""

                            CREATE TABLE IF NOT EXISTS articles
                            (

                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,

                                category_id
                                INTEGER
                                NOT
                                NULL,

                                name
                                TEXT
                                NOT
                                NULL,

                                price
                                REAL
                                NOT
                                NULL,

                                purchase_price
                                REAL
                                NOT
                                NULL
                                DEFAULT
                                0,

                                image
                                TEXT,

                                description
                                TEXT,

                                active
                                INTEGER
                                DEFAULT
                                1,

                                article_type TEXT NOT NULL DEFAULT 'SINGLE',

                                cash_visible INTEGER NOT NULL DEFAULT 1,

                                stock_unit TEXT NOT NULL DEFAULT 'Stück',

                                bottle_size_ml REAL,

                                linked_shot_article_id INTEGER,

                                sort_order INTEGER NOT NULL DEFAULT 0,

                                created_at
                                TEXT,

                                updated_at
                                TEXT,

                                FOREIGN
                                KEY
                            (
                                category_id
                            )
                                REFERENCES categories
                            (
                                id
                            )

                                )

                            """)

    #################################################################
    # Tabelle Lagerbestand
    #################################################################

    def _create_article_stock_table(self):

        self.cursor.execute("""

                            CREATE TABLE IF NOT EXISTS article_stock
                            (

                                article_id
                                INTEGER
                                PRIMARY
                                KEY,

                                quantity
                                REAL
                                NOT
                                NULL
                                DEFAULT
                                0,

                                FOREIGN
                                KEY
                            (
                                article_id
                            )
                                REFERENCES articles
                            (
                                id
                            )

                                )

                            """)

    #################################################################
    # Tabelle Lagerhistorie
    #################################################################

    def _create_article_stock_history_table(self):

        self.cursor.execute("""

                            CREATE TABLE IF NOT EXISTS article_stock_history
                            (

                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,

                                article_id
                                INTEGER
                                NOT
                                NULL,

                                old_quantity
                                REAL
                                NOT
                                NULL,

                                new_quantity
                                REAL
                                NOT
                                NULL,

                                reason
                                TEXT
                                NOT
                                NULL,

                                changed_by
                                TEXT
                                NOT
                                NULL,

                                changed_at
                                TEXT
                                NOT
                                NULL,

                                FOREIGN
                                KEY
                            (
                                article_id
                            )
                                REFERENCES articles
                            (
                                id
                            )

                                )

                            """)

    #################################################################
    # Tabelle Einkaufsliste
    #################################################################

    def _create_order_items_table(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items(
                article_id INTEGER PRIMARY KEY,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                updated_at TEXT NOT NULL,
                FOREIGN KEY(article_id) REFERENCES articles(id)
            )
        """)

    #################################################################
    # Tabelle Rezeptzutaten
    #################################################################

    def _create_recipe_ingredients_table(self):
        """Zutaten und Mengen, die zu einem Rezeptartikel gehören.

        ingredient_article_id ist bewusst NULLABLE: Zutaten ohne
        eigenen Artikelstamm (z. B. "Minze", "Limette", "brauner
        Zucker") tragen stattdessen einen free_text_name - sie dienen
        rein der Anzeige im Rezept/an der Kasse, ohne Bestandsführung.
        Genau eine der beiden Spalten ist je Zeile gesetzt.

        Eigene id als Primärschlüssel (statt des früher
        zusammengesetzten Schlüssels aus recipe_article_id +
        ingredient_article_id) - Freitext-Zutaten haben kein eindeutiges
        ingredient_article_id, über das sie sonst adressierbar wären.
        """

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_ingredients(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_article_id INTEGER NOT NULL,
                ingredient_article_id INTEGER,
                free_text_name TEXT,
                quantity REAL NOT NULL CHECK(quantity > 0),
                unit TEXT,
                FOREIGN KEY(recipe_article_id) REFERENCES articles(id),
                FOREIGN KEY(ingredient_article_id) REFERENCES articles(id)
            )
        """)

        self._ensure_recipe_ingredient_index()

    def _ensure_recipe_ingredient_index(self):
        """Ein Rezept darf dieselbe (echte) Zutat nur einmal enthalten -
        gilt bewusst NICHT für Freitext-Zutaten (ingredient_article_id
        NULL), von denen mehrere mit unterschiedlichem Namen im selben
        Rezept vorkommen können (z. B. "Minze" UND "Limette")."""

        self.cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_recipe_ingredient_unique
            ON recipe_ingredients(recipe_article_id, ingredient_article_id)
            WHERE ingredient_article_id IS NOT NULL
        """)

    #################################################################
    # Datenbankmigrationen
    #################################################################

    def _migrate_database(self):
        """
        Führt notwendige Schema-Anpassungen für bestehende
        Datenbanken durch.
        """

        # ---------------------------------------------------------
        # Artikel prüfen
        # ---------------------------------------------------------

        self.cursor.execute(
            "PRAGMA table_info(articles)"
        )

        article_columns = {
            row["name"]
            for row in self.cursor.fetchall()
        }

        # Einkaufspreis ergänzen
        if "purchase_price" not in article_columns:
            self.cursor.execute("""
                                ALTER TABLE articles
                                    ADD COLUMN purchase_price REAL NOT NULL DEFAULT 0
                                """)

            self.logger.info(
                "Migration: purchase_price zu articles hinzugefügt."
            )

        article_migrations = {
            "article_type": "TEXT NOT NULL DEFAULT 'SINGLE'",
            "cash_visible": "INTEGER NOT NULL DEFAULT 1",
            "stock_unit": "TEXT NOT NULL DEFAULT 'Stück'",
            "bottle_size_ml": "REAL",
            "linked_shot_article_id": "INTEGER",

            # Kosten je Lagereinheit (je ml, je Stück, je g).
            #
            # Das ist der Wert, mit dem Rezepte rechnen. Er hängt
            # bewusst NICHT mehr an "Preis einer Flasche" und einer
            # einzigen Flaschengröße: Wer heute 0,7 l für 30 EUR und
            # morgen 1 l für 35 EUR kauft, bekommt sonst je nach
            # zuletzt eingetragener Größe einen falschen Preis - oder
            # gar keinen (siehe _kosten_je_einheit_mischen).
            "cost_per_unit": "REAL",
        }
        for column, definition in article_migrations.items():
            if column not in article_columns:
                self.cursor.execute(
                    f"ALTER TABLE articles ADD COLUMN {column} {definition}"
                )

        if "cost_per_unit" not in article_columns:
            self._migrate_cost_per_unit()

        # ---------------------------------------------------------
        # Kategorie "Zutat" ergänzen
        # ---------------------------------------------------------

        self._ensure_zutat_category()

        # ---------------------------------------------------------
        # Eigene Einheit je Rezeptzutat
        # ---------------------------------------------------------

        self.cursor.execute("PRAGMA table_info(recipe_ingredients)")
        recipe_ingredient_columns = {
            row["name"] for row in self.cursor.fetchall()
        }

        if "unit" not in recipe_ingredient_columns:
            self.cursor.execute(
                "ALTER TABLE recipe_ingredients ADD COLUMN unit TEXT"
            )
            self.logger.info(
                "Migration: unit zu recipe_ingredients hinzugefügt."
            )

        # ---------------------------------------------------------
        # Freitext-Zutaten ohne eigenen Artikelstamm ermöglichen
        # ---------------------------------------------------------

        if "id" not in recipe_ingredient_columns:
            self._migrate_recipe_ingredients_free_text()

        # ---------------------------------------------------------
        # Oberflächen-Einstellungen ergänzen
        #
        # Bei einer komplett neuen (leeren) settings-Tabelle NICHT
        # eingreifen - das übernimmt _insert_default_settings()
        # gleich im Anschluss mit dem vollständigen Standard-Set
        # (sonst hielte sich die Tabelle fälschlich für nicht mehr
        # leer, siehe _ensure_zutat_category()).
        # ---------------------------------------------------------

        self.cursor.execute("SELECT COUNT(*) FROM settings")

        if self.cursor.fetchone()[0] > 0:

            for schluessel, standardwert in (
                ("theme_mode", "light"),
                ("screen_orientation", ""),
            ):

                self.cursor.execute(
                    "SELECT 1 FROM settings WHERE key = ?",
                    (schluessel,)
                )

                if self.cursor.fetchone() is None:

                    self.cursor.execute("""
                        INSERT INTO settings(key, value, datatype)
                        VALUES (?, ?, 'string')
                    """, (schluessel, standardwert))

                    self.logger.info(
                        f"Migration: Einstellung '{schluessel}' ergänzt."
                    )

        # ---------------------------------------------------------
        # Verkaufspositionen prüfen
        # ---------------------------------------------------------

        self.cursor.execute(
            "PRAGMA table_info(sale_items)"
        )

        sale_item_columns = {
            row["name"]
            for row in self.cursor.fetchall()
        }

        # Historischen Einkaufspreis speichern
        if "purchase_price" not in sale_item_columns:
            self.cursor.execute("""
                                ALTER TABLE sale_items
                                    ADD COLUMN purchase_price REAL NOT NULL DEFAULT 0
                                """)

            self.logger.info(
                "Migration: purchase_price zu sale_items hinzugefügt."
            )
        self.cursor.execute("PRAGMA table_info(sales)")
        sales_columns = {row["name"]: row for row in self.cursor.fetchall()}
        event_column = sales_columns.get("event_id")
        if event_column is not None and event_column["notnull"]:
            self._migrate_sales_event_to_optional()

        # ---------------------------------------------------------
        # Fehlende Lagerbestände erzeugen
        # ---------------------------------------------------------

        self.cursor.execute(
            """
            INSERT INTO article_stock(article_id,
                                      quantity)

            SELECT a.id,
                   0

            FROM articles a

                     LEFT JOIN article_stock s
                               ON s.article_id = a.id

            WHERE s.article_id IS NULL
            """
        )

        self.commit()

    def _ensure_zutat_category(self):
        """Legt die Kategorie 'Zutat' nach, falls die Datenbank sie noch
        nicht kennt (z. B. bei bereits bestehenden Installationen).

        Bei einer komplett neuen (leeren) Datenbank NICHT eingreifen:
        Das übernimmt create_default_data()/_insert_default_categories()
        gleich im Anschluss mit dem vollständigen Standard-Set. Würde
        hier schon "Zutat" eingefügt, hielte sich die Kategorientabelle
        für nicht mehr leer und die übrigen Standardkategorien würden
        nie angelegt.
        """

        self.cursor.execute("SELECT COUNT(*) FROM categories")

        if self.cursor.fetchone()[0] == 0:
            return

        self.cursor.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(?)",
            ("Zutat",)
        )

        if self.cursor.fetchone() is not None:
            return

        self.cursor.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 1 FROM categories"
        )
        next_order = self.cursor.fetchone()[0]

        now = self.timestamp()

        self.cursor.execute("""
            INSERT INTO categories(name, color, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("Zutat", "#616161", next_order, now, now))

        self.logger.info("Migration: Kategorie 'Zutat' ergänzt.")

    def _migrate_cost_per_unit(self):
        """Füllt die neue Spalte cost_per_unit aus dem, was bisher da
        war.

        Bisher galt: Bei Einheit "Flasche" ist purchase_price der Preis
        EINER Flasche (also durch die Flaschengröße zu teilen), bei
        allen anderen Einheiten der Preis je Lagereinheit. Genau so
        wird der Startwert gebildet.

        Bleibt die Spalte leer (Flasche ohne hinterlegte Größe), ist der
        Preis schlicht unbekannt - das war er vorher auch, nur hat es
        niemand gesehen: Die Kasse hat für solche Rezepte stillschweigend
        0,00 gebucht.
        """

        self.cursor.execute("""
            UPDATE articles
            SET cost_per_unit = CASE
                WHEN stock_unit = ? THEN
                    CASE WHEN bottle_size_ml > 0
                         THEN purchase_price / bottle_size_ml
                         ELSE NULL END
                ELSE
                    CASE WHEN purchase_price > 0
                         THEN purchase_price
                         ELSE NULL END
            END
        """, (config.BOTTLE_UNIT,))

        self.logger.info(
            "Migration: cost_per_unit aus Einkaufspreis und "
            "Flaschengröße gefüllt (%s Artikel).",
            self.cursor.rowcount
        )

    def _migrate_recipe_ingredients_free_text(self):
        """Baut recipe_ingredients auf das freitextfähige Schema um
        (siehe _create_recipe_ingredients_table): eigene id als
        Primärschlüssel statt des bisherigen zusammengesetzten
        Schlüssels, plus neue Spalte free_text_name.

        SQLite kennt kein ALTER TABLE zum Ändern von NOT NULL/PRIMARY
        KEY - die Tabelle wird deshalb komplett neu angelegt, die
        bestehenden Zeilen (alle mit gesetztem ingredient_article_id)
        unverändert übernommen und die alte Tabelle ersetzt.
        """

        self.logger.info(
            "Migration: recipe_ingredients wird auf freitextfähiges Schema umgestellt."
        )

        self.cursor.execute("""
            CREATE TABLE recipe_ingredients_new(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_article_id INTEGER NOT NULL,
                ingredient_article_id INTEGER,
                free_text_name TEXT,
                quantity REAL NOT NULL CHECK(quantity > 0),
                unit TEXT,
                FOREIGN KEY(recipe_article_id) REFERENCES articles(id),
                FOREIGN KEY(ingredient_article_id) REFERENCES articles(id)
            )
        """)

        self.cursor.execute("""
            INSERT INTO recipe_ingredients_new(
                recipe_article_id, ingredient_article_id, quantity, unit
            )
            SELECT recipe_article_id, ingredient_article_id, quantity, unit
            FROM recipe_ingredients
        """)

        self.cursor.execute("DROP TABLE recipe_ingredients")
        self.cursor.execute(
            "ALTER TABLE recipe_ingredients_new RENAME TO recipe_ingredients"
        )

        self._ensure_recipe_ingredient_index()
        self.commit()

    def _migrate_sales_event_to_optional(self):
        """Macht die Eventzuordnung bestehender Verkaufstabellen optional."""

        self.commit()
        self.cursor.execute("PRAGMA foreign_keys = OFF")
        self.cursor.execute("ALTER TABLE sale_items RENAME TO sale_items_legacy")
        self.cursor.execute("ALTER TABLE sales RENAME TO sales_legacy")
        self._create_sales_table()
        self._create_sale_items_table()

        self.cursor.execute("""
            INSERT INTO sales(id, event_id, receipt_number, sale_date, sale_time,
                              payment_type, subtotal, deposit_total, total,
                              received, change, created_at)
            SELECT id, event_id, receipt_number, sale_date, sale_time,
                   payment_type, subtotal, deposit_total, total,
                   received, change, created_at
            FROM sales_legacy
        """)
        self.cursor.execute("""
            INSERT INTO sale_items(id, sale_id, article_id, article_name, quantity,
                                   unit_price, purchase_price, deposit_name,
                                   deposit_price, discount, vat, line_total, created_at)
            SELECT id, sale_id, article_id, article_name, quantity,
                   unit_price, purchase_price, deposit_name,
                   deposit_price, discount, vat, line_total, created_at
            FROM sale_items_legacy
        """)
        self.cursor.execute("DROP TABLE sale_items_legacy")
        self.cursor.execute("DROP TABLE sales_legacy")
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.commit()

    #################################################################
    # Bestand lesen
    #################################################################

    def get_stock_quantity(
            self,
            article_id
    ):

        self.cursor.execute(
            """
            SELECT quantity

            FROM article_stock

            WHERE article_id = ?
            """,
            (article_id,)
        )

        row = self.cursor.fetchone()

        if row is None:
            return 0

        return row["quantity"]

    #################################################################
    # Einkaufsliste
    #################################################################

    def get_order_items(self):
        """Liefert alle noch offenen Bestellmengen."""

        self.cursor.execute("""
            SELECT o.article_id, o.quantity, o.updated_at,
                   a.name AS article_name, c.name AS category_name
            FROM order_items o
            JOIN articles a ON a.id = o.article_id
            LEFT JOIN categories c ON c.id = a.category_id
            ORDER BY c.sort_order, a.sort_order, a.name
        """)
        return self.cursor.fetchall()

    def set_order_quantity(self, article_id, quantity):
        """Speichert die offene Bestellmenge eines Artikels."""

        if quantity <= 0:
            self.clear_order_item(article_id)
            return

        self.cursor.execute("""
            INSERT INTO order_items(article_id, quantity, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(article_id) DO UPDATE SET
                quantity = excluded.quantity,
                updated_at = excluded.updated_at
        """, (article_id, int(quantity), self.timestamp()))
        self.commit()

    def clear_order_item(self, article_id):
        """Entfernt einen Artikel aus der offenen Einkaufsliste."""

        self.cursor.execute(
            "DELETE FROM order_items WHERE article_id = ?", (article_id,)
        )
        self.commit()

    #################################################################
    # Bestand setzen
    #################################################################

    def update_stock(
            self,
            article_id,
            quantity
    ):

        self.cursor.execute(
            """
            UPDATE article_stock

            SET quantity = ?

            WHERE article_id = ?
            """,
            (
                quantity,
                article_id
            )
        )

        self.commit()

        return self.cursor.rowcount == 1

    #################################################################
    # Kosten je Lagereinheit
    #################################################################

    def get_cost_per_unit(self, article_id):
        """Kosten einer Lagereinheit (je ml, je Stück, je g).

        Liefert None, wenn sich der Preis nicht bestimmen lässt - dann
        fehlt bei einer Flasche die Größe oder es wurde nie ein
        Einkaufspreis erfasst.
        """

        self.cursor.execute(
            "SELECT cost_per_unit, purchase_price, stock_unit, bottle_size_ml "
            "FROM articles WHERE id = ?",
            (article_id,)
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        if row["cost_per_unit"] is not None:
            return row["cost_per_unit"]

        # Rückfall für Artikel, die seit der Migration nicht wieder
        # angefasst wurden.
        return self._kosten_aus_einkaufspreis(
            row["purchase_price"], row["stock_unit"], row["bottle_size_ml"]
        )

    @staticmethod
    def _kosten_aus_einkaufspreis(purchase_price, stock_unit, bottle_size_ml):
        """Rechnet den eingetragenen Einkaufspreis in Kosten je
        Lagereinheit um.

        Bei "Flasche" gilt der Preis für eine ganze Flasche und muss
        durch deren Inhalt geteilt werden; sonst gilt er direkt je
        Lagereinheit.
        """

        if not purchase_price or purchase_price <= 0:
            return None

        if stock_unit == config.BOTTLE_UNIT:

            if not bottle_size_ml or bottle_size_ml <= 0:
                return None

            return purchase_price / bottle_size_ml

        return purchase_price

    def set_cost_per_unit(self, article_id, cost_per_unit):
        """Setzt die Kosten je Lagereinheit direkt."""

        self.cursor.execute(
            "UPDATE articles SET cost_per_unit = ?, updated_at = ? WHERE id = ?",
            (cost_per_unit, self.timestamp(), article_id)
        )

        self.commit()

        return self.cursor.rowcount == 1

    def book_goods_receipt(
            self,
            article_id,
            quantity,
            cost_per_unit=None,
            reason="Wareneingang",
            changed_by="Einkauf",
    ):
        """Bucht einen Wareneingang und mischt den Einkaufspreis.

        quantity ist immer in der Lagereinheit (bei Flaschen also in
        ml, nicht in Flaschen).

        cost_per_unit sind die Kosten je Lagereinheit dieser Lieferung.
        Ohne Angabe bleibt der bisherige Wert stehen - dann wird
        angenommen, dass zum selben Preis wie zuletzt eingekauft wurde.

        Der neue Preis ist der gewichtete Durchschnitt aus altem
        Bestand und Zugang:

            (Restmenge x alter Preis + Zugang x neuer Preis)
            -------------------------------------------------
                        Restmenge + Zugang

        So zählt bei gemischten Lieferungen das, was tatsächlich im
        Regal steht: Wer 0,7 l für 30 EUR und danach 1 l für 35 EUR
        kauft, rechnet mit 65 EUR auf 1700 ml.
        """

        alter_bestand = self.get_stock_quantity(article_id)
        neuer_bestand = alter_bestand + quantity

        alte_kosten = self.get_cost_per_unit(article_id)

        gemischt = self._kosten_je_einheit_mischen(
            alter_bestand, alte_kosten, quantity, cost_per_unit
        )

        if gemischt is not None:
            self.set_cost_per_unit(article_id, gemischt)

        self.update_stock(article_id, neuer_bestand)

        self.add_stock_history(
            article_id=article_id,
            old_quantity=alter_bestand,
            new_quantity=neuer_bestand,
            reason=reason,
            changed_by=changed_by,
            changed_at=self.timestamp(),
        )

        return gemischt

    @staticmethod
    def _kosten_je_einheit_mischen(
            alter_bestand, alte_kosten, menge, neue_kosten
    ):
        """Gewichteter Durchschnitt aus Restbestand und Zugang.

        Sonderfälle, die in der Praxis vorkommen:

            kein neuer Preis    -> es bleibt beim alten
            kein alter Preis    -> der neue gilt für alles
            Bestand <= 0        -> es gibt nichts zu mischen, der
                                   neue Preis gilt (ein negativer
                                   Bestand aus Nachbuchungen darf den
                                   Durchschnitt nicht verzerren)
        """

        if neue_kosten is None:
            return alte_kosten

        if alte_kosten is None or alter_bestand <= 0 or menge <= 0:
            return neue_kosten

        gesamtmenge = alter_bestand + menge

        if gesamtmenge <= 0:
            return neue_kosten

        return (
            (alter_bestand * alte_kosten + menge * neue_kosten) / gesamtmenge
        )

    #################################################################
    # Flaschengröße merken (Wareneingang in "Flasche")
    #################################################################

    def set_bottle_size(self, article_id, bottle_size_ml):
        """Merkt sich die zuletzt beim Wareneingang verwendete
        Flaschengröße als neuen Vorgabewert für dieses Artikel."""

        self.cursor.execute(
            "UPDATE articles SET bottle_size_ml = ? WHERE id = ?",
            (bottle_size_ml, article_id)
        )

        self.commit()

    #################################################################
    # Verknüpfter Shot-Artikel (Flasche -> Mix-Artikel)
    #################################################################

    def get_linked_shot(self, bottle_article_id):
        """Liefert den mit dieser Flasche verknüpften Shot-Artikel
        (falls vorhanden) oder None."""

        self.cursor.execute(
            "SELECT linked_shot_article_id FROM articles WHERE id = ?",
            (bottle_article_id,)
        )
        row = self.cursor.fetchone()

        if row is None or row["linked_shot_article_id"] is None:
            return None

        return self.get_article(row["linked_shot_article_id"])

    def set_linked_shot(self, bottle_article_id, shot_article_id):
        """Verknüpft (oder löst, bei shot_article_id=None) den
        Shot-Artikel einer Flasche."""

        self.cursor.execute(
            "UPDATE articles SET linked_shot_article_id = ? WHERE id = ?",
            (shot_article_id, bottle_article_id)
        )

        self.commit()

    #################################################################
    # Historieneintrag speichern
    #################################################################

    def add_stock_history(
            self,
            article_id,
            old_quantity,
            new_quantity,
            reason,
            changed_by,
            changed_at
    ):

        self.cursor.execute(
            """
            INSERT INTO article_stock_history(article_id,
                                              old_quantity,
                                              new_quantity,
                                              reason,
                                              changed_by,
                                              changed_at)

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                article_id,

                old_quantity,

                new_quantity,

                reason,

                changed_by,

                changed_at
            )
        )

        self.commit()

        return True

    #################################################################
    # Lagerhistorie lesen
    #################################################################

    def get_stock_history(
            self,
            article_id
    ):

        self.cursor.execute(
            """
            SELECT *

            FROM article_stock_history

            WHERE article_id = ?

            -- Die ID wird beim Speichern fortlaufend vergeben und ist
            -- damit unabhängig vom Anzeigeformat des Zeitstempels.
            ORDER BY id DESC
            """,
            (article_id,)
        )

        return self.cursor.fetchall()

    #################################################################
    # Tabelle Pfandarten
    #################################################################

    def _create_deposits_table(self):

        self.cursor.execute("""

                            CREATE TABLE IF NOT EXISTS deposits
                            (

                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,

                                name
                                TEXT
                                NOT
                                NULL
                                UNIQUE,

                                amount
                                REAL
                                NOT
                                NULL,

                                active
                                INTEGER
                                DEFAULT
                                1,

                                created_at
                                TEXT,

                                updated_at
                                TEXT

                            )

                            """)

    #################################################################
    # Tabelle Artikel -> Pfand
    #################################################################

    def _create_article_deposits_table(self):

        self.cursor.execute("""

                            CREATE TABLE IF NOT EXISTS article_deposits
                            (

                                article_id
                                INTEGER,

                                deposit_id
                                INTEGER,

                                mandatory
                                INTEGER
                                DEFAULT
                                0,

                                PRIMARY
                                KEY
                            (
                                article_id,
                                deposit_id
                            ),
                                FOREIGN KEY
                            (
                                article_id
                            )
                                REFERENCES articles
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                deposit_id
                            )
                                REFERENCES deposits
                            (
                                id
                            )

                                )

                            """)

    #################################################################
    # Tabelle Veranstaltungen
    #################################################################

    def _create_cash_book_table(self):
        """Kassenbuch: je Zeile ein Tag mit Kassenstand und Bewegungen.

        Bewusst getrennt von den Verkäufen: Das Kassenbuch hält fest,
        was tatsächlich in der Kasse liegt - einschließlich Einlagen,
        Entnahmen und allem, was nicht über die Kasse gebucht wurde.
        Die Verkaufsstatistik beantwortet eine andere Frage.
        """

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS cash_book_entries(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            entry_date TEXT NOT NULL,

            opening_balance REAL NOT NULL DEFAULT 0,

            income REAL NOT NULL DEFAULT 0,

            expenses REAL NOT NULL DEFAULT 0,

            closing_balance REAL NOT NULL DEFAULT 0,

            comment TEXT,

            auditor TEXT,

            created_at TEXT,

            updated_at TEXT

        )

        """)

    def _create_events_table(self):

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS events(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            location TEXT,

            organizer TEXT,

            start_date TEXT,

            end_date TEXT,

            status TEXT,

            entry_type TEXT NOT NULL DEFAULT 'EVENT',

            staff_names TEXT,

            created_at TEXT,

            updated_at TEXT

        )

        """)

        # Bestehende Datenbanken aus älteren Versionen erweitern.
        self.cursor.execute("PRAGMA table_info(events)")
        columns = {row["name"] for row in self.cursor.fetchall()}

        if "entry_type" not in columns:
            self.cursor.execute(
                "ALTER TABLE events ADD COLUMN entry_type TEXT NOT NULL DEFAULT 'EVENT'"
            )

        if "staff_names" not in columns:
            self.cursor.execute(
                "ALTER TABLE events ADD COLUMN staff_names TEXT"
            )

    #################################################################
    # Tabelle Verkäufe
    #################################################################

    def _create_sales_table(self):

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS sales(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER,

            receipt_number INTEGER,

            sale_date TEXT,

            sale_time TEXT,

            payment_type TEXT,

            subtotal REAL,

            deposit_total REAL,

            total REAL,

            received REAL,

            change REAL,

            created_at TEXT,

            FOREIGN KEY(event_id)
                REFERENCES events(id)

        )

        """)

    #################################################################
    # Tabelle Verkaufspositionen
    #################################################################

    def _create_sale_items_table(self):

        self.cursor.execute("""

                            CREATE TABLE IF NOT EXISTS sale_items
                            (

                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,

                                sale_id
                                INTEGER
                                NOT
                                NULL,

                                article_id
                                INTEGER,

                                article_name
                                TEXT,

                                quantity
                                INTEGER,

                                unit_price
                                REAL,

                                purchase_price
                                REAL
                                NOT
                                NULL
                                DEFAULT
                                0,

                                deposit_name
                                TEXT,

                                deposit_price
                                REAL,

                                discount
                                REAL
                                DEFAULT
                                0,

                                vat
                                REAL
                                DEFAULT
                                0,

                                line_total
                                REAL,

                                created_at
                                TEXT,

                                FOREIGN
                                KEY
                            (
                                sale_id
                            )
                                REFERENCES sales
                            (
                                id
                            )

                                )

                            """)

    #################################################################
    # Tabelle Einstellungen
    #################################################################

    def _create_settings_table(self):

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS settings(

            key TEXT PRIMARY KEY,

            value TEXT,

            datatype TEXT

        )

        """)

    #################################################################
    # Standarddaten erstellen
    #################################################################

    def create_default_data(self):
        """
        Erstellt sämtliche Standarddaten.
        """

        self._insert_default_categories()

        self._insert_default_deposits()

        self._insert_default_settings()

        self.commit()

        self.logger.info("Standarddaten erfolgreich erstellt.")

    #################################################################
    # Standardkategorien
    #################################################################

    def _insert_default_categories(self):

        self.cursor.execute("SELECT COUNT(*) FROM categories")

        if self.cursor.fetchone()[0] > 0:
            return

        now = self.timestamp()

        categories = [

            ("Alkoholfrei", "#1976D2", 1),

            ("Alkohol", "#F57C00", 2),

            ("Cocktail", "#D32F2F", 3),

            ("Essen", "#43A047", 4),

            ("Sonstiges", "#7B1FA2", 5),

            ("Zutat", "#616161", 6)

        ]

        for name, color, order in categories:

            self.cursor.execute("""

                INSERT INTO categories(

                    name,

                    color,

                    sort_order,

                    created_at,

                    updated_at

                )

                VALUES(?,?,?,?,?)

            """, (

                name,

                color,

                order,

                now,

                now

            ))

    #################################################################
    # Standardpfand
    #################################################################

    def _insert_default_deposits(self):

        self.cursor.execute("SELECT COUNT(*) FROM deposits")

        if self.cursor.fetchone()[0] > 0:
            return

        now = self.timestamp()

        deposits = [

            ("Becher", 2.00),

            ("Flasche", 0.50),

            ("Krug", 5.00)

        ]

        for name, amount in deposits:

            self.cursor.execute("""

                INSERT INTO deposits(

                    name,

                    amount,

                    created_at,

                    updated_at

                )

                VALUES(?,?,?,?)

            """, (

                name,

                amount,

                now,

                now

            ))

    #################################################################
    # Grundeinstellungen
    #################################################################

    def _insert_default_settings(self):

        self.cursor.execute("SELECT COUNT(*) FROM settings")

        if self.cursor.fetchone()[0] > 0:
            return

        settings = [

            ("verein", config.VEREIN, "string"),

            ("programm", config.APP_NAME, "string"),

            ("version", config.VERSION, "string"),

            ("build", config.BUILD, "string"),

            ("database_version", "1", "integer"),

            ("waehrung", config.CURRENCY, "string"),

            ("sprache", config.LANGUAGE, "string"),

            ("standard_zahlungsart", "Bar", "string"),

            ("pfand_aktiv", "True", "bool"),

            ("theme_mode", "light", "string"),

            # Leer = noch nicht gewaehlt. Beim ersten Start entscheidet
            # dann die Form des Bildschirms (siehe
            # KiG_POS._ausrichtung_bestimmen) - ein Telefon startet so
            # hochkant, ein Rechner im Querformat.
            ("screen_orientation", "", "string")

        ]

        self.cursor.executemany("""

            INSERT INTO settings(

                key,

                value,

                datatype

            )

            VALUES(?,?,?)

        """, settings)

        self.logger.info("Grundeinstellungen eingefügt.")

    #################################################################
    # Kategorien abrufen
    #################################################################

    def get_categories(self, cash_only=False):
        """Liefert alle aktiven Kategorien.

        cash_only=True liefert ausschließlich Kategorien, die
        mindestens einen an der Kasse verkäuflichen Artikel
        enthalten (aktiv und cash_visible). Reine Zutat-Kategorien
        ohne verkäufliche Artikel tauchen dann nicht mehr auf.
        """

        query = """

            SELECT

                c.id,

                c.name,

                c.color,

                c.icon,

                c.sort_order

            FROM categories c

            WHERE c.active = 1

        """

        if cash_only:
            query += """
                AND EXISTS (
                    SELECT 1 FROM articles a
                    WHERE a.category_id = c.id
                      AND a.active = 1
                      AND a.cash_visible = 1
                )
            """

        query += " ORDER BY c.sort_order"

        self.cursor.execute(query)

        return self.cursor.fetchall()

    def get_category(self, category_id):

        self.cursor.execute("""
            SELECT id, name, color, icon, sort_order, active
            FROM categories
            WHERE id = ?
        """, (category_id,))

        return self.cursor.fetchone()

    def category_exists(self, name, exclude_id=None):

        query = "SELECT id FROM categories WHERE LOWER(name) = LOWER(?)"
        parameters = [name]

        if exclude_id is not None:
            query += " AND id != ?"
            parameters.append(exclude_id)

        self.cursor.execute(query, parameters)
        return self.cursor.fetchone() is not None

    def add_category(self, name, color=None):

        name = name.strip()
        if not name or self.category_exists(name):
            return False

        self.cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM categories")
        sort_order = self.cursor.fetchone()[0]
        now = self.timestamp()

        self.cursor.execute("""
            INSERT INTO categories(name, color, sort_order, created_at, updated_at)
            VALUES(?,?,?,?,?)
        """, (name, color or "#F44611", sort_order, now, now))
        self.commit()
        return self.cursor.lastrowid

    def update_category(self, category_id, name):

        name = name.strip()
        if not name or self.category_exists(name, exclude_id=category_id):
            return False

        self.cursor.execute("""
            UPDATE categories
            SET name = ?, updated_at = ?
            WHERE id = ?
        """, (name, self.timestamp(), category_id))
        self.commit()
        return self.cursor.rowcount == 1

    def delete_category(self, category_id):
        """Löscht nur Kategorien, die keine Artikel mehr enthalten."""

        self.cursor.execute(
            "SELECT COUNT(*) FROM articles WHERE category_id = ?",
            (category_id,)
        )
        if self.cursor.fetchone()[0] > 0:
            return False

        self.cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.commit()
        return self.cursor.rowcount == 1

    def set_category_order(self, category_ids):
        """Speichert die Reihenfolge der Kategorien atomar."""

        with self.connection:
            for sort_order, category_id in enumerate(category_ids, start=1):
                self.cursor.execute(
                    "UPDATE categories SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (sort_order, self.timestamp(), category_id)
                )

    #################################################################
    # Pfandarten abrufen
    #################################################################

    def get_deposits(self):

        self.cursor.execute("""

            SELECT

                id,

                name,

                amount

            FROM deposits

            WHERE active = 1

            ORDER BY id

        """)

        return self.cursor.fetchall()

    #################################################################
    # Einstellung lesen
    #################################################################

    def get_setting(self, key):

        self.cursor.execute("""

            SELECT

                value

            FROM settings

            WHERE key = ?

        """, (key,))

        row = self.cursor.fetchone()

        if row:

            return row["value"]

        return None

    #################################################################
    # Einstellung speichern
    #################################################################

    def set_setting(self, key, value):
        """Speichert eine Einstellung.

        Bewusst als INSERT mit ON CONFLICT: Ein reines UPDATE würde
        einen noch nicht vorhandenen Schlüssel kommentarlos verwerfen -
        die Einstellung wäre nach dem nächsten Start wieder weg, ohne
        dass irgendwo ein Fehler auftaucht. Neu angelegte Schlüssel
        gelten dabei als "string" (andere Typen bitte weiterhin über
        _insert_default_settings mit passendem datatype anlegen).
        """

        self.cursor.execute("""

            INSERT INTO settings(key, value, datatype)

            VALUES (?, ?, 'string')

            ON CONFLICT(key) DO UPDATE SET value = excluded.value

        """, (

            key,

            value

        ))

        self.commit()

    #################################################################
    # Artikel abrufen
    #################################################################

    def get_articles(self, active_only=True, cash_only=False, exclude_mix=False):

        query = """

                SELECT a.id, \

                       a.name, \

                       a.price, \

                       a.purchase_price, \

                       a.image, \

                       a.description, \

                       a.sort_order, \

                       a.active, \

                       a.article_type, \

                       a.cash_visible, \

                       a.stock_unit, \

                       a.bottle_size_ml, \

                       c.id    AS category_id, \

                       c.name  AS category_name, \

                       c.color AS category_color

                FROM articles a

                         INNER JOIN categories c \
                                    ON c.id = a.category_id \

                """

        conditions = []
        if active_only:
            conditions.append("a.active = 1")
        if cash_only:
            conditions.append("a.cash_visible = 1")
        if exclude_mix:
            conditions.append("a.article_type != 'MIX'")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """

            ORDER BY

                c.sort_order,

                a.sort_order,

                a.name

        """

        self.cursor.execute(query)

        return self.cursor.fetchall()

    #################################################################
    # Einzelnen Artikel abrufen
    #################################################################

    def get_article(self, article_id):
        """Liefert einen einzelnen Artikel (inkl. Kategorie) oder None."""

        self.cursor.execute("""
            SELECT a.id, a.name, a.price, a.purchase_price, a.image,
                   a.description, a.sort_order, a.active, a.article_type,
                   a.cash_visible, a.stock_unit, a.bottle_size_ml,
                   c.id AS category_id, c.name AS category_name, c.color AS category_color
            FROM articles a
            INNER JOIN categories c ON c.id = a.category_id
            WHERE a.id = ?
        """, (article_id,))

        return self.cursor.fetchone()

    def get_article_id_by_name(self, name):
        """Liefert die ID des Artikels mit exakt diesem Namen (ohne
        Berücksichtigung von Groß-/Kleinschreibung) oder None.

        Wird u. a. gebraucht, um nach add_article() (liefert nur
        True/False) an die ID des gerade angelegten Artikels zu
        kommen - z. B. beim automatischen Anlegen des verknüpften
        Shot-Artikels einer Flasche.
        """

        self.cursor.execute(
            "SELECT id FROM articles WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        row = self.cursor.fetchone()
        return row["id"] if row is not None else None

    #################################################################
    # Artikel einer Kategorie
    #################################################################

    def get_articles_by_category(
            self,
            category_id,
            active_only=True,
            cash_only=False,
            exclude_mix=False
    ):

        query = """
                SELECT a.id, \
                       a.category_id, \
                       a.name, \
                       a.price, \
                       a.purchase_price, \
                       a.image, \
                       a.description, \
                       a.sort_order, \
                       a.active

                       ,a.article_type, \
                       a.cash_visible, \
                       a.stock_unit, \
                       a.bottle_size_ml, \
                       c.name  AS category_name, \
                       c.color AS category_color

                FROM articles a

                INNER JOIN categories c ON c.id = a.category_id

                WHERE a.category_id = ? \
                """

        if active_only:
            query += " AND a.active = 1"
        if cash_only:
            query += " AND a.cash_visible = 1"
        if exclude_mix:
            query += " AND a.article_type != 'MIX'"

        query += " ORDER BY a.sort_order, a.name"

        self.cursor.execute(
            query,
            (category_id,)
        )

        return self.cursor.fetchall()

    def set_article_order(self, article_ids):
        """Speichert die Reihenfolge einer Kategorie atomar."""

        with self.connection:
            for sort_order, article_id in enumerate(article_ids, start=1):
                self.cursor.execute(
                    "UPDATE articles SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (sort_order, self.timestamp(), article_id)
                )

    def get_recipe_articles(self):
        """Liefert alle Artikel, die als Mix/Rezept angelegt wurden."""

        self.cursor.execute("""
            SELECT a.id, a.name, a.category_id, c.name AS category_name
            FROM articles a
            JOIN categories c ON c.id = a.category_id
            WHERE a.article_type = 'MIX'
            ORDER BY c.sort_order, a.sort_order, a.name
        """)
        return self.cursor.fetchall()

    def get_ingredient_articles(self):
        """Liefert echte Zutaten-Artikel als mögliche Rezeptzutaten.

        Bewusst nur Einzelartikel, die NICHT an der Kasse verkauft
        werden (cash_visible = 0) - das sind reine Zutaten (z. B.
        Flaschen, Sirupe), keine eigenständig verkäuflichen Produkte.
        So taucht im Dropdown nicht jeder beliebige Verkaufsartikel
        auf, sondern wirklich nur das, was als Zutat gedacht ist.
        """

        self.cursor.execute("""
            SELECT id, name, stock_unit, category_id
            FROM articles
            WHERE article_type = 'SINGLE' AND cash_visible = 0
            ORDER BY name
        """)
        return self.cursor.fetchall()

    def get_recipes_using_ingredient(self, ingredient_article_id):
        """Liefert alle Mix-/Rezeptartikel, die diese Zutat verwenden,
        inklusive der dafür benötigten Menge + Einheit.

        Dient dazu, aus dem aktuellen Bestand einer Zutat zu berechnen,
        für wie viele Verkäufe jedes einzelne Rezept damit noch
        reicht - mehrere Rezepte (z. B. "Jack Daniels pur" und "Jacky
        Cola") teilen sich dabei denselben Bestand, ein Verkauf des
        einen wirkt sich also automatisch auf die verfügbare Menge des
        anderen aus.
        """

        self.cursor.execute("""
            SELECT ri.recipe_article_id, ri.quantity,
                   COALESCE(ri.unit, ingredient.stock_unit) AS unit,
                   recipe.name AS recipe_name
            FROM recipe_ingredients ri
            JOIN articles recipe ON recipe.id = ri.recipe_article_id
            JOIN articles ingredient ON ingredient.id = ri.ingredient_article_id
            WHERE ri.ingredient_article_id = ?
            ORDER BY recipe.name
        """, (ingredient_article_id,))

        return self.cursor.fetchall()

    def get_recipe_ingredients(self, recipe_article_id):
        """Liefert Zutaten und Mengen eines Rezeptartikels.

        Jede Rezeptzutat trägt ihre eigene Einheit (ri.unit, z. B. "l"
        obwohl die Zutat selbst in "ml" gelagert wird). Ist für eine
        bereits bestehende Zeile noch keine Einheit gesetzt (Zeilen von
        vor dieser Funktion), wird ersatzweise die aktuelle Lagereinheit
        des Artikels verwendet.

        article_stock_unit liefert zusätzlich die AKTUELLE Lagereinheit
        des Artikels (unabhängig von der Rezept-Einheit) - benötigt, um
        beim Verkauf exakt in diese Einheit umzurechnen.

        LEFT JOIN statt JOIN, da Freitext-Zutaten (z. B. "Minze") kein
        ingredient_article_id besitzen - für sie liefert name den
        hinterlegten free_text_name und article_stock_unit bleibt NULL
        (kein Bestand, keine Umrechnung möglich/nötig).
        """

        self.cursor.execute("""
            SELECT ri.id, ri.recipe_article_id, ri.ingredient_article_id, ri.quantity,
                   ri.free_text_name,
                   COALESCE(a.name, ri.free_text_name) AS name,
                   COALESCE(ri.unit, a.stock_unit) AS unit,
                   a.stock_unit AS article_stock_unit
            FROM recipe_ingredients ri
            LEFT JOIN articles a ON a.id = ri.ingredient_article_id
            WHERE ri.recipe_article_id = ?
            ORDER BY name
        """, (recipe_article_id,))
        return self.cursor.fetchall()

    def get_recipe_available_quantity(self, recipe_article_id):
        """Berechnet die 'umgekehrte Reicht-für'-Zahl: wie oft lässt
        sich dieser Mix-/Rezeptartikel mit dem AKTUELLEN Bestand seiner
        Zutaten noch verkaufen? Limitierend ist die Zutat, die als
        erstes ausgeht (Minimum über alle Zutaten).

        Gilt für beliebig viele Zutaten - nicht nur für den
        Sonderfall "Shot" mit genau einer Zutat (Flasche).

        Liefert None, wenn (noch) keine Zutaten hinterlegt sind
        (Bestand unbestimmbar statt fälschlich 0).
        """

        ingredients = self.get_recipe_ingredients(recipe_article_id)

        if not ingredients:
            return None

        available = None

        for ingredient in ingredients:
            if ingredient["ingredient_article_id"] is None:
                # Freitext-Zutat ohne eigenen Artikelstamm (z. B.
                # "Minze") - führt keinen eigenen Bestand und bleibt
                # daher bei der Berechnung unberücksichtigt, statt die
                # Zahl fälschlich auf 0 zu ziehen.
                continue

            base_unit = units.stock_dimension_unit(ingredient["article_stock_unit"])
            required = units.convert(ingredient["quantity"], ingredient["unit"], base_unit)

            if not required or required <= 0:
                # Nicht umrechenbare/leere Zutat blockiert die
                # Berechnung nicht - siehe set_recipe_ingredient(),
                # das so etwas eigentlich schon verhindert.
                continue

            stock = self.get_stock_quantity(ingredient["ingredient_article_id"])
            possible = int(stock // required)

            available = possible if available is None else min(available, possible)

        return available if available is not None else 0

    def get_recipe_cost(self, recipe_article_id):
        """Berechnet den Einkaufspreis eines Mix-/Rezeptartikels aus
        den Einkaufspreisen seiner Zutaten, jeweils auf die im Rezept
        verwendete Menge umgerechnet und aufsummiert.

        Beispiel: Shot "Jack Daniels" (20 ml) aus einer Flasche, deren
        Inhalt mit 0,0429 EUR je ml zu Buche steht -> 20 x 0,0429 =
        0,86 EUR.

        Maßgeblich sind die Kosten je Lagereinheit (siehe
        get_cost_per_unit). Die entstehen beim Wareneingang als
        gewichteter Durchschnitt und sind deshalb unabhängig davon, in
        welcher Flaschengröße zuletzt eingekauft wurde.

        Gilt generell für beliebig viele Zutaten, nicht nur den
        Sonderfall "Shot" mit einer Zutat.

        Liefert None, wenn sich für mindestens eine Zutat kein Preis
        ermitteln lässt (z. B. Flasche ohne hinterlegte Flaschengröße
        und ohne Wareneingang) - lieber unbestimmt als ein irreführend
        zu niedriger Preis.
        """

        ingredients = self.get_recipe_ingredients(recipe_article_id)

        if not ingredients:
            return None

        total = 0.0

        for ingredient in ingredients:
            if ingredient["ingredient_article_id"] is None:
                # Freitext-Zutat (z. B. "Minze") ohne eigenen
                # Artikelstamm - hat keinen hinterlegten Einkaufspreis,
                # der Gesamtpreis des Rezepts ist damit nicht verlässlich
                # bestimmbar (siehe Docstring oben).
                return None

            article = self.get_article(ingredient["ingredient_article_id"])

            if article is None:
                return None

            base_unit = units.stock_dimension_unit(article["stock_unit"])
            qty_in_base = units.convert(ingredient["quantity"], ingredient["unit"], base_unit)

            if qty_in_base is None:
                return None

            cost_per_base_unit = self.get_cost_per_unit(
                ingredient["ingredient_article_id"]
            )

            if cost_per_base_unit is None:
                return None

            total += qty_in_base * cost_per_base_unit

        return total

    def set_recipe_ingredient(
            self,
            recipe_article_id,
            ingredient_article_id,
            quantity,
            unit=None
    ):
        """Fügt eine Rezeptzutat hinzu oder aktualisiert Menge und Einheit.

        unit=None übernimmt beim Anlegen die aktuelle Lagereinheit des
        Artikels als Vorgabe. Beim Aktualisieren einer bestehenden Zeile
        MUSS die gewünschte Einheit explizit übergeben werden, sonst
        würde sie hier auf NULL zurückgesetzt.

        Absicherung: Eine Einheit, die sich nicht verlustfrei in die
        aktuelle Lagereinheit des Artikels umrechnen lässt (andere
        physikalische Größe, z. B. "g" für eine in "ml" geführte
        Zutat), wird abgelehnt - sonst würde der spätere Lagerabzug
        beim Verkauf falsch rechnen.
        """

        if recipe_article_id == ingredient_article_id or quantity <= 0:
            return False

        self.cursor.execute(
            "SELECT stock_unit FROM articles WHERE id = ?",
            (ingredient_article_id,)
        )
        row = self.cursor.fetchone()
        article_stock_unit = row["stock_unit"] if row is not None else None

        # "Flasche" hat keinen festen ml-Wert - der tatsächliche
        # Bestand einer Flasche-Zutat wird immer in ml geführt (siehe
        # config.BOTTLE_UNIT). Für die Umrechnungsprüfung gilt eine
        # Flasche daher wie ml.
        stock_dimension_unit = units.stock_dimension_unit(article_stock_unit)

        if unit is None:
            unit = stock_dimension_unit

        if (
                stock_dimension_unit is not None
                and units.convert(quantity, unit, stock_dimension_unit) is None
        ):
            self.logger.warning(
                "Rezeptzutat abgelehnt: Einheit '%s' lässt sich nicht in "
                "die Lagereinheit '%s' des Artikels umrechnen.",
                unit, stock_dimension_unit
            )
            return False

        self.cursor.execute("""
            SELECT id FROM recipe_ingredients
            WHERE recipe_article_id = ? AND ingredient_article_id = ?
        """, (recipe_article_id, ingredient_article_id))
        existing = self.cursor.fetchone()

        if existing is not None:
            self.cursor.execute(
                "UPDATE recipe_ingredients SET quantity = ?, unit = ? WHERE id = ?",
                (quantity, unit, existing["id"])
            )
        else:
            self.cursor.execute("""
                INSERT INTO recipe_ingredients(recipe_article_id, ingredient_article_id, quantity, unit)
                VALUES (?, ?, ?, ?)
            """, (recipe_article_id, ingredient_article_id, quantity, unit))

        self.commit()
        return True

    def add_recipe_free_text_ingredient(self, recipe_article_id, name, quantity, unit):
        """Fügt eine Rezeptzutat OHNE eigenen Artikelstamm hinzu (z. B.
        "Minze", "Limette", "brauner Zucker") - dient nur der Anzeige
        im Rezept und an der Kasse (siehe cash_screen.py:
        show_recipe_tooltip), ohne Bestandsführung oder Einkaufspreis.

        unit ist hier bewusst freier Text (z. B. "Blätter", "TL",
        "Scheiben") statt einer geprüften Lagereinheit - eine
        Freitext-Zutat hat ja keinen Artikel, gegen dessen Lagereinheit
        sich die Umrechnung prüfen ließe.
        """

        name = (name or "").strip()

        if not name or quantity is None or quantity <= 0:
            return False

        self.cursor.execute("""
            INSERT INTO recipe_ingredients(recipe_article_id, ingredient_article_id, free_text_name, quantity, unit)
            VALUES (?, NULL, ?, ?, ?)
        """, (recipe_article_id, name, quantity, (unit or "").strip() or None))
        self.commit()
        return True

    def update_recipe_ingredient_quantity_by_id(self, recipe_ingredient_id, quantity):
        """Ändert nur die Menge einer bestehenden Rezeptzutat - über
        die eigene id adressiert, funktioniert daher gleichermaßen für
        echte Artikel-Zutaten wie für Freitext-Zutaten."""

        if quantity is None or quantity <= 0:
            return False

        self.cursor.execute(
            "UPDATE recipe_ingredients SET quantity = ? WHERE id = ?",
            (quantity, recipe_ingredient_id)
        )
        self.commit()
        return self.cursor.rowcount == 1

    def delete_recipe_ingredient(self, recipe_article_id, ingredient_article_id):
        self.cursor.execute("""
            DELETE FROM recipe_ingredients
            WHERE recipe_article_id = ? AND ingredient_article_id = ?
        """, (recipe_article_id, ingredient_article_id))
        self.commit()
        return self.cursor.rowcount == 1

    def delete_recipe_ingredient_by_id(self, recipe_ingredient_id):
        """Entfernt eine Rezeptzutat über ihre eigene id - notwendig für
        Freitext-Zutaten (ingredient_article_id ist NULL, ein Vergleich
        mit '= NULL' würde in SQL nie zutreffen und stillschweigend
        nichts löschen)."""

        self.cursor.execute(
            "DELETE FROM recipe_ingredients WHERE id = ?",
            (recipe_ingredient_id,)
        )
        self.commit()
        return self.cursor.rowcount == 1

    #################################################################
    # Prüfen ob Artikel existiert
    #################################################################

    def article_exists(self, name, exclude_id=None):

        query = """

            SELECT id

            FROM articles

            WHERE LOWER(name)=LOWER(?)

        """

        parameters = [name]

        if exclude_id is not None:
            query += " AND id != ?"
            parameters.append(exclude_id)

        self.cursor.execute(query, parameters)

        return self.cursor.fetchone() is not None

    #################################################################
    # Artikel hinzufügen
    #################################################################

    def add_article(
            self,
            category_id,
            name,
            price,
            purchase_price=0.0,
            image=None,
            description="",
            sort_order=0,
            article_type="SINGLE",
            cash_visible=True,
            stock_unit="Stück",
            bottle_size_ml=None
    ):

        name = name.strip()

        if not name:
            return False

        if price < 0:
            return False

        if purchase_price < 0:
            return False

        if self.article_exists(name):
            return False

        now = self.timestamp()

        self.cursor.execute("""

                            INSERT INTO articles(category_id,
                                                 name,
                                                 price,
                                                 purchase_price,
                                                 image,
                                                 description,
                                                 sort_order,
                                                 article_type,
                                                 cash_visible,
                                                 stock_unit,
                                                 bottle_size_ml,
                                                 created_at,
                                                 updated_at)

                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                            """, (

            category_id,

            name,

            price,

            purchase_price,

            image,

            description,

            sort_order,

            article_type,

            int(cash_visible),

            stock_unit,

            bottle_size_ml,

            now,

            now

                            ))

        article_id = self.cursor.lastrowid

        # Kosten je Lagereinheit aus dem eingetragenen Einkaufspreis
        # ableiten. Beim ersten Wareneingang wird daraus ein
        # gewichteter Durchschnitt (siehe book_goods_receipt).
        self.cursor.execute(
            "UPDATE articles SET cost_per_unit = ? WHERE id = ?",
            (
                self._kosten_aus_einkaufspreis(
                    purchase_price, stock_unit, bottle_size_ml
                ),
                article_id,
            )
        )

        self.cursor.execute(
            """
            INSERT INTO article_stock(article_id,
                                      quantity)
            VALUES (?, ?)
            """,
            (
                article_id,
                0
            )
        )

        self.commit()

        return True

    #################################################################
    # Artikel ändern
    #################################################################

    def update_article(
            self,
            article_id,
            category_id,
            name,
            price,
            purchase_price,
            image,
            description,
            sort_order,
            active,
            article_type="SINGLE",
            cash_visible=True,
            stock_unit="Stück",
            bottle_size_ml=None
    ):

        name = name.strip()

        if not name:
            return False

        if price < 0:
            return False

        if purchase_price < 0:
            return False

        if self.article_exists(
                name,
                exclude_id=article_id
        ):
            return False

        # Wurde am Einkaufspreis oder an der Flaschengröße etwas
        # geändert, gilt das als neue Ansage: Die Kosten je
        # Lagereinheit werden daraus neu abgeleitet. Bleiben beide
        # unverändert, bleibt auch der über Wareneingänge gemittelte
        # Wert stehen - sonst würde jedes Speichern eines Artikels den
        # Durchschnitt wieder auf "Preis geteilt durch Flaschengröße"
        # zurückwerfen.
        self.cursor.execute(
            "SELECT purchase_price, stock_unit, bottle_size_ml "
            "FROM articles WHERE id = ?",
            (article_id,)
        )

        vorher = self.cursor.fetchone()

        preis_geaendert = vorher is not None and (
            vorher["purchase_price"] != purchase_price
            or vorher["bottle_size_ml"] != bottle_size_ml
            or vorher["stock_unit"] != stock_unit
        )

        now = self.timestamp()

        self.cursor.execute("""

                            UPDATE articles

                            SET category_id    = ?,

                                name           = ?,

                                price          = ?,

                                purchase_price = ?,

                                image          = ?,

                                description    = ?,

                                sort_order     = ?,

                                active         = ?,

                                article_type   = ?,

                                cash_visible   = ?,

                                stock_unit     = ?,

                                bottle_size_ml = ?,

                                updated_at     = ?

                            WHERE id = ?

                            """, (

                                category_id,

                                name,

                                price,

                                purchase_price,

                                image,

                                description,

                                sort_order,

                                active,

                                article_type,

                                int(cash_visible),

                                stock_unit,

                                bottle_size_ml,

                                now,

                                article_id

                            ))

        geaendert = self.cursor.rowcount == 1

        if geaendert and preis_geaendert:
            self.cursor.execute(
                "UPDATE articles SET cost_per_unit = ? WHERE id = ?",
                (
                    self._kosten_aus_einkaufspreis(
                        purchase_price, stock_unit, bottle_size_ml
                    ),
                    article_id,
                )
            )

        self.commit()

        return geaendert

    #################################################################
    # Artikel deaktivieren
    #################################################################

    def delete_article(self, article_id):

        now = self.timestamp()

        self.cursor.execute("""

            UPDATE articles

            SET

                active=0,

                updated_at=?

            WHERE id=?

        """, (

            now,

            article_id

        ))

        self.commit()

    #################################################################
    # Pfand einem Artikel zuweisen
    #################################################################

    def add_deposit_to_article(

        self,

        article_id,

        deposit_id,

        mandatory=True

    ):

        self.cursor.execute("""

            INSERT OR REPLACE INTO article_deposits(

                article_id,

                deposit_id,

                mandatory

            )

            VALUES(?,?,?)

        """, (

            article_id,

            deposit_id,

            int(mandatory)

        ))

        self.commit()

    #################################################################
    # Pfand entfernen
    #################################################################

    def remove_deposit_from_article(

        self,

        article_id,

        deposit_id

    ):

        self.cursor.execute("""

            DELETE

            FROM article_deposits

            WHERE

                article_id=?

                AND deposit_id=?

        """, (

            article_id,

            deposit_id

        ))

        self.commit()

    #################################################################
    # Pfand eines Artikels abrufen
    #################################################################

    def get_article_deposits(self, article_id):

        self.cursor.execute("""

            SELECT

                d.id,

                d.name,

                d.amount,

                ad.mandatory

            FROM article_deposits ad

            INNER JOIN deposits d

                ON d.id = ad.deposit_id

            WHERE ad.article_id=?

            ORDER BY d.name

        """, (article_id,))

        return self.cursor.fetchall()

    #################################################################
    # Veranstaltungen
    #################################################################

    def get_events(self):

        self.cursor.execute("""

            SELECT

                id,

                name,

                location,

                organizer,

                start_date,

                end_date,

                status

                ,entry_type

                ,staff_names

            FROM events

            ORDER BY start_date DESC

        """)

        return self.cursor.fetchall()

    #################################################################
    # Veranstaltung anlegen
    #################################################################

    def add_event(

        self,

        name,

        location,

        organizer,

        start_date,

        end_date,

        status="OPEN",
        entry_type="EVENT",
        staff_names=""

    ):

        now = self.timestamp()

        self.cursor.execute("""

            INSERT INTO events(

                name,

                location,

                organizer,

                start_date,

                end_date,

                status,

                entry_type,

                staff_names,

                created_at,

                updated_at

            )

            VALUES(?,?,?,?,?,?,?,?,?,?)

        """, (

            name,

            location,

            organizer,

            start_date,

            end_date,

                status,

                entry_type,

                staff_names,

            now,

            now

        ))

        self.commit()

        return self.cursor.lastrowid

    def get_entries_for_date(self, entry_date):
        """Liefert alle Kalender-Einträge eines Tages."""

        self.cursor.execute("""
            SELECT id, name, location, organizer, start_date, end_date,
                   status, entry_type, staff_names
            FROM events
            WHERE start_date = ?
            ORDER BY id
        """, (entry_date,))

        return self.cursor.fetchall()

    def get_event_for_date(self, event_date):
        """Liefert das Event eines Kalendertags für die Verkaufszuordnung."""

        self.cursor.execute("""
            SELECT id, name, start_date
            FROM events
            WHERE start_date = ? AND entry_type = 'EVENT'
            ORDER BY id
            LIMIT 1
        """, (event_date,))

        return self.cursor.fetchone()

    def get_entries_for_month(self, year, month):
        """Liefert alle Einträge eines Monats im ISO-Datumsformat."""

        start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1:04d}-01-01"
        else:
            end = f"{year:04d}-{month + 1:02d}-01"

        self.cursor.execute("""
            SELECT id, name, start_date, entry_type, staff_names
            FROM events
            WHERE start_date >= ? AND start_date < ?
            ORDER BY start_date, id
        """, (start, end))

        return self.cursor.fetchall()

    def count_sales_for_event(self, event_id):
        """Anzahl der Verkäufe, die diesem Kalender-Eintrag zugeordnet sind.

        Wird vor dem Löschen gebraucht: Solange Verkäufe am Eintrag
        hängen, lässt die Datenbank ihn nicht einfach verschwinden
        (siehe delete_event).
        """

        self.cursor.execute(
            "SELECT COUNT(*) FROM sales WHERE event_id = ?",
            (event_id,)
        )

        return self.cursor.fetchone()[0]

    def delete_event(self, event_id, detach_sales=False):
        """Löscht einen Kalender-Eintrag.

        Hängen Verkäufe daran, verweigert die Datenbank das Löschen -
        ein Verkauf darf nicht auf ein Event zeigen, das es nicht mehr
        gibt. Mit detach_sales=True werden die Verkäufe zuerst vom
        Event gelöst: Sie bleiben mit allen Beträgen in der Statistik
        stehen, nur die Zuordnung zum Event entfällt. Das ist die
        einzige Möglichkeit, ein bereits bespieltes Event loszuwerden,
        ohne Umsätze zu verlieren.
        """

        try:
            if detach_sales:
                self.cursor.execute(
                    "UPDATE sales SET event_id = NULL WHERE event_id = ?",
                    (event_id,)
                )

            self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            self.commit()
            return self.cursor.rowcount == 1

        except sqlite3.IntegrityError:
            self.connection.rollback()
            return False

    def update_event(self, event_id, name, entry_type, staff_names=""):
        """Aktualisiert einen Kalender-Eintrag."""

        self.cursor.execute("""
            UPDATE events
            SET name = ?, entry_type = ?, staff_names = ?, updated_at = ?
            WHERE id = ?
        """, (name, entry_type, staff_names, self.timestamp(), event_id))
        self.commit()
        return self.cursor.rowcount == 1

    #################################################################
    # Kassenbuch
    #################################################################
    #
    # Eine Zeile je Tag: Womit die Kasse begonnen hat, was hinein- und
    # herausgegangen ist, womit sie geschlossen wurde. Ob das
    # zusammenpasst, rechnet die Anwendung nach - siehe
    # cash_book_entry_is_valid.

    # Rundungsspielraum beim Nachrechnen. Beträge werden in Cent
    # eingegeben, ein halber Cent Toleranz fängt lediglich
    # Fließkomma-Ungenauigkeiten ab.
    CASH_BOOK_TOLERANCE = 0.005

    @staticmethod
    def cash_book_entry_is_valid(entry):
        """Prüft, ob Startbestand + Einnahmen - Ausgaben den
        Endbestand ergibt."""

        erwartet = (
            (entry["opening_balance"] or 0)
            + (entry["income"] or 0)
            - (entry["expenses"] or 0)
        )

        abweichung = abs(erwartet - (entry["closing_balance"] or 0))

        return abweichung <= DatabaseManager.CASH_BOOK_TOLERANCE

    def get_cash_book_entries(self, year=None, month=None):
        """Kassenbuchzeilen, nach Datum aufsteigend.

        year/month grenzen auf einen Monat ein; ohne Angabe kommt
        alles.
        """

        query = "SELECT * FROM cash_book_entries WHERE 1 = 1"
        parameters = []

        if year:
            query += " AND substr(entry_date, 1, 4) = ?"
            parameters.append(f"{int(year):04d}")

        if month:
            query += " AND substr(entry_date, 6, 2) = ?"
            parameters.append(f"{int(month):02d}")

        query += " ORDER BY entry_date, id"

        self.cursor.execute(query, parameters)

        return self.cursor.fetchall()

    def get_cash_book_years(self):
        """Jahre, in denen es Kassenbucheinträge gibt - absteigend.

        Das laufende Jahr ist immer dabei, auch wenn noch nichts
        erfasst wurde: Sonst stünde beim ersten Eintrag kein Jahr zur
        Auswahl.
        """

        self.cursor.execute("""
            SELECT DISTINCT substr(entry_date, 1, 4) AS jahr
            FROM cash_book_entries
            ORDER BY jahr DESC
        """)

        jahre = {int(row["jahr"]) for row in self.cursor.fetchall() if row["jahr"]}

        jahre.add(datetime.now().year)

        return sorted(jahre, reverse=True)

    def get_cash_book_entry(self, entry_id):

        self.cursor.execute(
            "SELECT * FROM cash_book_entries WHERE id = ?", (entry_id,)
        )

        return self.cursor.fetchone()

    def get_previous_closing_balance(self, entry_date):
        """Endbestand des letzten Eintrags VOR diesem Datum.

        Damit lässt sich der Startbestand vorbelegen: In der Kasse
        liegt am Morgen das, was am Abend zuvor drin lag. Gibt es
        keinen Vorgänger, kommt None zurück.
        """

        self.cursor.execute("""
            SELECT closing_balance
            FROM cash_book_entries
            WHERE entry_date < ?
            ORDER BY entry_date DESC, id DESC
            LIMIT 1
        """, (entry_date,))

        row = self.cursor.fetchone()

        return None if row is None else row["closing_balance"]

    def add_cash_book_entry(
            self,
            entry_date,
            opening_balance=0.0,
            income=0.0,
            expenses=0.0,
            closing_balance=0.0,
            comment="",
            auditor="",
    ):
        """Legt eine Kassenbuchzeile an und liefert deren id."""

        if not entry_date:
            return None

        now = self.timestamp()

        self.cursor.execute("""
            INSERT INTO cash_book_entries(
                entry_date, opening_balance, income, expenses,
                closing_balance, comment, auditor, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_date, opening_balance, income, expenses,
            closing_balance, comment or "", auditor or "", now, now,
        ))

        self.commit()

        return self.cursor.lastrowid

    def update_cash_book_entry(
            self,
            entry_id,
            entry_date,
            opening_balance=0.0,
            income=0.0,
            expenses=0.0,
            closing_balance=0.0,
            comment="",
            auditor="",
    ):

        if not entry_date:
            return False

        self.cursor.execute("""
            UPDATE cash_book_entries
            SET entry_date = ?, opening_balance = ?, income = ?,
                expenses = ?, closing_balance = ?, comment = ?,
                auditor = ?, updated_at = ?
            WHERE id = ?
        """, (
            entry_date, opening_balance, income, expenses,
            closing_balance, comment or "", auditor or "",
            self.timestamp(), entry_id,
        ))

        self.commit()

        return self.cursor.rowcount == 1

    def delete_cash_book_entry(self, entry_id):

        self.cursor.execute(
            "DELETE FROM cash_book_entries WHERE id = ?", (entry_id,)
        )

        self.commit()

        return self.cursor.rowcount == 1

    def get_cash_book_totals(self, year=None, month=None):
        """Summen eines Monats: Einnahmen, Ausgaben, Anzahl Zeilen und
        wie viele davon nicht aufgehen."""

        eintraege = self.get_cash_book_entries(year, month)

        return {
            "income": sum(e["income"] or 0 for e in eintraege),
            "expenses": sum(e["expenses"] or 0 for e in eintraege),
            "entries": len(eintraege),
            "invalid": sum(
                0 if self.cash_book_entry_is_valid(e) else 1
                for e in eintraege
            ),
            "closing_balance": (
                eintraege[-1]["closing_balance"] if eintraege else 0
            ),
        }

    #################################################################
    # Nächste Bonnummer
    #################################################################

    def get_next_receipt_number(self):

        self.cursor.execute("""

            SELECT MAX(receipt_number)

            FROM sales

        """)

        number = self.cursor.fetchone()[0]

        if number is None:
            return 1

        return number + 1

    #################################################################
    # Verkauf speichern
    #################################################################

    def save_sale(

        self,

        event_id,

        payment_type,

        subtotal,

        deposit_total,

        total,

        received,

        change,

        items

    ):

        now = datetime.now()

        sale_date = now.strftime(config.DATE_FORMAT)

        sale_time = now.strftime(config.TIME_FORMAT)

        created = self.timestamp()

        receipt = self.get_next_receipt_number()

        self.cursor.execute("""

            INSERT INTO sales(

                event_id,

                receipt_number,

                sale_date,

                sale_time,

                payment_type,

                subtotal,

                deposit_total,

                total,

                received,

                change,

                created_at

            )

            VALUES(?,?,?,?,?,?,?,?,?,?,?)

        """, (

            event_id,

            receipt,

            sale_date,

            sale_time,

            payment_type,

            subtotal,

            deposit_total,

            total,

            received,

            change,

            created

        ))

        sale_id = self.cursor.lastrowid

        for item in items:
            self.cursor.execute("""

                                INSERT INTO sale_items(sale_id,
                                                       article_id,
                                                       article_name,
                                                       quantity,
                                                       unit_price,
                                                       purchase_price,
                                                       deposit_name,
                                                       deposit_price,
                                                       discount,
                                                       vat,
                                                       line_total,
                                                       created_at)

                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                                """, (

                                    sale_id,

                                    item["article_id"],

                                    item["name"],

                                    item["quantity"],

                                    item["price"],

                                    item.get("purchase_price", 0),

                                    item.get("deposit_name"),

                                    item.get("deposit_price", 0),

                                    item.get("discount", 0),

                                    item.get("vat", 0),

                                    item["line_total"],

                                    created

                                ))

        self.commit()

        return receipt

    #################################################################
    # Statistik
    #################################################################

    @staticmethod
    def _sales_business_day_sql():
        """SQLite-Ausdruck für den Geschäftstag von 06:00 bis 06:00 Uhr."""

        iso_date = (
            "substr(s.sale_date, 7, 4) || '-' || "
            "substr(s.sale_date, 4, 2) || '-' || substr(s.sale_date, 1, 2)"
        )
        return (
            "CASE WHEN s.sale_time < '06:00:00' "
            f"THEN date({iso_date}, '-1 day') ELSE date({iso_date}) END"
        )

    def get_statistic_sale_items(self, date_from=None, date_to=None, event_id=None):
        """Liefert Verkaufspositionen mit Event, Kategorie und Gewinn."""

        business_day = self._sales_business_day_sql()
        query = f"""
            SELECT si.id AS sale_item_id,
                   s.id AS sale_id,
                   COALESCE(e.name, 'Ohne Event') AS event_name,
                   {business_day} AS business_date,
                   COALESCE(c.name, '-') AS category_name,
                   si.article_name,
                   si.quantity,
                   si.unit_price,
                   si.purchase_price,
                   (si.unit_price - si.purchase_price) * si.quantity AS profit
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            LEFT JOIN events e ON e.id = s.event_id
            LEFT JOIN articles a ON a.id = si.article_id
            LEFT JOIN categories c ON c.id = a.category_id
            WHERE 1 = 1
        """
        parameters = []

        if date_from:
            query += f" AND {business_day} >= ?"
            parameters.append(date_from)
        if date_to:
            query += f" AND {business_day} <= ?"
            parameters.append(date_to)
        if event_id is not None:
            query += " AND s.event_id = ?"
            parameters.append(event_id)

        query += " ORDER BY business_date DESC, s.id DESC, si.id DESC"
        self.cursor.execute(query, parameters)
        sale_items = self.cursor.fetchall()

        # Eine Verkaufsposition kann mehrere Einheiten enthalten. Für die
        # Statistik wird jede Einheit als eigene, auswählbare Zeile gezeigt.
        #
        # Stornos stehen als Positionen mit NEGATIVER Menge in denselben
        # Tabellen. Deshalb wird hier über den Betrag gezählt und das
        # Vorzeichen an Menge und Gewinn weitergereicht - sonst würde ein
        # Storno über drei Einheiten als eine einzelne Zeile mit positivem
        # Gewinn erscheinen und den Umsatz nach oben statt nach unten
        # verschieben.
        individual_items = []
        for sale_item in sale_items:

            menge = int(sale_item["quantity"] or 0)

            if menge == 0:
                continue

            vorzeichen = 1 if menge > 0 else -1

            for item_number in range(abs(menge)):
                item = dict(sale_item)
                item["quantity"] = vorzeichen
                item["profit"] = (
                    item["unit_price"] - item["purchase_price"]
                ) * vorzeichen
                item["row_key"] = f"{item['sale_item_id']}-{item_number}"
                individual_items.append(item)

        return individual_items

    def get_top_selling_articles(self, date_from=None, date_to=None, event_id=None, limit=5):
        """Liefert die meistverkauften Artikel im gewählten Zeitraum."""

        rows = self.get_statistic_sale_items(date_from, date_to, event_id)
        totals = {}
        for row in rows:
            totals[row["article_name"]] = (
                totals.get(row["article_name"], 0) + row["quantity"]
            )
        return sorted(
            totals.items(), key=lambda item: (-item[1], item[0])
        )[:limit]

    def get_article_revenues(self, date_from=None, date_to=None, event_id=None):
        """Liefert die Einnahmen pro Artikel, absteigend nach Umsatz."""

        rows = self.get_statistic_sale_items(date_from, date_to, event_id)
        totals = {}
        for row in rows:
            totals[row["article_name"]] = (
                totals.get(row["article_name"], 0)
                + row["quantity"] * row["unit_price"]
            )
        return sorted(
            totals.items(), key=lambda item: (-item[1], item[0])
        )

    def get_category_revenues(self, date_from=None, date_to=None, event_id=None):
        """Liefert die Einnahmen pro Kategorie, absteigend nach Umsatz.

        Je Kategorie ein Tupel (Name, Einnahmen, Farbe). Die Farbe ist
        die in der Kategorienverwaltung hinterlegte - so zeigt das
        Kreisdiagramm dieselben Farben, die der Verein seinen
        Kategorien gegeben hat.
        """

        self.cursor.execute("SELECT name, color FROM categories")
        farben = {row["name"]: row["color"] for row in self.cursor.fetchall()}

        rows = self.get_statistic_sale_items(date_from, date_to, event_id)

        totals = {}

        for row in rows:
            name = row["category_name"]
            totals[name] = (
                totals.get(name, 0) + row["quantity"] * row["unit_price"]
            )

        sortiert = sorted(totals.items(), key=lambda item: (-item[1], item[0]))

        return [(name, betrag, farben.get(name)) for name, betrag in sortiert]

    def count_missing_recipe_costs(self, date_from=None, date_to=None, event_id=None):
        """Zählt Verkaufspositionen von Mix-/Rezeptartikeln, bei denen
        kein Einkaufspreis erfasst wurde.

        Das passiert bei Verkäufen aus der Zeit, in der die Kosten der
        Zutaten nicht bestimmbar waren (z. B. Flasche ohne
        Flaschengröße): Gebucht wurde dann 0,00 - der Gewinn dieser
        Positionen ist damit zu hoch ausgewiesen.
        """

        sale_item_ids = self._sale_items_ohne_einkaufspreis(
            date_from, date_to, event_id
        )

        return len(sale_item_ids)

    def repair_recipe_costs(self, date_from=None, date_to=None, event_id=None):
        """Trägt bei diesen Positionen den heute gültigen Rezeptpreis
        nach.

        Bewusst eine ausdrückliche Aktion und nichts, was im
        Hintergrund geschieht: Es werden Zahlen einer abgeschlossenen
        Abrechnung verändert. Positionen, deren Rezeptpreis auch heute
        nicht bestimmbar ist, bleiben unangetastet.

        Liefert die Anzahl der geänderten Positionen.
        """

        geaendert = 0

        for sale_item_id, article_id in self._sale_items_ohne_einkaufspreis(
            date_from, date_to, event_id
        ):

            kosten = self.get_recipe_cost(article_id)

            if kosten is None or kosten <= 0:
                continue

            self.cursor.execute(
                "UPDATE sale_items SET purchase_price = ? WHERE id = ?",
                (kosten, sale_item_id)
            )

            geaendert += 1

        self.commit()

        self.logger.info(
            "Einkaufspreise nachgetragen: %s Verkaufspositionen.", geaendert
        )

        return geaendert

    def _sale_items_ohne_einkaufspreis(
            self, date_from=None, date_to=None, event_id=None
    ):
        """Verkaufspositionen von Rezeptartikeln ohne Einkaufspreis -
        als Liste aus (sale_item_id, article_id)."""

        business_day = self._sales_business_day_sql()

        query = f"""
            SELECT si.id AS sale_item_id, si.article_id
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            JOIN articles a ON a.id = si.article_id
            WHERE a.article_type = 'MIX'
              AND si.purchase_price <= 0
              AND si.quantity > 0
        """

        parameters = []

        if date_from:
            query += f" AND {business_day} >= ?"
            parameters.append(date_from)

        if date_to:
            query += f" AND {business_day} <= ?"
            parameters.append(date_to)

        if event_id is not None:
            query += " AND s.event_id = ?"
            parameters.append(event_id)

        self.cursor.execute(query, parameters)

        return [
            (row["sale_item_id"], row["article_id"])
            for row in self.cursor.fetchall()
        ]

    def get_period_totals(self, date_from=None, date_to=None, event_id=None):
        """Kennzahlen des gewählten Zeitraums.

            revenue    Einnahmen (verkaufte Menge x Verkaufspreis)
            expenses   Ausgaben (verkaufte Menge x Einkaufspreis)
            profit     Einnahmen abzüglich Ausgaben
            quantity   Anzahl verkaufter Einheiten
            receipts   Anzahl der Bons

        Stornos stehen mit negativer Menge in denselben Tabellen und
        ziehen die Beträge damit von selbst wieder ab.
        """

        rows = self.get_statistic_sale_items(date_from, date_to, event_id)

        einnahmen = sum(row["quantity"] * row["unit_price"] for row in rows)
        ausgaben = sum(row["quantity"] * row["purchase_price"] for row in rows)

        return {
            "revenue": einnahmen,
            "expenses": ausgaben,
            "profit": einnahmen - ausgaben,
            "quantity": sum(row["quantity"] for row in rows),
            "receipts": len({row["sale_id"] for row in rows}),
        }

    def delete_sale_item(self, sale_item_id):
        """Löscht eine Verkaufsposition und bereinigt den zugehörigen Bon."""

        self.cursor.execute(
            "SELECT sale_id FROM sale_items WHERE id = ?", (sale_item_id,)
        )
        row = self.cursor.fetchone()
        if row is None:
            return False

        sale_id = row["sale_id"]
        self.cursor.execute("DELETE FROM sale_items WHERE id = ?", (sale_item_id,))
        self.cursor.execute(
            "SELECT COALESCE(SUM(line_total), 0) AS total FROM sale_items WHERE sale_id = ?",
            (sale_id,),
        )
        total = self.cursor.fetchone()["total"]

        if total == 0:
            self.cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        else:
            self.cursor.execute(
                "UPDATE sales SET subtotal = ?, total = ? WHERE id = ?",
                (total, total, sale_id),
            )

        self.commit()
        return True

    def delete_sale_units(self, sale_item_id, quantity):
        """Löscht einzelne Einheiten einer Verkaufsposition."""

        self.cursor.execute(
            "SELECT sale_id, quantity, unit_price FROM sale_items WHERE id = ?",
            (sale_item_id,),
        )
        row = self.cursor.fetchone()
        if row is None:
            return False

        remaining_quantity = row["quantity"] - quantity
        if remaining_quantity <= 0:
            return self.delete_sale_item(sale_item_id)

        new_line_total = remaining_quantity * row["unit_price"]
        self.cursor.execute(
            "UPDATE sale_items SET quantity = ?, line_total = ? WHERE id = ?",
            (remaining_quantity, new_line_total, sale_item_id),
        )
        self.cursor.execute(
            "SELECT COALESCE(SUM(line_total), 0) AS total FROM sale_items WHERE sale_id = ?",
            (row["sale_id"],),
        )
        total = self.cursor.fetchone()["total"]
        self.cursor.execute(
            "UPDATE sales SET subtotal = ?, total = ? WHERE id = ?",
            (total, total, row["sale_id"]),
        )
        self.commit()
        return True

    def delete_sales_in_period(self, date_from, date_to):
        """Löscht alle Verkaufsdaten eines Geschäftstags-Zeitraums."""

        business_day = self._sales_business_day_sql()
        self.cursor.execute(
            f"SELECT id FROM sales s WHERE {business_day} >= ? AND {business_day} <= ?",
            (date_from, date_to),
        )
        sale_ids = [row["id"] for row in self.cursor.fetchall()]
        if not sale_ids:
            return 0

        placeholders = ",".join("?" for _ in sale_ids)
        self.cursor.execute(
            f"DELETE FROM sale_items WHERE sale_id IN ({placeholders})", sale_ids
        )
        self.cursor.execute(
            f"DELETE FROM sales WHERE id IN ({placeholders})", sale_ids
        )
        self.commit()
        return len(sale_ids)

    #################################################################
    # Tagesumsatz
    #################################################################

    def get_daily_revenue(self, sale_date=None):

        if sale_date is None:

            sale_date = datetime.now().strftime(config.DATE_FORMAT)

        self.cursor.execute("""

            SELECT

                COALESCE(SUM(total),0)

            FROM sales

            WHERE sale_date = ?

        """, (sale_date,))

        return self.cursor.fetchone()[0]

    #################################################################
    # Verkäufe zählen
    #################################################################

    def get_sales_count(self, sale_date=None):

        if sale_date is None:

            sale_date = datetime.now().strftime(config.DATE_FORMAT)

        self.cursor.execute("""

            SELECT COUNT(*)

            FROM sales

            WHERE sale_date=?

        """, (sale_date,))

        return self.cursor.fetchone()[0]

    #################################################################
    # Datenbank schließen
    #################################################################

    def __del__(self):

        try:

            self.close()

        except Exception:

            pass

    #################################################################
    # Bestand reduzieren
    #################################################################

    def decrease_stock(
            self,
            article_id,
            quantity
    ):

        self.cursor.execute(
            """
            UPDATE article_stock

            SET quantity = quantity - ?

            WHERE article_id = ?
            """,
            (
                quantity,
                article_id
            )
        )

        self.commit()

        return self.cursor.rowcount == 1
