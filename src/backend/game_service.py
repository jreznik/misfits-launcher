import subprocess
import json
import sqlite3
import os
import re
import threading
import shutil
from PySide6.QtCore import QObject, Signal, Slot
from .database import get_db_connection
from .protondb_service import ProtonDBService

def get_default_install_dir():
    # Prefer ~/Games/MisfitsLauncher
    path = os.path.expanduser("~/Games/MisfitsLauncher")
    os.makedirs(path, exist_ok=True)
    return path

class GameService(QObject):
    install_progress = Signal(str, float, str) # app_id, percentage, status_msg
    install_finished = Signal(str, bool) # app_id, success
    uninstall_finished = Signal(str, bool) # app_id, success

    game_info_fetched = Signal(str, dict) # app_id, data
    proton_info_fetched = Signal(str, dict) # app_id, data

    def fetch_game_info(self, app_id):
        """Fetches detailed game info asynchronously in stages."""
        def run_fetch():
            try:
                process = subprocess.run(
                    ["legendary", "info", "--json", app_id],
                    capture_output=True,
                    text=True
                )
                if process.returncode == 0:
                    data = json.loads(process.stdout)
                    self.game_info_fetched.emit(app_id, data)
                    
                    title = data.get('game', {}).get('title')
                    if title:
                        compat = ProtonDBService.get_game_compatibility(title)
                        if compat:
                            self.proton_info_fetched.emit(app_id, compat)
                else:
                    self.game_info_fetched.emit(app_id, {})
            except Exception as e:
                print(f"Error fetching game info: {e}")
                self.game_info_fetched.emit(app_id, {})

        threading.Thread(target=run_fetch, daemon=True).start()

    @staticmethod
    def get_game_info(app_id):
        try:
            process = subprocess.run(
                ["legendary", "info", "--json", app_id],
                capture_output=True,
                text=True
            )
            if process.returncode == 0:
                return json.loads(process.stdout)
        except Exception as e:
            print(f"Error fetching game info: {e}")
        return None

    def install_game(self, app_id):
        """Installs a game via legendary with progress tracking."""
        def run_install():
            try:
                # Use dynamic base path
                base_path = get_default_install_dir()
                cmd = ["legendary", "install", app_id, "--yes", "--base-path", base_path]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                for line in process.stdout:
                    line = line.strip()
                    if not line: continue
                    match = re.search(r"Progress: (\d+\.\d+)%", line)
                    if match:
                        percentage = float(match.group(1))
                        self.install_progress.emit(app_id, percentage, "Downloading...")
                    elif "Preparing download" in line:
                        self.install_progress.emit(app_id, 0, "Preparing...")
                    elif "All done" in line:
                        self.install_progress.emit(app_id, 100, "Finishing...")

                process.wait()
                success = (process.returncode == 0)
                if success:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE games SET is_installed = 1 WHERE app_id = ?", (app_id,))
                    conn.commit()
                    conn.close()

                self.install_finished.emit(app_id, success)
            except Exception as e:
                print(f"Installation error: {e}")
                self.install_finished.emit(app_id, False)

        threading.Thread(target=run_install, daemon=True).start()

    def uninstall_game(self, app_id):
        def run_uninstall():
            try:
                process = subprocess.run(
                    ["legendary", "uninstall", app_id],
                    capture_output=True,
                    text=True
                )
                success = (process.returncode == 0)
                if success:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE games SET is_installed = 0 WHERE app_id = ?", (app_id,))
                    conn.commit()
                    conn.close()
                self.uninstall_finished.emit(app_id, success)
            except Exception as e:
                print(f"Uninstallation error: {e}")
                self.uninstall_finished.emit(app_id, False)

        threading.Thread(target=run_uninstall, daemon=True).start()
