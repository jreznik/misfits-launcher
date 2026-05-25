import os
import zlib
import vdf
import requests
import shutil
from pathlib import Path

def calculate_appid(exe, appname):
    """Calculates the 32-bit appid stored in shortcuts.vdf."""
    key = exe + appname
    crc = zlib.crc32(key.encode('utf-8')) & 0xFFFFFFFF
    appid_32 = crc | 0x80000000
    
    # Steam stores this as a signed 32-bit integer
    if appid_32 > 0x7FFFFFFF:
        appid_32 -= 0x100000000
    return appid_32

def calculate_long_id(appid_32):
    """Calculates the 64-bit ID used for grid art."""
    unsigned_32 = appid_32 & 0xFFFFFFFF
    return (unsigned_32 << 32) | 0x02000000

def get_steam_user_dirs():
    base_path = Path("~/.steam/root/userdata").expanduser()
    if not base_path.exists():
        return []
    return [d for d in base_path.iterdir() if d.is_dir() and d.name.isdigit()]

def add_to_steam(app_name, launch_command, icon_path=None, grid_art_path=None, hero_art_path=None, logo_art_path=None):
    user_dirs = get_steam_user_dirs()
    if not user_dirs:
        print("No Steam user directories found.")
        return False

    # For simplicity, we'll update all users found
    for user_dir in user_dirs:
        shortcuts_path = user_dir / "config" / "shortcuts.vdf"
        grid_dir = user_dir / "config" / "grid"
        grid_dir.mkdir(parents=True, exist_ok=True)

        shortcuts = {"shortcuts": {}}
        if shortcuts_path.exists():
            with open(shortcuts_path, "rb") as f:
                try:
                    shortcuts = vdf.binary_load(f)
                except Exception as e:
                    print(f"Error loading shortcuts.vdf: {e}")
                    shortcuts = {"shortcuts": {}}

        # Calculate IDs
        # Steam usually expects the exe to be quoted
        quoted_exe = f'"{launch_command}"'
        appid_32 = calculate_appid(quoted_exe, app_name)
        long_id = calculate_long_id(appid_32)

        # Check if already exists
        found = False
        for key, s in shortcuts.get("shortcuts", {}).items():
            if s.get("AppName") == app_name:
                found = True
                new_shortcut = s
                break
        
        if not found:
            idx = str(len(shortcuts.get("shortcuts", {})))
            new_shortcut = {
                "appid": appid_32,
                "AppName": app_name,
                "Exe": quoted_exe,
                "StartDir": f'"{os.path.dirname(launch_command)}"',
                "icon": icon_path if icon_path else "",
                "ShortcutPath": "",
                "LaunchOptions": "",
                "IsHidden": 0,
                "AllowDesktopConfig": 1,
                "AllowOverlay": 1,
                "OpenVR": 0,
                "Devkit": 0,
                "DevkitGameID": "",
                "LastPlayTime": 0,
                "tags": {}
            }
            if "shortcuts" not in shortcuts:
                shortcuts["shortcuts"] = {}
            shortcuts["shortcuts"][idx] = new_shortcut

        # Save shortcuts.vdf
        with open(shortcuts_path, "wb") as f:
            vdf.binary_dump(shortcuts, f)

        # Artwork Injection
        art_map = {
            "p.jpg": grid_art_path,        # Vertical Grid
            "_hero.jpg": hero_art_path,    # Hero
            "_logo.png": logo_art_path,    # Logo
            ".png": icon_path              # Icon (fallback)
        }

        for suffix, src in art_map.items():
            if src:
                dest = grid_dir / f"{long_id}{suffix}"
                try:
                    if src.startswith("http"):
                        resp = requests.get(src, stream=True)
                        if resp.status_code == 200:
                            with open(dest, "wb") as f:
                                shutil.copyfileobj(resp.raw, f)
                    else:
                        shutil.copy2(src, dest)
                except Exception as e:
                    print(f"Error saving artwork {suffix}: {e}")

    return True
