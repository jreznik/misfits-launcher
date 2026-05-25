import subprocess
import json
import sqlite3
import time
from .database import get_db_connection

class EpicService:
    @staticmethod
    def is_installed():
        try:
            subprocess.run(["legendary", "--version"], capture_output=True)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def login(token, is_code=True):
        """Authenticates using an Epic Authorization Code or SID."""
        try:
            flag = "--code" if is_code else "--sid"
            process = subprocess.run(
                ["legendary", "auth", flag, token],
                capture_output=True,
                text=True
            )
            if process.returncode != 0:
                print(f"DEBUG: Legendary Auth Error: {process.stderr}")
            return process.returncode == 0
        except Exception as e:
            print(f"Epic Login Error: {e}")
            return False

    @staticmethod
    def sync_library():
        """Fetches library from legendary and updates the local database."""
        try:
            # 1. Fetch full game list
            process = subprocess.run(
                ["legendary", "list-games", "--json"],
                capture_output=True,
                text=True
            )
            if process.returncode != 0:
                return False
            games_data = json.loads(process.stdout)

            # 2. Fetch installed games list
            installed_process = subprocess.run(
                ["legendary", "list-installed", "--json"],
                capture_output=True,
                text=True
            )
            installed_ids = set()
            if installed_process.returncode == 0:
                installed_data = json.loads(installed_process.stdout)
                installed_ids = {g.get("app_name") for g in installed_data}

            conn = get_db_connection()
            cursor = conn.cursor()

            now = int(time.time())
            for game in games_data:
                app_id = game.get("app_name") # Internal Epic ID
                name = game.get("app_title")
                is_installed = 1 if app_id in installed_ids else 0
                
                # Metadata extraction
                metadata = game.get("metadata", {})
                description = metadata.get("description", "")
                key_images = metadata.get("keyImages", [])
                
                artwork = ""
                hero = ""
                logo = ""
                
                # Broaden image search - iterate through all images and find best matches
                for img in key_images:
                    img_type = img.get("type", "").lower()
                    url = img.get("url")
                    
                    if not url: continue

                    # Artwork (Poster) matches
                    if "box" in img_type or "poster" in img_type or "tall" in img_type:
                        if not artwork or "tall" in img_type: # Prefer tall
                            artwork = url
                    
                    # Hero matches
                    if "hero" in img_type or "landscape" in img_type or "wide" in img_type:
                        if not hero or "hero" in img_type:
                            hero = url
                    
                    # Logo matches
                    if "logo" in img_type or "clear" in img_type:
                        logo = url

                # Fallbacks if none found
                if not artwork and key_images: artwork = key_images[0].get("url")
                if not hero and key_images: hero = key_images[0].get("url")
                if not logo and key_images: logo = key_images[0].get("url")

                cursor.execute('''
                    INSERT INTO games (app_id, name, store_source, is_installed, artwork_path, hero_path, logo_path, install_timestamp, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(app_id) DO UPDATE SET
                        is_installed=excluded.is_installed,
                        artwork_path=excluded.artwork_path,
                        hero_path=excluded.hero_path,
                        logo_path=excluded.logo_path,
                        description=excluded.description
                ''', (app_id, name, "Epic", is_installed, artwork, hero, logo, now, description))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Epic Sync Error: {e}")
            return False
