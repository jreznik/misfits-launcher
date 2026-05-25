import os
import shutil
import requests
import tarfile
import threading
from PySide6.QtCore import QObject, Signal, Slot, Property

class UMURuntimeManager(QObject):
    runtimes_changed = Signal()
    install_progress = Signal(float, str) # progress, status
    install_finished = Signal(bool, str) # success, message

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Discover Steam compatibility tools directory
        # 1. Check standard path
        self._steam_runtimes_dir = os.path.expanduser("~/.local/share/Steam/compatibilitytools.d/")
        
        # 2. Check if Steam is installed via Flatpak
        flatpak_steam_dir = os.path.expanduser("~/.var/app/com.steampowered.Steam/.local/share/Steam/compatibilitytools.d/")
        
        if not os.path.exists(self._steam_runtimes_dir) and os.path.exists(flatpak_steam_dir):
            self._steam_runtimes_dir = flatpak_steam_dir
            
        # Discover UMU native runtimes
        self._umu_runtimes_dir = os.path.expanduser("~/.local/share/umu/compatibilitytools/")
        
        # Ensure directories exist
        os.makedirs(self._steam_runtimes_dir, exist_ok=True)
        os.makedirs(self._umu_runtimes_dir, exist_ok=True)
        
        self._runtimes = [] 
        self.refresh_runtimes()

    @Property(list, notify=runtimes_changed)
    def runtimes(self):
        return [r["name"] for r in self._runtimes]

    @Slot()
    def refresh_runtimes(self):
        try:
            self._runtimes = []
            
            # Scan Steam dir
            if os.path.exists(self._steam_runtimes_dir):
                for d in os.listdir(self._steam_runtimes_dir):
                    full_path = os.path.join(self._steam_runtimes_dir, d)
                    if os.path.isdir(full_path):
                        self._runtimes.append({"name": d, "path": full_path})
            
            # Scan UMU dir
            if os.path.exists(self._umu_runtimes_dir):
                for d in os.listdir(self._umu_runtimes_dir):
                    full_path = os.path.join(self._umu_runtimes_dir, d)
                    if os.path.isdir(full_path):
                        if not any(r["name"] == d for r in self._runtimes):
                            self._runtimes.append({"name": d, "path": full_path})
                            
            self.runtimes_changed.emit()
        except Exception as e:
            print(f"Error listing runtimes: {e}")

    @Slot(str)
    def remove_runtime(self, name):
        for r in self._runtimes:
            if r["name"] == name:
                runtime_path = r["path"]
                if os.path.exists(runtime_path):
                    try:
                        shutil.rmtree(runtime_path)
                        self.refresh_runtimes()
                    except Exception as e:
                        print(f"Error removing runtime: {e}")
                break

    @Slot()
    def install_latest_ge_proton(self):
        """Fetches and installs the latest GE-Proton from GitHub."""
        def run_install():
            try:
                self.install_progress.emit(0, "Fetching latest release info...")
                api_url = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
                resp = requests.get(api_url, timeout=15)
                if resp.status_code != 200:
                    self.install_finished.emit(False, "Failed to get release info.")
                    return
                
                data = resp.json()
                tag_name = data.get("tag_name")
                assets = data.get("assets", [])
                
                download_url = None
                file_name = None
                for asset in assets:
                    if asset["name"].endswith(".tar.gz"):
                        download_url = asset["browser_download_url"]
                        file_name = asset["name"]
                        break
                
                if not download_url:
                    self.install_finished.emit(False, "No tarball found in release.")
                    return

                dest_dir = os.path.join(self._steam_runtimes_dir, tag_name)
                if os.path.exists(dest_dir):
                    self.install_finished.emit(True, "Already installed.")
                    return

                self.install_progress.emit(10, f"Downloading {file_name}...")
                
                temp_path = os.path.join("/tmp", file_name)
                with requests.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    with open(temp_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                prog = 10 + (downloaded / total_size * 70)
                                self.install_progress.emit(prog, f"Downloading... {int(downloaded/1024/1024)}MB / {int(total_size/1024/1024)}MB")

                self.install_progress.emit(85, "Extracting...")
                
                with tarfile.open(temp_path, "r:gz") as tar:
                    tar.extractall(path=self._steam_runtimes_dir)
                
                os.remove(temp_path)
                self.install_progress.emit(100, "Done!")
                self.refresh_runtimes()
                self.install_finished.emit(True, f"Successfully installed {tag_name}")

            except Exception as e:
                print(f"Runtime install error: {e}")
                self.install_finished.emit(False, str(e))

        threading.Thread(target=run_install, daemon=True).start()
