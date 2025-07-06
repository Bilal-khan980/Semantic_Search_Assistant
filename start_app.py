#!/usr/bin/env python3
"""
Complete application startup script for Semantic Search Assistant.
Starts both the Python backend and Electron frontend.
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SemanticSearchApp:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.app_dir = Path(__file__).parent
        self.electron_dir = self.app_dir / "electron-app"
        
    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        logger.info("Checking dependencies...")
        
        # Check Python dependencies
        try:
            import lancedb
            import sentence_transformers
            import fastapi
            logger.info("✓ Python dependencies found")
        except ImportError as e:
            logger.error(f"✗ Missing Python dependency: {e}")
            logger.info("Please run: pip install -r requirements.txt")
            return False
        
        # Check if Node.js is available
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Node.js found: {result.stdout.strip()}")
            else:
                logger.error("✗ Node.js not found")
                return False
        except FileNotFoundError:
            logger.error("✗ Node.js not found")
            return False
        
        # Check if Electron app is built
        if not (self.electron_dir / "node_modules").exists():
            logger.warning("⚠ Electron dependencies not installed")
            logger.info("Installing Electron dependencies...")
            try:
                subprocess.run(['npm', 'install'], 
                             cwd=self.electron_dir, check=True)
                logger.info("✓ Electron dependencies installed")
            except subprocess.CalledProcessError:
                logger.error("✗ Failed to install Electron dependencies")
                return False
        
        return True
    
    def start_backend(self):
        """Start the Python backend server."""
        logger.info("Starting Python backend...")
        
        try:
            # Start the FastAPI server
            self.backend_process = subprocess.Popen([
                sys.executable, 'start_server.py'
            ], cwd=self.app_dir)
            
            # Wait for backend to start
            logger.info("Waiting for backend to start...")
            time.sleep(5)
            
            # Check if backend is running
            if self.backend_process.poll() is None:
                logger.info("✓ Backend started successfully")
                return True
            else:
                logger.error("✗ Backend failed to start")
                return False
                
        except Exception as e:
            logger.error(f"✗ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the Electron frontend."""
        logger.info("Starting Electron frontend...")

        try:
            # Check if build directory exists
            build_dir = self.electron_dir / "src" / "renderer" / "build"

            if not build_dir.exists():
                logger.info("Build directory not found, but HTML files should be there...")

            # Start Electron directly
            self.frontend_process = subprocess.Popen([
                'npx', 'electron', '.'
            ], cwd=self.electron_dir)

            logger.info("✓ Frontend started successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to start frontend: {e}")
            logger.info("Trying alternative startup method...")
            try:
                # Alternative: use npm start
                self.frontend_process = subprocess.Popen([
                    'npm', 'start'
                ], cwd=self.electron_dir)
                logger.info("✓ Frontend started with npm start")
                return True
            except Exception as e2:
                logger.error(f"✗ Alternative startup also failed: {e2}")
                return False
    
    def stop_processes(self):
        """Stop all running processes."""
        logger.info("Stopping application...")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                logger.info("✓ Frontend stopped")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                logger.info("✓ Frontend force stopped")
            except Exception as e:
                logger.error(f"Error stopping frontend: {e}")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                logger.info("✓ Backend stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                logger.info("✓ Backend force stopped")
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
    
    def run(self):
        """Run the complete application."""
        logger.info("Starting Semantic Search Assistant...")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("Dependency check failed. Exiting.")
            return 1
        
        try:
            # Start backend
            if not self.start_backend():
                logger.error("Failed to start backend. Exiting.")
                return 1
            
            # Start frontend
            if not self.start_frontend():
                logger.error("Failed to start frontend. Exiting.")
                self.stop_processes()
                return 1
            
            logger.info("🚀 Semantic Search Assistant is running!")
            logger.info("Backend: http://localhost:8000")
            logger.info("Frontend: Electron app should open automatically")
            logger.info("Press Ctrl+C to stop")
            
            # Wait for processes
            try:
                while True:
                    # Check if processes are still running
                    if self.backend_process.poll() is not None:
                        logger.error("Backend process died unexpectedly")
                        break
                    
                    if self.frontend_process.poll() is not None:
                        logger.info("Frontend process ended")
                        break
                    
                    time.sleep(1)
            
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
            
        finally:
            self.stop_processes()
        
        logger.info("Application stopped")
        return 0

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    logger.info("Received signal, shutting down...")
    sys.exit(0)

def main():
    """Main entry point."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run app
    app = SemanticSearchApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
