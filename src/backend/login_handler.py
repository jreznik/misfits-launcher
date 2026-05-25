import subprocess
import os
import sys
from PySide6.QtCore import QThread, Signal, QObject

class LoginThread(QThread):
    sid_captured = Signal(str)
    error_occurred = Signal(str)

    def run(self):
        # Path to the helper script
        helper_path = os.path.join(os.path.dirname(__file__), "epic_login_helper.py")
        
        try:
            # Run the helper as a separate process
            process = subprocess.Popen(
                [sys.executable, helper_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            sid = None
            # Read stdout line by line
            for line in process.stdout:
                print(f"HELPER: {line.strip()}")
                sys.stdout.flush()
                if line.startswith("SID:"):
                    sid = line.strip().split(":")[1]
                    # We don't break here to keep seeing debug logs if needed, 
                    # but sid is captured. Actually, break is fine once captured.
                    break
            
            process.wait()
            
            if sid:
                self.sid_captured.emit(sid)
            else:
                self.error_occurred.emit("Login failed or was cancelled.")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
