#!/usr/bin/env python3
"""
Comprehensive test script for all main backend API endpoints (rag_server_prisma.py)
"""
import requests
import json

BASE_URL = "http://localhost:8001"
SITE_ID = "cmcu4th0h0004woufa9gh58wn"

def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def test_root():
    print_section("GET /")
    r = requests.get(f"{BASE_URL}/")
    print(r.status_code, r.text)

def test_health():
    print_section("GET /health")
    r = requests.get(f"{BASE_URL}/health")
    print(r.status_code, r.text)

def test_add_documents():
    print_section("POST /add-documents")
    data = [{
        "url": "test://multi-api",
        "title": "API Test Document",
        "content": "This is a test document for API testing.",
        "site_id": SITE_ID
    }]
    r = requests.post(f"{BASE_URL}/add-documents", json=data)
    print(r.status_code, r.text)

def test_search():
    print_section("POST /search")
    data = {
        "query": "API testing",
        "site_id": SITE_ID,
        "top_k": 3,
        "threshold": 0.0
    }
    r = requests.post(f"{BASE_URL}/search", json=data)
    print(r.status_code, r.text)

def test_list_documents():
    print_section("GET /documents")
    r = requests.get(f"{BASE_URL}/documents", params={"site_id": SITE_ID})
    print(r.status_code, r.text)

def test_clear_documents():
    print_section("DELETE /clear-documents")
    r = requests.delete(f"{BASE_URL}/clear-documents", params={"site_id": SITE_ID})
    print(r.status_code, r.text)

def test_stats():
    print_section("GET /stats")
    r = requests.get(f"{BASE_URL}/stats", params={"site_id": SITE_ID})
    print(r.status_code, r.text)

def test_rag_generate():
    print_section("POST /rag-generate (no token)")
    data = {
        "query": "API testing",
        "site_id": SITE_ID,
        "top_k": 3,
        "threshold": 0.0
    }
    r = requests.post(f"{BASE_URL}/rag-generate", json=data)
    print(r.status_code, r.text)

def main():
    test_root()
    test_health()
    test_add_documents()
    test_search()
    test_list_documents()
    test_stats()
    test_clear_documents()
    test_list_documents()
    test_stats()
    test_rag_generate()

if __name__ == "__main__":
    main() 