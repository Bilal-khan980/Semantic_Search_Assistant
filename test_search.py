#!/usr/bin/env python3
"""
Test Search Script
Test the semantic search functionality with various queries
"""

import requests
import json
from pathlib import Path

def test_search():
    """Test the search functionality with sample queries."""
    api_url = "http://127.0.0.1:8000"
    
    # Test queries
    test_queries = [
        "productivity techniques",
        "semantic search features",
        "document processing",
        "time management",
        "Pomodoro Technique",
        "deep work",
        "focus",
        "Bilal",
        "programming",
        "development"
    ]
    
    print("🔍 Testing Semantic Search Functionality")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{api_url}/search",
                json={"query": query, "limit": 3},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total_results = data.get('total_results', 0)
                processing_time = data.get('processing_time_ms', 0)
                
                print(f"✅ Found {total_results} results ({processing_time:.1f}ms)")
                
                for i, result in enumerate(results, 1):
                    score = result.get('final_score', 0)
                    source = result.get('source', 'Unknown')
                    filename = Path(source).name
                    snippet = result.get('display_snippet', '')[:100] + "..."
                    
                    print(f"  {i}. {filename} (Score: {score:.3f})")
                    print(f"     {snippet}")
                    
                if not results:
                    print("   ❌ No results found")
                    
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Search testing completed!")

if __name__ == "__main__":
    test_search()
