#!/usr/bin/env python3
"""
Launcher for Real-time Semantic Search Assistant
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    print("🚀 Real-time Semantic Search Assistant")
    print("=" * 50)
    print("✨ Features:")
    print("  • Real-time letter-by-letter search")
    print("  • Press SPACEBAR to clear search")
    print("  • Instant suggestions as you type")
    print("  • Copy results with double-click")
    print("  • Web interface available")
    print("=" * 50)
    print()
    
    try:
        from realtime_search_app import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
