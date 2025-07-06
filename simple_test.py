#!/usr/bin/env python3
"""
Simple test to verify basic functionality.
"""

import asyncio
import logging
import tempfile
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simple_test():
    """Simple test of core functionality."""
    
    print("🧪 Simple Backend Test")
    print("=" * 30)
    
    try:
        from main import DocumentSearchBackend
        
        # Initialize backend
        print("1. Initializing backend...")
        backend = DocumentSearchBackend()
        await backend.initialize()
        print("✅ Backend initialized")
        
        # Check stats
        print("\n2. Getting stats...")
        stats = await backend.get_stats()
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        
        # Test simple search
        print("\n3. Testing search...")
        results = await backend.search("test", limit=3, similarity_threshold=0.1)
        print(f"   Search results: {len(results)}")
        
        if len(results) > 0:
            print("   First result:")
            print(f"     Content: {results[0].get('content', '')[:100]}...")
            print(f"     Score: {results[0].get('score', 0):.3f}")
        
        print("\n✅ Test completed successfully")
        
        # Cleanup
        await backend.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
