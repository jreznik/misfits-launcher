import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def make_installed_json(*games):
    """Create an installed.json dict for one or more game entries.
    Each game is a tuple of (app_id, title, install_path)."""
    data = {}
    for app_id, title, install_path in games:
        data[app_id] = {
            "app_name": app_id,
            "title": title,
            "install_path": install_path,
            "version": "1.0",
        }
    return data


class TempConfigDir:
    """Context manager that creates a temporary legendary config directory
    with optional installed.json."""

    def __init__(self, installed_data=None):
        self.path = None
        self.installed_data = installed_data

    def __enter__(self):
        self.path = tempfile.mkdtemp(prefix="legendary_config_")
        if self.installed_data is not None:
            with open(os.path.join(self.path, "installed.json"), "w") as f:
                json.dump(self.installed_data, f)
        return self.path

    def __exit__(self, *args):
        shutil.rmtree(self.path, ignore_errors=True)
