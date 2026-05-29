import subprocess
import json
import os
import re
import threading
from PySide6.QtCore import QObject, Signal, Slot, Property, QAbstractListModel, Qt, QModelIndex


class DownloadItem:
    def __init__(self, app_id, name, base_path=None):
        self.app_id = app_id
        self.name = name
        self.base_path = base_path
        self.progress = 0.0
        self.status = "Queued" # Queued, Downloading, Paused, Finished, Failed
        self.speed = ""
        self.eta = ""
        self.process = None


class DownloadModel(QAbstractListModel):
    AppIdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    ProgressRole = Qt.UserRole + 3
    StatusRole = Qt.UserRole + 4
    SpeedRole = Qt.UserRole + 5
    EtaRole = Qt.UserRole + 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        item = self._items[index.row()]
        if role == self.AppIdRole: return item.app_id
        if role == self.NameRole: return item.name
        if role == self.ProgressRole: return item.progress
        if role == self.StatusRole: return item.status
        if role == self.SpeedRole: return item.speed
        if role == self.EtaRole: return item.eta
        return None

    def roleNames(self):
        return {
            self.AppIdRole: b"appId",
            self.NameRole: b"name",
            self.ProgressRole: b"progress",
            self.StatusRole: b"status",
            self.SpeedRole: b"speed",
            self.EtaRole: b"eta"
        }

    def add_item(self, item):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()

    def update_item(self, app_id):
        for i, item in enumerate(self._items):
            if item.app_id == app_id:
                self.dataChanged.emit(self.index(i), self.index(i))
                break
    
    def remove_item(self, app_id):
        for i, item in enumerate(self._items):
            if item.app_id == app_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._items.pop(i)
                self.endRemoveRows()
                break


class DownloadManager(QObject):
    queue_changed = Signal()
    global_progress_changed = Signal(float)
    install_finished = Signal(str, bool)  # app_id, success
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = DownloadModel()
        self._current_app_id = None
        self._is_paused = False
        self._restore_queue()

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    def _save_queue(self):
        try:
            from .database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM download_queue")
            for item in self._model._items:
                cursor.execute(
                    "INSERT OR REPLACE INTO download_queue (app_id, name, base_path, status) VALUES (?, ?, ?, ?)",
                    (item.app_id, item.name, item.base_path, item.status),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DOWNLOAD] Error saving download queue: {e}")

    def _restore_queue(self):
        try:
            from .database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT app_id, name, base_path, status FROM download_queue")
            rows = cursor.fetchall()
            conn.close()
            print(f"[DOWNLOAD] Restoring {len(rows)} queued item(s) from database")
            for app_id, name, base_path, status in rows:
                if status == "Downloading":
                    print(f"[DOWNLOAD]   {app_id}: was Downloading, reset to Queued")
                    status = "Queued"
                print(f"[DOWNLOAD]   {app_id}: {name or '(unnamed)'} base_path={base_path} status={status}")
                item = DownloadItem(app_id, name, base_path)
                item.status = status
                self._model.add_item(item)
            if rows:
                self._check_queue()
        except Exception as e:
            print(f"[DOWNLOAD] Error restoring download queue: {e}")

    @Slot(str, str)
    def add_to_queue(self, app_id, name):
        print(f"[DOWNLOAD] add_to_queue(app_id={app_id}, name={name!r})")
        self.add_to_queue_with_base(app_id, name, None)

    @Slot(str, str, str)
    def add_to_queue_with_base(self, app_id, name, base_path):
        print(f"[DOWNLOAD] add_to_queue_with_base(app_id={app_id}, name={name!r}, base_path={base_path!r})")
        for item in self._model._items:
            if item.app_id == app_id:
                if item.status in ("Finished", "Failed"):
                    print(f"[DOWNLOAD]   removing stale {item.status} entry and re-adding")
                    self._model.remove_item(app_id)
                    self._remove_from_db(app_id)
                    break
                elif item.status == "Paused":
                    print(f"[DOWNLOAD]   item is Paused, resuming instead")
                    self.resume_download(app_id)
                    return
                else:
                    print(f"[DOWNLOAD]   already in queue (status={item.status}), skipping")
                    return
        
        new_item = DownloadItem(app_id, name, base_path)
        print(f"[DOWNLOAD]   created DownloadItem (name={name!r}, base_path={base_path!r})")
        self._model.add_item(new_item)
        self._save_queue()
        self._check_queue()

    @Slot(str)
    def pause_download(self, app_id):
        print(f"[DOWNLOAD] pause_download({app_id})")
        for item in self._model._items:
            if item.app_id == app_id and item.status == "Downloading":
                if item.process:
                    item.process.terminate()
                item.status = "Paused"
                self._model.update_item(app_id)
                self._save_queue()
                self._current_app_id = None
                print(f"[DOWNLOAD]   paused {app_id}")
                self._check_queue()
                break

    @Slot(str)
    def resume_download(self, app_id):
        print(f"[DOWNLOAD] resume_download({app_id})")
        for item in self._model._items:
            if item.app_id == app_id and item.status == "Paused":
                item.status = "Queued"
                self._model.update_item(app_id)
                self._save_queue()
                print(f"[DOWNLOAD]   queued {app_id} for resume")
                self._check_queue()
                break

    @Slot(str)
    def cancel_download(self, app_id):
        print(f"[DOWNLOAD] cancel_download({app_id})")
        for item in self._model._items:
            if item.app_id == app_id:
                if item.status == "Downloading" and item.process:
                    item.process.terminate()
                self._model.remove_item(app_id)
                self._remove_from_db(app_id)
                if self._current_app_id == app_id:
                    self._current_app_id = None
                print(f"[DOWNLOAD]   cancelled and removed {app_id}")
                self._check_queue()
                break

    def _remove_from_db(self, app_id):
        try:
            from .database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM download_queue WHERE app_id = ?", (app_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DOWNLOAD] Error removing from download queue DB: {e}")

    def _check_queue(self):
        if self._current_app_id:
            print(f"[DOWNLOAD] _check_queue: busy with {self._current_app_id}")
            return
        
        for item in self._model._items:
            if item.status == "Queued":
                print(f"[DOWNLOAD] _check_queue: starting {item.app_id}")
                self._start_download(item)
                return
        print(f"[DOWNLOAD] _check_queue: nothing to start")

    def _start_download(self, item):
        self._current_app_id = item.app_id
        item.status = "Downloading"
        self._model.update_item(item.app_id)
        self._save_queue()
        
        print(f"[INSTALL] Starting install for {item.app_id} (name={item.name!r}, base_path={item.base_path!r})")
        
        def run_proc():
            try:
                from .game_service import get_default_install_dir
                cmd = ["legendary", "install", item.app_id, "--yes"]
                if item.base_path and item.base_path != "/":
                    install_dir = os.path.join(item.base_path, "Games", "Heroic")
                    os.makedirs(install_dir, exist_ok=True)
                    cmd += ["--base-path", install_dir]
                    print(f"[INSTALL]   SD card path: {install_dir}")
                else:
                    install_dir = get_default_install_dir()
                    cmd += ["--base-path", install_dir]
                    print(f"[INSTALL]   internal path: {install_dir}")

                print(f"[INSTALL]   command: {' '.join(cmd)}")
                item.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                print(f"[INSTALL]   subprocess PID: {item.process.pid}")

                for line in item.process.stdout:
                    line = line.strip()
                    if not line: continue
                    
                    progress_match = re.search(r"Progress: (\d+\.\d+)%", line)
                    if progress_match:
                        item.progress = float(progress_match.group(1))
                        eta_match = re.search(r"ETA: (\d+:\d+:\d+)", line)
                        if eta_match:
                            item.eta = eta_match.group(1)
                        self._model.update_item(item.app_id)
                    
                    speed_match = re.search(r"Download\s+-\s+([\d\.]+\s+\w+/s)", line)
                    if speed_match:
                        item.speed = speed_match.group(1)
                        self._model.update_item(item.app_id)

                item.process.wait()
                success = (item.process.returncode == 0)
                print(f"[INSTALL]   process exited with code {item.process.returncode}")
                if success:
                    item.status = "Finished"
                    print(f"[INSTALL]   download finished successfully for {item.app_id}")
                    self._on_download_finished(item.app_id, True)
                else:
                    if item.status != "Paused":
                        item.status = "Failed"
                    success = False
                    print(f"[INSTALL]   download FAILED for {item.app_id}")
                
                self._model.update_item(item.app_id)
                self._save_queue()
                self._current_app_id = None
                if not success:
                    print(f"[INSTALL]   emitting install_finished({item.app_id}, False)")
                    self.install_finished.emit(item.app_id, False)
                print(f"[INSTALL]   checking queue for next item")
                self._check_queue()
                
            except Exception as e:
                import traceback
                print(f"[INSTALL]   THREAD EXCEPTION: {e}")
                traceback.print_exc()
                item.status = "Failed"
                self._model.update_item(item.app_id)
                self._save_queue()
                self._current_app_id = None
                self.install_finished.emit(item.app_id, False)
                self._check_queue()

        threading.Thread(target=run_proc, daemon=True).start()

    def _on_download_finished(self, app_id, success):
        print(f"[INSTALL] _on_download_finished({app_id}, success={success})")
        try:
            from .database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE games SET is_installed = 1 WHERE app_id = ?", (app_id,))
            conn.commit()
            print(f"[INSTALL]   updated DB: is_installed=1 for {app_id}")
            conn.close()
        except Exception as e:
            print(f"[INSTALL]   ERROR updating install status: {e}")
        try:
            from .epic_service import sync_installed_to_heroic_config
            sync_installed_to_heroic_config(app_id, add=True)
            print(f"[INSTALL]   synced to Heroic config for {app_id}")
        except Exception as e:
            print(f"[INSTALL]   ERROR syncing to heroic config: {e}")
        print(f"[INSTALL]   emitting install_finished({app_id}, True)")
        self.install_finished.emit(app_id, True)
