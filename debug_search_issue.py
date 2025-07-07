#!/usr/bin/env python3
"""
Debug script to test search functionality and identify scoring issues.
"""

import asyncio
import sys
import json
from main import DocumentSearchBackend

async def test_search():
    """Test search functionality and examine results."""
    print("🔍 Testing Semantic Search...")

    backend = DocumentSearchBackend()
    await backend.initialize()
    
    # Test with different queries
    test_queries = [
        "pdf",
        "productivity",
        "machine learning",
        "random nonsense xyz123"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        print("-" * 50)
        
        results = await backend.search(query, limit=3, similarity_threshold=0.3)
        
        if not results:
            print("❌ No results found")
            continue
            
        print(f"✅ Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Result:")
            print(f"   Final Score: {result.get('final_score', 'N/A')}")
            print(f"   Similarity: {result.get('similarity', 'N/A')}")
            print(f"   Source: {result.get('source', 'N/A')}")
            print(f"   Content: {result.get('content', '')[:100]}...")
            
            # Check if scores are valid numbers
            final_score = result.get('final_score')
            similarity = result.get('similarity')
            
            if final_score is None or str(final_score) == 'nan':
                print("   ⚠️  WARNING: final_score is NaN or None!")
            if similarity is None or str(similarity) == 'nan':
                print("   ⚠️  WARNING: similarity is NaN or None!")

if __name__ == "__main__":
    asyncio.run(test_search())
