#!/usr/bin/env python3
"""
Auto-debug script for frontend document fetch issues
"""
import requests
import sqlite3
import json

BACKEND_URL = "http://localhost:5000"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/auth/login"
DOCUMENTS_ENDPOINT = f"{BACKEND_URL}/api/upload/documents"
USERNAME = "lvhuayu02"  # Change as needed
PASSWORD = "123456"     # Change as needed
DB_PATH = '../rag-chatbot-widget/backend/rag_database.db'

def login_and_get_token():
    data = {"username": USERNAME, "password": PASSWORD}
    resp = requests.post(LOGIN_ENDPOINT, json=data)
    if resp.status_code == 200 and "token" in resp.json():
        print("✅ Login successful.")
        return resp.json()["token"], resp.json()["user"]["id"]
    else:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return None, None

def fetch_documents(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(DOCUMENTS_ENDPOINT, headers=headers)
    print(f"\n[API] /api/upload/documents status: {resp.status_code}")
    try:
        print("[API] Response:", json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception:
        print("[API] Raw Response:", resp.text)

def print_user_site_and_docs(user_id):
    print(f"\n[DB] User, Site, and Documents for user_id={user_id}:")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        print(f"  Username: {user[0] if user else 'N/A'}")
        cursor.execute("SELECT site_id FROM sites WHERE user_id=?", (user_id,))
        site = cursor.fetchone()
        if not site:
            print("  No site found for this user.")
            return
        site_id = site[0]
        print(f"  Site ID: {site_id}")
        cursor.execute("SELECT id, title, url, created_at FROM documents WHERE site_id=?", (site_id,))
        docs = cursor.fetchall()
        if not docs:
            print("  No documents found for this site.")
        else:
            for doc in docs:
                print(f"    id={doc[0]}, title={doc[1]}, url={doc[2]}, created_at={doc[3]}")
        conn.close()
    except Exception as e:
        print(f"  [DB ERROR] {e}")

def main():
    print("=== Auto Debug Frontend Document Fetch ===")
    token, user_id = login_and_get_token()
    if not token or not user_id:
        return
    fetch_documents(token)
    print_user_site_and_docs(user_id)
    print("\n=== End Debug ===")

if __name__ == "__main__":
    main() 