#!/usr/bin/env python3
"""
Simple Launcher for Semantic Search Assistant.
Works without Node.js and focuses on core functionality.
"""

import asyncio
import logging
import sys
import time
import webbrowser
from pathlib import Path
import subprocess
import signal
import threading

# Setup simple logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleLauncher:
    """Simple launcher focusing on core backend functionality."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.backend_process = None
        self.is_running = False
        
    def check_python_dependencies(self):
        """Check if required Python packages are available."""
        logger.info("Checking Python dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'lancedb', 'sentence_transformers',
            'PyPDF2', 'watchdog', 'psutil'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
        
        if missing:
            logger.warning(f"Missing packages: {', '.join(missing)}")
            logger.info("Installing missing packages...")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--upgrade'
                ] + missing, check=True)
                logger.info("Packages installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install packages: {e}")
                return False
        else:
            logger.info("All Python dependencies satisfied")
            return True
    
    def start_backend(self):
        """Start the backend server."""
        logger.info("Starting backend server...")
        
        try:
            # Start the backend using the API service directly
            api_script = self.app_dir / "api_service.py"
            if api_script.exists():
                self.backend_process = subprocess.Popen([
                    sys.executable, str(api_script)
                ], cwd=self.app_dir)
            else:
                # Fallback to main.py
                main_script = self.app_dir / "main.py"
                self.backend_process = subprocess.Popen([
                    sys.executable, str(main_script)
                ], cwd=self.app_dir)
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Check if process is still running
            if self.backend_process.poll() is None:
                logger.info("Backend server started successfully")
                return True
            else:
                logger.error("Backend process terminated unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def open_web_interface(self):
        """Open the web interface."""
        logger.info("Opening web interface...")
        
        url = "http://127.0.0.1:8000"
        
        try:
            webbrowser.open(url)
            logger.info(f"Web interface opened: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open web interface: {e}")
            return False
    
    def wait_for_shutdown(self):
        """Wait for user to stop the application."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("SEMANTIC SEARCH ASSISTANT IS RUNNING")
        logger.info("=" * 60)
        logger.info("Backend API: http://127.0.0.1:8000")
        logger.info("Web Interface: http://127.0.0.1:8000")
        logger.info("")
        logger.info("Features available:")
        logger.info("  - Local document processing and indexing")
        logger.info("  - Advanced semantic search with ranking")
        logger.info("  - Real-time document monitoring")
        logger.info("  - Enhanced PDF highlight detection")
        logger.info("  - Readwise integration")
        logger.info("  - Citation management system")
        logger.info("  - Background processing with progress")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
    
    def shutdown(self):
        """Shutdown the application."""
        logger.info("Shutting down...")
        self.is_running = False
        
        if self.backend_process:
            logger.info("Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        logger.info("Shutdown complete")
    
    def run(self):
        """Main run method."""
        logger.info("Starting Semantic Search Assistant")
        logger.info("=" * 60)
        
        try:
            # Check dependencies
            if not self.check_python_dependencies():
                logger.error("Failed to install dependencies")
                return False
            
            # Start backend
            if not self.start_backend():
                logger.error("Failed to start backend")
                return False
            
            # Open web interface
            self.open_web_interface()
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
            signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())
            
            self.is_running = True
            
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
    launcher = SimpleLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
