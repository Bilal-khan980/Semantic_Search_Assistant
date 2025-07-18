#!/usr/bin/env python3
"""
Simple launcher for Global Real-time Search Monitor
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    print("🌍 Simple Global Real-time Search Monitor")
    print("=" * 60)
    print("🎯 EXACTLY WHAT YOU REQUESTED:")
    print("   • Type in ANY text editor (Notepad, Word, VS Code)")
    print("   • Watch your typing appear in this search app")
    print("   • Get instant suggestions for each letter")
    print("   • Press SPACEBAR to clear and start new word")
    print("=" * 60)
    print()
    
    try:
        from simple_global_app import main as app_main
        app_main()
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
