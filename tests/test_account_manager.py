import time
import unittest
from unittest.mock import patch, MagicMock


def make_manager():
    """Create an AccountManager with legendary status mocked to avoid init errors."""
    with (
        patch(
            "src.backend.account_manager.AccountManager._check_legendary_status",
            return_value=False,
        ),
        patch("src.backend.account_manager.LoginThread"),
    ):
        from src.backend.account_manager import AccountManager
        return AccountManager()


class TestAccountManager(unittest.TestCase):
    @patch("src.backend.account_manager.subprocess.run")
    def test_legendary_status_logged_in(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Epic account: user@example.com", returncode=0
        )
        from src.backend.account_manager import AccountManager
        manager = AccountManager()
        result = manager._check_legendary_status()
        self.assertTrue(result)

    @patch("src.backend.account_manager.subprocess.run")
    def test_legendary_status_not_logged_in(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Epic account: not logged in", returncode=0
        )
        from src.backend.account_manager import AccountManager
        manager = AccountManager()
        result = manager._check_legendary_status()
        self.assertFalse(result)

    @patch("src.backend.account_manager.subprocess.run")
    def test_legendary_status_no_account(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="No Epic account configured", returncode=0
        )
        from src.backend.account_manager import AccountManager
        manager = AccountManager()
        result = manager._check_legendary_status()
        self.assertFalse(result)

    @patch("src.backend.account_manager.subprocess.run",
           side_effect=FileNotFoundError("not found"))
    def test_legendary_status_file_not_found(self, mock_run):
        from src.backend.account_manager import AccountManager
        manager = AccountManager()
        result = manager._check_legendary_status()
        self.assertFalse(result)

    def test_refresh_status_sets_epic(self):
        manager = make_manager()
        with patch.object(manager, "_check_legendary_status", return_value=True):
            manager.refresh_status()
            self.assertTrue(manager._status["Epic"])

    def test_refresh_status_logged_out(self):
        manager = make_manager()
        with patch.object(manager, "_check_legendary_status", return_value=False):
            manager.refresh_status()
            self.assertFalse(manager._status["Epic"])

    @patch("src.backend.account_manager.EpicService.login")
    def test_login_calls_sync_on_success(self, mock_login):
        mock_login.return_value = True
        manager = make_manager()
        with patch("src.backend.account_manager.EpicService.sync_library") as mock_sync:
            manager.login("Epic", "test_token", is_code=True)
            mock_sync.assert_called_once()

    @patch("src.backend.account_manager.EpicService.login")
    def test_login_does_not_sync_on_failure(self, mock_login):
        mock_login.return_value = False
        manager = make_manager()
        with patch("src.backend.account_manager.EpicService.sync_library") as mock_sync:
            manager.login("Epic", "bad_token", is_code=True)
            mock_sync.assert_not_called()

    def test_logout_runs_auth_delete(self):
        with patch("src.backend.account_manager.subprocess.run") as mock_run:
            manager = make_manager()
            manager.logout("Epic")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("auth", args)
            self.assertIn("--delete", args)


if __name__ == "__main__":
    unittest.main()
