import time
import os
import sqlite3
import subprocess
import threading
import shutil
from PySide6.QtCore import QObject, Signal, Slot
from .database import get_db_connection

def find_umu_run():
    """Finds the umu-run binary dynamically."""
    # 1. Check common absolute paths
    common_paths = [
        os.path.expanduser("~/.local/bin/umu-run"),
        "/usr/local/bin/umu-run",
        "/usr/bin/umu-run"
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
            
    # 2. Check in PATH
    which_umu = shutil.which("umu-run")
    if which_umu:
        return which_umu
        
    return "umu-run" # Final fallback

class UMULauncher(QObject):
    finished = Signal(int)
    error = Signal(str)
    output_received = Signal(str)
    game_started = Signal(str, int) # app_id, timestamp

    def __init__(self, parent=None):
        super().__init__(parent)

    def launch_via_legendary(self, app_id, app_name, umu_path):
        # Update last played timestamp
        conn = get_db_connection()
        cursor = conn.cursor()
        now = int(time.time())
        cursor.execute("UPDATE games SET last_played_timestamp = ? WHERE app_id = ?", (now, app_id))
        conn.commit()
        conn.close()
        
        self.game_started.emit(app_id, now)

        def run_thread():
            env = os.environ.copy()
            
            # Check if we are in a Flatpak
            is_flatpak = os.path.exists("/.flatpak-info")
            
            if is_flatpak:
                print("DEBUG: Flatpak detected, using flatpak-spawn --host")
                # When using flatpak-spawn --host, we rely on host's PATH
                cmd = ["flatpak-spawn", "--host", "legendary", "launch", app_id, "--wrapper", "umu-run", "--no-wine"]
            else:
                # Normal native execution
                for var in ["DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS"]:
                    val = os.environ.get(var)
                    if val:
                        env[var] = val
                
                env["UMU_ID"] = app_id
                env["GAMEID"] = app_id
                env["STORE"] = "epic"
                env["UMU_LOG"] = "1"
                
                cmd = ["legendary", "launch", app_id, "--wrapper", umu_path, "--no-wine"]

            self.output_received.emit(f"Launching {app_name}...")
            try:
                process = subprocess.Popen(
                    cmd,
                    env=env if not is_flatpak else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                for line in process.stdout:
                    msg = line.strip()
                    if msg:
                        print(f"GAME: {msg}")
                        self.output_received.emit(msg)
                
                process.wait()
                print(f"Game finished with exit code: {process.returncode}")
                self.finished.emit(process.returncode)
                self.output_received.emit("Game finished.")
                
            except Exception as e:
                err_msg = str(e)
                print(f"Game launch error: {err_msg}")
                self.error.emit(err_msg)
                self.output_received.emit(f"Launch Error: {err_msg}")

        threading.Thread(target=run_thread, daemon=True).start()

    def launch(self, app_id, app_name, exe_path, prefix_path):
        self.launch_via_legendary(app_id, app_name, find_umu_run())
