@echo off
echo Building Semantic Search Assistant executable...
echo.

REM Install PyInstaller if not already installed
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onedir --windowed --name "SemanticSearchAssistant" --add-data "config.json;." --add-data "requirements.txt;." enhanced_global_monitor.py

echo.
echo Build complete!
echo The executable will be in the 'dist\SemanticSearchAssistant' folder.
echo.
echo To distribute to client:
echo 1. Copy the entire 'dist\SemanticSearchAssistant' folder to client
echo 2. Client should create 'SemanticFiles' folder on their Desktop
echo 3. Client can run SemanticSearchAssistant.exe from the copied folder
echo.
pause
