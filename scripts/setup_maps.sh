#!/bin/bash
# setup_maps.sh — Download and install SC2 ladder maps for macOS
#
# This script requires:
#   - curl and unzip (included in macOS)
#   - StarCraft II installed at /Applications/StarCraft II/
#
# The map packs are from Blizzard's official s2client-proto repository.
# By downloading you agree to the AI and Machine Learning License:
#   http://blzdistsc2-a.akamaihd.net/AI_AND_MACHINE_LEARNING_LICENSE.html

set -e

MAPS_DIR="/Applications/StarCraft II/Maps"
PASSWORD="iagreetotheeula"

echo "=== SC2AI Map Setup ==="
echo "Target: $MAPS_DIR"
echo ""

mkdir -p "$MAPS_DIR"

download_map_pack() {
    local name="$1"
    local url="$2"
    local zip_file="/tmp/${name}.zip"

    echo "Downloading $name..."
    curl -L -o "$zip_file" "$url"

    echo "Extracting $name..."
    unzip -o -P "$PASSWORD" "$zip_file" -d "$MAPS_DIR"

    rm "$zip_file"
    echo "Done: $name"
    echo ""
}

# Ladder 2019 Season 3 (includes Acropolis LE, Thunderbird LE, etc.)
download_map_pack "Ladder2019Season3" \
    "https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2019Season3.zip"

# Melee maps
download_map_pack "Melee" \
    "https://blzdistsc2-a.akamaihd.net/MapPacks/Melee.zip"

echo "=== All maps installed ==="
echo "Verify with: uv run python -c \"from sc2 import maps; print(maps.get('Acropolis'))\""
