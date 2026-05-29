#!/bin/bash
# MisfitsLauncher Entry Point Script
# Works both inside Flatpak and directly on the host.
# Sets the same environment variables for interoperability with Heroic/legendary.

# 1. Force Legendary to use the host configuration directory
export LEGENDARY_CONFIG_PATH="$HOME/.config/legendary"

# 2. Detect environment
if [ -n "$FLATPAK_ID" ] || [ -d /app/share/misfitslauncher ]; then
    # --- Running inside Flatpak ---
    APP_DIR=/app/share/misfitslauncher

    # Symlink host UMU data into the sandbox if not already present
    INTERNAL_DATA_DIR="${XDG_DATA_HOME:-$HOME/.var/app/io.github.misfitslauncher.MisfitsLauncher/data}"
    mkdir -p "$INTERNAL_DATA_DIR"
    if [ ! -d "$INTERNAL_DATA_DIR/umu" ] && [ -d "$HOME/.local/share/umu" ]; then
        ln -s "$HOME/.local/share/umu" "$INTERNAL_DATA_DIR/umu"
    fi

    PYTHON=/usr/bin/python3
else
    # --- Running directly on host ---
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    APP_DIR="$SCRIPT_DIR"
    PYTHON=python3
    export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"
fi

# 3. Launch the application
exec "$PYTHON" "$APP_DIR/main.py" "$@" > "$HOME/misfits.log" 2>&1
