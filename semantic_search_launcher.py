
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
        
        # Open the web interface
        print("Opening web interface...")
        webbrowser.open("http://127.0.0.1:8000")

        # Also open the simple web interface as backup
        web_interface_path = app_dir / "web" / "index.html"
        if web_interface_path.exists():
            webbrowser.open(f"file:///{web_interface_path.absolute()}")
            print(f"Backup web interface: file:///{web_interface_path.absolute()}")
        
        print("Semantic Search Assistant is running!")
        print("Backend API: http://127.0.0.1:8000")
        print("Web Interface: http://127.0.0.1:8000 (if available)")
        print(f"Local Interface: file:///{web_interface_path.absolute()}")
        print("")
        print("Features available:")
        print("✓ Document indexing and search")
        print("✓ Readwise highlights import")
        print("✓ Settings management")
        print("✓ Real-time folder monitoring")
        print("")
        print("Press Ctrl+C to stop")
        
        # Keep the launcher running
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
            backend_process.terminate()
            backend_process.wait()
            
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
