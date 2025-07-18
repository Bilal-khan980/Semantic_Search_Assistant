
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    print("Starting Semantic Search Assistant...")
    
    # Get the directory where this script is located
    app_dir = Path(__file__).parent
    
    # Start the backend
    backend_script = app_dir / "start_backend.py"
    print(f"Starting backend from: {backend_script}")
    
    try:
        # Start backend process
        backend_process = subprocess.Popen([
            sys.executable, str(backend_script)
        ], cwd=app_dir)
        
        # Wait a moment for backend to start
        print("Waiting for backend to start...")
        time.sleep(5)

        # Start the Electron desktop application
        electron_app_dir = app_dir / "electron-app"
        electron_process = None

        if electron_app_dir.exists():
            print("Starting Electron desktop application...")
            try:
                # Check if npm is available and dependencies are installed
                package_json = electron_app_dir / "package.json"
                node_modules = electron_app_dir / "node_modules"

                if package_json.exists():
                    if not node_modules.exists():
                        print("Installing Electron dependencies...")
                        subprocess.run([
                            "npm", "install"
                        ], cwd=electron_app_dir, check=True)

                    # Start Electron app
                    electron_process = subprocess.Popen([
                        "npm", "start"
                    ], cwd=electron_app_dir)

                    print("✅ Desktop application started!")
                else:
                    print("⚠️ Electron app not properly configured, falling back to web interface")
                    raise FileNotFoundError("package.json not found")

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"⚠️ Could not start Electron app: {e}")
                print("📱 Opening web interface as fallback...")

                # Fallback to web interface
                webbrowser.open("http://127.0.0.1:8000")

                # Also open the simple web interface as backup
                web_interface_path = app_dir / "web" / "index.html"
                if web_interface_path.exists():
                    webbrowser.open(f"file:///{web_interface_path.absolute()}")
        else:
            print("⚠️ Electron app directory not found, opening web interface...")
            webbrowser.open("http://127.0.0.1:8000")

            # Also open the simple web interface as backup
            web_interface_path = app_dir / "web" / "index.html"
            if web_interface_path.exists():
                webbrowser.open(f"file:///{web_interface_path.absolute()}")

        print("\n🚀 Semantic Search Assistant is running!")
        print("📊 Backend API: http://127.0.0.1:8000")
        if electron_process:
            print("🖥️ Desktop Application: Running")
        else:
            print("🌐 Web Interface: http://127.0.0.1:8000")
        print("")
        print("✨ Features available:")
        print("  ✓ Document indexing and search")
        print("  ✓ Readwise highlights import")
        print("  ✓ Context-aware floating window")
        print("  ✓ Cross-application drag & drop")
        print("  ✓ Canvas for organizing notes")
        print("  ✓ Real-time document monitoring")
        print("  ✓ Enhanced PDF highlight detection")
        print("")
        print("Press Ctrl+C to stop")

        # Keep the launcher running and monitor both processes
        try:
            while True:
                # Check if backend is still running
                if backend_process.poll() is not None:
                    print("❌ Backend process stopped")
                    break

                # Check if electron is still running (if it was started)
                if electron_process and electron_process.poll() is not None:
                    print("❌ Desktop application stopped")
                    break

                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")

            if electron_process:
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
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
