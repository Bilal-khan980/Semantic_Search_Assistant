#!/usr/bin/env python3
"""
Complete Desktop Application Launcher.
Starts backend and floating desktop application with all features.
"""

import os
import sys
import subprocess
import time
import logging
import threading
import signal
from pathlib import Path
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteDesktopLauncher:
    """Complete desktop application launcher."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.backend_process = None
        self.floating_app_process = None
        self.is_running = False
        
    def check_dependencies(self):
        """Check required dependencies."""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'tkinter', 'requests', 'pyperclip', 'keyboard', 
            'pyautogui', 'PyMuPDF', 'watchdog'
        ]
        
        missing = []
        for package in required_packages:
            try:
                if package == 'tkinter':
                    import tkinter
                elif package == 'PyMuPDF':
                    import fitz
                else:
                    __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            logger.warning(f"Missing packages: {', '.join(missing)}")
            logger.info("Installing missing packages...")
            try:
                # Install missing packages
                install_cmd = [sys.executable, '-m', 'pip', 'install']
                
                # Map package names to pip names
                pip_names = {
                    'PyMuPDF': 'PyMuPDF',
                    'pyperclip': 'pyperclip',
                    'keyboard': 'keyboard',
                    'pyautogui': 'pyautogui',
                    'watchdog': 'watchdog'
                }
                
                for pkg in missing:
                    if pkg in pip_names:
                        install_cmd.append(pip_names[pkg])
                
                if len(install_cmd) > 4:  # Has packages to install
                    subprocess.run(install_cmd, check=True)
                    logger.info("Dependencies installed successfully")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {e}")
                return False
        
        logger.info("All dependencies satisfied")
        return True
    
    def start_backend(self):
        """Start the backend server."""
        logger.info("Starting backend server...")
        
        try:
            self.backend_process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 
                'api_service:app',
                '--host', '127.0.0.1',
                '--port', '8000'
            ], cwd=self.app_dir)
            
            # Wait for backend to start
            if self.wait_for_backend():
                logger.info("Backend server started successfully")
                return True
            else:
                logger.error("Backend failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def wait_for_backend(self):
        """Wait for backend to be ready."""
        for attempt in range(30):  # 30 second timeout
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=1)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(1)
            
            # Check if process is still running
            if self.backend_process and self.backend_process.poll() is not None:
                logger.error("Backend process terminated unexpectedly")
                return False
        
        return False
    
    def start_floating_app(self):
        """Start the real-time floating desktop application."""
        logger.info("Starting real-time floating desktop application...")

        try:
            self.floating_app_process = subprocess.Popen([
                sys.executable, 'real_time_floating_app.py'
            ], cwd=self.app_dir)
            
            # Wait a moment to see if it starts
            time.sleep(2)
            
            if self.floating_app_process.poll() is None:
                logger.info("Floating desktop application started successfully")
                return True
            else:
                logger.error("Floating app process terminated unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start floating app: {e}")
            return False
    
    def display_status(self):
        """Display the application status."""
        print("\n" + "=" * 80)
        print("     SEMANTIC SEARCH ASSISTANT - COMPLETE DESKTOP APPLICATION")
        print("=" * 80)
        print("🚀 Status: RUNNING")
        print("")
        print("🖥️  Floating Desktop App:  Active (always on top)")
        print("📊 Backend API:           http://127.0.0.1:8000")
        print("🌐 Web Interface:         http://127.0.0.1:8000")
        print("📚 API Documentation:     http://127.0.0.1:8000/docs")
        print("")
        print("✨ FEATURES ACTIVE:")
        print("  • Context-aware floating window (monitors all apps)")
        print("  • Real-time context detection while writing")
        print("  • Cross-application drag & drop with citations")
        print("  • PDF highlighting with metadata")
        print("  • Readwise markdown integration")
        print("  • Canvas for organizing notes (SUBLIME-like)")
        print("  • Background processing with progress")
        print("  • Global keyboard shortcuts")
        print("")
        print("⌨️  GLOBAL SHORTCUTS:")
        print("  • Ctrl+Shift+Space  - Toggle floating window")
        print("  • Ctrl+Shift+S      - Quick search with clipboard")
        print("  • Ctrl+Shift+C      - Open canvas")
        print("  • Ctrl+Shift+X      - Force context update")
        print("")
        print("🎯 HOW TO USE:")
        print("  1. Start writing in Word, Notion, or any app")
        print("  2. The floating window will show related suggestions")
        print("  3. Double-click suggestions to copy with citations")
        print("  4. Right-click for more options (add to canvas, etc.)")
        print("  5. Use PDF Highlighter for annotating documents")
        print("")
        print("🔧 ADDITIONAL TOOLS:")
        print("  • PDF Highlighter: python pdf_highlighter.py")
        print("  • Readwise Import: Automatic from watched folders")
        print("")
        print("Press Ctrl+C to stop")
        print("=" * 80)
    
    def wait_for_shutdown(self):
        """Wait for user to stop the application."""
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
    
    def shutdown(self):
        """Shutdown all processes."""
        logger.info("Shutting down complete desktop application...")
        self.is_running = False
        
        # Stop floating app
        if self.floating_app_process:
            logger.info("Stopping floating desktop application...")
            self.floating_app_process.terminate()
            try:
                self.floating_app_process.wait(timeout=10)
                logger.info("Floating app stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Force killing floating app process")
                self.floating_app_process.kill()
        
        # Stop backend
        if self.backend_process:
            logger.info("Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
                logger.info("Backend server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Force killing backend process")
                self.backend_process.kill()
        
        logger.info("Shutdown complete")
    
    def run(self):
        """Main run method."""
        print("🚀 Starting Complete Semantic Search Assistant Desktop Application")
        print("=" * 80)
        
        try:
            # Check dependencies
            if not self.check_dependencies():
                print("\n❌ Failed to install dependencies")
                return False
            
            # Start backend
            if not self.start_backend():
                print("\n❌ Failed to start backend server")
                return False
            
            # Start floating app
            if not self.start_floating_app():
                print("\n❌ Failed to start floating desktop application")
                print("🌐 You can still use the web interface at http://127.0.0.1:8000")
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
            signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())
            
            self.is_running = True
            
            # Display status
            self.display_status()
            
            # Wait for shutdown
            self.wait_for_shutdown()
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
        finally:
            self.shutdown()

def main():
    """Main entry point."""
    launcher = CompleteDesktopLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
