#!/usr/bin/env python3
"""
Test the API search functionality with improved relevance filtering.
"""

import requests
import json

def test_search_api():
    """Test the search API with various queries."""
    base_url = "http://127.0.0.1:8000"
    
    test_queries = [
        "productivity",
        "machine learning", 
        "pdf",
        "random nonsense xyz123",
        "eisenhower matrix",
        "python programming"
    ]
    
    print("🔍 Testing Search API with Improved Relevance...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/search",
                json={
                    "query": query,
                    "limit": 5,
                    "similarity_threshold": 0.3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    print("❌ No results found")
                else:
                    print(f"✅ Found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        score = result.get('final_score', result.get('similarity', 0))
                        print(f"  {i}. {score:.1%} - {result.get('source', 'Unknown')}")
                        print(f"     {result.get('content', '')[:80]}...")
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API Test Complete!")

if __name__ == "__main__":
    test_search_api()
