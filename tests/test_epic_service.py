import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from tests.conftest import make_installed_json, TempConfigDir


class TestConfigHelpers(unittest.TestCase):
    def setUp(self):
        self.patcher = patch(
            "src.backend.epic_service.LEGENDARY_CONFIG_DIRS",
            ["/tmp/legendary_standard", "/tmp/legendary_heroic"],
        )
        self.mock_dirs = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("src.backend.epic_service.os.path.exists")
    @patch("builtins.open")
    def test_merges_empty_configs(self, mock_open, mock_exists):
        mock_exists.return_value = False
        from src.backend.epic_service import get_installed_games_from_all_configs
        result = get_installed_games_from_all_configs()
        self.assertEqual(result, {})

    @patch("src.backend.epic_service.os.path.exists")
    def test_merges_single_config(self, mock_exists):
        data = make_installed_json(
            ("game1", "Test Game 1", "/games/test1"),
            ("game2", "Test Game 2", "/games/test2"),
        )
        mock_exists.side_effect = lambda p: p == "/tmp/legendary_standard/installed.json"
        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(data))):
            from src.backend.epic_service import get_installed_games_from_all_configs
            result = get_installed_games_from_all_configs()
            self.assertIn("game1", result)
            self.assertIn("game2", result)
            self.assertEqual(len(result), 2)

    @patch("src.backend.epic_service.os.path.exists")
    def test_merges_across_configs(self, mock_exists):
        std_data = make_installed_json(
            ("game1", "Standard Game", "/games/std1"),
        )
        heroic_data = make_installed_json(
            ("game2", "Heroic Game", "/games/hero2"),
        )

        def exists_side_effect(p):
            if p == "/tmp/legendary_standard/installed.json":
                return True
            if p == "/tmp/legendary_heroic/installed.json":
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        def open_side_effect(path, *args, **kwargs):
            if "legendary_standard" in path:
                return unittest.mock.mock_open(read_data=json.dumps(std_data)).return_value
            return unittest.mock.mock_open(read_data=json.dumps(heroic_data)).return_value

        with patch("builtins.open", side_effect=open_side_effect):
            from src.backend.epic_service import get_installed_games_from_all_configs
            result = get_installed_games_from_all_configs()
            self.assertIn("game1", result)
            self.assertIn("game2", result)
            self.assertEqual(len(result), 2)

    @patch("src.backend.epic_service.os.path.exists")
    def test_heroic_overrides_standard(self, mock_exists):
        std_data = make_installed_json(("game1", "Old Version", "/games/old"))
        heroic_data = make_installed_json(("game1", "New Version", "/games/new"))

        def exists_side_effect(p):
            return p in (
                "/tmp/legendary_standard/installed.json",
                "/tmp/legendary_heroic/installed.json",
            )

        mock_exists.side_effect = exists_side_effect

        def open_side_effect(path, *args, **kwargs):
            if "legendary_heroic" in path:
                return unittest.mock.mock_open(read_data=json.dumps(heroic_data)).return_value
            return unittest.mock.mock_open(read_data=json.dumps(std_data)).return_value

        with patch("builtins.open", side_effect=open_side_effect):
            from src.backend.epic_service import get_installed_games_from_all_configs
            result = get_installed_games_from_all_configs()
            # Heroic comes second, so it overrides
            self.assertEqual(result["game1"]["install_path"], "/games/new")


class TestGetInstallPath(unittest.TestCase):
    def setUp(self):
        self.patcher = patch(
            "src.backend.epic_service.LEGENDARY_CONFIG_DIRS",
            ["/tmp/legendary_standard", "/tmp/legendary_heroic"],
        )
        self.mock_dirs = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("src.backend.epic_service.os.path.exists")
    def test_finds_path_in_standard(self, mock_exists):
        data = make_installed_json(
            ("game1", "Test", "/games/test1"),
        )

        def exists_side_effect(p):
            return p == "/tmp/legendary_standard/installed.json"

        mock_exists.side_effect = exists_side_effect

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(data))):
            from src.backend.epic_service import get_install_path_from_all_configs
            path = get_install_path_from_all_configs("game1")
            self.assertEqual(path, "/games/test1")

    @patch("src.backend.epic_service.os.path.exists")
    def test_returns_none_for_missing_game(self, mock_exists):
        data = make_installed_json(
            ("game1", "Test", "/games/test1"),
        )

        def exists_side_effect(p):
            return p == "/tmp/legendary_standard/installed.json"

        mock_exists.side_effect = exists_side_effect

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(data))):
            from src.backend.epic_service import get_install_path_from_all_configs
            path = get_install_path_from_all_configs("unknown_game")
            self.assertIsNone(path)

    @patch("src.backend.epic_service.os.path.exists")
    def test_returns_none_when_no_configs(self, mock_exists):
        mock_exists.return_value = False
        from src.backend.epic_service import get_install_path_from_all_configs
        path = get_install_path_from_all_configs("game1")
        self.assertIsNone(path)


class TestSyncToHeroic(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="misfit_test_")
        # sync_installed_to_heroic_config uses a hardcoded path with os.path.expanduser
        self.heroic_config = os.path.join(
            self.tmpdir,
            ".var/app/com.heroicgameslauncher.hgl/config/heroic/legendaryConfig/legendary",
        )
        os.makedirs(self.heroic_config)
        self.standard_config = os.path.join(self.tmpdir, ".config/legendary")
        os.makedirs(self.standard_config)

        # Patch expanduser so ~ resolves to our temp dir
        self.expanduser_patcher = patch(
            "src.backend.epic_service.os.path.expanduser",
            side_effect=lambda p: p.replace("~", self.tmpdir, 1) if p.startswith("~") else p,
        )
        self.expanduser_patcher.start()

        # Also patch LEGENDARY_CONFIG_DIRS to use our temp standard path
        self.dirs_patcher = patch(
            "src.backend.epic_service.LEGENDARY_CONFIG_DIRS",
            [self.standard_config, self.heroic_config],
        )
        self.dirs_patcher.start()

    def tearDown(self):
        self.dirs_patcher.stop()
        self.expanduser_patcher.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_standard(self, data):
        with open(os.path.join(self.standard_config, "installed.json"), "w") as f:
            json.dump(data, f)

    def _write_heroic(self, data):
        with open(os.path.join(self.heroic_config, "installed.json"), "w") as f:
            json.dump(data, f)

    def _read_heroic(self):
        path = os.path.join(self.heroic_config, "installed.json")
        if not os.path.exists(path):
            return {}
        with open(path) as f:
            return json.load(f)

    def test_add_copies_from_standard(self):
        std_data = make_installed_json(
            ("game1", "Test Game", "/games/test1"),
        )
        self._write_standard(std_data)
        from src.backend.epic_service import sync_installed_to_heroic_config
        sync_installed_to_heroic_config("game1", add=True)
        heroic = self._read_heroic()
        self.assertIn("game1", heroic)
        self.assertEqual(heroic["game1"]["install_path"], "/games/test1")

    def test_add_updates_existing_heroic(self):
        std_data = make_installed_json(("game1", "Updated", "/games/updated"))
        heroic_before = make_installed_json(
            ("game1", "Old", "/games/old"),
            ("game2", "Other", "/games/other"),
        )
        self._write_standard(std_data)
        self._write_heroic(heroic_before)
        from src.backend.epic_service import sync_installed_to_heroic_config
        sync_installed_to_heroic_config("game1", add=True)
        heroic = self._read_heroic()
        self.assertIn("game1", heroic)
        self.assertIn("game2", heroic)
        self.assertEqual(heroic["game1"]["install_path"], "/games/updated")

    def test_remove_deletes_from_heroic(self):
        heroic_before = make_installed_json(
            ("game1", "Test", "/games/test1"),
            ("game2", "Other", "/games/other"),
        )
        self._write_heroic(heroic_before)
        from src.backend.epic_service import sync_installed_to_heroic_config
        sync_installed_to_heroic_config("game1", add=False)
        heroic = self._read_heroic()
        self.assertNotIn("game1", heroic)
        self.assertIn("game2", heroic)

    def test_remove_nonexistent_is_noop(self):
        heroic_before = make_installed_json(
            ("game2", "Other", "/games/other"),
        )
        self._write_heroic(heroic_before)
        from src.backend.epic_service import sync_installed_to_heroic_config
        sync_installed_to_heroic_config("game1", add=False)
        heroic = self._read_heroic()
        self.assertIn("game2", heroic)
        self.assertEqual(len(heroic), 1)

    def test_no_heroic_config_is_noop(self):
        import shutil
        shutil.rmtree(self.heroic_config)
        std_data = make_installed_json(("game1", "Test", "/games/test1"))
        self._write_standard(std_data)
        from src.backend.epic_service import sync_installed_to_heroic_config
        sync_installed_to_heroic_config("game1", add=True)

    def test_no_standard_config_is_noop_on_add(self):
        import shutil
        shutil.rmtree(self.standard_config)
        from src.backend.epic_service import sync_installed_to_heroic_config
        sync_installed_to_heroic_config("game1", add=True)


class TestConfigPaths(unittest.TestCase):
    def test_paths_are_absolute(self):
        from src.backend.epic_service import LEGENDARY_CONFIG_DIRS
        for p in LEGENDARY_CONFIG_DIRS:
            self.assertTrue(os.path.isabs(p))

    def test_standard_config_has_legendary(self):
        from src.backend.epic_service import LEGENDARY_CONFIG_DIRS
        self.assertIn(".config/legendary", LEGENDARY_CONFIG_DIRS[0])

    def test_heroic_config_has_heroic(self):
        from src.backend.epic_service import LEGENDARY_CONFIG_DIRS
        self.assertIn("heroicgameslauncher", LEGENDARY_CONFIG_DIRS[1])


if __name__ == "__main__":
    unittest.main()
