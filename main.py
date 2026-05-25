import sys
import os
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtCore import QObject, QTimer, QEvent, Qt, QCoreApplication, QDateTime
from PySide6.QtQml import QQmlApplicationEngine
from src.backend.database import init_db
from src.backend.game_manager import GameManager
from src.backend.account_manager import AccountManager
from src.backend.umu_runtime_manager import UMURuntimeManager
from src.backend.download_manager import DownloadManager

class GamepadManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_gamepad)
        
        # Deadzones and state trackers
        self.deadzone = 12000  # SDL axis ranges from -32768 to 32767
        self.last_axis_state = {
            "LeftX": 0,   # -1: Left, 0: Neutral, 1: Right
            "LeftY": 0,   # -1: Up,    0: Neutral, 1: Down
            "RightX": 0,  # -1: Left, 0: Neutral, 1: Right
            "RightY": 0,  # -1: Up,    0: Neutral, 1: Down
        }
        self.last_trigger_state = {
            "TriggerLeft": 0,  # 0: Unpressed, 1: Pressed
            "TriggerRight": 0, # 0: Unpressed, 1: Pressed
        }
        self.last_button_state = {} # Tracks raw button press states
        
        # Continuous hold repeats for analog stick (per-axis)
        self.repeat_interval = 200  # ms
        self.last_key_sent = {}
        self.last_key_time = {}
        
        # Try to initialize SDL2 Game Controller subsystem
        self.initialized = False
        try:
            import sdl2
            import sdl2.joystick
            
            if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_JOYSTICK) >= 0:
                self.initialized = True
                print("DEBUG: SDL2 Game Controller initialized successfully.")
                self.timer.start(15)  # Poll every 15ms
                self.find_controller()
            else:
                print(f"DEBUG: Failed to initialize SDL2: {sdl2.SDL_GetError()}")
        except Exception as e:
            print(f"DEBUG: SDL2 import or init failed: {e}")

    def find_controller(self):
        import sdl2
        import sdl2.joystick
        
        if self.controller:
            sdl2.SDL_GameControllerClose(self.controller)
            self.controller = None
            
        num_joysticks = sdl2.joystick.SDL_NumJoysticks()
        for i in range(num_joysticks):
            if sdl2.SDL_IsGameController(i):
                self.controller = sdl2.SDL_GameControllerOpen(i)
                if self.controller:
                    name = sdl2.SDL_GameControllerName(self.controller).decode('utf-8', 'ignore')
                    print(f"DEBUG: Opened Game Controller: {name}")
                    break
        if not self.controller:
            print("DEBUG: No gamepad/game controller detected yet.")

    def send_key(self, key_code):
        app = QCoreApplication.instance()
        if not app:
            return

        window = app.focusWindow()
        if not window:
            return

        press = QKeyEvent(QEvent.Type.KeyPress, key_code, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.sendEvent(window, press)

        release = QKeyEvent(QEvent.Type.KeyRelease, key_code, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.sendEvent(window, release)

        print(f"DEBUG: Virtualized Key sent: {key_code} to window {window}")

    def poll_gamepad(self):
        if not self.initialized:
            return
            
        import sdl2
        import sdl2.joystick
        
        # 1. Pump events to refresh game controller button/axis states
        sdl2.SDL_GameControllerUpdate()
        
        # 2. Process hotplug events cleanly via SDL event loop
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event) != 0:
            if event.type == sdl2.SDL_CONTROLLERDEVICEADDED:
                print("DEBUG: Controller added event received.")
                self.find_controller()
            elif event.type == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                print("DEBUG: Controller removed event received.")
                if self.controller:
                    sdl2.SDL_GameControllerClose(self.controller)
                    self.controller = None
                    
        if not self.controller:
            return
            
        current_time = QDateTime.currentMSecsSinceEpoch()

        # 1. Poll Buttons
        buttons_to_track = [
            sdl2.SDL_CONTROLLER_BUTTON_A,
            sdl2.SDL_CONTROLLER_BUTTON_B,
            sdl2.SDL_CONTROLLER_BUTTON_X,
            sdl2.SDL_CONTROLLER_BUTTON_Y,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT,
            sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER,
            sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER,
            sdl2.SDL_CONTROLLER_BUTTON_BACK,
            sdl2.SDL_CONTROLLER_BUTTON_START,
            sdl2.SDL_CONTROLLER_BUTTON_GUIDE,
        ]
        
        for btn in buttons_to_track:
            is_pressed = sdl2.SDL_GameControllerGetButton(self.controller, btn)
            last_state = self.last_button_state.get(btn, 0)
            if is_pressed != last_state:
                self.last_button_state[btn] = is_pressed
                self.handle_button(btn, is_pressed == 1)

        # 2. Poll Left Stick axes
        left_x = sdl2.SDL_GameControllerGetAxis(self.controller, sdl2.SDL_CONTROLLER_AXIS_LEFTX)
        left_y = sdl2.SDL_GameControllerGetAxis(self.controller, sdl2.SDL_CONTROLLER_AXIS_LEFTY)
        
        # Left Stick X-axis
        new_lx_state = 0
        if left_x < -self.deadzone:
            new_lx_state = -1
        elif left_x > self.deadzone:
            new_lx_state = 1
            
        if new_lx_state != self.last_axis_state["LeftX"]:
            self.last_axis_state["LeftX"] = new_lx_state
            if new_lx_state == -1:
                self.send_key(Qt.Key_Left)
                self.last_key_sent["LeftX"] = Qt.Key_Left
                self.last_key_time["LeftX"] = current_time
            elif new_lx_state == 1:
                self.send_key(Qt.Key_Right)
                self.last_key_sent["LeftX"] = Qt.Key_Right
                self.last_key_time["LeftX"] = current_time
            else:
                self.last_key_sent.pop("LeftX", None)
                self.last_key_time.pop("LeftX", None)
        elif new_lx_state != 0:
            expected = Qt.Key_Left if new_lx_state == -1 else Qt.Key_Right
            if self.last_key_sent.get("LeftX") == expected and (current_time - self.last_key_time.get("LeftX", 0) > self.repeat_interval):
                self.send_key(expected)
                self.last_key_time["LeftX"] = current_time

        # Left Stick Y-axis
        new_ly_state = 0
        if left_y < -self.deadzone:
            new_ly_state = -1
        elif left_y > self.deadzone:
            new_ly_state = 1
            
        if new_ly_state != self.last_axis_state["LeftY"]:
            self.last_axis_state["LeftY"] = new_ly_state
            if new_ly_state == -1:
                self.send_key(Qt.Key_Up)
                self.last_key_sent["LeftY"] = Qt.Key_Up
                self.last_key_time["LeftY"] = current_time
            elif new_ly_state == 1:
                self.send_key(Qt.Key_Down)
                self.last_key_sent["LeftY"] = Qt.Key_Down
                self.last_key_time["LeftY"] = current_time
            else:
                self.last_key_sent.pop("LeftY", None)
                self.last_key_time.pop("LeftY", None)
        elif new_ly_state != 0:
            expected = Qt.Key_Up if new_ly_state == -1 else Qt.Key_Down
            if self.last_key_sent.get("LeftY") == expected and (current_time - self.last_key_time.get("LeftY", 0) > self.repeat_interval):
                self.send_key(expected)
                self.last_key_time["LeftY"] = current_time

        # 3. Poll Right Stick axes
        right_x = sdl2.SDL_GameControllerGetAxis(self.controller, sdl2.SDL_CONTROLLER_AXIS_RIGHTX)
        right_y = sdl2.SDL_GameControllerGetAxis(self.controller, sdl2.SDL_CONTROLLER_AXIS_RIGHTY)

        # Right Stick X-axis
        new_rx_state = 0
        if right_x < -self.deadzone:
            new_rx_state = -1
        elif right_x > self.deadzone:
            new_rx_state = 1
            
        if new_rx_state != self.last_axis_state["RightX"]:
            self.last_axis_state["RightX"] = new_rx_state
            if new_rx_state == -1:
                self.send_key(Qt.Key_Left)
                self.last_key_sent["RightX"] = Qt.Key_Left
                self.last_key_time["RightX"] = current_time
            elif new_rx_state == 1:
                self.send_key(Qt.Key_Right)
                self.last_key_sent["RightX"] = Qt.Key_Right
                self.last_key_time["RightX"] = current_time
            else:
                self.last_key_sent.pop("RightX", None)
                self.last_key_time.pop("RightX", None)
        elif new_rx_state != 0:
            expected = Qt.Key_Left if new_rx_state == -1 else Qt.Key_Right
            if self.last_key_sent.get("RightX") == expected and (current_time - self.last_key_time.get("RightX", 0) > self.repeat_interval):
                self.send_key(expected)
                self.last_key_time["RightX"] = current_time

        # Right Stick Y-axis
        new_ry_state = 0
        if right_y < -self.deadzone:
            new_ry_state = -1
        elif right_y > self.deadzone:
            new_ry_state = 1
            
        if new_ry_state != self.last_axis_state["RightY"]:
            self.last_axis_state["RightY"] = new_ry_state
            if new_ry_state == -1:
                self.send_key(Qt.Key_Up)
                self.last_key_sent["RightY"] = Qt.Key_Up
                self.last_key_time["RightY"] = current_time
            elif new_ry_state == 1:
                self.send_key(Qt.Key_Down)
                self.last_key_sent["RightY"] = Qt.Key_Down
                self.last_key_time["RightY"] = current_time
            else:
                self.last_key_sent.pop("RightY", None)
                self.last_key_time.pop("RightY", None)
        elif new_ry_state != 0:
            expected = Qt.Key_Up if new_ry_state == -1 else Qt.Key_Down
            if self.last_key_sent.get("RightY") == expected and (current_time - self.last_key_time.get("RightY", 0) > self.repeat_interval):
                self.send_key(expected)
                self.last_key_time["RightY"] = current_time

        # 4. Poll Triggers (L2/R2)
        left_trigger = sdl2.SDL_GameControllerGetAxis(self.controller, sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT)
        right_trigger = sdl2.SDL_GameControllerGetAxis(self.controller, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT)

        # Trigger Left (L2) -> Qt.Key_BracketLeft
        new_lt_state = 1 if left_trigger > 12000 else 0
        if new_lt_state != self.last_trigger_state["TriggerLeft"]:
            self.last_trigger_state["TriggerLeft"] = new_lt_state
            if new_lt_state == 1:
                self.send_key(Qt.Key_BracketLeft)
                
        # Trigger Right (R2) -> Qt.Key_BracketRight
        new_rt_state = 1 if right_trigger > 12000 else 0
        if new_rt_state != self.last_trigger_state["TriggerRight"]:
            self.last_trigger_state["TriggerRight"] = new_rt_state
            if new_rt_state == 1:
                self.send_key(Qt.Key_BracketRight)

    def handle_button(self, btn, is_down):
        if not is_down:
            return
            
        import sdl2
        # Map controller buttons to standard navigation keys
        if btn == sdl2.SDL_CONTROLLER_BUTTON_A:
            self.send_key(Qt.Key_Return)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_B:
            self.send_key(Qt.Key_Escape)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
            self.send_key(Qt.Key_Up)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
            self.send_key(Qt.Key_Down)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
            self.send_key(Qt.Key_Left)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
            self.send_key(Qt.Key_Right)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER:
            self.send_key(Qt.Key_F1)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
            self.send_key(Qt.Key_F2)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_BACK:
            self.send_key(Qt.Key_Menu)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_START:
            self.send_key(Qt.Key_M)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_X:
            self.send_key(Qt.Key_X)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_Y:
            self.send_key(Qt.Key_Y)
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_GUIDE:
            self.send_key(Qt.Key_M)

def main():
    # Initialize DB
    init_db()

    app = QGuiApplication(sys.argv)
    
    # Initialize Gamepad controller bridge
    gamepad_manager = GamepadManager(app)

    engine = QQmlApplicationEngine()

    game_manager = GameManager()
    account_manager = AccountManager()
    umu_manager = UMURuntimeManager()
    download_manager = DownloadManager()
    
    # Connect account changes to library refreshes
    account_manager.accounts_changed.connect(game_manager.refresh_models)
    
    engine.rootContext().setContextProperty("gameManager", game_manager)
    engine.rootContext().setContextProperty("accountManager", account_manager)
    engine.rootContext().setContextProperty("umuManager", umu_manager)
    engine.rootContext().setContextProperty("downloadManager", download_manager)

    # Load QML
    qml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "src/ui/qml/main.qml"))
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
