#!/usr/bin/env python3
"""
Build script for the Semantic Search Assistant desktop application.
Builds the React frontend and prepares the Electron app.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_node_npm():
    """Check if Node.js and npm are installed."""
    try:
        node_result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        npm_result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        
        print(f"✅ Node.js version: {node_result.stdout.strip()}")
        print(f"✅ npm version: {npm_result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Node.js and/or npm not found. Please install Node.js from https://nodejs.org/")
        return False

def build_react_app(app_dir):
    """Build the React renderer application."""
    renderer_dir = app_dir / "electron-app" / "src" / "renderer"
    
    if not renderer_dir.exists():
        print(f"❌ Renderer directory not found: {renderer_dir}")
        return False
    
    print("📦 Building React renderer application...")
    
    # Install dependencies if node_modules doesn't exist
    node_modules = renderer_dir / "node_modules"
    if not node_modules.exists():
        print("📥 Installing React dependencies...")
        run_command(['npm', 'install'], cwd=renderer_dir)
    
    # Build the React app
    print("🔨 Building React app...")
    run_command(['npm', 'run', 'build'], cwd=renderer_dir)
    
    # Check if build was successful
    build_dir = renderer_dir / "build"
    if build_dir.exists() and (build_dir / "index.html").exists():
        print("✅ React app built successfully!")
        return True
    else:
        print("❌ React app build failed!")
        return False

def setup_electron_app(app_dir):
    """Set up the Electron application."""
    electron_dir = app_dir / "electron-app"
    
    if not electron_dir.exists():
        print(f"❌ Electron directory not found: {electron_dir}")
        return False
    
    print("⚡ Setting up Electron application...")
    
    # Install Electron dependencies if node_modules doesn't exist
    node_modules = electron_dir / "node_modules"
    if not node_modules.exists():
        print("📥 Installing Electron dependencies...")
        run_command(['npm', 'install'], cwd=electron_dir)
    
    print("✅ Electron app setup complete!")
    return True

def create_start_script(app_dir):
    """Create an optimized start script."""
    start_script_content = '''#!/usr/bin/env python3
"""
Optimized launcher for Semantic Search Assistant desktop application.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    print("🚀 Starting Semantic Search Assistant Desktop Application...")
    
    app_dir = Path(__file__).parent
    
    # Start the backend
    backend_script = app_dir / "start_backend.py"
    print(f"📊 Starting backend from: {backend_script}")
    
    try:
        # Start backend process
        backend_process = subprocess.Popen([
            sys.executable, str(backend_script)
        ], cwd=app_dir)
        
        # Wait for backend to start
        print("⏳ Waiting for backend to start...")
        time.sleep(3)
        
        # Start Electron desktop app
        electron_dir = app_dir / "electron-app"
        print("🖥️ Starting desktop application...")
        
        electron_process = subprocess.Popen([
            "npm", "start"
        ], cwd=electron_dir)
        
        print("✅ Desktop application started!")
        print("")
        print("🎉 Semantic Search Assistant is now running!")
        print("📊 Backend API: http://127.0.0.1:8000")
        print("🖥️ Desktop Application: Active")
        print("")
        print("✨ Features:")
        print("  • Context-aware floating window")
        print("  • Cross-application drag & drop")
        print("  • Canvas for organizing notes")
        print("  • Real-time document monitoring")
        print("  • Enhanced PDF highlight detection")
        print("  • Readwise integration")
        print("")
        print("Press Ctrl+C to stop")
        
        # Monitor both processes
        try:
            while True:
                if backend_process.poll() is not None:
                    print("❌ Backend stopped")
                    break
                if electron_process.poll() is not None:
                    print("❌ Desktop app stopped")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 Shutting down...")
            
            print("Stopping desktop application...")
            electron_process.terminate()
            try:
                electron_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                electron_process.kill()
            
            print("Stopping backend...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
            
            print("✅ Shutdown complete")
            
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    start_script_path = app_dir / "start_desktop_app.py"
    with open(start_script_path, 'w', encoding='utf-8') as f:
        f.write(start_script_content)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod(start_script_path, 0o755)
    
    print(f"✅ Created optimized start script: {start_script_path}")

def create_desktop_batch_file(app_dir):
    """Create a Windows batch file for easy desktop app launching."""
    batch_content = '''@echo off
echo 🚀 Starting Semantic Search Assistant Desktop Application...
python start_desktop_app.py
pause
'''
    
    batch_path = app_dir / "start_desktop_app.bat"
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Created desktop batch file: {batch_path}")

def main():
    """Main build function."""
    print("🔧 Building Semantic Search Assistant Desktop Application")
    print("=" * 60)
    
    # Get the app directory
    app_dir = Path(__file__).parent
    
    # Check prerequisites
    if not check_node_npm():
        return False
    
    # Build React app
    if not build_react_app(app_dir):
        return False
    
    # Setup Electron app
    if not setup_electron_app(app_dir):
        return False
    
    # Create optimized start scripts
    create_start_script(app_dir)
    create_desktop_batch_file(app_dir)
    
    print("")
    print("🎉 Build completed successfully!")
    print("=" * 60)
    print("📋 Next steps:")
    print("  1. Run 'start_desktop_app.bat' (Windows) or 'python start_desktop_app.py' to launch")
    print("  2. The desktop application will start automatically")
    print("  3. Use the floating window for context-aware search")
    print("  4. Drag and drop results to any application")
    print("")
    print("🔧 For development:")
    print("  • Backend: python start_backend.py")
    print("  • Frontend: cd electron-app && npm start")
    print("")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
