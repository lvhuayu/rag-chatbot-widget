#!/usr/bin/env python3
"""
Test script for uploading a file to the Node.js /upload endpoint with authentication
"""
import requests
import os

BACKEND_URL = "http://localhost:5000"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/auth/login"
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/upload"
USERNAME = "lvhuayu02"
PASSWORD = "123456"

# Path to a test file to upload (ensure this file exists)
TEST_FILE_PATH = "test-upload.txt"

def ensure_test_file():
    if not os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("This is a test upload file for /upload endpoint.\n")

def login_and_get_token():
    data = {"username": USERNAME, "password": PASSWORD}
    resp = requests.post(LOGIN_ENDPOINT, json=data)
    if resp.status_code == 200 and "token" in resp.json():
        print("✅ Login successful.")
        return resp.json()["token"]
    else:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return None

def upload_file(token):
    with open(TEST_FILE_PATH, "rb") as f:
        files = {"files": (os.path.basename(TEST_FILE_PATH), f)}
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(UPLOAD_ENDPOINT, files=files, headers=headers)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        if resp.status_code == 200:
            print("✅ File uploaded successfully!")
        else:
            print("❌ Upload failed.")

def main():
    ensure_test_file()
    token = login_and_get_token()
    if not token:
        return
    upload_file(token)

if __name__ == "__main__":
    main() 