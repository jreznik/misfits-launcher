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
    # Match Heroic's default path for interoperability
    path = os.path.expanduser("~/Games/Heroic")
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

    def install_game(self, app_id, base_path=None):
        """Installs a game via legendary with progress tracking."""
        def run_install():
            try:
                if base_path and base_path != "/":
                    install_dir = os.path.join(base_path, "Games", "Heroic")
                else:
                    install_dir = get_default_install_dir()
                os.makedirs(install_dir, exist_ok=True)
                cmd = ["legendary", "install", app_id, "--yes", "--base-path", install_dir]
                
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

                if success:
                    from .epic_service import sync_installed_to_heroic_config
                    sync_installed_to_heroic_config(app_id, add=True)
                self.install_finished.emit(app_id, success)
            except Exception as e:
                print(f"Installation error: {e}")
                self.install_finished.emit(app_id, False)

        threading.Thread(target=run_install, daemon=True).start()

    def uninstall_game(self, app_id):
        print(f"[UNINSTALL] GameService.uninstall_game({app_id})")
        def run_uninstall():
            try:
                from .umu_launcher import find_legendary

                # Read install path before uninstall (check all configs)
                from .epic_service import get_install_path_from_all_configs
                install_path = get_install_path_from_all_configs(app_id)
                print(f"[UNINSTALL]   install path from configs: {install_path!r}")

                legendary_bin = find_legendary()
                print(f"[UNINSTALL]   running: {legendary_bin} uninstall {app_id} -y")
                process = subprocess.run(
                    [legendary_bin, "uninstall", app_id, "-y"],
                    capture_output=True,
                    text=True
                )
                success = (process.returncode == 0)
                print(f"[UNINSTALL]   legendary exited with code {process.returncode}")
                if process.stdout: print(f"[UNINSTALL]   stdout: {process.stdout.strip()}")
                if process.stderr: print(f"[UNINSTALL]   stderr: {process.stderr.strip()}")
                if success:
                    print(f"[UNINSTALL]   uninstall successful")
                    if install_path and os.path.exists(install_path):
                        try:
                            shutil.rmtree(install_path, ignore_errors=True)
                            print(f"[UNINSTALL]   cleaned up leftover directory: {install_path}")
                        except Exception as e:
                            print(f"[UNINSTALL]   WARNING: could not fully remove {install_path}: {e}")
                    else:
                        print(f"[UNINSTALL]   no leftover directory to clean")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE games SET is_installed = 0 WHERE app_id = ?", (app_id,))
                    conn.commit()
                    conn.close()
                    print(f"[UNINSTALL]   updated DB: is_installed=0 for {app_id}")
                    from .epic_service import sync_installed_to_heroic_config
                    sync_installed_to_heroic_config(app_id, add=False)
                    print(f"[UNINSTALL]   synced removal to Heroic config")
                else:
                    print(f"[UNINSTALL]   uninstall FAILED")
                print(f"[UNINSTALL]   emitting uninstall_finished({app_id}, {success})")
                self.uninstall_finished.emit(app_id, success)
            except Exception as e:
                import traceback
                print(f"[UNINSTALL]   THREAD EXCEPTION: {e}")
                traceback.print_exc()
                self.uninstall_finished.emit(app_id, False)

        threading.Thread(target=run_uninstall, daemon=True).start()
