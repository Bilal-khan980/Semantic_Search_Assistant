#!/usr/bin/env python3
"""
Simple test to verify the semantic search system works correctly.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import DocumentSearchBackend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_system():
    """Test the complete semantic search system."""
    
    print("🧪 Testing Semantic Search System")
    print("=" * 50)
    
    try:
        # Initialize backend
        print("1. Initializing backend...")
        backend = DocumentSearchBackend()
        await backend.initialize()
        print("✅ Backend initialized successfully")
        
        # Test file processing
        print("\n2. Processing test document...")
        test_file = Path("test_docs/sample_document.md")
        
        if test_file.exists():
            results = await backend.process_documents([str(test_file)])
            print(f"📊 Processing results: {len(results)} files processed")
            
            if results and len(results) > 0:
                result = results[0]
                if result.get('status') == 'success':
                    print(f"✅ File processed successfully!")
                    print(f"   - Chunks created: {result.get('chunks_count', 0)}")
                else:
                    print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print("❌ No results returned from processing")
                return False
        else:
            print(f"❌ Test file not found: {test_file}")
            return False
        
        # Test search functionality
        print("\n3. Testing search functionality...")
        
        # Test searches with different terms
        test_queries = [
            "bilal",
            "artificial intelligence",
            "Python programming",
            "machine learning"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Searching for: '{query}'")
            search_results = await backend.search(query, limit=5)
            
            if 'results' in search_results:
                results = search_results['results']
                print(f"   Found {len(results)} results")
                
                for i, result in enumerate(results[:3], 1):
                    score = result.get('score', 0)
                    source = result.get('source', 'Unknown')
                    print(f"   {i}. {Path(source).name} (score: {score:.1f})")
            else:
                print(f"   No results found")
        
        # Test backend stats
        print("\n4. Backend statistics...")
        stats = await backend.get_stats()
        print(f"📈 Total chunks: {stats.get('total_chunks', 0)}")
        print(f"📄 Document chunks: {stats.get('document_chunks', 0)}")
        print(f"📚 Unique sources: {stats.get('unique_sources', 0)}")
        
        print("\n✅ All tests completed successfully!")
        
        # Cleanup
        await backend.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system())
    if success:
        print("\n🎉 System is working correctly!")
        print("You can now:")
        print("1. Start the API server: python api_service.py")
        print("2. Start the Electron frontend")
        print("3. Add new documents to test_docs folder")
        print("4. Search for content with scores > 50")
    else:
        print("\n❌ System test failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
