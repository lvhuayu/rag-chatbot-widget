#!/usr/bin/env python3
"""
Test script for retrieving documents from the Node.js /documents endpoint
"""
import requests
import json

BACKEND_URL = "http://localhost:5000"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/auth/login"
DOCUMENTS_ENDPOINT = f"{BACKEND_URL}/api/upload/documents"
USERNAME = "lvhuayu02"
PASSWORD = "123456"

def login_and_get_token():
    data = {"username": USERNAME, "password": PASSWORD}
    resp = requests.post(LOGIN_ENDPOINT, json=data)
    if resp.status_code == 200 and "token" in resp.json():
        print("✅ Login successful.")
        return resp.json()["token"]
    else:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return None

def get_documents(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(DOCUMENTS_ENDPOINT, headers=headers)
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        documents = resp.json()
        print(f"✅ Retrieved {len(documents)} documents:")
        for i, doc in enumerate(documents, 1):
            print(f"  {i}. {doc.get('title', 'No title')} (ID: {doc.get('id', 'No ID')})")
            print(f"     URL: {doc.get('url', 'No URL')}")
            print(f"     Created: {doc.get('createdAt', 'No date')}")
            print()
    else:
        print(f"❌ Failed to retrieve documents: {resp.text}")

def main():
    token = login_and_get_token()
    if not token:
        return
    get_documents(token)

if __name__ == "__main__":
    main() 