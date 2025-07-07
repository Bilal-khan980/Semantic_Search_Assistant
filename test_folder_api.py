#!/usr/bin/env python3
"""
Test the folder scanning API to see what files are available.
"""

import requests
import json
import os

def test_folder_api():
    """Test the folder scanning API."""
    base_url = "http://127.0.0.1:8000"
    
    print("📁 Testing Folder API...")
    
    # Test scanning test_docs folder
    test_docs_path = os.path.abspath("test_docs")
    print(f"Scanning folder: {test_docs_path}")
    
    try:
        response = requests.post(
            f"{base_url}/folders/scan",
            json={"folder_path": test_docs_path},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Folder scan successful!")
            print(f"📂 Folder: {data.get('folder_path')}")
            
            files = data.get('files', [])
            print(f"📄 Found {len(files)} files:")
            
            for file in files:
                print(f"  • {file['name']} ({file['extension']}) - {file['size']} bytes")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    
    # Test listing connected folders
    print(f"\n📋 Testing connected folders list...")
    try:
        response = requests.get(f"{base_url}/folders/list", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Connected folders:")
            for folder in data.get('connected_folders', []):
                print(f"  • {folder}")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_folder_api()
