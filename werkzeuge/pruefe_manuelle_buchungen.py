"""Isolierte Datenbanktests ohne Zugriff auf Vereinsdaten oder Kivy-Fenster."""
import ast
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sqlite3
import unittest


def database_class():
    source = Path(__file__).resolve().parents[1] / 'database.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'DatabaseManager')
    names = {'_create_manual_entries_table', 'get_manual_entries', 'save_manual_entry',
             'void_manual_entry', 'get_period_totals', 'timestamp'}
    cls = ast.ClassDef(name='TestDatabase', bases=[], keywords=[],
                      body=[n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in names],
                      decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    from types import SimpleNamespace
    scope = dict(datetime=datetime, Decimal=Decimal, InvalidOperation=InvalidOperation,
                 config=SimpleNamespace(TIMESTAMP_FORMAT='%Y-%m-%d %H:%M:%S'))
    exec(compile(module, str(source), 'exec'), scope)
    return scope['TestDatabase']


class ManualTests(unittest.TestCase):
    def setUp(self):
        self.db = database_class()()
        self.db.connection = sqlite3.connect(':memory:')
        self.db.connection.row_factory = sqlite3.Row
        self.db.cursor = self.db.connection.cursor()
        self.db.cursor.execute('PRAGMA foreign_keys=ON')
        self.db.cursor.execute('CREATE TABLE events(id INTEGER PRIMARY KEY, name TEXT, entry_type TEXT)')
        self.db.cursor.executemany('INSERT INTO events VALUES(?,?,?)', [(1, 'Fest', 'EVENT'), (2, 'Schicht', 'SHIFT')])
        self.db._create_manual_entries_table()
        self.db.get_entwertet = lambda *a: {'kig_karte': 2, 'gutschein': 0}

    def tearDown(self):
        self.db.connection.close()

    def test_filters_totals_edit_void(self):
        db = self.db
        income = db.save_manual_entry('2026-09-20', 1, 'INCOME', '100,25', 'Sponsor', 'S1')
        expense = db.save_manual_entry('2026-09-20', 1, 'EXPENSE', '30.10', 'Miete')
        db.save_manual_entry('2026-09-21', None, 'INCOME', '5', 'Spende')
        self.assertEqual(len(db.get_manual_entries()), 3)
        self.assertEqual(len(db.get_manual_entries('2026-09-20', '2026-09-20', 1)), 2)
        self.assertEqual(db.get_manual_entries(category_id=1), [])
        sales = [dict(quantity=2, unit_price=5, purchase_price=1, sale_id=1)]
        totals = db.get_period_totals(event_id=1, zeilen=sales)
        self.assertAlmostEqual(totals['revenue'], 110.25)
        self.assertAlmostEqual(totals['expenses'], 32.10)
        self.assertAlmostEqual(totals['profit'], 78.15)
        self.assertEqual(totals['quantity'], 2)
        self.assertEqual(totals['bar'], 8)
        db.save_manual_entry('2026-09-22', None, 'INCOME', '80', 'Geändert', entry_id=income)
        self.assertEqual(len(db.get_manual_entries(event_id=1)), 1)
        db.void_manual_entry(expense)
        self.assertEqual(len(db.get_manual_entries(event_id=1)), 0)
        self.assertEqual(db.cursor.execute('SELECT count(*) FROM manual_entries').fetchone()[0], 3)

    def test_invalid_input(self):
        for amount in ('0', '-1', 'nan', 'Infinity', '1.001', 'abc'):
            with self.assertRaises(ValueError):
                self.db.save_manual_entry('2026-09-20', None, 'INCOME', amount, 'Test')
        for day, event, kind, name in [('2026-02-30', None, 'INCOME', 'x'),
                                      ('2026-09-20', 2, 'INCOME', 'x'),
                                      ('2026-09-20', None, 'OTHER', 'x'),
                                      ('2026-09-20', None, 'INCOME', '')]:
            with self.assertRaises(ValueError):
                self.db.save_manual_entry(day, event, kind, '1', name)
        self.assertEqual(self.db.get_manual_entries(), [])


if __name__ == '__main__':
    unittest.main()
