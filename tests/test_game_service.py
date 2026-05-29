import os
import time
import unittest
from unittest.mock import patch, MagicMock


class TestGetDefaultInstallDir(unittest.TestCase):
    @patch("src.backend.game_service.os.path.expanduser")
    @patch("src.backend.game_service.os.makedirs")
    def test_returns_heroic_path(self, mock_makedirs, mock_expanduser):
        mock_expanduser.side_effect = lambda p: p.replace("~", "/home/user", 1) if p.startswith("~") else p
        from src.backend.game_service import get_default_install_dir
        path = get_default_install_dir()
        self.assertEqual(path, "/home/user/Games/Heroic")
        mock_makedirs.assert_called_once_with("/home/user/Games/Heroic", exist_ok=True)

    @patch("src.backend.game_service.os.makedirs")
    def test_creates_directory(self, mock_makedirs):
        with patch("src.backend.game_service.os.path.expanduser", return_value="/home/user"):
            from src.backend.game_service import get_default_install_dir
            get_default_install_dir()
            mock_makedirs.assert_called_once()


class TestInstallGame(unittest.TestCase):
    def setUp(self):
        self.subprocess_patcher = patch(
            "src.backend.game_service.subprocess.Popen"
        )
        self.mock_popen = self.subprocess_patcher.start()
        self.mock_proc = MagicMock()
        self.mock_proc.stdout = ["Progress: 50.00%", "All done\n"]
        self.mock_proc.returncode = 0
        self.mock_popen.return_value = self.mock_proc

        self.makedirs_patcher = patch("src.backend.game_service.os.makedirs")
        self.mock_makedirs = self.makedirs_patcher.start()

        self.db_patcher = patch(
            "src.backend.game_service.get_db_connection"
        )
        self.mock_db = self.db_patcher.start()
        self.mock_db.return_value = MagicMock()

    def tearDown(self):
        self.subprocess_patcher.stop()
        self.makedirs_patcher.stop()
        self.db_patcher.stop()

    def test_install_uses_default_dir_on_empty_base(self):
        with patch(
            "src.backend.game_service.get_default_install_dir",
            return_value="/home/user/Games/Heroic",
        ):
            from src.backend.game_service import GameService
            service = GameService()
            service.install_game("test_app")
            time.sleep(0.5)
            install_calls = [c for c in self.mock_popen.call_args_list if "install" in c[0][0]]
            self.assertGreater(len(install_calls), 0)
            call_args = install_calls[-1][0][0]
            self.assertIn("--base-path", call_args)
            self.assertIn("/home/user/Games/Heroic", call_args)

    def test_install_sd_card_uses_joined_path(self):
        from src.backend.game_service import GameService
        service = GameService()
        service.install_game("test_app", "/run/media/deck/MySD")
        time.sleep(0.3)
        self.assertGreater(self.mock_popen.call_count, 0)
        call_args = self.mock_popen.call_args[0][0]
        self.assertIn("/run/media/deck/MySD/Games/Heroic", call_args)

    def test_sync_to_heroic_called_on_success(self):
        with patch(
            "src.backend.epic_service.sync_installed_to_heroic_config"
        ) as mock_sync:
            from src.backend.game_service import GameService
            service = GameService()
            service.install_game("test_app")
            time.sleep(0.3)
            mock_sync.assert_called_once_with("test_app", add=True)

    def test_sync_not_called_on_failure(self):
        self.mock_proc.returncode = 1
        with patch(
            "src.backend.epic_service.sync_installed_to_heroic_config"
        ) as mock_sync:
            from src.backend.game_service import GameService
            service = GameService()
            service.install_game("test_app")
            time.sleep(0.3)
            mock_sync.assert_not_called()


class TestUninstallGame(unittest.TestCase):
    def setUp(self):
        subprocess_patcher = patch(
            "src.backend.game_service.subprocess.run"
        )
        self.mock_run = subprocess_patcher.start()
        self.mock_run.return_value = MagicMock(returncode=0)
        self.addCleanup(subprocess_patcher.stop)

        path_patcher = patch(
            "src.backend.epic_service.get_install_path_from_all_configs"
        )
        self.mock_path = path_patcher.start()
        self.addCleanup(path_patcher.stop)

        leg_patcher = patch(
            "src.backend.umu_launcher.find_legendary",
            return_value="legendary",
        )
        self.mock_leg = leg_patcher.start()
        self.addCleanup(leg_patcher.stop)

        db_patcher = patch(
            "src.backend.game_service.get_db_connection"
        )
        self.mock_db = db_patcher.start()
        self.mock_db.return_value = MagicMock()
        self.addCleanup(db_patcher.stop)

    def test_uninstall_calls_legendary(self):
        from src.backend.game_service import GameService
        service = GameService()
        service.uninstall_game("test_app")
        time.sleep(0.3)
        self.mock_run.assert_called_once()
        call_args = self.mock_run.call_args[0][0]
        self.assertIn("uninstall", call_args)
        self.assertEqual(call_args[0], "legendary")

    def test_rmtree_called_when_dir_exists(self):
        self.mock_path.return_value = "/tmp/test_gamedir"
        with patch("src.backend.game_service.shutil.rmtree") as mock_rmtree, \
             patch("src.backend.game_service.os.path.exists", return_value=True):
            from src.backend.game_service import GameService
            service = GameService()
            service.uninstall_game("test_app")
            time.sleep(0.3)
            mock_rmtree.assert_called_once_with("/tmp/test_gamedir", ignore_errors=True)

    def test_sync_heroic_called_on_success(self):
        with patch(
            "src.backend.epic_service.sync_installed_to_heroic_config"
        ) as mock_sync:
            from src.backend.game_service import GameService
            service = GameService()
            service.uninstall_game("test_app")
            time.sleep(0.3)
            mock_sync.assert_called_once_with("test_app", add=False)


if __name__ == "__main__":
    unittest.main()
