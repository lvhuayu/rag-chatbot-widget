#!/usr/bin/env python3
"""
Test script to check database connection and user/site data
"""
import requests
import json

BACKEND_URL = "http://localhost:5000"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/auth/login"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"
USERNAME = "lvhuayu02"
PASSWORD = "123456"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(HEALTH_ENDPOINT)
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")

def test_login_and_get_user_info():
    """Test login and get user info from token"""
    data = {"username": USERNAME, "password": PASSWORD}
    resp = requests.post(LOGIN_ENDPOINT, json=data)
    
    if resp.status_code == 200:
        result = resp.json()
        print("✅ Login successful.")
        print(f"Token: {result.get('token', 'No token')[:50]}...")
        print(f"User ID: {result.get('user', {}).get('id', 'No user ID')}")
        return result.get('token')
    else:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return None

def main():
    print("🧪 Testing database connection and user data...")
    print("=" * 60)
    
    test_health()
    print()
    test_login_and_get_user_info()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    main() 