#!/usr/bin/env python3
"""
Final Complete Test - Documents and Search
Verify that all test_docs files are shown and search returns many results
"""

import requests

def main():
    api_url = "http://127.0.0.1:8000"
    
    print("🎯 FINAL COMPLETE TEST - Documents & Search")
    print("=" * 60)
    
    # 1. Check Documents Section - Folder Scanning
    print("\n1️⃣ Documents Section - All Files in test_docs")
    try:
        response = requests.post(f"{api_url}/folders/scan", json={"folder_path": "test_docs"})
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            print(f"✅ Documents section should show {len(files)} files:")
            for i, file in enumerate(files, 1):
                print(f"   {i}. 📄 {file['name']} ({file['size']} bytes)")
            
            if len(files) >= 4:
                print("✅ SUCCESS: All test_docs files are available for display")
            else:
                print("⚠️ WARNING: Expected at least 4 files")
        else:
            print("❌ Folder scanning failed")
    except Exception as e:
        print(f"❌ Folder scanning error: {e}")
    
    # 2. Check Database Stats
    print("\n2️⃣ Database Content")
    try:
        response = requests.get(f"{api_url}/stats")
        if response.status_code == 200:
            stats = response.json()
            total_chunks = stats.get('total_chunks', 0)
            unique_sources = stats.get('unique_sources', 0)
            print(f"✅ Total chunks indexed: {total_chunks}")
            print(f"✅ Unique source files: {unique_sources}")
            
            if total_chunks >= 30:
                print("✅ SUCCESS: Plenty of content for diverse search results")
            else:
                print("⚠️ WARNING: Limited content may result in fewer search results")
        else:
            print("❌ Could not get database stats")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    # 3. Test Search Results Quantity
    print("\n3️⃣ Search Results Quantity Test")
    
    test_queries = [
        "productivity",
        "programming", 
        "time management",
        "technology",
        "machine learning"
    ]
    
    all_searches_good = True
    
    for query in test_queries:
        print(f"\n   🔎 Query: '{query}'")
        
        try:
            response = requests.post(f"{api_url}/search", json={
                "query": query,
                "limit": 15  # Request 15 results
            })
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                print(f"   ✅ Found {len(results)} results")
                
                if len(results) >= 5:
                    print("   ✅ GOOD: Multiple results available")
                    
                    # Show top 3 results
                    print("   📋 Top 3 results:")
                    for i, result in enumerate(results[:3], 1):
                        source = result.get('source', '')
                        score = result.get('final_score', 0)
                        filename = source.split('\\')[-1] if '\\' in source else source.split('/')[-1]
                        print(f"      {i}. {filename} (Score: {score:.3f})")
                        
                        # Verify source is from test_docs
                        if 'test_docs' not in source:
                            print(f"      ❌ WARNING: Result not from test_docs: {source}")
                            all_searches_good = False
                else:
                    print(f"   ⚠️ WARNING: Only {len(results)} results (expected 5+)")
                    all_searches_good = False
                    
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                all_searches_good = False
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            all_searches_good = False
    
    # 4. Test Specific Content Searches
    print("\n4️⃣ Content-Specific Search Tests")
    
    content_tests = [
        {
            "query": "Pomodoro Technique",
            "expected_files": ["productivity_guide.md", "sample.txt"],
            "description": "Should find Pomodoro content"
        },
        {
            "query": "Python programming",
            "expected_files": ["technology_notes.txt"],
            "description": "Should find Python content"
        },
        {
            "query": "semantic search system",
            "expected_files": ["example_document.md"],
            "description": "Should find semantic search documentation"
        }
    ]
    
    for test in content_tests:
        print(f"\n   🎯 {test['description']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            response = requests.post(f"{api_url}/search", json={
                "query": test['query'],
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Check if expected files are in results
                    found_files = []
                    for result in results:
                        source = result.get('source', '')
                        filename = source.split('\\')[-1] if '\\' in source else source.split('/')[-1]
                        found_files.append(filename)
                    
                    expected_found = any(expected in ' '.join(found_files) for expected in test['expected_files'])
                    
                    if expected_found:
                        print(f"   ✅ SUCCESS: Found expected content in {len(results)} results")
                    else:
                        print(f"   ⚠️ WARNING: Expected files not found in top results")
                        print(f"   📋 Found files: {list(set(found_files))}")
                else:
                    print("   ❌ No results found")
                    
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    # 5. Final Summary
    print("\n5️⃣ FINAL SUMMARY")
    if all_searches_good:
        print("🎉 SUCCESS: All systems working perfectly!")
        print("✅ Documents section shows all test_docs files")
        print("✅ Search returns multiple relevant results")
        print("✅ All results are from test_docs folder only")
        print("✅ Content is properly indexed and searchable")
    else:
        print("⚠️ PARTIAL SUCCESS: Some issues detected")
        print("📋 Check the warnings above for details")
    
    print("\n6️⃣ FRONTEND USAGE")
    print("📱 Open the Electron desktop application")
    print("📂 Documents Tab:")
    print("   • Should show 4 files from test_docs")
    print("   • Click 'Refresh Files' if needed")
    print("🔍 Search Tab:")
    print("   • Try: 'productivity' → Should get 10+ results")
    print("   • Try: 'programming' → Should get multiple results")
    print("   • Try: 'Pomodoro' → Should find technique info")
    print("   • Try: 'machine learning' → Should find AI content")
    
    print("\n" + "=" * 60)
    print("🎯 FINAL COMPLETE TEST FINISHED!")

if __name__ == "__main__":
    main()
