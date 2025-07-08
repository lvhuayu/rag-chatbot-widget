#!/usr/bin/env python3
"""
Test script to check if user has a site record
"""
import requests
import json

BACKEND_URL = "http://localhost:5000"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/auth/login"
USERNAME = "lvhuayu02"
PASSWORD = "123456"

def test_user_site():
    """Test if user has a site record by trying to upload a file"""
    # First login
    data = {"username": USERNAME, "password": PASSWORD}
    resp = requests.post(LOGIN_ENDPOINT, json=data)
    
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return
    
    token = resp.json()["token"]
    print("✅ Login successful.")
    
    # Try to upload a file to see if site lookup works
    import os
    test_file = "test-site-check.txt"
    with open(test_file, "w") as f:
        f.write("Test file for site check")
    
    try:
        with open(test_file, "rb") as f:
            files = {"files": (test_file, f)}
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.post(f"{BACKEND_URL}/api/upload", files=files, headers=headers)
            
        print(f"Upload Status: {resp.status_code}")
        print(f"Upload Response: {resp.text}")
        
        if resp.status_code == 400 and "No site found for user" in resp.text:
            print("❌ User has no site record!")
        elif resp.status_code == 200:
            print("✅ User has a site record and upload works!")
        else:
            print(f"⚠️ Unexpected response: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    print("🧪 Testing user site record...")
    print("=" * 60)
    
    test_user_site()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    main() 