#!/usr/bin/env python3
"""
Test Improved Search Results
"""

import requests

def main():
    api_url = "http://127.0.0.1:8000"
    
    print("🔍 TESTING IMPROVED SEARCH RESULTS")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "productivity",
        "semantic search", 
        "document processing",
        "time management",
        "Pomodoro"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        try:
            response = requests.post(f"{api_url}/search", json={
                "query": query,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    source = result.get('source', '')
                    score = result.get('final_score', 0)
                    filename = source.split('\\')[-1] if '\\' in source else source.split('/')[-1]
                    print(f"   {i}. {filename} (Score: {score:.3f})")
                    
            else:
                print(f"❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Check database stats
    print(f"\n📊 Database Stats:")
    try:
        response = requests.get(f"{api_url}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total chunks: {stats.get('total_chunks', 0)}")
            print(f"   Unique sources: {stats.get('unique_sources', 0)}")
        else:
            print("   ❌ Could not get stats")
    except Exception as e:
        print(f"   ❌ Stats error: {e}")
    
    # Check folder scanning
    print(f"\n📁 Folder Contents:")
    try:
        response = requests.post(f"{api_url}/folders/scan", json={"folder_path": "test_docs"})
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            print(f"   Found {len(files)} files in test_docs:")
            for file in files:
                print(f"   📄 {file['name']} ({file['size']} bytes)")
        else:
            print("   ❌ Could not scan folder")
    except Exception as e:
        print(f"   ❌ Folder scan error: {e}")

if __name__ == "__main__":
    main()
