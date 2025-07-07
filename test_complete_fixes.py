#!/usr/bin/env python3
"""
Test both fixes:
1. Search results with proper scores (no NaN%)
2. Folder files API working correctly
"""

import requests
import json

def test_search_scores():
    """Test that search returns proper scores without NaN."""
    print("🔍 Testing Search Scores...")
    
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
            
            print(f"✅ Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                final_score = result.get('final_score')
                similarity = result.get('similarity')
                
                print(f"  {i}. Final Score: {final_score}")
                print(f"     Similarity: {similarity}")
                
                # Check for valid scores
                if final_score is None or str(final_score).lower() == 'nan':
                    print(f"     ❌ Invalid final_score!")
                    return False
                    
                if similarity is None or str(similarity).lower() == 'nan':
                    print(f"     ❌ Invalid similarity!")
                    return False
                    
                # Check score is reasonable (0-1 range)
                if not (0 <= final_score <= 1):
                    print(f"     ❌ final_score out of range: {final_score}")
                    return False
                    
                print(f"     ✅ Valid scores")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_folder_files():
    """Test that folder scanning returns files correctly."""
    print("\n📁 Testing Folder Files API...")
    
    try:
        # Test folder list
        response = requests.get("http://127.0.0.1:8000/folders/list", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            folders = data.get('connected_folders', [])
            print(f"✅ Connected folders: {folders}")
            
            if not folders:
                print("❌ No connected folders found")
                return False
                
            # Test folder scan
            response = requests.post(
                "http://127.0.0.1:8000/folders/scan",
                json={"folder_path": "test_docs"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                
                print(f"✅ Found {len(files)} files in test_docs:")
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
                return False
        else:
            print(f"❌ Folder list error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Complete Fixes...")
    print("=" * 50)
    
    # Test 1: Search scores
    scores_ok = test_search_scores()
    
    # Test 2: Folder files
    folders_ok = test_folder_files()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Search Scores: {'✅ PASS' if scores_ok else '❌ FAIL'}")
    print(f"  Folder Files:  {'✅ PASS' if folders_ok else '❌ FAIL'}")
    
    if scores_ok and folders_ok:
        print("\n🎉 All tests passed! Both fixes are working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    main()
