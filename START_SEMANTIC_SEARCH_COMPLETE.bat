@echo off
title Semantic Search Assistant - Complete System Launcher
color 0A

echo.
echo ===============================================================================
echo                    SEMANTIC SEARCH ASSISTANT - COMPLETE MVP
echo ===============================================================================
echo.
echo 🚀 Starting the complete semantic search system...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python detected
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ❌ main.py not found. Please run this script from the project directory.
    echo.
    pause
    exit /b 1
)

echo ✅ Project files found
echo.

REM Option menu
echo Please choose how to start the system:
echo.
echo [1] Desktop Application (Full featured - requires Node.js)
echo [2] Web Interface (Works without Node.js)
echo [3] Complete System Test (Recommended first run)
echo [4] Backend Only (API server)
echo [5] Install/Update Dependencies
echo [6] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto desktop_app
if "%choice%"=="2" goto web_interface
if "%choice%"=="3" goto test_system
if "%choice%"=="4" goto backend_only
if "%choice%"=="5" goto install_deps
if "%choice%"=="6" goto exit
goto invalid_choice

:desktop_app
echo.
echo 🖥️ Starting complete desktop application...
echo This will start the floating window that monitors all applications.
echo.
python launch_complete_desktop.py
goto end

:web_interface
echo.
echo 🌐 Starting web interface...
echo This will start the web-based interface (no Node.js required).
echo.
python final_launcher.py
goto end

:test_system
echo.
echo 🧪 Running complete system test...
echo This will verify all components are working correctly.
echo.
python start_complete_system.py
if errorlevel 1 (
    echo.
    echo ❌ System test failed. Please check the errors above.
    echo.
    pause
    exit /b 1
)
echo.
echo ✅ System test completed successfully!
echo You can now run the production launcher (option 2).
echo.
pause
goto menu

:production_launcher
echo.
echo 🚀 Starting production launcher...
echo This will start the complete application with desktop interface.
echo.
python production_launcher.py
goto end

:backend_only
echo.
echo 📊 Starting backend only...
echo This will start just the API server for development.
echo.
python main.py
goto end

:install_deps
echo.
echo 📦 Installing/updating dependencies...
echo.
echo Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

REM Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️ Node.js not found. Desktop app features will not be available.
    echo To install Node.js, visit: https://nodejs.org
    echo.
) else (
    echo.
    echo Installing Electron dependencies...
    if exist "electron-app\package.json" (
        cd electron-app
        npm install
        if errorlevel 1 (
            echo ❌ Failed to install Electron dependencies
            cd ..
            pause
            exit /b 1
        )
        cd ..
        echo ✅ Electron dependencies installed
    ) else (
        echo ⚠️ Electron app not found, skipping...
    )
)

echo.
echo ✅ All dependencies installed successfully!
echo.
pause
goto menu

:invalid_choice
echo.
echo ❌ Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.
echo.
pause
goto menu

:menu
cls
echo.
echo ===============================================================================
echo                    SEMANTIC SEARCH ASSISTANT - COMPLETE MVP
echo ===============================================================================
echo.
echo Please choose how to start the system:
echo.
echo [1] Desktop Application (Full featured - requires Node.js)
echo [2] Web Interface (Works without Node.js)
echo [3] Complete System Test (Recommended first run)
echo [4] Backend Only (API server)
echo [5] Install/Update Dependencies
echo [6] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto desktop_app
if "%choice%"=="2" goto web_interface
if "%choice%"=="3" goto test_system
if "%choice%"=="4" goto backend_only
if "%choice%"=="5" goto install_deps
if "%choice%"=="6" goto exit
goto invalid_choice

:exit
echo.
echo 👋 Goodbye!
exit /b 0

:end
echo.
echo 🛑 Application stopped.
echo.
pause
