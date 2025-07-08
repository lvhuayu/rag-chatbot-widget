#!/usr/bin/env python3
"""
Debug script to list all documents for a specific site
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from rag_storage_prisma import PrismaRAGStorage

def main():
    site_id = "cmctk4mpy000390ufey4y1bx1"  # The site ID from your logs
    
    storage = PrismaRAGStorage()
    
    print(f"Checking documents for site: {site_id}")
    print("=" * 50)
    
    # Get documents for this site
    documents, embeddings = storage.get_documents_by_site(site_id)
    
    print(f"Total documents found: {len(documents)}")
    print()
    
    for i, doc in enumerate(documents, 1):
        print(f"Document {i}:")
        print(f"  ID: {doc['id']}")
        print(f"  Title: {doc['title']}")
        print(f"  URL: {doc['url']}")
        print(f"  Created: {doc['created_at']}")
        print(f"  Content length: {len(doc['content'])} characters")
        print(f"  Has embedding: {len(embeddings[i-1]) > 0 if i <= len(embeddings) else 'N/A'}")
        print()
    
    # Also check if there are any duplicate titles or URLs
    titles = [doc['title'] for doc in documents]
    urls = [doc['url'] for doc in documents]
    
    print("Duplicate check:")
    print(f"  Unique titles: {len(set(titles))} out of {len(titles)}")
    print(f"  Unique URLs: {len(set(urls))} out of {len(urls)}")
    
    if len(set(titles)) < len(titles):
        print("  WARNING: Duplicate titles found!")
        from collections import Counter
        title_counts = Counter(titles)
        for title, count in title_counts.items():
            if count > 1:
                print(f"    '{title}' appears {count} times")
    
    if len(set(urls)) < len(urls):
        print("  WARNING: Duplicate URLs found!")
        from collections import Counter
        url_counts = Counter(urls)
        for url, count in url_counts.items():
            if count > 1:
                print(f"    '{url}' appears {count} times")

    # Print only the most recent document for 'test-upload.txt'
    print("\nMost recent 'test-upload.txt' document:")
    test_docs = [doc for doc in documents if doc['title'] == 'test-upload.txt']
    if test_docs:
        latest = max(test_docs, key=lambda d: d['created_at'])
        print(f"  ID: {latest['id']}")
        print(f"  Title: {latest['title']}")
        print(f"  URL: {latest['url']}")
        print(f"  Created: {latest['created_at']}")
        print(f"  Content length: {len(latest['content'])} characters")
    else:
        print("  No document found for 'test-upload.txt'")

if __name__ == "__main__":
    main() 