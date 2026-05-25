#!/bin/bash
# MisfitsLauncher Remote Deployment Script
# Use this to quickly sync and test your code on a Steam Deck in your network.

DECK_IP=$1
TARGET_DIR="~/misfits-launcher"

if [ -z "$DECK_IP" ]; then
    echo "Usage: ./deploy.sh <steam_deck_ip>"
    echo "Example: ./deploy.sh 192.168.1.100"
    exit 1
fi

echo "--- Syncing source code to Steam Deck ($DECK_IP) ---"
# We exclude artifacts and large bundles to keep the sync fast
rsync -avz --exclude='.git/' --exclude='.flatpak-builder/' --exclude='build-dir/' --exclude='repo/' --exclude='*.flatpak' ./ deck@$DECK_IP:$TARGET_DIR

echo ""
echo "--- Remote Sync Complete ---"
echo "You can now run it on your Deck via SSH:"
echo "  ssh deck@$DECK_IP 'cd $TARGET_DIR && python3 main.py'"
echo ""
echo "Or, if you want to push the Flatpak bundle:"
if [ -f "MisfitsLauncher.flatpak" ]; then
    echo "Sending Flatpak bundle..."
    scp MisfitsLauncher.flatpak deck@$DECK_IP:~/
    echo "To install on Deck: ssh deck@$DECK_IP 'flatpak install --user ~/MisfitsLauncher.flatpak'"
else
    echo "MisfitsLauncher.flatpak not found. Build it first with flatpak-builder."
fi
