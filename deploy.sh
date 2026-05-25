#!/bin/bash
# MisfitsLauncher Remote Deployment Script
# Optimized for Flatpak-only deployment to Steam Deck

DECK_IP=$1
BUNDLE_FILE="MisfitsLauncher.flatpak"
APP_ID="io.github.misfitslauncher.MisfitsLauncher"

if [ -z "$DECK_IP" ]; then
    echo "Usage: ./deploy.sh <steam_deck_ip>"
    echo "Example: ./deploy.sh 192.168.0.125"
    exit 1
fi

# 1. Build the Flatpak bundle if it doesn't exist or if requested
echo "--- Ensuring Flatpak bundle is ready ---"
flatpak-builder --repo=repo --force-clean build-dir io.github.misfitslauncher.MisfitsLauncher.yaml
flatpak build-bundle repo "$BUNDLE_FILE" "$APP_ID"

# 2. Sync the bundle to the Deck
echo "--- Sending $BUNDLE_FILE to Steam Deck ($DECK_IP) ---"
scp "$BUNDLE_FILE" "deck@$DECK_IP:~/"

# 3. Trigger remote installation
echo "--- Installing MisfitsLauncher on Steam Deck ---"
ssh "deck@$DECK_IP" "flatpak install --user -y ~/$BUNDLE_FILE && rm ~/$BUNDLE_FILE"


echo ""
echo "--- Deployment Complete ---"
echo "You can now run MisfitsLauncher on your Deck via Game Mode or SSH:"
echo "  ssh deck@$DECK_IP 'flatpak run $APP_ID'"
echo ""
