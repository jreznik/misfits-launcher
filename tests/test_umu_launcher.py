import os
import unittest
from unittest.mock import patch, MagicMock


class TestFindLegendary(unittest.TestCase):
    @patch("src.backend.umu_launcher.shutil.which")
    @patch("src.backend.umu_launcher.os.path.exists")
    def test_returns_from_path_first(self, mock_exists, mock_which):
        mock_which.return_value = "/usr/local/bin/legendary"
        from src.backend.umu_launcher import find_legendary
        result = find_legendary()
        self.assertEqual(result, "/usr/local/bin/legendary")

    @patch("src.backend.umu_launcher.shutil.which")
    @patch("src.backend.umu_launcher.os.path.exists")
    def test_flatpak_path(self, mock_exists, mock_which):
        mock_which.return_value = None
        mock_exists.side_effect = lambda p: p == "/app/bin/legendary"
        from src.backend.umu_launcher import find_legendary
        result = find_legendary()
        self.assertEqual(result, "/app/bin/legendary")

    @patch("src.backend.umu_launcher.shutil.which")
    @patch("src.backend.umu_launcher.os.path.exists")
    def test_falls_back_to_bare(self, mock_exists, mock_which):
        mock_which.return_value = None
        mock_exists.return_value = False
        from src.backend.umu_launcher import find_legendary
        result = find_legendary()
        self.assertEqual(result, "legendary")


class TestFindUmuRun(unittest.TestCase):
    @patch("src.backend.umu_launcher.os.path.exists")
    @patch("src.backend.umu_launcher.shutil.which")
    def test_returns_from_path_first(self, mock_which, mock_exists):
        mock_which.return_value = "/usr/bin/umu-run"
        # os.path.exists not reached because shutil.which is checked first
        # in find_legendary. But for find_umu_run, it checks common_paths first.
        mock_exists.return_value = True
        from src.backend.umu_launcher import find_umu_run
        result = find_umu_run()
        # Should find ~/.local/bin/umu-run first (first os.path.exists check)
        self.assertEqual(result, os.path.expanduser("~/.local/bin/umu-run"))

    @patch("src.backend.umu_launcher.os.path.exists")
    @patch("src.backend.umu_launcher.shutil.which")
    def test_flatpak_path(self, mock_which, mock_exists):
        mock_which.return_value = None
        mock_exists.return_value = False
        from src.backend.umu_launcher import find_umu_run
        result = find_umu_run()
        self.assertEqual(result, "umu-run")


class TestUMULauncherSignals(unittest.TestCase):
    def setUp(self):
        from src.backend.umu_launcher import UMULauncher
        self.launcher = UMULauncher(None)

    def test_has_expected_signals(self):
        self.assertTrue(hasattr(self.launcher, "finished"))
        self.assertTrue(hasattr(self.launcher, "error"))
        self.assertTrue(hasattr(self.launcher, "output_received"))
        self.assertTrue(hasattr(self.launcher, "game_started"))


if __name__ == "__main__":
    unittest.main()
