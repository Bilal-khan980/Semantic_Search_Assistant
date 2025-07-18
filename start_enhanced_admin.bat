@echo off
echo ========================================
echo  Enhanced Global Monitor (Administrator)
echo ========================================
echo.
echo This will run the global monitor with
echo administrator privileges for better
echo compatibility with Word and other apps.
echo.
echo Features:
echo - Global keyboard monitoring
echo - Works with Word, Notepad, VS Code
echo - Real-time text detection
echo - Spacebar clearing
echo - Instant search suggestions
echo.
echo ========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - Good!
    echo.
    python enhanced_global_monitor.py
) else (
    echo Requesting Administrator privileges...
    echo.
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %cd% && python enhanced_global_monitor.py && pause' -Verb RunAs"
)

pause
