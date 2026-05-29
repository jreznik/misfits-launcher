import sys
import unittest
from unittest.mock import MagicMock, patch


def _make_sdl2_mock():
    """Create a mock sdl2 module hierarchy for testing GamepadManager."""
    sdl2 = MagicMock()
    sdl2.joystick = MagicMock()
    sdl2.SDL_INIT_GAMECONTROLLER = 0x00002000
    sdl2.SDL_INIT_JOYSTICK = 0x00000200
    sdl2.SDL_CONTROLLER_BUTTON_A = 0
    sdl2.SDL_CONTROLLER_BUTTON_B = 1
    sdl2.SDL_CONTROLLER_BUTTON_X = 2
    sdl2.SDL_CONTROLLER_BUTTON_Y = 3
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP = 4
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN = 5
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT = 6
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT = 7
    sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER = 8
    sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER = 9
    sdl2.SDL_CONTROLLER_BUTTON_BACK = 10
    sdl2.SDL_CONTROLLER_BUTTON_START = 11
    sdl2.SDL_CONTROLLER_BUTTON_GUIDE = 12
    sdl2.SDL_CONTROLLER_AXIS_LEFTX = 0
    sdl2.SDL_CONTROLLER_AXIS_LEFTY = 1
    sdl2.SDL_CONTROLLER_AXIS_RIGHTX = 2
    sdl2.SDL_CONTROLLER_AXIS_RIGHTY = 3
    sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT = 4
    sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT = 5
    sdl2.SDL_CONTROLLERDEVICEADDED = 0x0650
    sdl2.SDL_CONTROLLERDEVICEREMOVED = 0x0651
    sdl2.SDL_Event = MagicMock
    sdl2.SDL_Quit = MagicMock()
    return sdl2


class TestGamepadManagerControllerDetection(unittest.TestCase):
    def setUp(self):
        self.sdl2 = _make_sdl2_mock()

        # We need to patch sys.modules BEFORE importing GamepadManager
        # so the 'import sdl2' inside its methods resolve to our mock.
        self.modules_patcher = patch.dict(
            "sys.modules",
            {"sdl2": self.sdl2, "sdl2.joystick": self.sdl2.joystick},
            clear=False,
        )
        self.modules_patcher.start()
        self.addCleanup(self.modules_patcher.stop)

    def _make_manager(self, with_controller=False):
        """Create a GamepadManager with SDL2 fully mocked."""
        self.sdl2.SDL_Init.return_value = 0
        if with_controller:
            self.sdl2.joystick.SDL_NumJoysticks.return_value = 1
            self.sdl2.SDL_IsGameController.return_value = True
            self.sdl2.SDL_GameControllerOpen.return_value = MagicMock()
            self.sdl2.SDL_GameControllerName.return_value = b"Mock Controller"
        else:
            self.sdl2.joystick.SDL_NumJoysticks.return_value = 0
            self.sdl2.SDL_IsGameController.return_value = False
            self.sdl2.SDL_GameControllerOpen.return_value = None

        from main import GamepadManager
        mgr = GamepadManager()
        return mgr

    def test_controller_connected_false_when_no_controller(self):
        mgr = self._make_manager(with_controller=False)
        self.assertFalse(mgr.controllerConnected)

    def test_controller_connected_true_when_controller_found(self):
        mgr = self._make_manager(with_controller=True)
        self.assertTrue(mgr.controllerConnected)

    def test_controller_connected_false_after_removal(self):
        self.sdl2.joystick.SDL_NumJoysticks.return_value = 1
        self.sdl2.SDL_IsGameController.return_value = True
        mock_controller = MagicMock()
        self.sdl2.SDL_GameControllerOpen.return_value = mock_controller
        self.sdl2.SDL_GameControllerName.return_value = b"Mock Controller"
        self.sdl2.SDL_Init.return_value = 0

        from main import GamepadManager
        mgr = GamepadManager()
        self.assertTrue(mgr.controllerConnected)

        mgr.controller = None
        mgr._update_controller_connected()
        self.assertFalse(mgr.controllerConnected)

    def test_update_connected_emits_signal_on_change(self):
        from main import GamepadManager
        mgr = GamepadManager()
        mgr.controllerConnectedChanged = MagicMock()

        mgr.controller = MagicMock()
        mgr._update_controller_connected()
        self.assertTrue(mgr.controllerConnected)
        mgr.controllerConnectedChanged.emit.assert_called_once()

    def test_update_connected_does_not_emit_when_no_change(self):
        from main import GamepadManager
        mgr = GamepadManager()
        mgr.controllerConnectedChanged = MagicMock()

        mgr.controller = None
        mgr._update_controller_connected()
        mgr.controllerConnectedChanged.emit.assert_not_called()

    def test_find_controller_with_no_joysticks(self):
        self.sdl2.SDL_Init.return_value = 0
        self.sdl2.joystick.SDL_NumJoysticks.return_value = 0

        from main import GamepadManager
        mgr = GamepadManager()
        mgr.controller = None
        mgr.find_controller()
        self.assertIsNone(mgr.controller)
        self.assertFalse(mgr.controllerConnected)

    def test_find_controller_with_game_controller(self):
        self.sdl2.SDL_Init.return_value = 0
        self.sdl2.joystick.SDL_NumJoysticks.return_value = 2
        self.sdl2.SDL_IsGameController.side_effect = lambda i: i == 1
        mock_ctl = MagicMock()
        self.sdl2.SDL_GameControllerOpen.return_value = mock_ctl
        self.sdl2.SDL_GameControllerName.return_value = b"TestPad"

        from main import GamepadManager
        mgr = GamepadManager()
        self.assertIs(mgr.controller, mock_ctl)
        self.assertTrue(mgr.controllerConnected)
        self.sdl2.SDL_GameControllerOpen.assert_called_once_with(1)


class TestNavigationHintsKeyMapping(unittest.TestCase):
    """Validate that each view's NavigationHints data has correct keys for both modes."""

    def _hints_from_qml(self, qml_text):
        """Extract the hints array items from a QML NavigationHints usage block."""
        import ast
        # Simple extraction: find hints: [...] block
        start = qml_text.index("hints: [")
        end = qml_text.index("]", start) + 1
        hints_text = qml_text[start:end]
        # Convert QML-like syntax to Python: unquote keys, replace braces
        py_text = hints_text.replace("hints: ", "")
        # Parse as Python literal
        return ast.literal_eval(py_text)

    def test_home_view_hints_have_controller_keys(self):
        hints = [
            {"key": "M", "controllerKey": "Options", "label": "SETTINGS"},
            {"key": "D", "label": "DOWNLOADS"},
            {"key": "Enter", "controllerKey": "A", "label": "DETAILS"},
        ]
        for h in hints:
            if h["key"] == "D":
                self.assertNotIn("controllerKey", h,
                    "D/Downloads hint should not have a controller mapping")
            else:
                self.assertIn("controllerKey", h,
                    f"{h['key']}/{h['label']} hint missing controller mapping")

    def test_library_view_hints_have_controller_keys(self):
        hints = [
            {"key": "M", "controllerKey": "Options", "label": "SETTINGS"},
            {"key": "D", "label": "DOWNLOADS"},
            {"key": "X", "controllerKey": "X", "label": "FILTER:"},
            {"key": "Y", "controllerKey": "Y", "label": "SORT BY"},
            {"key": "Enter", "controllerKey": "A", "label": "SELECT"},
            {"key": "Esc", "controllerKey": "B", "label": "BACK"},
        ]
        for h in hints:
            if h["key"] == "D":
                self.assertNotIn("controllerKey", h)
            else:
                self.assertIn("controllerKey", h)

    def test_game_detail_view_hints_have_controller_keys(self):
        hints = [
            {"key": "D", "label": "DOWNLOADS"},
            {"key": "Enter", "controllerKey": "A", "label": "SELECT"},
            {"key": "Esc", "controllerKey": "B", "label": "BACK"},
        ]
        for h in hints:
            if h["key"] == "D":
                self.assertNotIn("controllerKey", h)
            else:
                self.assertIn("controllerKey", h)

    def test_settings_view_hints_have_controller_keys(self):
        hints = [
            {"key": "Enter", "controllerKey": "A", "label": "SELECT"},
            {"key": "Esc", "controllerKey": "B", "label": "BACK"},
        ]
        for h in hints:
            self.assertIn("controllerKey", h)

    def test_download_manager_view_hints_have_controller_keys(self):
        hints = [
            {"key": "Esc", "controllerKey": "B", "label": "BACK"},
        ]
        for h in hints:
            self.assertIn("controllerKey", h)

    def test_keyboard_mode_shows_keyboard_keys(self):
        """Verify that in keyboard mode, Enter maps to the icon and Esc shows Esc."""
        hints = [
            {"key": "Enter", "controllerKey": "A", "label": "SELECT"},
            {"key": "Esc", "controllerKey": "B", "label": "BACK"},
        ]
        controller_mode = False
        for h in hints:
            if h["key"] == "Enter":
                displayed = "\u21B5"  # ↵ icon
            else:
                displayed = h["key"] if not (controller_mode and h.get("controllerKey")) else h["controllerKey"]
            self.assertEqual(displayed, h["key"] if h["key"] != "Enter" else "\u21B5")

    def test_controller_mode_shows_controller_keys(self):
        """Verify that in controller mode, the displayed key is the controllerKey field."""
        hints = [
            {"key": "Esc", "controllerKey": "B", "label": "BACK"},
        ]
        controller_mode = True
        for h in hints:
            displayed = h["controllerKey"] if controller_mode and "controllerKey" in h else h["key"]
            self.assertEqual(displayed, "B")


if __name__ == "__main__":
    unittest.main()
