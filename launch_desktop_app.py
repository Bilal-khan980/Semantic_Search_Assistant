#!/usr/bin/env python3
"""
Complete Desktop Application Launcher for Semantic Search Assistant.
Builds and launches the full desktop application with all features.
"""

import os
import sys
import subprocess
import time
import logging
import signal
import threading
from pathlib import Path
import webbrowser
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DesktopAppLauncher:
    """Complete desktop application launcher."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.electron_dir = self.app_dir / "electron-app"
        self.backend_process = None
        self.electron_process = None
        self.is_running = False
        
    def check_node_js(self):
        """Check if Node.js is available."""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Node.js found: {version}")
                return True
            else:
                logger.error("Node.js not found")
                return False
        except FileNotFoundError:
            logger.error("Node.js not installed")
            return False
    
    def check_npm(self):
        """Check if npm is available."""
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"npm found: {version}")
                return True
            else:
                logger.error("npm not found")
                return False
        except FileNotFoundError:
            logger.error("npm not installed")
            return False
    
    def install_electron_dependencies(self):
        """Install Electron app dependencies."""
        if not self.electron_dir.exists():
            logger.error("Electron app directory not found")
            return False
        
        logger.info("Installing Electron dependencies...")
        try:
            result = subprocess.run(
                ['npm', 'install'], 
                cwd=self.electron_dir, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("Electron dependencies installed successfully")
                return True
            else:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("npm install timed out")
            return False
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
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
            time.sleep(5)
            
            if self.backend_process.poll() is None:
                logger.info("Backend server started successfully")
                return True
            else:
                logger.error("Backend process terminated unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def start_electron_app(self):
        """Start the Electron desktop application."""
        logger.info("Starting Electron desktop application...")
        
        try:
            # Check if dependencies are installed
            node_modules = self.electron_dir / "node_modules"
            if not node_modules.exists():
                logger.info("Node modules not found, installing...")
                if not self.install_electron_dependencies():
                    return False
            
            # Start Electron app
            self.electron_process = subprocess.Popen(
                ['npm', 'start'], 
                cwd=self.electron_dir
            )
            
            # Wait a moment to see if it starts successfully
            time.sleep(3)
            
            if self.electron_process.poll() is None:
                logger.info("Electron desktop application started successfully")
                return True
            else:
                logger.error("Electron process terminated unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Electron app: {e}")
            return False
    
    def wait_for_backend(self):
        """Wait for backend to be ready."""
        import requests
        
        for attempt in range(30):  # 30 second timeout
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=1)
                if response.status_code == 200:
                    logger.info("Backend is ready")
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(1)
        
        logger.warning("Backend health check timed out")
        return False
    
    def display_status(self):
        """Display the application status."""
        print("\n" + "=" * 80)
        print("           SEMANTIC SEARCH ASSISTANT - DESKTOP APPLICATION")
        print("=" * 80)
        print("🚀 Status: RUNNING")
        print("")
        print("🖥️  Desktop Application: Active")
        print("📊 Backend API:         http://127.0.0.1:8000")
        print("🌐 Web Interface:       http://127.0.0.1:8000")
        print("📚 API Documentation:   http://127.0.0.1:8000/docs")
        print("")
        print("✨ FEATURES ACTIVE:")
        print("  • Context-aware floating window")
        print("  • Cross-application drag & drop")
        print("  • Canvas for organizing notes (SUBLIME-like)")
        print("  • Real-time document monitoring")
        print("  • Enhanced PDF highlight detection")
        print("  • Advanced Readwise integration")
        print("  • Citation management system")
        print("  • Background processing with progress")
        print("  • Global keyboard shortcuts")
        print("")
        print("⌨️  GLOBAL SHORTCUTS:")
        print("  • Ctrl+Shift+Space  - Toggle floating window")
        print("  • Ctrl+Alt+F        - Focus search")
        print("  • Ctrl+Shift+S      - Quick search with clipboard")
        print("  • Ctrl+Shift+C      - Switch to canvas view")
        print("  • Ctrl+Shift+A      - Add selection to canvas")
        print("  • Ctrl+Shift+X      - Show context suggestions")
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
        logger.info("Shutting down desktop application...")
        self.is_running = False
        
        # Stop Electron app
        if self.electron_process:
            logger.info("Stopping Electron application...")
            self.electron_process.terminate()
            try:
                self.electron_process.wait(timeout=10)
                logger.info("Electron application stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Force killing Electron process")
                self.electron_process.kill()
        
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
        print("🚀 Starting Semantic Search Assistant Desktop Application")
        print("=" * 80)
        
        try:
            # Check Node.js and npm
            if not self.check_node_js():
                print("\n❌ Node.js is required for the desktop application.")
                print("📥 Please install Node.js from: https://nodejs.org")
                print("🌐 Alternatively, you can use the web interface:")
                print("   python final_launcher.py")
                return False
            
            if not self.check_npm():
                print("\n❌ npm is required for the desktop application.")
                return False
            
            # Start backend
            if not self.start_backend():
                print("\n❌ Failed to start backend server")
                return False
            
            # Wait for backend to be ready
            if not self.wait_for_backend():
                print("\n⚠️ Backend health check failed, but continuing...")
            
            # Start Electron app
            if not self.start_electron_app():
                print("\n❌ Failed to start desktop application")
                print("🌐 Opening web interface as fallback...")
                webbrowser.open("http://127.0.0.1:8000")
            
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
    launcher = DesktopAppLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
