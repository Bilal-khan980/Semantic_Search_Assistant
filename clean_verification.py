#!/usr/bin/env python3
"""
Clean Verification Script
Verify that ONLY test_docs files are indexed and searchable
"""

import requests
import json
from pathlib import Path

def main():
    api_url = "http://127.0.0.1:8000"
    
    print("🧹 CLEAN VERIFICATION - Only test_docs Files")
    print("=" * 60)
    
    # 1. Check folder scanning shows test_docs files
    print("\n1️⃣ Folder Scanning - test_docs")
    try:
        response = requests.post(f"{api_url}/folders/scan", json={"folder_path": "test_docs"})
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            print(f"✅ Found {len(files)} files in test_docs:")
            for file in files:
                print(f"   📄 {file['name']} ({file['size']} bytes)")
        else:
            print("❌ Folder scanning failed")
    except Exception as e:
        print(f"❌ Folder scanning error: {e}")
    
    # 2. Test searches and verify sources are ONLY from test_docs
    print("\n2️⃣ Search Verification - Sources Should ONLY be from test_docs")
    
    test_queries = [
        "productivity techniques",
        "semantic search", 
        "Pomodoro Technique",
        "document processing"
    ]
    
    all_sources_clean = True
    
    for query in test_queries:
        print(f"\n   🔎 Query: '{query}'")
        
        try:
            response = requests.post(f"{api_url}/search", json={
                "query": query,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    print(f"   ✅ Found {len(results)} results")
                    
                    # Check each result source
                    for i, result in enumerate(results, 1):
                        source = result.get('source', '')
                        score = result.get('final_score', 0)
                        filename = Path(source).name
                        
                        # Verify source is from test_docs
                        if 'test_docs' in source:
                            print(f"   ✅ {i}. {filename} (Score: {score:.3f}) - FROM test_docs")
                        else:
                            print(f"   ❌ {i}. {filename} (Score: {score:.3f}) - NOT from test_docs!")
                            print(f"       Source: {source}")
                            all_sources_clean = False
                else:
                    print("   ⚠️ No results found")
                    
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    # 3. Summary
    print("\n3️⃣ Clean Database Summary")
    if all_sources_clean:
        print("✅ SUCCESS: All search results are from test_docs folder only!")
        print("✅ Database is clean - no mixed content")
        print("✅ Frontend Documents section should show only test_docs files")
        print("✅ Search results will only come from test_docs content")
    else:
        print("❌ ISSUE: Some search results are NOT from test_docs folder")
        print("❌ Database still contains mixed content")
    
    print("\n4️⃣ Expected Files in Documents Section:")
    print("   📄 example_document.md - Contains semantic search documentation")
    print("   📄 sample.txt - Contains productivity and time management content")
    
    print("\n5️⃣ Test These Searches in the Frontend:")
    print("   🔍 'productivity' → Should find sample.txt content")
    print("   🔍 'semantic search' → Should find example_document.md content") 
    print("   🔍 'Pomodoro' → Should find productivity techniques from sample.txt")
    print("   🔍 'document processing' → Should find system info from example_document.md")
    
    print("\n🎉 CLEAN VERIFICATION COMPLETE!")
    print("📱 Open the Electron app and check the Documents section")
    print("🔄 If files don't appear, click 'Refresh Files' button")

if __name__ == "__main__":
    main()
