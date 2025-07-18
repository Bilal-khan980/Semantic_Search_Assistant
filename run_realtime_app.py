#!/usr/bin/env python3
"""
Simple launcher for the Real-time Semantic Search Assistant.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the main app
from app import main

if __name__ == "__main__":
    print("🚀 Starting Real-time Semantic Search Assistant...")
    print("📝 This app will monitor your typing in real-time!")
    print("⌨️  Type in any text editor to see instant suggestions")
    print("🔍 Press SPACEBAR to clear search and start new word")
    print("=" * 60)
    
    main()
