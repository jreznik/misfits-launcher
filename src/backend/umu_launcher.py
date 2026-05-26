import time
import os
import sys
import sqlite3
import subprocess
import threading
import shutil
from PySide6.QtCore import QObject, Signal, Slot
from .database import get_db_connection

def log(msg):
    print(f"[LAUNCHER] {msg}", flush=True)

def find_umu_run():
    log("Searching for umu-run...")
    common_paths = [
        os.path.expanduser("~/.local/bin/umu-run"),
        "/usr/local/bin/umu-run",
        "/usr/bin/umu-run",
        "/app/bin/umu-run",
    ]
    for p in common_paths:
        if os.path.exists(p):
            log(f"Found umu-run at {p}")
            return p
    which_umu = shutil.which("umu-run")
    if which_umu:
        log(f"Found umu-run via PATH at {which_umu}")
        return which_umu
    log("umu-run not found, using bare 'umu-run' as fallback")
    return "umu-run"

def find_legendary():
    log("Searching for legendary...")
    common = [
        shutil.which("legendary"),
        "/app/bin/legendary",
        os.path.expanduser("~/.local/bin/legendary"),
        "/usr/local/bin/legendary",
        "/usr/bin/legendary",
    ]
    for p in common:
        if p and os.path.exists(p):
            log(f"Found legendary at {p}")
            return p
    log("legendary not found, using bare 'legendary' as fallback")
    return "legendary"

class UMULauncher(QObject):
    finished = Signal(int)
    error = Signal(str)
    output_received = Signal(str)
    game_started = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def launch_via_legendary(self, app_id, app_name, umu_path):
        log(f"=== GAME LAUNCH REQUESTED ===")
        log(f"App ID: {app_id}, Name: {app_name}")
        log(f"umu path: {umu_path}")
        log(f"Is Flatpak: {os.path.exists('/.flatpak-info')}")
        log(f"LEGENDARY_CONFIG_PATH: {os.environ.get('LEGENDARY_CONFIG_PATH', 'NOT SET')}")
        log(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")
        log(f"PATH: {os.environ.get('PATH', 'NOT SET')}")
        log(f"CWD: {os.getcwd()}")

        legendary_bin = find_legendary()
        log(f"Legendary binary: {legendary_bin}")

        # Test legendary works
        try:
            ver = subprocess.run([legendary_bin, "--version"], capture_output=True, text=True, timeout=10)
            log(f"Legendary version: {ver.stdout.strip() or ver.stderr.strip()}")
        except Exception as e:
            log(f"Legendary version check failed: {e}")

        # Update last played
        conn = get_db_connection()
        cursor = conn.cursor()
        now = int(time.time())
        cursor.execute("UPDATE games SET last_played_timestamp = ? WHERE app_id = ?", (now, app_id))
        conn.commit()
        conn.close()

        self.game_started.emit(app_id, now)

        def run_thread():
            try:
                cmd = [
                    legendary_bin, "launch", app_id,
                    "--wrapper", umu_path, "--no-wine"
                ]
                log(f"Launch command: {' '.join(cmd)}")
                log(f"Full env: LEGENDARY_CONFIG_PATH={os.environ.get('LEGENDARY_CONFIG_PATH', 'UNSET')}")

                self.output_received.emit(f"Starting {app_name}...")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )

                log("Process started, reading output...")

                # Read stdout and stderr concurrently
                import queue
                q = queue.Queue()

                def reader(stream, label):
                    for line in iter(stream.readline, ""):
                        q.put((label, line.strip()))
                    stream.close()

                threading.Thread(target=reader, args=(process.stdout, "OUT"), daemon=True).start()
                threading.Thread(target=reader, args=(process.stderr, "ERR"), daemon=True).start()

                active = 2
                while active > 0:
                    try:
                        label, msg = q.get(timeout=0.5)
                        if msg is None:
                            active -= 1
                            continue
                        log(f"[{label}] {msg}")
                        self.output_received.emit(msg)
                    except queue.Empty:
                        # Still running, check if processes are alive
                        if process.poll() is not None and q.empty():
                            break

                process.wait()
                log(f"Process exited with code: {process.returncode}")
                self.finished.emit(process.returncode)
                self.output_received.emit(f"Game finished (exit code {process.returncode}).")

            except Exception as e:
                err_msg = str(e)
                log(f"LAUNCH EXCEPTION: {err_msg}")
                import traceback
                log(traceback.format_exc())
                self.error.emit(err_msg)
                self.output_received.emit(f"Launch Error: {err_msg}")

        threading.Thread(target=run_thread, daemon=True).start()

    def launch(self, app_id, app_name, exe_path, prefix_path):
        self.launch_via_legendary(app_id, app_name, find_umu_run())
