#!/usr/bin/env python3
"""
Test script to verify that both fixes are working in the desktop application:
1. Search scores display correctly (no NaN%)
2. Document browser shows files from test_docs folder
"""

import requests
import time
import json

def test_backend_connection():
    """Test that the backend is running and responding."""
    print("🔗 Testing backend connection...")
    
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_search_api():
    """Test search API returns proper scores."""
    print("\n🔍 Testing search API...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/search",
            json={
                "query": "productivity",
                "limit": 3,
                "similarity_threshold": 0.3
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"✅ Search API working - found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                final_score = result.get('final_score')
                similarity = result.get('similarity')
                
                print(f"  {i}. final_score: {final_score}, similarity: {similarity}")
                
                # Check for valid scores
                if final_score is None or str(final_score).lower() == 'nan':
                    print(f"     ❌ Invalid final_score!")
                    return False
                    
                if not (0 <= final_score <= 1):
                    print(f"     ❌ final_score out of range: {final_score}")
                    return False
                    
                print(f"     ✅ Valid scores - {final_score:.1%} match")
            
            return True
        else:
            print(f"❌ Search API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Search API error: {e}")
        return False

def test_folder_api():
    """Test folder scanning API."""
    print("\n📁 Testing folder scanning API...")
    
    try:
        # Test folder scan
        response = requests.post(
            "http://127.0.0.1:8000/folders/scan",
            json={"folder_path": "test_docs"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            
            print(f"✅ Folder scan working - found {len(files)} files:")
            for file in files:
                print(f"  • {file['name']} ({file['extension']}) - {file['size']} bytes")
            
            if len(files) >= 4:  # We expect at least 4 files
                print("✅ Expected number of files found")
                return True
            else:
                print(f"❌ Expected at least 4 files, found {len(files)}")
                return False
        else:
            print(f"❌ Folder scan error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Folder scan error: {e}")
        return False

def main():
    """Run all tests and provide instructions for manual testing."""
    print("🧪 Testing Desktop App Fixes")
    print("=" * 50)
    
    # Test backend APIs
    backend_ok = test_backend_connection()
    search_ok = test_search_api() if backend_ok else False
    folder_ok = test_folder_api() if backend_ok else False
    
    print("\n" + "=" * 50)
    print("📊 API Test Results:")
    print(f"  Backend Connection: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"  Search API:         {'✅ PASS' if search_ok else '❌ FAIL'}")
    print(f"  Folder API:         {'✅ PASS' if folder_ok else '❌ FAIL'}")
    
    if backend_ok and search_ok and folder_ok:
        print("\n🎉 All API tests passed!")
        print("\n📱 DESKTOP APP TESTING INSTRUCTIONS:")
        print("=" * 60)
        print("✅ FIXED: Web frontend deleted - only desktop app remains")
        print("✅ FIXED: Score display in static HTML (was using result.score)")
        print("✅ FIXED: Added document browser functionality")
        print("")
        print("🔍 TEST 1: Search Score Display")
        print("1. Open the Semantic Search Assistant desktop app")
        print("2. Go to the Search tab and search for 'productivity'")
        print("3. ✅ Check: Scores should show '68%', '57%', '57%' (NOT 'NaN%')")
        print("")
        print("📄 TEST 2: Document Browser")
        print("1. Click on the 'Documents' tab")
        print("2. ✅ Check: Should show 'test_docs folder • 4 files'")
        print("3. ✅ Check: Should display 4 files:")
        print("   • 📄 example_document.md (MD • 1.2 KB)")
        print("   • 📄 productivity_guide.md (MD • 5.1 KB)")
        print("   • 📄 sample.txt (TXT • 430 B)")
        print("   • 📄 technology_notes.txt (TXT • 6.9 KB)")
        print("4. ✅ Check: Each file should show '✅ Indexed' status")
        print("")
        print("🚀 If both tests pass, the desktop app is fully fixed!")
    else:
        print("\n❌ Some API tests failed. Check the backend setup.")
        
    return backend_ok and search_ok and folder_ok

if __name__ == "__main__":
    main()
