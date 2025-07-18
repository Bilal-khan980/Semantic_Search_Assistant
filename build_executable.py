#!/usr/bin/env python3
"""
Build desktop executable for Real-time Semantic Search Assistant.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def create_executable():
    """Create the executable using PyInstaller."""
    print("🔨 Building executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "SemanticSearchAssistant",
        "--icon", "icon.ico" if Path("icon.ico").exists() else None,
        "--add-data", "web;web",
        "--add-data", "config.json;.",
        "--add-data", "requirements.txt;.",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "keyboard",
        "--hidden-import", "pyperclip",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32con",
        "--hidden-import", "sentence_transformers",
        "--hidden-import", "lancedb",
        "--collect-all", "sentence_transformers",
        "--collect-all", "transformers",
        "--collect-all", "torch",
        "realtime_search_app.py"
    ]
    
    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build executable: {e}")
        return False

def create_portable_package():
    """Create a portable package with all necessary files."""
    print("📦 Creating portable package...")
    
    # Create package directory
    package_dir = Path("SemanticSearchAssistant_Portable")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    exe_path = Path("dist/SemanticSearchAssistant.exe")
    if exe_path.exists():
        shutil.copy2(exe_path, package_dir / "SemanticSearchAssistant.exe")
    
    # Copy essential files
    essential_files = [
        "config.json",
        "requirements.txt",
        "DEPLOYMENT_GUIDE.md"
    ]
    
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, package_dir / file)
    
    # Copy web directory
    if Path("web").exists():
        shutil.copytree("web", package_dir / "web")
    
    # Copy test_docs directory
    if Path("test_docs").exists():
        shutil.copytree("test_docs", package_dir / "test_docs")
    
    # Create README for portable package
    readme_content = """# Semantic Search Assistant - Portable Version

## Quick Start

1. Double-click `SemanticSearchAssistant.exe` to start the application
2. Click "Start Monitoring" to begin real-time text monitoring
3. Open any text editor and start typing
4. Each letter you type will trigger a search in your indexed documents
5. Press SPACEBAR to clear the search and start a new word
6. Double-click any search result to copy it to clipboard

## Adding Documents

1. Click "Add Documents" to select files for indexing
2. Supported formats: TXT, PDF, DOCX, MD
3. Documents will be processed and indexed automatically

## Features

- ⌨️  Real-time typing monitoring across all text applications
- 🔍 Letter-by-letter search with instant results
- 📋 One-click copy to clipboard
- 🌐 Web interface available at http://127.0.0.1:8000/static/app.html
- 🔒 100% local processing - no data sent to external servers

## Troubleshooting

- If the app doesn't start, run as administrator
- Make sure no antivirus is blocking the executable
- Check that port 8000 is not in use by another application

Enjoy your real-time semantic search experience! 🚀
"""
    
    with open(package_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✅ Portable package created: {package_dir}")
    return True

def cleanup_build_files():
    """Clean up build artifacts."""
    print("🧹 Cleaning up build files...")
    
    cleanup_dirs = ["build", "__pycache__"]
    cleanup_files = ["*.spec"]
    
    for dir_name in cleanup_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    # Remove .spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"   Removed {spec_file}")

def main():
    """Main build process."""
    print("🚀 Building Real-time Semantic Search Assistant Executable")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("realtime_search_app.py").exists():
        print("❌ realtime_search_app.py not found. Please run this script from the project directory.")
        return False
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Create executable
    if not create_executable():
        return False
    
    # Create portable package
    if not create_portable_package():
        return False
    
    # Cleanup
    cleanup_build_files()
    
    print("\n" + "=" * 60)
    print("🎉 BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📁 Your executable is ready in: SemanticSearchAssistant_Portable/")
    print("🚀 Run SemanticSearchAssistant.exe to start the application")
    print("\n✨ Features included:")
    print("   • Real-time typing monitoring")
    print("   • Letter-by-letter search")
    print("   • Spacebar clearing")
    print("   • Web interface")
    print("   • Document indexing")
    print("   • Clipboard integration")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
