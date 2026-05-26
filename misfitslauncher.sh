#!/bin/bash
# MisfitsLauncher Entry Point Script
# Ensures portability and interoperability with host system

# 1. Force Legendary to use the host's configuration directory
export LEGENDARY_CONFIG_PATH="$HOME/.config/legendary"


# 2. Ensure UMU data is accessible within the Flatpak sandbox
# We symlink the host's UMU data to the internal XDG_DATA_HOME if it's not already there
INTERNAL_DATA_DIR="${XDG_DATA_HOME:-$HOME/.var/app/io.github.misfitslauncher.MisfitsLauncher/data}"
mkdir -p "$INTERNAL_DATA_DIR"

if [ ! -d "$INTERNAL_DATA_DIR/umu" ] && [ -d "$HOME/.local/share/umu" ]; then
    ln -s "$HOME/.local/share/umu" "$INTERNAL_DATA_DIR/umu"
fi

# 3. Launch the Python application
exec python3 /app/share/misfitslauncher/main.py "$@" > "$HOME/misfits.log" 2>&1

