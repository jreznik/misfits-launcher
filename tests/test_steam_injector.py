import unittest
from unittest.mock import patch, MagicMock, mock_open


class TestCalculateAppId(unittest.TestCase):
    def test_known_values(self):
        from src.backend.steam_injector import calculate_appid
        # Test with known inputs to ensure consistency
        result = calculate_appid(
            "/some/game.exe", "Test Game"
        )
        self.assertIsInstance(result, int)
        # Same inputs should always give same output
        result2 = calculate_appid(
            "/some/game.exe", "Test Game"
        )
        self.assertEqual(result, result2)

    def test_different_inputs_give_different_ids(self):
        from src.backend.steam_injector import calculate_appid
        id1 = calculate_appid("/game1.exe", "Game One")
        id2 = calculate_appid("/game2.exe", "Game Two")
        self.assertNotEqual(id1, id2)

    def test_appid_negative_for_high_crc(self):
        from src.backend.steam_injector import calculate_appid
        result = calculate_appid("/path/to/exe.exe", "My Game")
        # Steam appids are 32-bit signed
        self.assertLess(abs(result), 2**31)


class TestCalculateLongId(unittest.TestCase):
    def test_conversion(self):
        from src.backend.steam_injector import calculate_long_id
        result = calculate_long_id(12345)
        self.assertIsInstance(result, int)
        self.assertGreater(result, 2**32)

    def test_consistency(self):
        from src.backend.steam_injector import calculate_long_id
        self.assertEqual(
            calculate_long_id(12345),
            calculate_long_id(12345),
        )


class TestAddToSteam(unittest.TestCase):
    @patch("src.backend.steam_injector.get_steam_user_dirs")
    @patch("src.backend.steam_injector.Path")
    @patch("builtins.open", new_callable=mock_open, read_data=b"\x00" * 100)
    @patch("src.backend.steam_injector.vdf.binary_loads")
    @patch("src.backend.steam_injector.vdf.binary_dumps")
    def test_add_to_steam_basic(
        self, mock_dumps, mock_loads, mock_file, mock_path, mock_user_dirs
    ):
        mock_user_dirs.return_value = []
        mock_loads.return_value = {"shortcuts": {}}

        from src.backend.steam_injector import add_to_steam
        result = add_to_steam(
            "Test Game", "/usr/bin/true",
            icon_path=None,
            grid_art_path=None,
            hero_art_path=None,
            logo_art_path=None,
        )
        self.assertIsInstance(result, bool)
        # Should fail gracefully when no steam user dirs exist
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
