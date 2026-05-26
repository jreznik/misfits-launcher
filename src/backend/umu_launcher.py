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
    common_paths = [
        os.path.expanduser("~/.local/bin/umu-run"),
        "/usr/local/bin/umu-run",
        "/usr/bin/umu-run",
        "/app/bin/umu-run" # Internal Flatpak path
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    which_umu = shutil.which("umu-run")
    if which_umu:
        return which_umu
    return "umu-run"

class UMULauncher(QObject):
    finished = Signal(int)
    error = Signal(str)
    output_received = Signal(str)
    game_started = Signal(str, int)

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
            is_flatpak = os.path.exists("/.flatpak-info")

            try:
                if is_flatpak:
                    # Run legendary + umu-run on the host via flatpak-spawn
                    cmd = [
                        "flatpak-spawn", "--host",
                        "legendary", "launch", app_id,
                        "--wrapper", "umu-run", "--no-wine"
                    ]
                else:
                    cmd = [
                        "legendary", "launch", app_id,
                        "--wrapper", umu_path, "--no-wine"
                    ]

                self.output_received.emit(f"Starting {app_name}...")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )

                for line in process.stdout:
                    msg = line.strip()
                    if msg:
                        print(f"GAME: {msg}")
                        self.output_received.emit(msg)

                process.wait()
                self.finished.emit(process.returncode)
                self.output_received.emit("Game finished.")

            except Exception as e:
                err_msg = str(e)
                print(f"Launch Error: {err_msg}")
                self.error.emit(err_msg)
                self.output_received.emit(f"Launch Error: {err_msg}")

        threading.Thread(target=run_thread, daemon=True).start()

    def launch(self, app_id, app_name, exe_path, prefix_path):
        self.launch_via_legendary(app_id, app_name, find_umu_run())
