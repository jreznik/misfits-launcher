import os
import sys
import tempfile
import unittest
from unittest.mock import patch, PropertyMock

import src.backend.database as db


class TestGetDataDir(unittest.TestCase):
    @patch("src.backend.database.os.makedirs")
    def test_default_path(self, mock_mkdir):
        with patch.dict(os.environ, {}, clear=True):
            path = db.get_data_dir()
            self.assertTrue(path.endswith("/.local/share/misfitslauncher"))

    @patch("src.backend.database.os.makedirs")
    def test_respects_xdg_data_home(self, mock_mkdir):
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}):
            path = db.get_data_dir()
            self.assertEqual(path, "/custom/data/misfitslauncher")

    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"XDG_DATA_HOME": tmp}):
                path = db.get_data_dir()
                self.assertTrue(os.path.isdir(path))


class TestDatabaseInit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_patcher = patch(
            "src.backend.database.DB_PATH",
            os.path.join(self.tmpdir, "games.db"),
        )
        self.db_patcher.start()

    def tearDown(self):
        self.db_patcher.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_db_creates_games_table(self):
        db.init_db()
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='games'"
        )
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_games_table_has_expected_columns(self):
        db.init_db()
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(games)")
        columns = {r[1] for r in cursor.fetchall()}
        expected = {
            "app_id", "name", "store_source", "is_installed",
            "last_played_timestamp", "install_timestamp",
            "artwork_path", "hero_path", "logo_path",
            "description", "protondb_tier",
        }
        self.assertTrue(expected.issubset(columns))
        conn.close()

    def test_get_db_connection_returns_writable(self):
        db.init_db()
        conn = db.get_db_connection()
        conn.execute(
            "INSERT INTO games (app_id, name, store_source) VALUES (?, ?, ?)",
            ("test_id", "Test Game", "Epic"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT name FROM games WHERE app_id=?", ("test_id",)
        ).fetchone()
        self.assertEqual(row[0], "Test Game")
        conn.close()

    def test_init_db_is_idempotent(self):
        db.init_db()
        db.init_db()
        db.init_db()
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        )
        self.assertEqual(cursor.fetchone()[0], 2)
        conn.close()


if __name__ == "__main__":
    unittest.main()
