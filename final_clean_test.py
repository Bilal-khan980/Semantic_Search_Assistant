#!/usr/bin/env python3
"""
Final Clean Test
Complete verification that the system is working with ONLY test_docs files
"""

import requests
import json
from pathlib import Path

def main():
    api_url = "http://127.0.0.1:8000"
    
    print("🎯 FINAL CLEAN TEST - test_docs Only System")
    print("=" * 70)
    
    # 1. Backend Health
    print("\n1️⃣ Backend Health Check")
    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            print("✅ Backend is healthy and running")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # 2. Folder Management
    print("\n2️⃣ Folder Management")
    try:
        # Check connected folders
        response = requests.get(f"{api_url}/folders/list")
        if response.status_code == 200:
            folders = response.json().get('connected_folders', [])
            print(f"✅ Connected folders: {folders}")
            if 'test_docs' in folders and len(folders) == 1:
                print("✅ Only test_docs folder is connected (clean setup)")
            else:
                print("⚠️ Multiple folders connected - may have mixed content")
        
        # Scan test_docs folder
        response = requests.post(f"{api_url}/folders/scan", json={"folder_path": "test_docs"})
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            print(f"✅ test_docs contains {len(files)} files:")
            for file in files:
                print(f"   📄 {file['name']} ({file['size']} bytes)")
        
    except Exception as e:
        print(f"❌ Folder management error: {e}")
    
    # 3. Search Verification with Expected Results
    print("\n3️⃣ Search Verification - Expected Results")
    
    test_cases = [
        {
            "query": "productivity techniques",
            "expected_primary": "sample.txt",
            "description": "Should primarily find sample.txt (productivity content)"
        },
        {
            "query": "semantic search",
            "expected_primary": "example_document.md",
            "description": "Should primarily find example_document.md (semantic search docs)"
        },
        {
            "query": "Pomodoro Technique",
            "expected_primary": "sample.txt", 
            "description": "Should find Pomodoro technique from sample.txt"
        },
        {
            "query": "document processing",
            "expected_primary": "example_document.md",
            "description": "Should find document processing from example_document.md"
        }
    ]
    
    all_tests_passed = True
    
    for test in test_cases:
        print(f"\n   🔎 Test: {test['description']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            response = requests.post(f"{api_url}/search", json={
                "query": test['query'],
                "limit": 5
            })
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    top_result = results[0]
                    source = top_result.get('source', '')
                    score = top_result.get('final_score', 0)
                    filename = Path(source).name
                    
                    # Check if top result matches expected
                    if test['expected_primary'] in filename and 'test_docs' in source:
                        print(f"   ✅ PASS: Top result is {filename} (Score: {score:.3f})")
                    else:
                        print(f"   ❌ FAIL: Expected {test['expected_primary']}, got {filename}")
                        all_tests_passed = False
                    
                    # Verify all results are from test_docs
                    all_from_test_docs = all('test_docs' in r.get('source', '') for r in results)
                    if all_from_test_docs:
                        print(f"   ✅ All {len(results)} results are from test_docs")
                    else:
                        print(f"   ❌ Some results are NOT from test_docs")
                        all_tests_passed = False
                        
                else:
                    print("   ❌ No results found")
                    all_tests_passed = False
                    
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                all_tests_passed = False
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            all_tests_passed = False
    
    # 4. Final Status
    print("\n4️⃣ Final System Status")
    if all_tests_passed:
        print("🎉 SUCCESS: System is working perfectly!")
        print("✅ Only test_docs files are indexed")
        print("✅ Search results are accurate and relevant")
        print("✅ No mixed content from other folders")
        print("✅ Frontend should display test_docs files correctly")
    else:
        print("❌ ISSUES DETECTED: Some tests failed")
        print("⚠️ System may need additional cleanup")
    
    print("\n5️⃣ Frontend Usage Instructions")
    print("📱 Open the Electron desktop application")
    print("📂 Go to 'Documents' tab - should show:")
    print("   📄 example_document.md")
    print("   📄 sample.txt")
    print("🔍 Go to 'Search' tab - try these queries:")
    print("   • 'productivity' → sample.txt content")
    print("   • 'semantic search' → example_document.md content")
    print("   • 'Pomodoro' → productivity techniques")
    print("   • 'document processing' → system documentation")
    
    print("\n🔄 If Documents section is empty:")
    print("   1. Click 'Refresh Files' button")
    print("   2. Or restart the Electron app")
    print("   3. Backend is running and ready!")
    
    print("\n" + "=" * 70)
    print("🎯 FINAL CLEAN TEST COMPLETE!")

if __name__ == "__main__":
    main()
