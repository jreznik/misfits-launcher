import unittest
from unittest.mock import patch, MagicMock


class TestProtonDBService(unittest.TestCase):
    @patch("src.backend.protondb_service.requests.get")
    def test_get_steam_appid_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "total": 1,
            "items": [{"id": 12345, "name": "Test Game"}],
        }
        mock_get.return_value = mock_resp

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_steam_appid("Test Game")
        self.assertEqual(result, "12345")

    @patch("src.backend.protondb_service.requests.get")
    def test_get_steam_appid_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"total": 0}
        mock_get.return_value = mock_resp

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_steam_appid("Unknown Game")
        self.assertIsNone(result)

    @patch("src.backend.protondb_service.requests.get")
    def test_get_proton_summary(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tier": "gold",
            "score": 0.8,
            "confidence": "strong",
            "trendingTier": "gold",
        }
        mock_get.return_value = mock_resp

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_proton_summary("12345")
        self.assertIsNotNone(result)
        self.assertEqual(result["tier"], "gold")

    @patch("src.backend.protondb_service.requests.get")
    def test_get_proton_summary_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_proton_summary("99999")
        self.assertIsNone(result)

    @patch("src.backend.protondb_service.requests.get")
    def test_get_proton_summary_connection_error(self, mock_get):
        mock_get.side_effect = Exception("Connection failed")

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_proton_summary("12345")
        self.assertIsNone(result)

    @patch("src.backend.protondb_service.requests.get")
    def test_get_steam_details(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "12345": {
                "success": True,
                "data": {
                    "short_description": "An amazing game"
                }
            }
        }
        mock_get.return_value = mock_resp

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_steam_details("12345")
        self.assertIsNotNone(result)
        self.assertEqual(
            result["short_description"], "An amazing game"
        )

    @patch("src.backend.protondb_service.requests.get")
    def test_get_steam_details_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "12345": {"success": False}
        }
        mock_get.return_value = mock_resp

        from src.backend.protondb_service import ProtonDBService
        result = ProtonDBService.get_steam_details("12345")
        self.assertIsNone(result)

    def test_get_game_compatibility_combines_data(self):
        from src.backend.protondb_service import ProtonDBService
        with (
            patch.object(
                ProtonDBService, "get_steam_appid", return_value="12345"
            ),
            patch.object(
                ProtonDBService,
                "get_proton_summary",
                return_value={"tier": "gold", "score": 0.8},
            ),
            patch.object(
                ProtonDBService,
                "get_steam_details",
                return_value={
                    "short_description": "Great game", "name": "Game"
                },
            ),
        ):
            result = ProtonDBService.get_game_compatibility("Test Game")
            self.assertIsNotNone(result)
            self.assertEqual(result["tier"], "gold")
            self.assertEqual(result["steam_appid"], "12345")
            self.assertEqual(result["steam_description"], "Great game")

    def test_get_game_compatibility_returns_none_on_failure(self):
        from src.backend.protondb_service import ProtonDBService
        with patch.object(
            ProtonDBService, "get_steam_appid", return_value=None
        ):
            result = ProtonDBService.get_game_compatibility("Unknown Game")
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
