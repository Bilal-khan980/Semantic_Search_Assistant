#!/usr/bin/env python3
"""
Complete Semantic Search Assistant Launcher
Starts both the Python backend and Electron frontend with all features enabled.
"""

import asyncio
import subprocess
import sys
import os
import time
import logging
import signal
import platform
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticSearchLauncher:
    """Complete application launcher with all features."""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        
    def check_dependencies(self):
        """Check if all required dependencies are available."""
        logger.info("Checking dependencies...")
        
        # Check Python dependencies
        python_deps = [
            'lancedb', 'sentence_transformers', 'PyMuPDF', 'fastapi', 
            'uvicorn', 'pynput', 'psutil'
        ]
        
        missing_deps = []
        for dep in python_deps:
            try:
                __import__(dep.replace('-', '_'))
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            logger.error(f"Missing Python dependencies: {', '.join(missing_deps)}")
            logger.info("Install with: pip install " + " ".join(missing_deps))
            return False
        
        # Check Node.js and npm
        try:
            subprocess.run(['node', '--version'], check=True, capture_output=True)
            subprocess.run(['npm', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Node.js and npm are required for the Electron frontend")
            return False
        
        logger.info("✅ All dependencies are available")
        return True
    
    def setup_environment(self):
        """Setup the application environment."""
        logger.info("Setting up environment...")
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Install Node.js dependencies if needed
        electron_dir = Path("electron-app")
        if electron_dir.exists():
            node_modules = electron_dir / "node_modules"
            if not node_modules.exists():
                logger.info("Installing Electron dependencies...")
                try:
                    subprocess.run(['npm', 'install'], cwd=electron_dir, check=True)
                    logger.info("✅ Electron dependencies installed")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install Electron dependencies: {e}")
                    return False
        
        return True
    
    def start_backend(self):
        """Start the Python backend server."""
        logger.info("Starting Python backend...")
        
        try:
            # Start the FastAPI server
            self.backend_process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 
                'api_service:app',
                '--host', '127.0.0.1',
                '--port', '8000',
                '--reload'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Check if the process is still running
            if self.backend_process.poll() is None:
                logger.info("✅ Backend server started on http://127.0.0.1:8000")
                return True
            else:
                logger.error("Backend server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the Electron frontend."""
        logger.info("Starting Electron frontend...")
        
        electron_dir = Path("electron-app")
        if not electron_dir.exists():
            logger.error("Electron app directory not found")
            return False
        
        try:
            # Start Electron
            self.frontend_process = subprocess.Popen([
                'npm', 'start'
            ], cwd=electron_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for Electron to start
            time.sleep(2)
            
            # Check if the process is still running
            if self.frontend_process.poll() is None:
                logger.info("✅ Electron frontend started")
                return True
            else:
                logger.error("Electron frontend failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return False
    
    def run_integration_tests(self):
        """Run integration tests to verify everything is working."""
        logger.info("Running integration tests...")
        
        try:
            result = subprocess.run([
                sys.executable, 'integration_test.py'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("✅ Integration tests passed")
                return True
            else:
                logger.warning("⚠️ Some integration tests failed")
                logger.info("Check the test output for details")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("Integration tests timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to run integration tests: {e}")
            return False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping application...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Windows doesn't have SIGQUIT
        if platform.system() != 'Windows':
            signal.signal(signal.SIGQUIT, signal_handler)
    
    def stop(self):
        """Stop all processes."""
        logger.info("Stopping Semantic Search Assistant...")
        self.running = False
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                logger.info("✅ Frontend stopped")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                logger.info("⚠️ Frontend force-killed")
            except Exception as e:
                logger.warning(f"Error stopping frontend: {e}")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                logger.info("✅ Backend stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                logger.info("⚠️ Backend force-killed")
            except Exception as e:
                logger.warning(f"Error stopping backend: {e}")
    
    def run(self, run_tests=False):
        """Run the complete application."""
        logger.info("🚀 Starting Semantic Search Assistant...")
        logger.info("=" * 60)
        
        try:
            # Check dependencies
            if not self.check_dependencies():
                return False
            
            # Setup environment
            if not self.setup_environment():
                return False
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Start backend
            if not self.start_backend():
                return False
            
            # Start frontend
            if not self.start_frontend():
                self.stop()
                return False
            
            # Run integration tests if requested
            if run_tests:
                time.sleep(5)  # Give everything time to fully start
                self.run_integration_tests()
            
            self.running = True
            
            logger.info("=" * 60)
            logger.info("🎉 Semantic Search Assistant is running!")
            logger.info("📱 Frontend: Electron app should open automatically")
            logger.info("🔧 Backend API: http://127.0.0.1:8000")
            logger.info("📚 API Docs: http://127.0.0.1:8000/docs")
            logger.info("⌨️  Global shortcuts:")
            logger.info("   - Ctrl+Shift+Space: Toggle floating window")
            logger.info("   - Ctrl+Alt+F: Focus search")
            logger.info("   - Ctrl+Shift+V: Smart paste")
            logger.info("=" * 60)
            logger.info("Press Ctrl+C to stop the application")
            
            # Keep running until stopped
            try:
                while self.running:
                    time.sleep(1)
                    
                    # Check if processes are still running
                    if self.backend_process and self.backend_process.poll() is not None:
                        logger.error("Backend process died unexpectedly")
                        break
                    
                    if self.frontend_process and self.frontend_process.poll() is not None:
                        logger.info("Frontend process closed")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
            
            return True
            
        except Exception as e:
            logger.error(f"Application failed: {e}")
            return False
        finally:
            self.stop()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Semantic Search Assistant Launcher')
    parser.add_argument('--test', action='store_true', 
                       help='Run integration tests after starting')
    parser.add_argument('--test-only', action='store_true',
                       help='Run integration tests only (no GUI)')
    
    args = parser.parse_args()
    
    launcher = SemanticSearchLauncher()
    
    if args.test_only:
        # Run tests only
        success = launcher.run_integration_tests()
        sys.exit(0 if success else 1)
    else:
        # Run the complete application
        success = launcher.run(run_tests=args.test)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
