#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary testing and development files.
Keeps only the essential files for the real-time search application.
"""

import os
import shutil
from pathlib import Path

def cleanup_files():
    """Remove unnecessary files and directories."""
    
    # Files to remove (testing and development files)
    files_to_remove = [
        # Testing files
        "test_integration.py",
        "test_system.py",
        "debug_database.py",
        
        # Development launchers (keep only the main ones)
        "final_launcher.py",
        "launch_complete_desktop.py",
        "launch_desktop_app.py",
        "simple_launcher.py",
        "semantic_search_launcher.py",
        "start_complete_system.py",
        
        # Alternative floating apps (keep only the main one)
        "desktop_floating_app.py",
        "real_time_floating_app.py",
        "simple_floating_app.py",
        
        # Alternative monitoring files (we have our new app.py)
        "realtime_monitor.py",
        "document_monitor.py",
        "clipboard_monitor.py",
        "word_monitor.py",
        
        # Build files for other systems
        "build_app.py",
        "build_desktop_app.py",
        "create_executable.py",
        
        # Log files
        "backend.log",
        "launcher.log",
        "semantic_search_launcher.log",
        
        # Alternative README files
        "README_COMPLETE.md",
        "README_EXECUTABLE.md",
        
        # Alternative batch files
        "START_SEMANTIC_SEARCH_COMPLETE.bat",
        "start_semantic_search.bat",
        "start_semantic_search.sh",
        
        # PDF highlighter (not needed for text monitoring)
        "pdf_highlighter.py"
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "__pycache__",
        "data/vector_db",  # Will be recreated when needed
    ]
    
    print("🧹 Cleaning up unnecessary files...")
    
    removed_files = 0
    removed_dirs = 0
    
    # Remove files
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                print(f"   ✅ Removed file: {file_path}")
                removed_files += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {file_path}: {e}")
    
    # Remove directories
    for dir_path in dirs_to_remove:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
                print(f"   ✅ Removed directory: {dir_path}")
                removed_dirs += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {dir_path}: {e}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   • Removed {removed_files} files")
    print(f"   • Removed {removed_dirs} directories")
    
    return removed_files + removed_dirs > 0

def show_remaining_files():
    """Show the essential files that remain."""
    
    essential_files = {
        "Core Application": [
            "app.py",
            "run_realtime_app.py",
            "start_realtime_app.bat"
        ],
        "Backend Components": [
            "api_service.py",
            "main.py",
            "start_backend.py",
            "document_processor.py",
            "search_engine.py",
            "database.py",
            "config.py",
            "background_processor.py",
            "citation_manager.py",
            "folder_manager.py",
            "readwise_importer.py"
        ],
        "Configuration": [
            "config.json",
            "connected_folders.json",
            "requirements.txt"
        ],
        "Web Interface": [
            "web/app.html",
            "web/index.html"
        ],
        "Build Tools": [
            "build_executable.py",
            "cleanup_project.py"
        ],
        "Documentation": [
            "DEPLOYMENT_GUIDE.md"
        ],
        "Test Documents": [
            "test_docs/"
        ],
        "Data Storage": [
            "data/"
        ]
    }
    
    print("\n📁 Essential Files Remaining:")
    print("=" * 50)
    
    for category, files in essential_files.items():
        print(f"\n{category}:")
        for file in files:
            path = Path(file)
            if path.exists():
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} (missing)")

def main():
    """Main cleanup process."""
    print("🚀 Project Cleanup for Real-time Semantic Search Assistant")
    print("=" * 60)
    print("\nThis will remove unnecessary testing and development files.")
    print("Only essential files for the real-time search app will remain.")
    
    response = input("\nProceed with cleanup? (y/N): ").strip().lower()
    
    if response != 'y':
        print("Cleanup cancelled.")
        return
    
    # Perform cleanup
    success = cleanup_files()
    
    if success:
        print("\n✅ Cleanup completed successfully!")
    else:
        print("\n⚠️  No files were removed (already clean or permission issues)")
    
    # Show remaining files
    show_remaining_files()
    
    print("\n🎯 Next Steps:")
    print("1. Run: python run_realtime_app.py")
    print("2. Or use: start_realtime_app.bat")
    print("3. To build executable: python build_executable.py")

if __name__ == "__main__":
    main()
