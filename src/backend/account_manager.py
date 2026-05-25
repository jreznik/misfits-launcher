import subprocess
import json
from PySide6.QtCore import QObject, Signal, Slot, Property, QThread
from .epic_service import EpicService
from .login_handler import LoginThread

class AccountManager(QObject):
    accounts_changed = Signal()
    login_finished = Signal(str, bool) # store, success
    login_status_changed = Signal(str) # Status message for UI

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = {
            "Epic": False,
            "GOG": False,
            "Amazon": False
        }
        self._login_thread = None
        self.refresh_status()
        
        # Auto-sync on startup if logged in
        if self._status["Epic"]:
            def run_sync():
                from .epic_service import EpicService
                if EpicService.sync_library():
                    self.accounts_changed.emit()
            
            import threading
            threading.Thread(target=run_sync, daemon=True).start()

    @Property(bool, notify=accounts_changed)
    def epicLoggedIn(self): return self._status["Epic"]

    @Property(bool, notify=accounts_changed)
    def gogLoggedIn(self): return self._status["GOG"]

    @Property(bool, notify=accounts_changed)
    def amazonLoggedIn(self): return self._status["Amazon"]

    @Slot()
    def trigger_epic_login(self):
        """Starts the automated browser login flow for Epic."""
        self.login_status_changed.emit("Opening browser for Epic Games login...")
        self._login_thread = LoginThread()
        self._login_thread.sid_captured.connect(self._on_sid_captured)
        self._login_thread.error_occurred.connect(self._on_login_error)
        self._login_thread.start()

    def _on_sid_captured(self, sid):
        print(f"SID captured: {sid[:5]}...")
        self.login("Epic", sid)

    def _on_login_error(self, err):
        print(f"Login error: {err}")
        self.login_status_changed.emit(f"Login error: {err}")
        self.login_finished.emit("Epic", False)

    @Slot()
    def refresh_status(self):
        try:
            # Epic (Legendary)
            self._status["Epic"] = self._check_legendary_status()
            # Others still placeholders
            self._status["GOG"] = False
            self._status["Amazon"] = False
        except Exception:
            pass
        self.accounts_changed.emit()

    def _check_legendary_status(self):
        try:
            process = subprocess.run(["legendary", "status"], capture_output=True, text=True)
            # Logged in usually shows "Epic account: <username>"
            return "Epic account:" in process.stdout and "not logged in" not in process.stdout.lower()
        except FileNotFoundError:
            return False

    @Slot()
    def trigger_epic_browser(self):
        """Opens the system browser to the Epic login page."""
        import webbrowser
        webbrowser.open("https://legendary.gl/epiclogin")
        self.login_status_changed.emit("Please log in and copy the 'authorizationCode' from the browser.")

    @Slot(str, str, bool)
    def login(self, store, token, is_code=True):
        success = False
        self.login_status_changed.emit(f"Authenticating with {store}...")
        if store == "Epic":
            success = EpicService.login(token, is_code)
            if success:
                self.login_status_changed.emit("Login successful! Syncing library...")
                EpicService.sync_library()
                self.refresh_status()
                self.accounts_changed.emit()
        
        if success:
            self._status[store] = True
            self.accounts_changed.emit()
        else:
            self.login_status_changed.emit("Login failed. Please check the code.")
        
        self.login_finished.emit(store, success)

    @Slot(str)
    def logout(self, store):
        if store == "Epic":
            subprocess.run(["legendary", "auth", "--delete"], capture_output=True)
        
        self._status[store] = False
        self.accounts_changed.emit()
