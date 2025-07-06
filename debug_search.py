#!/usr/bin/env python3
"""
Debug script to test search functionality and identify issues.
"""

import asyncio
import logging
import tempfile
import os
from pathlib import Path

from main import DocumentSearchBackend

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_search():
    """Debug the search functionality step by step."""
    
    print("🔍 Starting Search Debug Session")
    print("=" * 50)
    
    try:
        # Initialize backend
        print("1. Initializing backend...")
        backend = DocumentSearchBackend()
        await backend.initialize()
        print("✅ Backend initialized")
        
        # Check initial stats
        print("\n2. Checking initial stats...")
        stats = await backend.get_stats()
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Readwise highlights: {stats.get('readwise_highlights', 0)}")
        
        # Test if we have any data
        if stats.get('total_chunks', 0) == 0:
            print("\n⚠️  No documents found. Let's add some test data...")
            
            # Create test document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("""
                This is a test document about productivity and time management.
                It contains information about various productivity techniques
                including the Pomodoro Technique, Getting Things Done (GTD),
                and time blocking strategies.
                
                Key concepts include:
                - Focus and concentration
                - Task prioritization
                - Goal setting and achievement
                - Work-life balance
                
                The document also discusses machine learning concepts,
                artificial intelligence, and data science methodologies.
                """)
                test_file = f.name
            
            print(f"   Created test file: {test_file}")
            
            # Process the test document
            print("   Processing test document...")
            results = await backend.process_documents([test_file])
            print(f"   Processing results: {results}")
            
            # Clean up
            os.unlink(test_file)
            
            # Check stats again
            stats = await backend.get_stats()
            print(f"   Updated total chunks: {stats.get('total_chunks', 0)}")
        
        # Test vector store directly
        print("\n3. Testing vector store directly...")
        try:
            vector_results = await backend.vector_store.search("productivity", limit=5)
            print(f"   Vector store results: {len(vector_results)} items")
            for i, result in enumerate(vector_results[:3]):
                print(f"   [{i+1}] Similarity: {result.get('similarity', 0):.3f}")
                print(f"       Content: {result.get('content', '')[:100]}...")
        except Exception as e:
            print(f"   ❌ Vector store search failed: {e}")
        
        # Test search engine
        print("\n4. Testing search engine...")
        try:
            search_results = await backend.search_engine.search("productivity", limit=5)
            print(f"   Search engine results: {len(search_results)} items")
            for i, result in enumerate(search_results[:3]):
                print(f"   [{i+1}] Score: {result.get('score', 0):.3f}")
                print(f"       Content: {result.get('content', '')[:100]}...")
        except Exception as e:
            print(f"   ❌ Search engine failed: {e}")
        
        # Test main backend search
        print("\n5. Testing main backend search...")
        try:
            backend_results = await backend.search("productivity", limit=5)
            print(f"   Backend search results: {len(backend_results)} items")
            for i, result in enumerate(backend_results[:3]):
                print(f"   [{i+1}] Score: {result.get('score', 0):.3f}")
                print(f"       Content: {result.get('content', '')[:100]}...")
        except Exception as e:
            print(f"   ❌ Backend search failed: {e}")
        
        # Test different queries
        print("\n6. Testing various queries...")
        test_queries = [
            "machine learning",
            "time management", 
            "artificial intelligence",
            "productivity tips",
            "data science"
        ]
        
        for query in test_queries:
            try:
                results = await backend.search(query, limit=3, similarity_threshold=0.1)
                print(f"   Query '{query}': {len(results)} results")
            except Exception as e:
                print(f"   Query '{query}': ERROR - {e}")
        
        # Check embedding model
        print("\n7. Testing embedding model...")
        try:
            if hasattr(backend.vector_store, 'embedding_model'):
                test_embedding = backend.vector_store.embedding_model.encode(["test query"])
                print(f"   Embedding shape: {test_embedding.shape}")
                print(f"   Embedding model: {backend.config.get('embedding.model_name', 'unknown')}")
            else:
                print("   ❌ No embedding model found")
        except Exception as e:
            print(f"   ❌ Embedding test failed: {e}")
        
        # Check table structure
        print("\n8. Checking database table...")
        try:
            if backend.vector_store.table:
                count = backend.vector_store.table.count_rows()
                print(f"   Table row count: {count}")
                
                if count > 0:
                    # Get a sample row
                    sample = backend.vector_store.table.head(1).to_list()
                    if sample:
                        print(f"   Sample row keys: {list(sample[0].keys())}")
                else:
                    print("   ⚠️  Table is empty")
            else:
                print("   ❌ No table found")
        except Exception as e:
            print(f"   ❌ Table check failed: {e}")
        
        print("\n" + "=" * 50)
        print("🔍 Debug session complete")
        
        # Cleanup
        await backend.cleanup()
        
    except Exception as e:
        print(f"❌ Debug session failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_search())
