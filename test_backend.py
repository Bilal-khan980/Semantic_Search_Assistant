#!/usr/bin/env python3
"""
Simple test script to verify backend functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_backend():
    """Test basic backend functionality"""
    try:
        print("Testing backend imports...")
        
        # Test imports
        from main import DocumentSearchBackend
        print("✓ Main backend imported successfully")
        
        from config import Config
        print("✓ Config imported successfully")
        
        # Test config loading
        config = Config("config.json")
        print(f"✓ Config loaded: {config.embedding_model}")
        
        # Test backend initialization
        print("Initializing backend...")
        backend = DocumentSearchBackend()
        
        print("✓ Backend created successfully")
        print("✓ All tests passed!")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_backend())
    sys.exit(0 if success else 1)
