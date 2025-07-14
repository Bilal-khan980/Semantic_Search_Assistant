#!/usr/bin/env python3
"""
Build script for creating a complete executable of the Semantic Search Assistant.
This script handles the entire build process including dependencies and packaging.
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=check, 
            shell=True if isinstance(cmd, str) else False,
            capture_output=True,
            text=True
        )
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

def install_python_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not in a virtual environment. Consider creating one.")
    
    # Install dependencies
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_react_app():
    """Build the React frontend."""
    print("Building React frontend...")
    
    renderer_path = Path("electron-app/src/renderer")
    
    # Install npm dependencies
    run_command(["npm", "install"], cwd=renderer_path)
    
    # Build the React app
    run_command(["npm", "run", "build"], cwd=renderer_path)

def install_electron_dependencies():
    """Install Electron dependencies."""
    print("Installing Electron dependencies...")
    
    electron_path = Path("electron-app")
    
    # Install npm dependencies
    run_command(["npm", "install"], cwd=electron_path)

def create_executable():
    """Create the executable using electron-builder."""
    print("Creating executable...")
    
    electron_path = Path("electron-app")
    
    # Build the executable
    run_command(["npm", "run", "dist"], cwd=electron_path)

def setup_test_environment():
    """Set up test environment with sample data."""
    print("Setting up test environment...")
    
    # Ensure test_docs directory exists
    test_docs = Path("test_docs")
    test_docs.mkdir(exist_ok=True)
    
    # Create sample documents if they don't exist
    sample_files = [
        ("sample_document.txt", "This is a sample document for testing the semantic search functionality."),
        ("another_sample.md", "# Another Sample\n\nThis is another sample document with markdown formatting."),
    ]
    
    for filename, content in sample_files:
        file_path = test_docs / filename
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

def verify_build():
    """Verify that the build was successful."""
    print("Verifying build...")
    
    dist_path = Path("electron-app/dist")
    if not dist_path.exists():
        print("Error: Distribution directory not found!")
        return False
    
    # Check for executable files
    exe_files = list(dist_path.glob("*.exe")) + list(dist_path.glob("*.dmg")) + list(dist_path.glob("*.AppImage"))
    
    if exe_files:
        print(f"Build successful! Executable found: {exe_files[0]}")
        print(f"Full path: {exe_files[0].absolute()}")
        return True
    else:
        print("Error: No executable file found in distribution directory!")
        return False

def main():
    """Main build process."""
    print("Starting build process for Semantic Search Assistant...")
    
    # Change to the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    try:
        # Step 1: Install Python dependencies
        install_python_dependencies()
        
        # Step 2: Set up test environment
        setup_test_environment()
        
        # Step 3: Build React app
        build_react_app()
        
        # Step 4: Install Electron dependencies
        install_electron_dependencies()
        
        # Step 5: Create executable
        create_executable()
        
        # Step 6: Verify build
        if verify_build():
            print("\n" + "="*50)
            print("BUILD COMPLETED SUCCESSFULLY!")
            print("="*50)
            print("\nYour executable is ready in the electron-app/dist directory.")
            print("You can now run the application by double-clicking the executable.")
        else:
            print("\nBuild completed but verification failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
