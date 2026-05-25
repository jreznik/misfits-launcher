import time
import os
import sqlite3
import subprocess
import threading
import shutil
import json
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
            
            # Step 1: Use INTERNAL legendary to get launch info
            # This works because we've synced the config path to host
            self.output_received.emit(f"Getting launch parameters for {app_name}...")
            try:
                # We need a temporary exchange token and launch command
                # Legendary info --json is good, but launch --json gives the actual command + env
                res = subprocess.run(
                    ["legendary", "launch", app_id, "--json"],
                    capture_output=True,
                    text=True,
                    env=os.environ.copy()
                )
                
                if res.returncode != 0:
                    raise Exception(f"Legendary failed to generate launch JSON: {res.stderr}")
                
                launch_data = json.loads(res.stdout)
                # launch_data typically has: "cmd", "env", "cwd"
                
                game_cmd = launch_data.get("cmd", [])
                game_env = launch_data.get("env", {})
                game_cwd = launch_data.get("cwd", "")

                if not game_cmd:
                    raise Exception("No command found in launch JSON")

                # Step 2: Construct the final command
                # We want to run: umu-run <exe>
                # The first item in game_cmd is usually the wine binary, we replace it with umu-run
                # or just use the whole command if it's already wrapped.
                
                final_args = []
                # If the first arg is wine/proton, we skip it and let umu-run handle it
                # For Legendary, the cmd usually starts with the wine path.
                # The actual game exe is often the 2nd or later arg.
                
                # Best approach: take the game exe and args from legendary, wrap in umu-run
                # Legendary 'cmd' usually looks like: ["/path/to/wine", "game.exe", "arg1"...]
                actual_game_exe = game_cmd[1] if len(game_cmd) > 1 else game_cmd[0]
                game_args = game_cmd[2:] if len(game_cmd) > 2 else []

                if is_flatpak:
                    print("DEBUG: Flatpak detected, launching via host umu-run")
                    # Command: flatpak-spawn --host umu-run /path/to/game.exe
                    # We pass the environment via env vars in the command if needed, 
                    # but flatpak-spawn doesn't have an easy way to pass complex env.
                    # We can use 'env' command on host.
                    
                    remote_cmd = ["flatpak-spawn", "--host", "env"]
                    # Add legendary's required env vars
                    for k, v in game_env.items():
                        remote_cmd.append(f"{k}={v}")
                    
                    # Add UMU specific vars
                    remote_cmd.append(f"UMU_ID={app_id}")
                    remote_cmd.append(f"GAMEID={app_id}")
                    remote_cmd.append(f"STORE=epic")
                    
                    # Add umu-run and game
                    remote_cmd.append("umu-run")
                    remote_cmd.append(actual_game_exe)
                    remote_cmd.extend(game_args)
                    
                    cmd = remote_cmd
                else:
                    # Native launch
                    cmd = ["legendary", "launch", app_id, "--wrapper", umu_path, "--no-wine"]

                self.output_received.emit(f"Starting {app_name}...")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=game_cwd if not is_flatpak else None
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
