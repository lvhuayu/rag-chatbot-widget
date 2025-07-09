#!/usr/bin/env python3
"""
Auto-debug script for document listing issues and DB consolidation
"""
import sqlite3
import requests
import json

SITE_ID = 'cmctk4mpy000390ufey4y1bx1'
DB_PATH = '../rag-chatbot-widget/backend/rag_database.db'  # Corrected path for your project
PYTHON_BACKEND_URL = 'http://localhost:8001'

def list_db_documents(site_id):
    print(f'\n[DB] Documents for site_id={site_id}:')
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, site_id, title, url, created_at FROM documents WHERE site_id = ?", (site_id,))
        rows = cursor.fetchall()
        if not rows:
            print('  (No documents found in DB)')
        for row in rows:
            print(f'  id={row[0]}, site_id={row[1]}, title={row[2]}, url={row[3]}, created_at={row[4]}')
        # Also print all documents for manual inspection
        print('\n[DB] All documents in DB:')
        cursor.execute("SELECT id, site_id, title, url, created_at FROM documents")
        all_rows = cursor.fetchall()
        for row in all_rows:
            print(f'  id={row[0]}, site_id={row[1]}, title={row[2]}, url={row[3]}, created_at={row[4]}')
        conn.close()
    except Exception as e:
        print(f'  [DB ERROR] {e}')

def list_api_documents(site_id):
    print(f'\n[API] Documents from /documents?site_id={site_id}:')
    try:
        resp = requests.get(f'{PYTHON_BACKEND_URL}/documents?site_id={site_id}', timeout=10)
        print(f'  Status: {resp.status_code}')
        if resp.status_code == 200:
            docs = resp.json()
            if not docs:
                print('  (No documents returned by API)')
            for doc in docs:
                print(f'  id={doc.get("id")}, title={doc.get("title")}, url={doc.get("url")}, created_at={doc.get("created_at")}')
        else:
            print(f'  [API ERROR] {resp.text}')
    except Exception as e:
        print(f'  [API ERROR] {e}')

def list_users_and_sites():
    print(f'\n[DB] Users and Sites:')
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()
        cursor.execute("SELECT site_id, user_id, site_name FROM sites")
        sites = cursor.fetchall()
        print('  Users:')
        for user in users:
            print(f'    id={user[0]}, username={user[1]}')
        print('  Sites:')
        for site in sites:
            print(f'    site_id={site[0]}, user_id={site[1]}, site_name={site[2]}')
        print('  User -> Site mapping:')
        for user in users:
            user_sites = [site for site in sites if site[1] == user[0]]
            print(f'    {user[1]} ({user[0]}): {[s[0] for s in user_sites]}')
        conn.close()
    except Exception as e:
        print(f'  [DB ERROR] {e}')

def main():
    print('=== Auto Debug Document Listing & DB Consolidation ===')
    list_users_and_sites()
    list_db_documents(SITE_ID)
    list_api_documents(SITE_ID)
    print('\n=== End Debug ===')

if __name__ == '__main__':
    main() 