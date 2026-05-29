import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from PySide6.QtCore import Qt, QModelIndex


class TestGameModel(unittest.TestCase):
    def setUp(self):
        from src.backend.game_manager import GameModel
        self.model = GameModel()

    def test_empty_model(self):
        self.assertEqual(self.model.rowCount(), 0)

    def test_update_games(self):
        games = [
            {
                "app_id": "game1",
                "name": "Test Game",
                "store_source": "Epic",
                "is_installed": 1,
                "last_played_timestamp": 1000,
                "install_timestamp": 500,
                "artwork_path": "/art/game1.jpg",
                "hero_path": "/hero/game1.jpg",
                "logo_path": "/logo/game1.png",
                "protondb_tier": "gold",
                "is_new": False,
            }
        ]
        self.model.update_games(games)
        self.assertEqual(self.model.rowCount(), 1)

        idx = self.model.index(0, 0)
        self.assertEqual(
            self.model.data(idx, self.model.AppIdRole), "game1"
        )
        self.assertEqual(
            self.model.data(idx, self.model.NameRole), "Test Game"
        )
        self.assertEqual(
            self.model.data(idx, self.model.StoreSourceRole), "Epic"
        )
        self.assertEqual(
            self.model.data(idx, self.model.IsInstalledRole), True
        )
        self.assertEqual(
            self.model.data(idx, self.model.LastPlayedRole), 1000
        )
        self.assertEqual(
            self.model.data(idx, self.model.ArtworkRole), "/art/game1.jpg"
        )
        self.assertEqual(
            self.model.data(idx, self.model.HeroRole), "/hero/game1.jpg"
        )
        self.assertEqual(
            self.model.data(idx, self.model.LogoRole), "/logo/game1.png"
        )
        self.assertEqual(
            self.model.data(idx, self.model.ProtonTierRole), "gold"
        )
        self.assertEqual(
            self.model.data(idx, self.model.InstallTimestampRole), 500
        )

    def test_update_games_replaces(self):
        self.model.update_games([
            {"app_id": "g1", "name": "G1", "store_source": "Epic"}
        ])
        self.model.update_games([
            {"app_id": "g2", "name": "G2", "store_source": "Epic"}
        ])
        self.assertEqual(self.model.rowCount(), 1)
        idx = self.model.index(0, 0)
        self.assertEqual(
            self.model.data(idx, self.model.AppIdRole), "g2"
        )

    def test_invalid_index_returns_none(self):
        self.model.update_games([
            {"app_id": "g1", "name": "G1", "store_source": "Epic"}
        ])
        invalid = QModelIndex()
        self.assertIsNone(self.model.data(invalid, self.model.NameRole))
        self.assertIsNone(self.model.data(self.model.index(5, 0), self.model.NameRole))

    def test_role_names(self):
        names = self.model.roleNames()
        self.assertEqual(names[self.model.AppIdRole], b"appId")
        self.assertEqual(names[self.model.NameRole], b"name")
        self.assertEqual(names[self.model.IsInstalledRole], b"isInstalled")


class TestGameManagerInstallRouting(unittest.TestCase):
    def setUp(self):
        self.mock_dl = MagicMock()

        self.mock_conn = MagicMock()

        self.db_patcher = patch("src.backend.game_manager.get_db_connection")
        self.mock_db = self.db_patcher.start()
        self.addCleanup(self.db_patcher.stop)
        self.mock_db.return_value = self.mock_conn

        self.db_patcher2 = patch("src.backend.database.get_db_connection")
        self.mock_db2 = self.db_patcher2.start()
        self.addCleanup(self.db_patcher2.stop)
        self.mock_db2.return_value = self.mock_conn

        # Patch all the heavy __init__ deps
        self.gs_patcher = patch("src.backend.game_manager.GameService")
        self.gs_patcher.start()
        self.addCleanup(self.gs_patcher.stop)

        self.umu_patcher = patch("src.backend.game_manager.UMULauncher")
        self.umu_patcher.start()
        self.addCleanup(self.umu_patcher.stop)

        self.proton_patcher = patch("src.backend.game_manager.ProtonDBService")
        self.proton_patcher.start()
        self.addCleanup(self.proton_patcher.stop)

    def from_manager(self):
        from src.backend.game_manager import GameManager
        return GameManager(download_manager=self.mock_dl)

    def test_install_with_base_path_calls_add_to_queue_with_base(self):
        manager = self.from_manager()
        with patch.object(manager, "_get_game_name", return_value="Game One"):
            manager.install_game("game1", "/run/media/sd")
            self.mock_dl.add_to_queue_with_base.assert_called_once_with(
                "game1", "Game One", "/run/media/sd"
            )

    def test_install_without_base_path_calls_add_to_queue(self):
        manager = self.from_manager()
        with patch.object(manager, "_get_game_name", return_value="Game One"):
            manager.install_game("game1")
            self.mock_dl.add_to_queue.assert_called_once_with("game1", "Game One")

    def test_install_with_none_base_path_calls_add_to_queue(self):
        manager = self.from_manager()
        with patch.object(manager, "_get_game_name", return_value="Game One"):
            manager.install_game("game1", None)
            self.mock_dl.add_to_queue.assert_called_once_with("game1", "Game One")

    def test_install_with_slash_base_path_calls_add_to_queue_with_base(self):
        """Even "/" gets passed through; the DownloadManager handles the "/" guard."""
        manager = self.from_manager()
        with patch.object(manager, "_get_game_name", return_value="Game One"):
            manager.install_game("game1", "/")
            self.mock_dl.add_to_queue_with_base.assert_called_once_with(
                "game1", "Game One", "/"
            )

    def test_install_no_dl_manager_does_not_crash(self):
        """GameManager should not crash when download_manager is None."""
        from src.backend.game_manager import GameManager
        manager = GameManager(download_manager=None)
        # Should not raise
        manager.install_game("game1", "/some/path")

    def test_get_game_name_returns_from_db(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("DB Game Name",)
        self.mock_conn.cursor.return_value = mock_cursor
        from src.backend.game_manager import GameManager
        manager = GameManager(download_manager=None)
        name = manager._get_game_name("game1")
        self.assertEqual(name, "DB Game Name")

    def test_get_game_name_returns_empty_on_missing(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        self.mock_conn.cursor.return_value = mock_cursor
        from src.backend.game_manager import GameManager
        manager = GameManager(download_manager=None)
        name = manager._get_game_name("unknown")
        self.assertEqual(name, "")

    def test_on_install_finished_refreshes_and_re_emits(self):
        manager = self.from_manager()
        with patch.object(manager, "refresh_models") as mock_refresh, \
             patch.object(manager, "fetch_game_info") as mock_fetch, \
             patch.object(manager, "install_finished") as mock_signal:
            manager._on_install_finished("game1", True)
            mock_refresh.assert_called_once()
            mock_fetch.assert_called_once_with("game1")
            mock_signal.emit.assert_called_once_with("game1", True)

    def test_on_uninstall_finished_refreshes_and_re_emits(self):
        manager = self.from_manager()
        with patch.object(manager, "refresh_models") as mock_refresh, \
             patch.object(manager, "fetch_game_info") as mock_fetch, \
             patch.object(manager, "uninstall_status_changed") as mock_signal:
            manager._on_uninstall_finished("game1", True)
            mock_refresh.assert_called_once()
            mock_fetch.assert_called_once_with("game1")
            mock_signal.emit.assert_called_once_with("game1", True)

    def test_uninstall_game_calls_service(self):
        manager = self.from_manager()
        with patch.object(manager._service, "uninstall_game") as mock_uninstall:
            manager.uninstall_game("game1")
            mock_uninstall.assert_called_once_with("game1")


if __name__ == "__main__":
    unittest.main()
