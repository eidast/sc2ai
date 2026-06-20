@echo off
setlocal enabledelayedexpansion

echo === SC2AI Map Setup (Windows) ===
set MAPS_DIR=C:\Program Files (x86)\StarCraft II\Maps
echo Target: %MAPS_DIR%
echo.

if not exist "%MAPS_DIR%" mkdir "%MAPS_DIR%"

echo Downloading Ladder2019Season3...
curl -L -o "%TEMP%\Ladder2019Season3.zip" "https://blzdistsc2-a.akamaihd.net/MapPacks/Ladder2019Season3.zip"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to download Ladder2019Season3.zip
    exit /b 1
)

echo Downloading Melee...
curl -L -o "%TEMP%\Melee.zip" "https://blzdistsc2-a.akamaihd.net/MapPacks/Melee.zip"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to download Melee.zip
    exit /b 1
)

echo Extracting maps...
uv run python -c "import zipfile; zipfile.ZipFile(r'%TEMP%\Ladder2019Season3.zip').extractall(r'%MAPS_DIR%', pwd=b'iagreetotheeula'); zipfile.ZipFile(r'%TEMP%\Melee.zip').extractall(r'%MAPS_DIR%', pwd=b'iagreetotheeula')"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to extract map packs
    del "%TEMP%\Ladder2019Season3.zip" 2>nul
    del "%TEMP%\Melee.zip" 2>nul
    exit /b 1
)

echo Cleaning up temporary files...
del "%TEMP%\Ladder2019Season3.zip"
del "%TEMP%\Melee.zip"

echo.
echo === All maps installed ===
echo Verify with: uv run python -c "from sc2 import maps; print(maps.get('Acropolis'))"
