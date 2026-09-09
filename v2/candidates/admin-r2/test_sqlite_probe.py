"""Independent preparation probe: no imports from future product implementation."""
import sqlite3
import tempfile
import unittest
from pathlib import Path


class SQLiteProbe(unittest.TestCase):
    def test_transaction_unique_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = sqlite3.connect(Path(directory) / "probe.sqlite")
            try:
                connection.executescript("CREATE TABLE item (id INTEGER PRIMARY KEY, value INTEGER); CREATE TABLE receipt (key TEXT UNIQUE);")
                connection.execute("INSERT INTO item VALUES (1, 1)")
                connection.commit()
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("UPDATE item SET value=0 WHERE id=1")
                connection.execute("INSERT INTO receipt VALUES ('synthetic-key')")
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("INSERT INTO receipt VALUES ('synthetic-key')")
                connection.rollback()
                self.assertEqual(connection.execute("SELECT value FROM item").fetchone(), (1,))
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM receipt").fetchone(), (0,))
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("UPDATE item SET value=0 WHERE id=1")
                connection.execute("INSERT INTO receipt VALUES ('synthetic-key')")
                connection.commit()
                self.assertEqual(connection.execute("SELECT value FROM item").fetchone(), (0,))
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM receipt").fetchone(), (1,))
            finally:
                connection.close()
