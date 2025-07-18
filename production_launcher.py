#!/usr/bin/env python3
"""
Production-Ready Launcher for Semantic Search Assistant.
Handles all edge cases, dependency checking, and graceful error recovery.
"""

import os
import sys
import subprocess
import time
import signal
import logging
import json
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import queue
import psutil

# Setup logging with UTF-8 encoding
import sys
import io

# Configure stdout to handle UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('semantic_search_launcher.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ProductionLauncher:
    """Production-ready launcher with comprehensive error handling."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.backend_process = None
        self.electron_process = None
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        # Configuration
        self.config = {
            'backend_port': 8000,
            'backend_host': '127.0.0.1',
            'startup_timeout': 30,
            'health_check_interval': 5,
            'max_restart_attempts': 3,
            'restart_delay': 5
        }
        
        # Process monitoring
        self.restart_attempts = 0
        self.last_restart_time = 0
        
    def check_dependencies(self) -> Dict[str, Any]:
        """Check all required dependencies."""
        logger.info("🔍 Checking dependencies...")
        
        results = {
            'python': self._check_python(),
            'python_packages': self._check_python_packages(),
            'node': self._check_node(),
            'electron_app': self._check_electron_app(),
            'data_directories': self._check_data_directories(),
            'port_availability': self._check_port_availability()
        }
        
        all_good = all(result['status'] for result in results.values())
        
        if all_good:
            logger.info("✅ All dependencies satisfied")
        else:
            logger.warning("⚠️ Some dependencies missing or have issues")
            
        return {'all_satisfied': all_good, 'details': results}
    
    def _check_python(self) -> Dict[str, Any]:
        """Check Python version and availability."""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                return {
                    'status': True,
                    'version': f"{version.major}.{version.minor}.{version.micro}",
                    'message': 'Python version OK'
                }
            else:
                return {
                    'status': False,
                    'version': f"{version.major}.{version.minor}.{version.micro}",
                    'message': 'Python 3.8+ required'
                }
        except Exception as e:
            return {'status': False, 'message': f'Python check failed: {e}'}
    
    def _check_python_packages(self) -> Dict[str, Any]:
        """Check required Python packages."""
        required_packages = [
            'fastapi', 'uvicorn', 'lancedb', 'sentence_transformers',
            'PyPDF2', 'python-docx', 'watchdog', 'psutil'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
        
        if not missing:
            return {'status': True, 'message': 'All Python packages available'}
        else:
            return {
                'status': False,
                'missing': missing,
                'message': f'Missing packages: {", ".join(missing)}'
            }
    
    def _check_node(self) -> Dict[str, Any]:
        """Check Node.js availability."""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                return {'status': True, 'version': version, 'message': 'Node.js available'}
            else:
                return {'status': False, 'message': 'Node.js not found'}
        except FileNotFoundError:
            return {'status': False, 'message': 'Node.js not installed'}
    
    def _check_electron_app(self) -> Dict[str, Any]:
        """Check Electron app configuration."""
        electron_dir = self.app_dir / "electron-app"
        package_json = electron_dir / "package.json"
        node_modules = electron_dir / "node_modules"
        
        if not electron_dir.exists():
            return {'status': False, 'message': 'Electron app directory not found'}
        
        if not package_json.exists():
            return {'status': False, 'message': 'package.json not found'}
        
        return {
            'status': True,
            'dependencies_installed': node_modules.exists(),
            'message': 'Electron app configured'
        }
    
    def _check_data_directories(self) -> Dict[str, Any]:
        """Check and create necessary data directories."""
        directories = ['data', 'logs', 'cache']
        created = []
        
        for dir_name in directories:
            dir_path = self.app_dir / dir_name
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created.append(dir_name)
                except Exception as e:
                    return {'status': False, 'message': f'Failed to create {dir_name}: {e}'}
        
        message = 'Data directories OK'
        if created:
            message += f' (created: {", ".join(created)})'
            
        return {'status': True, 'message': message}
    
    def _check_port_availability(self) -> Dict[str, Any]:
        """Check if the backend port is available."""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.config['backend_host'], self.config['backend_port']))
                return {'status': True, 'message': f'Port {self.config["backend_port"]} available'}
        except OSError:
            # Check if our own process is using the port
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            return {
                                'status': True,
                                'message': f'Port {self.config["backend_port"]} in use by our backend'
                            }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception:
                pass  # Ignore psutil errors
            
            return {
                'status': False,
                'message': f'Port {self.config["backend_port"]} in use by another process'
            }
    
    def install_missing_dependencies(self, dependency_check: Dict[str, Any]) -> bool:
        """Attempt to install missing dependencies."""
        logger.info("🔧 Installing missing dependencies...")
        
        details = dependency_check['details']
        
        # Install missing Python packages
        python_packages = details.get('python_packages', {})
        if not python_packages.get('status', True):
            missing = python_packages.get('missing', [])
            if missing:
                logger.info(f"📦 Installing Python packages: {', '.join(missing)}")
                try:
                    subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '--upgrade'
                    ] + missing, check=True)
                    logger.info("✅ Python packages installed")
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Failed to install Python packages: {e}")
                    return False
        
        # Install Electron dependencies
        electron_app = details.get('electron_app', {})
        if electron_app.get('status') and not electron_app.get('dependencies_installed'):
            electron_dir = self.app_dir / "electron-app"
            if electron_dir.exists() and details.get('node', {}).get('status'):
                logger.info("📦 Installing Electron dependencies...")
                try:
                    subprocess.run(['npm', 'install'], cwd=electron_dir, check=True)
                    logger.info("✅ Electron dependencies installed")
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Failed to install Electron dependencies: {e}")
                    return False
        
        return True
    
    def start_backend(self) -> bool:
        """Start the backend server."""
        logger.info("🚀 Starting backend server...")
        
        try:
            # Start the backend process
            backend_script = self.app_dir / "main.py"
            if not backend_script.exists():
                logger.error("❌ Backend script not found")
                return False
            
            self.backend_process = subprocess.Popen([
                sys.executable, str(backend_script)
            ], cwd=self.app_dir)
            
            # Wait for backend to start
            if self._wait_for_backend():
                logger.info("✅ Backend server started successfully")
                return True
            else:
                logger.error("❌ Backend failed to start within timeout")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            return False
    
    def _wait_for_backend(self) -> bool:
        """Wait for backend to become ready."""
        import requests
        
        url = f"http://{self.config['backend_host']}:{self.config['backend_port']}/health"
        
        for attempt in range(self.config['startup_timeout']):
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(1)
            
            # Check if process is still running
            if self.backend_process and self.backend_process.poll() is not None:
                logger.error("❌ Backend process terminated unexpectedly")
                return False
        
        return False
    
    def start_electron_app(self) -> bool:
        """Start the Electron desktop application."""
        logger.info("🖥️ Starting desktop application...")
        
        electron_dir = self.app_dir / "electron-app"
        
        if not electron_dir.exists():
            logger.warning("⚠️ Electron app not found, using web interface")
            return False
        
        try:
            self.electron_process = subprocess.Popen([
                'npm', 'start'
            ], cwd=electron_dir)
            
            logger.info("✅ Desktop application started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start desktop app: {e}")
            return False
    
    def open_web_interface(self):
        """Open the web interface as fallback."""
        logger.info("🌐 Opening web interface...")
        
        url = f"http://{self.config['backend_host']}:{self.config['backend_port']}"
        
        try:
            webbrowser.open(url)
            logger.info(f"✅ Web interface opened: {url}")
        except Exception as e:
            logger.error(f"❌ Failed to open web interface: {e}")
    
    def monitor_processes(self):
        """Monitor running processes and restart if needed."""
        logger.info("👁️ Starting process monitoring...")
        
        while not self.shutdown_event.is_set():
            try:
                # Check backend process
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.warning("⚠️ Backend process stopped")
                    if self._should_restart():
                        self._restart_backend()
                
                # Check electron process (less critical)
                if self.electron_process and self.electron_process.poll() is not None:
                    logger.info("ℹ️ Desktop application stopped")
                
                time.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in process monitoring: {e}")
                time.sleep(self.config['health_check_interval'])
    
    def _should_restart(self) -> bool:
        """Determine if we should attempt to restart."""
        current_time = time.time()
        
        # Reset restart attempts if enough time has passed
        if current_time - self.last_restart_time > 300:  # 5 minutes
            self.restart_attempts = 0
        
        return self.restart_attempts < self.config['max_restart_attempts']
    
    def _restart_backend(self):
        """Restart the backend process."""
        logger.info("🔄 Attempting to restart backend...")
        
        self.restart_attempts += 1
        self.last_restart_time = time.time()
        
        # Wait before restarting
        time.sleep(self.config['restart_delay'])
        
        if self.start_backend():
            logger.info("✅ Backend restarted successfully")
        else:
            logger.error("❌ Backend restart failed")
    
    def shutdown(self):
        """Gracefully shutdown all processes."""
        logger.info("🛑 Shutting down...")
        
        self.shutdown_event.set()
        
        # Stop Electron app
        if self.electron_process:
            logger.info("Stopping desktop application...")
            self.electron_process.terminate()
            try:
                self.electron_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.electron_process.kill()
        
        # Stop backend
        if self.backend_process:
            logger.info("Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        logger.info("✅ Shutdown complete")
    
    def run(self):
        """Main run method."""
        logger.info("🚀 Starting Semantic Search Assistant")
        logger.info("=" * 60)
        
        try:
            # Check dependencies
            dependency_check = self.check_dependencies()
            
            if not dependency_check['all_satisfied']:
                logger.info("🔧 Attempting to fix missing dependencies...")
                if not self.install_missing_dependencies(dependency_check):
                    logger.error("❌ Failed to install dependencies")
                    return False
            
            # Start backend
            if not self.start_backend():
                logger.error("❌ Failed to start backend")
                return False
            
            # Start desktop app or web interface
            desktop_started = self.start_electron_app()
            if not desktop_started:
                self.open_web_interface()
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
            signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())
            
            # Start monitoring in background
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            self.is_running = True
            
            logger.info("\n🎉 Semantic Search Assistant is running!")
            logger.info("=" * 60)
            logger.info("📊 Backend API: http://127.0.0.1:8000")
            if desktop_started:
                logger.info("🖥️ Desktop Application: Running")
            else:
                logger.info("🌐 Web Interface: http://127.0.0.1:8000")
            logger.info("")
            logger.info("✨ Features available:")
            logger.info("  • Context-aware floating window")
            logger.info("  • Cross-application drag & drop")
            logger.info("  • Canvas for organizing notes")
            logger.info("  • Real-time document monitoring")
            logger.info("  • Enhanced PDF highlight detection")
            logger.info("  • Readwise integration")
            logger.info("  • Citation management")
            logger.info("  • Background processing")
            logger.info("")
            logger.info("Press Ctrl+C to stop")
            
            # Keep running until shutdown
            while self.is_running and not self.shutdown_event.is_set():
                time.sleep(1)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Received shutdown signal")
            self.shutdown()
            return True
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.shutdown()
            return False

def main():
    """Main entry point."""
    launcher = ProductionLauncher()
    success = launcher.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
