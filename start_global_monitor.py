#!/usr/bin/env python3
"""
Launcher for Global Real-time Search Monitor
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    print("🌍 Global Real-time Search Monitor")
    print("=" * 60)
    print("🎯 This app monitors your typing in ANY application!")
    print()
    print("✨ Features:")
    print("  • Type in Notepad, Word, VS Code, any text editor")
    print("  • Watch your typing appear in the search app")
    print("  • Get instant suggestions as you type each letter")
    print("  • Press SPACEBAR to clear and start new word")
    print("  • Double-click results to copy to clipboard")
    print()
    print("⚠️  Note: You may need to run as administrator for global monitoring")
    print("=" * 60)
    print()
    
    try:
        from global_monitor_app import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install keyboard pyperclip")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
