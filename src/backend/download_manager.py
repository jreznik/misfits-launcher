import subprocess
import json
import os
import re
import threading
from PySide6.QtCore import QObject, Signal, Slot, Property, QAbstractListModel, Qt, QModelIndex

class DownloadItem:
    def __init__(self, app_id, name):
        self.app_id = app_id
        self.name = name
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = DownloadModel()
        self._current_app_id = None
        self._is_paused = False

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Slot(str, str)
    def add_to_queue(self, app_id, name):
        # Check if already in queue
        for item in self._model._items:
            if item.app_id == app_id:
                return
        
        new_item = DownloadItem(app_id, name)
        self._model.add_item(new_item)
        self._check_queue()

    @Slot(str)
    def pause_download(self, app_id):
        for item in self._model._items:
            if item.app_id == app_id and item.status == "Downloading":
                if item.process:
                    item.process.terminate()
                item.status = "Paused"
                self._model.update_item(app_id)
                self._current_app_id = None
                self._check_queue()
                break

    @Slot(str)
    def resume_download(self, app_id):
        for item in self._model._items:
            if item.app_id == app_id and item.status == "Paused":
                item.status = "Queued"
                self._model.update_item(app_id)
                self._check_queue()
                break

    @Slot(str)
    def cancel_download(self, app_id):
        for item in self._model._items:
            if item.app_id == app_id:
                if item.status == "Downloading" and item.process:
                    item.process.terminate()
                self._model.remove_item(app_id)
                if self._current_app_id == app_id:
                    self._current_app_id = None
                self._check_queue()
                break

    def _check_queue(self):
        if self._current_app_id:
            return
        
        for item in self._model._items:
            if item.status == "Queued":
                self._start_download(item)
                break

    def _start_download(self, item):
        self._current_app_id = item.app_id
        item.status = "Downloading"
        self._model.update_item(item.app_id)
        
        def run_proc():
            try:
                cmd = ["legendary", "install", item.app_id, "--yes"]
                item.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                for line in item.process.stdout:
                    line = line.strip()
                    if not line: continue
                    
                    # Parse progress, speed, ETA
                    # [DLManager] INFO: = Progress: 7.43% (20/269), Running for 00:00:01, ETA: 00:00:12
                    # [DLManager] INFO:  + Download	- 12.12 MiB/s (raw) / 40.99 MiB/s (decompressed)
                    
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
                if item.process.returncode == 0:
                    item.status = "Finished"
                    # Auto-remove finished after a delay? For now keep it.
                else:
                    if item.status != "Paused":
                        item.status = "Failed"
                
                self._model.update_item(item.app_id)
                self._current_app_id = None
                self._check_queue()
                
            except Exception as e:
                print(f"Download thread error: {e}")
                item.status = "Failed"
                self._model.update_item(item.app_id)
                self._current_app_id = None
                self._check_queue()

        threading.Thread(target=run_proc, daemon=True).start()
