import sqlite3
import time
import os
import threading
from PySide6.QtCore import QObject, Signal, Slot, Property, QAbstractListModel, Qt, QModelIndex
from .database import get_db_connection
from .umu_launcher import UMULauncher, find_umu_run
from .steam_injector import add_to_steam as steam_add
from .game_service import GameService

class GameModel(QAbstractListModel):
    AppIdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    StoreSourceRole = Qt.UserRole + 3
    IsInstalledRole = Qt.UserRole + 4
    LastPlayedRole = Qt.UserRole + 5
    ArtworkRole = Qt.UserRole + 6
    HeroRole = Qt.UserRole + 7
    LogoRole = Qt.UserRole + 8
    ProtonTierRole = Qt.UserRole + 9

    def __init__(self, parent=None):
        super().__init__(parent)
        self._games = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._games)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._games):
            return None
        
        game = self._games[index.row()]
        
        if role == self.AppIdRole: return game.get('app_id')
        if role == self.NameRole: return game.get('name')
        if role == self.StoreSourceRole: return game.get('store_source')
        if role == self.IsInstalledRole: return bool(game.get('is_installed', 0))
        if role == self.LastPlayedRole: return game.get('last_played_timestamp', 0)
        if role == self.ArtworkRole: return game.get('artwork_path', '')
        if role == self.HeroRole: return game.get('hero_path', '')
        if role == self.LogoRole: return game.get('logo_path', '')
        if role == self.ProtonTierRole: return game.get('protondb_tier', '')
        return None

    def roleNames(self):
        return {
            self.AppIdRole: b"appId",
            self.NameRole: b"name",
            self.StoreSourceRole: b"storeSource",
            self.IsInstalledRole: b"isInstalled",
            self.LastPlayedRole: b"lastPlayed",
            self.ArtworkRole: b"artwork",
            self.HeroRole: b"hero",
            self.LogoRole: b"logo",
            self.ProtonTierRole: b"protonTier"
        }

    def update_games(self, games):
        self.beginResetModel()
        self._games = games
        self.endResetModel()

class GameManager(QObject):
    recent_games_changed = Signal()
    library_games_changed = Signal()
    recently_added_changed = Signal()
    game_info_ready = Signal(dict)
    proton_info_ready = Signal(str, dict)
    launch_status_changed = Signal(str)
    install_status_changed = Signal(str, float, str)
    uninstall_status_changed = Signal(str, bool)
    last_played_updated = Signal(str, int) # app_id, timestamp
    
    # State properties
    sort_info_changed = Signal()

    def __init__(self):
        super().__init__()
        self._recent_model = GameModel()
        self._library_model = GameModel()
        self._added_model = GameModel()
        self._service = GameService()
        
        # State
        self._filter_type = "ALL GAMES"
        self._search_query = ""
        self._sort_field = "name"
        self._sort_order = "ASC"

        self._service.install_progress.connect(self.install_status_changed)
        self._service.install_finished.connect(self._on_install_finished)
        self._service.uninstall_finished.connect(self._on_uninstall_finished)
        self._service.game_info_fetched.connect(self._on_game_info_fetched)
        self._service.proton_info_fetched.connect(self._on_proton_info_fetched)
        
        self._launcher = UMULauncher(self)
        self._launcher.finished.connect(self.refresh_models)
        self._launcher.output_received.connect(self.launch_status_changed)
        self._launcher.game_started.connect(self._on_game_started)
        self.refresh_models()

    def _on_game_started(self, app_id, timestamp):
        self.last_played_updated.emit(app_id, timestamp)

    @Property(str, notify=sort_info_changed)
    def currentSortField(self): return self._sort_field
    
    @Property(str, notify=sort_info_changed)
    def currentSortOrder(self): return self._sort_order

    def _on_game_info_fetched(self, app_id, info):
        try:
            if not info: info = {}
            manifest = info.get('manifest', {})
            disk_size = manifest.get('disk_size', 0)
            info['disk_size_gb'] = round(disk_size / (1024**3), 2)

            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE app_id = ?", (app_id,))
            db_row = cursor.fetchone()
            conn.close()
            
            if db_row:
                db_game = dict(db_row)
                info['app_id'] = app_id
                if 'game' not in info: info['game'] = {'title': db_game['name']}
                if 'app_title' not in info: info['app_title'] = db_game['name']
                info['is_installed'] = bool(db_game.get('is_installed', 0))
                info['artwork'] = db_game.get('artwork_path', '')
                info['hero'] = db_game.get('hero_path', '')
                info['logo'] = db_game.get('logo_path', '')
                info['lastPlayed'] = db_game.get('last_played_timestamp', 0)
                tier = db_game.get('protondb_tier')
                info['protondb'] = {'tier': tier} if tier else None
                if 'metadata' not in info: info['metadata'] = {}
                pd_data = info.get('protondb')
                steam_desc = pd_data.get('steam_description') if pd_data else None
                if steam_desc: info['metadata']['description'] = steam_desc
                elif not info['metadata'].get('description'): info['metadata']['description'] = db_game.get('description', '')
        except Exception as e:
            print(f"ERROR: _on_game_info_fetched failed: {e}")
        self.game_info_ready.emit(info)

    def _on_proton_info_fetched(self, app_id, compat):
        try:
            tier = compat.get('tier')
            if tier:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE games SET protondb_tier = ? WHERE app_id = ?", (tier, app_id))
                conn.commit()
                conn.close()
            self.proton_info_ready.emit(app_id, compat)
        except Exception as e:
            print(f"ERROR: _on_proton_info_fetched failed: {e}")

    def _on_install_finished(self, app_id, success):
        self.refresh_models()
        self.fetch_game_info(app_id)

    def _on_uninstall_finished(self, app_id, success):
        self.refresh_models()
        self.fetch_game_info(app_id)
        self.uninstall_status_changed.emit(app_id, success)

    @Property(QObject, constant=True)
    def recentModel(self): return self._recent_model
    @Property(QObject, constant=True)
    def libraryModel(self): return self._library_model
    @Property(QObject, constant=True)
    def recentlyAddedModel(self): return self._added_model

    @Slot()
    def refresh_models(self):
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE last_played_timestamp > 0 ORDER BY last_played_timestamp DESC LIMIT 10")
            self._recent_model.update_games([dict(row) for row in cursor.fetchall()])
            cursor.execute("SELECT * FROM games ORDER BY install_timestamp DESC LIMIT 15")
            self._added_model.update_games([dict(row) for row in cursor.fetchall()])
            conn.close()
            self.apply_filter_sort()
        except Exception as e:
            print(f"ERROR: refresh_models failed: {e}")

    @Slot(str)
    def filter_library(self, filter_text):
        self._filter_type = filter_text
        self.apply_filter_sort()

    @Slot(str)
    def search_library(self, query):
        self._search_query = query
        self.apply_filter_sort()

    @Slot(str, str)
    def set_sort(self, field, order):
        self._sort_field = field
        self._sort_order = order
        self.sort_info_changed.emit()
        self.apply_filter_sort()

    def apply_filter_sort(self):
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM games"
            where_clauses = []
            params = []
            if self._filter_type == "INSTALLED": where_clauses.append("is_installed = 1")
            elif self._filter_type == "GREAT ON DECK": where_clauses.append("protondb_tier IN ('platinum', 'gold')")
            if self._search_query:
                where_clauses.append("name LIKE ?")
                params.append(f"%{self._search_query}%")
            if where_clauses: query += " WHERE " + " AND ".join(where_clauses)
            field_map = {"name": "name", "last_played": "last_played_timestamp", "date_added": "install_timestamp"}
            db_field = field_map.get(self._sort_field, "name")
            query += f" ORDER BY {db_field} {self._sort_order}"
            cursor.execute(query, params)
            self._library_model.update_games([dict(row) for row in cursor.fetchall()])
            conn.close()
        except Exception as e:
            print(f"ERROR: apply_filter_sort failed: {e}")

    @Slot(str)
    def fetch_game_info(self, app_id): 
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE app_id = ?", (app_id,))
            db_row = cursor.fetchone()
            conn.close()
            if db_row: self._on_game_info_fetched(app_id, {}) 
        except Exception: pass
        self._service.fetch_game_info(app_id)

    @Slot(str)
    def install_game(self, app_id): self._service.install_game(app_id)
    @Slot(str)
    def uninstall_game(self, app_id): self._service.uninstall_game(app_id)
    @Slot(str)
    def launch_game(self, app_id):
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE app_id = ?", (app_id,))
            game = cursor.fetchone()
            conn.close()
            if game:
                self._launcher.launch_via_legendary(game['app_id'], game['name'], find_umu_run())
        except Exception as e:
            print(f"ERROR: launch_game failed: {e}")

    @Slot(str)
    def inject_to_steam(self, app_id):
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE app_id = ?", (app_id,))
            game = cursor.fetchone()
            conn.close()
            if game:
                steam_add(game['name'], "/usr/bin/true", grid_art_path=game['artwork_path'], hero_art_path=game['hero_path'], logo_art_path=game['logo_path'])
        except Exception as e:
            print(f"ERROR: inject_to_steam failed: {e}")
