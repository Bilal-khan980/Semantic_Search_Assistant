#!/usr/bin/env python3
"""
Debug what the API is actually returning for search results.
"""

import requests
import json

def debug_api_response():
    """Debug the actual API response structure."""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Debugging API Response Structure...")
    
    try:
        response = requests.post(
            f"{base_url}/search",
            json={
                "query": "productivity",
                "limit": 2,
                "similarity_threshold": 0.3
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2))
            
            results = data.get('results', [])
            if results:
                print(f"\n📊 First result structure:")
                first_result = results[0]
                for key, value in first_result.items():
                    print(f"  {key}: {value} (type: {type(value).__name__})")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    debug_api_response()
