#!/usr/bin/env python3
"""
Test script to verify file modification detection and processing.
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8080"

def test_api(endpoint, method="GET", data=None):
    """Helper function to test API endpoints."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        else:
            response = requests.get(url)
        
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def main():
    print("=== Testing File Modification Detection ===\n")
    
    # 1. Check server health
    print("1. Checking server health...")
    health = test_api("/health")
    if not health:
        print("Server not responding. Exiting.")
        return
    
    # 2. Create sample files
    print("\n2. Creating sample files...")
    test_api("/api/v1/test/create-sample", "POST")
    
    # 3. Check preview before starting service
    print("\n3. Checking file preview...")
    test_api("/api/v1/files/preview")
    
    # 4. Start the service
    print("\n4. Starting file monitoring service...")
    start_result = test_api("/api/v1/start", "POST")
    
    # 5. Wait a moment for service to start
    time.sleep(2)
    
    # 6. Check service status
    print("\n5. Checking service status...")
    test_api("/api/v1/status")
    
    # 7. Test file rename
    print("\n6. Testing file rename...")
    rename_data = {
        "original_name": "test_document.pdf",
        "new_name": "Contract_TestClient_2024-01-15_signed.pdf"
    }
    test_api("/api/v1/test/rename", "POST", rename_data)
    
    # 8. Wait for processing
    print("\n7. Waiting for file processing...")
    time.sleep(3)
    
    # 9. Check recent files
    print("\n8. Checking recently processed files...")
    test_api("/api/v1/files/recent")
    
    # 10. Check logs
    print("\n9. Checking logs...")
    test_api("/api/v1/logs")
    
    # 11. Check if file was moved to destination
    print("\n10. Checking destination directory...")
    dest_path = Path("/tmp/destination")
    if dest_path.exists():
        print(f"Destination directory contents:")
        for item in dest_path.rglob("*"):
            if item.is_file():
                print(f"  {item}")
    else:
        print("Destination directory doesn't exist yet")

if __name__ == "__main__":
    main()
