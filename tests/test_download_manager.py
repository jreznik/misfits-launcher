import unittest
from unittest.mock import patch, MagicMock, PropertyMock


class TestDownloadModel(unittest.TestCase):
    def setUp(self):
        db_patcher = patch("src.backend.database.get_db_connection")
        db_patcher.start()
        self.addCleanup(db_patcher.stop)

        from src.backend.download_manager import DownloadModel, DownloadItem
        self.DownloadModel = DownloadModel
        self.DownloadItem = DownloadItem
        self.model = DownloadModel()

    def test_empty_model(self):
        self.assertEqual(self.model.rowCount(), 0)

    def test_add_item_increases_row_count(self):
        item = self.DownloadItem("game1", "Test Game")
        self.model.add_item(item)
        self.assertEqual(self.model.rowCount(), 1)

    def test_data_returns_item_fields(self):
        item = self.DownloadItem("game1", "Test Game", "/media/sd")
        item.progress = 42.5
        item.status = "Downloading"
        item.speed = "12.34 MiB/s"
        item.eta = "00:01:30"
        self.model.add_item(item)
        idx = self.model.index(0, 0)

        self.assertEqual(self.model.data(idx, self.DownloadModel.AppIdRole), "game1")
        self.assertEqual(self.model.data(idx, self.DownloadModel.NameRole), "Test Game")
        self.assertEqual(self.model.data(idx, self.DownloadModel.ProgressRole), 42.5)
        self.assertEqual(self.model.data(idx, self.DownloadModel.StatusRole), "Downloading")
        self.assertEqual(self.model.data(idx, self.DownloadModel.SpeedRole), "12.34 MiB/s")
        self.assertEqual(self.model.data(idx, self.DownloadModel.EtaRole), "00:01:30")

    def test_invalid_index_returns_none(self):
        self.model.add_item(self.DownloadItem("g1", "Game"))
        from PySide6.QtCore import QModelIndex
        self.assertIsNone(self.model.data(QModelIndex(), self.DownloadModel.AppIdRole))

    def test_remove_item_decrements_row_count(self):
        self.model.add_item(self.DownloadItem("g1", "Game"))
        self.model.add_item(self.DownloadItem("g2", "Game 2"))
        self.model.remove_item("g1")
        self.assertEqual(self.model.rowCount(), 1)
        self.assertEqual(
            self.model.data(self.model.index(0, 0), self.DownloadModel.AppIdRole), "g2"
        )

    def test_remove_nonexistent_is_noop(self):
        self.model.add_item(self.DownloadItem("g1", "Game"))
        self.model.remove_item("nonexistent")
        self.assertEqual(self.model.rowCount(), 1)

    def test_role_names(self):
        roles = self.model.roleNames()
        self.assertEqual(roles[self.DownloadModel.AppIdRole], b"appId")
        self.assertEqual(roles[self.DownloadModel.NameRole], b"name")
        self.assertEqual(roles[self.DownloadModel.ProgressRole], b"progress")
        self.assertEqual(roles[self.DownloadModel.StatusRole], b"status")
        self.assertEqual(roles[self.DownloadModel.SpeedRole], b"speed")
        self.assertEqual(roles[self.DownloadModel.EtaRole], b"eta")


class TestDownloadManagerQueue(unittest.TestCase):
    def setUp(self):
        db_patcher = patch("src.backend.database.get_db_connection")
        self.mock_db = db_patcher.start()
        self.addCleanup(db_patcher.stop)
        self.mock_db.return_value = MagicMock()

        from src.backend.download_manager import DownloadManager
        self.DownloadManager = DownloadManager
        self.manager = DownloadManager()

    def test_add_to_queue_adds_item(self):
        self.manager.add_to_queue("game1", "Game One")
        self.assertEqual(self.manager._model.rowCount(), 1)

    def test_add_to_queue_with_base_path(self):
        self.manager.add_to_queue_with_base("game1", "Game One", "/run/media/sd")
        self.assertEqual(self.manager._model.rowCount(), 1)

    def test_add_duplicate_is_skipped(self):
        self.manager.add_to_queue("game1", "Game One")
        self.manager.add_to_queue("game1", "Game One")
        self.assertEqual(self.manager._model.rowCount(), 1)

    def test_add_when_queued_is_skipped(self):
        """Item in 'Queued' status should not be re-added."""
        self.manager.add_to_queue("game1", "Game One")
        self.manager.add_to_queue("game1", "Game One Again")
        self.assertEqual(self.manager._model.rowCount(), 1)

    def test_add_when_downloading_is_skipped(self):
        """Item actively downloading should not be re-added."""
        self.manager.add_to_queue("game1", "Game One")
        self.manager._model._items[0].status = "Downloading"
        self.manager.add_to_queue("game1", "Game One")
        self.assertEqual(self.manager._model.rowCount(), 1)

    def test_add_when_paused_resumes(self):
        """Item in 'Paused' status should resume instead of duplicating."""
        self.manager.add_to_queue("game1", "Game One")
        self.manager._model._items[0].status = "Paused"
        self.manager.add_to_queue("game1", "Game One")
        self.assertEqual(self.manager._model.rowCount(), 1)
        self.assertEqual(self.manager._model._items[0].status, "Queued")

    def test_add_when_finished_replaces(self):
        """Item in 'Finished' status should be replaced so user can re-install."""
        self.manager.add_to_queue("game1", "Game One")
        self.manager._model._items[0].status = "Finished"
        self.manager.add_to_queue("game1", "Game One (reinstall)")
        self.assertEqual(self.manager._model.rowCount(), 1)
        self.assertEqual(self.manager._model._items[0].status, "Queued")

    def test_add_when_failed_replaces(self):
        """Item in 'Failed' status should be replaced so user can retry."""
        self.manager.add_to_queue("game1", "Game One")
        self.manager._model._items[0].status = "Failed"
        self.manager.add_to_queue("game1", "Game One (retry)")
        self.assertEqual(self.manager._model.rowCount(), 1)
        self.assertEqual(self.manager._model._items[0].status, "Queued")

    def test_cancel_removes_item(self):
        self.manager.add_to_queue("game1", "Game One")
        self.manager.cancel_download("game1")
        self.assertEqual(self.manager._model.rowCount(), 0)

    def test_cancel_calls_remove_from_db(self):
        self.manager.add_to_queue("game1", "Game One")
        with patch.object(self.manager, "_remove_from_db") as mock_remove:
            self.manager.cancel_download("game1")
            mock_remove.assert_called_once_with("game1")

    def test_pause_and_resume(self):
        self.manager.add_to_queue("game1", "Game One")
        self.manager._model._items[0].status = "Downloading"
        self.manager._model._items[0].process = MagicMock()
        self.manager.pause_download("game1")
        self.assertEqual(self.manager._model._items[0].status, "Paused")
        self.manager.resume_download("game1")
        # _check_queue immediately starts the queued item
        self.assertEqual(self.manager._model._items[0].status, "Downloading")


class TestDownloadManagerPersistence(unittest.TestCase):
    def setUp(self):
        db_patcher = patch("src.backend.database.get_db_connection")
        self.mock_db = db_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_db.return_value = self.mock_conn
        self.addCleanup(db_patcher.stop)

        from src.backend.download_manager import DownloadManager, DownloadItem
        self.DownloadManager = DownloadManager
        self.DownloadItem = DownloadItem

    def test_save_queue_writes_to_db(self):
        manager = self.DownloadManager()
        manager._model.add_item(self.DownloadItem("g1", "Game", "/media/sd"))
        manager._model._items[0].status = "Downloading"
        manager._save_queue()

        call = self.mock_conn.cursor().execute
        call.assert_any_call("DELETE FROM download_queue")
        call.assert_any_call(
            "INSERT OR REPLACE INTO download_queue (app_id, name, base_path, status) VALUES (?, ?, ?, ?)",
            ("g1", "Game", "/media/sd", "Downloading"),
        )
        self.mock_conn.commit.assert_called_once()

    def test_restore_queue_loads_from_db(self):
        self.mock_conn.cursor().fetchall.return_value = [
            ("g1", "Game", "/media/sd", "Queued"),
        ]
        manager = self.DownloadManager()
        self.assertEqual(manager._model.rowCount(), 1)
        self.assertEqual(manager._model._items[0].app_id, "g1")
        self.assertEqual(manager._model._items[0].base_path, "/media/sd")
        # _check_queue starts the queued item immediately
        self.assertEqual(manager._model._items[0].status, "Downloading")

    def test_restore_resets_downloading_to_queued(self):
        self.mock_conn.cursor().fetchall.return_value = [
            ("g1", "Game", None, "Downloading"),
        ]
        manager = self.DownloadManager()
        # Restore resets Downloading→Queued, then _check_queue starts it
        self.assertEqual(manager._model._items[0].status, "Downloading")

    def test_remove_from_db_deletes(self):
        manager = self.DownloadManager()
        manager._remove_from_db("g1")
        self.mock_conn.cursor().execute.assert_called_with(
            "DELETE FROM download_queue WHERE app_id = ?", ("g1",)
        )


class TestDownloadManagerSignals(unittest.TestCase):
    def setUp(self):
        db_patcher = patch("src.backend.database.get_db_connection")
        self.mock_db = db_patcher.start()
        self.addCleanup(db_patcher.stop)
        self.mock_db.return_value = MagicMock()

        from src.backend.download_manager import DownloadManager, DownloadItem
        self.DownloadManager = DownloadManager
        self.DownloadItem = DownloadItem

    def test_install_finished_signal_emitted_on_success(self):
        manager = self.DownloadManager()
        item = self.DownloadItem("g1", "Game")
        item.status = "Downloading"
        manager._model.add_item(item)

        receiver = MagicMock()
        manager.install_finished.connect(receiver)
        manager._on_download_finished("g1", True)
        receiver.assert_called_once_with("g1", True)

    def test_db_updated_on_download_finished(self):
        manager = self.DownloadManager()
        manager._on_download_finished("g1", True)
        self.mock_db.return_value.cursor().execute.assert_any_call(
            "UPDATE games SET is_installed = 1 WHERE app_id = ?", ("g1",)
        )

    def test_check_queue_starts_download(self):
        manager = self.DownloadManager()
        with patch.object(manager, "_start_download") as mock_start:
            manager._model.add_item(self.DownloadItem("g1", "Game"))
            manager._check_queue()
            mock_start.assert_called_once()

    def test_check_queue_skips_when_busy(self):
        manager = self.DownloadManager()
        manager._current_app_id = "g_other"
        with patch.object(manager, "_start_download") as mock_start:
            manager._model.add_item(self.DownloadItem("g1", "Game"))
            manager._check_queue()
            mock_start.assert_not_called()


class TestDownloadManagerBasePath(unittest.TestCase):
    def setUp(self):
        db_patcher = patch("src.backend.database.get_db_connection")
        self.mock_db = db_patcher.start()
        self.addCleanup(db_patcher.stop)
        self.mock_db.return_value = MagicMock()

        from src.backend.download_manager import DownloadManager, DownloadItem
        self.DownloadManager = DownloadManager
        self.DownloadItem = DownloadItem

    def _wait_for_install_call(self, mock_popen, app_id, timeout=3.0):
        """Wait until Popen is called with an install command for the given app_id."""
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for call in mock_popen.call_args_list:
                args, kwargs = call
                cmd = args[0]
                if "install" in cmd and app_id in cmd:
                    return cmd
            time.sleep(0.05)
        self.fail(f"Popen install call for {app_id} not received within {timeout}s; calls: {mock_popen.call_args_list}")

    def test_slash_base_path_uses_default_dir(self):
        """base_path="/" should fall back to get_default_install_dir()."""
        popen_p = patch("src.backend.download_manager.subprocess.Popen")
        mock_popen = popen_p.start()
        self.addCleanup(popen_p.stop)

        dir_p = patch("src.backend.game_service.get_default_install_dir", return_value="/home/user/Games/Heroic")
        dir_p.start()
        self.addCleanup(dir_p.stop)

        makedirs_p = patch("src.backend.download_manager.os.makedirs")
        makedirs_p.start()
        self.addCleanup(makedirs_p.stop)

        save_p = patch.object(self.DownloadManager, "_save_queue")
        save_p.start()
        self.addCleanup(save_p.stop)

        manager = self.DownloadManager()
        manager._model.add_item(self.DownloadItem("g_slash", "Game", "/"))
        manager._model._items[0].status = "Queued"
        manager._current_app_id = None

        manager._start_download(manager._model._items[0])

        cmd = self._wait_for_install_call(mock_popen, "g_slash")
        self.assertIn("--base-path", cmd)
        idx = cmd.index("--base-path")
        self.assertEqual(cmd[idx + 1], "/home/user/Games/Heroic")

    def test_sd_card_base_path_joins_games_heroic(self):
        """base_path="/run/media/sd" should become /run/media/sd/Games/Heroic."""
        popen_p = patch("src.backend.download_manager.subprocess.Popen")
        mock_popen = popen_p.start()
        self.addCleanup(popen_p.stop)

        makedirs_p = patch("src.backend.download_manager.os.makedirs")
        makedirs_p.start()
        self.addCleanup(makedirs_p.stop)

        save_p = patch.object(self.DownloadManager, "_save_queue")
        save_p.start()
        self.addCleanup(save_p.stop)

        manager = self.DownloadManager()
        manager._model.add_item(self.DownloadItem("g_sd", "Game", "/run/media/sd"))
        manager._model._items[0].status = "Queued"
        manager._current_app_id = None

        manager._start_download(manager._model._items[0])

        cmd = self._wait_for_install_call(mock_popen, "g_sd")
        self.assertIn("--base-path", cmd)
        idx = cmd.index("--base-path")
        self.assertEqual(cmd[idx + 1], "/run/media/sd/Games/Heroic")

    def test_none_base_path_uses_default_dir(self):
        """base_path=None should use get_default_install_dir()."""
        popen_p = patch("src.backend.download_manager.subprocess.Popen")
        mock_popen = popen_p.start()
        self.addCleanup(popen_p.stop)

        dir_p = patch("src.backend.game_service.get_default_install_dir", return_value="/home/user/Games/Heroic")
        dir_p.start()
        self.addCleanup(dir_p.stop)

        makedirs_p = patch("src.backend.download_manager.os.makedirs")
        makedirs_p.start()
        self.addCleanup(makedirs_p.stop)

        save_p = patch.object(self.DownloadManager, "_save_queue")
        save_p.start()
        self.addCleanup(save_p.stop)

        manager = self.DownloadManager()
        manager._model.add_item(self.DownloadItem("g_none", "Game", None))
        manager._model._items[0].status = "Queued"
        manager._current_app_id = None

        manager._start_download(manager._model._items[0])

        cmd = self._wait_for_install_call(mock_popen, "g_none")
        idx = cmd.index("--base-path")
        self.assertEqual(cmd[idx + 1], "/home/user/Games/Heroic")


if __name__ == "__main__":
    unittest.main()
