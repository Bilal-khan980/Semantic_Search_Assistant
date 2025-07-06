#!/usr/bin/env python3
"""
Build script for creating distributable Semantic Search Assistant.
Creates executables for Windows, macOS, and Linux.
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppBuilder:
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.electron_dir = self.app_dir / "electron-app"
        self.renderer_dir = self.electron_dir / "src" / "renderer"
        self.dist_dir = self.electron_dir / "dist"
        
    def clean_build(self):
        """Clean previous build artifacts."""
        logger.info("Cleaning previous builds...")
        
        # Clean React build
        react_build = self.renderer_dir / "build"
        if react_build.exists():
            shutil.rmtree(react_build)
            logger.info("✓ Cleaned React build")
        
        # Clean Electron dist
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            logger.info("✓ Cleaned Electron dist")
    
    def install_dependencies(self):
        """Install all required dependencies."""
        logger.info("Installing dependencies...")
        
        # Install Python dependencies
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], cwd=self.app_dir, check=True)
            logger.info("✓ Python dependencies installed")
        except subprocess.CalledProcessError:
            logger.error("✗ Failed to install Python dependencies")
            return False
        
        # Install Electron dependencies
        try:
            subprocess.run(['npm', 'install'], cwd=self.electron_dir, check=True)
            logger.info("✓ Electron dependencies installed")
        except subprocess.CalledProcessError:
            logger.error("✗ Failed to install Electron dependencies")
            return False
        
        # Install React dependencies
        try:
            subprocess.run(['npm', 'install'], cwd=self.renderer_dir, check=True)
            logger.info("✓ React dependencies installed")
        except subprocess.CalledProcessError:
            logger.error("✗ Failed to install React dependencies")
            return False
        
        return True
    
    def build_react_app(self):
        """Build the React frontend."""
        logger.info("Building React app...")
        
        try:
            subprocess.run(['npm', 'run', 'build'], 
                         cwd=self.renderer_dir, check=True)
            logger.info("✓ React app built successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error("✗ Failed to build React app")
            return False
    
    def build_electron_app(self):
        """Build the Electron application."""
        logger.info("Building Electron app...")
        
        try:
            subprocess.run(['npm', 'run', 'dist'], 
                         cwd=self.electron_dir, check=True)
            logger.info("✓ Electron app built successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error("✗ Failed to build Electron app")
            return False
    
    def create_portable_package(self):
        """Create a portable package with Python backend."""
        logger.info("Creating portable package...")
        
        try:
            # Create portable directory
            portable_dir = self.app_dir / "portable"
            if portable_dir.exists():
                shutil.rmtree(portable_dir)
            portable_dir.mkdir()
            
            # Copy Python backend files
            backend_files = [
                "*.py", "requirements.txt", "config.json", 
                "data", "sample_documents"
            ]
            
            for pattern in backend_files:
                for file_path in self.app_dir.glob(pattern):
                    if file_path.is_file():
                        shutil.copy2(file_path, portable_dir)
                    elif file_path.is_dir():
                        shutil.copytree(file_path, portable_dir / file_path.name, 
                                      dirs_exist_ok=True)
            
            # Copy Electron executable
            if sys.platform == "win32":
                exe_pattern = "*.exe"
            elif sys.platform == "darwin":
                exe_pattern = "*.app"
            else:
                exe_pattern = "*.AppImage"
            
            for exe_file in self.dist_dir.glob(exe_pattern):
                if exe_file.is_file():
                    shutil.copy2(exe_file, portable_dir)
                elif exe_file.is_dir():
                    shutil.copytree(exe_file, portable_dir / exe_file.name,
                                  dirs_exist_ok=True)
            
            # Create startup script
            if sys.platform == "win32":
                startup_script = portable_dir / "start.bat"
                startup_script.write_text("""@echo off
echo Starting Semantic Search Assistant...
start python start_app.py
""")
            else:
                startup_script = portable_dir / "start.sh"
                startup_script.write_text("""#!/bin/bash
echo "Starting Semantic Search Assistant..."
python3 start_app.py &
""")
                startup_script.chmod(0o755)
            
            logger.info(f"✓ Portable package created in {portable_dir}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to create portable package: {e}")
            return False
    
    def verify_build(self):
        """Verify the build was successful."""
        logger.info("Verifying build...")
        
        # Check if React build exists
        react_build = self.renderer_dir / "build"
        if not react_build.exists():
            logger.error("✗ React build not found")
            return False
        
        # Check if Electron dist exists
        if not self.dist_dir.exists() or not any(self.dist_dir.iterdir()):
            logger.error("✗ Electron dist not found or empty")
            return False
        
        logger.info("✓ Build verification passed")
        return True
    
    def build(self, clean=True, portable=True):
        """Build the complete application."""
        logger.info("🚀 Starting Semantic Search Assistant build...")
        
        try:
            if clean:
                self.clean_build()
            
            if not self.install_dependencies():
                return False
            
            if not self.build_react_app():
                return False
            
            if not self.build_electron_app():
                return False
            
            if not self.verify_build():
                return False
            
            if portable:
                if not self.create_portable_package():
                    logger.warning("⚠ Portable package creation failed")
            
            logger.info("🎉 Build completed successfully!")
            logger.info(f"📦 Distributables available in: {self.dist_dir}")
            
            if portable:
                logger.info(f"📦 Portable package available in: {self.app_dir / 'portable'}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Build failed: {e}")
            return False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Semantic Search Assistant")
    parser.add_argument("--no-clean", action="store_true", 
                       help="Skip cleaning previous builds")
    parser.add_argument("--no-portable", action="store_true",
                       help="Skip creating portable package")
    
    args = parser.parse_args()
    
    builder = AppBuilder()
    success = builder.build(
        clean=not args.no_clean,
        portable=not args.no_portable
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
