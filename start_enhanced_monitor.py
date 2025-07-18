#!/usr/bin/env python3
"""
Enhanced Global Monitor Launcher
"""

import sys
import ctypes
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def is_admin():
    """Check if running as administrator."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    print("🌍 Enhanced Global Real-time Search Monitor")
    print("=" * 60)
    print("🎯 FIXED VERSION - Should work with Word!")
    print()
    print("✨ Features:")
    print("  • Enhanced global keyboard monitoring")
    print("  • Multiple detection methods")
    print("  • Works with Word, Notepad, VS Code")
    print("  • Manual test box as backup")
    print("  • Administrator privilege detection")
    print()
    
    if not is_admin():
        print("⚠️  NOT running as Administrator")
        print("   For best results with Word, run as Administrator:")
        print("   Right-click start_enhanced_admin.bat → 'Run as administrator'")
        print()
    else:
        print("✅ Running as Administrator - Perfect!")
        print()
    
    print("=" * 60)
    print()
    
    try:
        from enhanced_global_monitor import main as app_main
        app_main()
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
