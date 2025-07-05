#!/usr/bin/env python3
"""
Migration Script: In-Memory to Persistent Storage
This script helps migrate existing in-memory data to the new SQLite persistent storage
"""

import json
import requests
import time
from typing import List, Dict, Any
from rag_storage import init_storage

def migrate_in_memory_data():
    """Migrate data from in-memory storage to persistent storage"""
    
    print("=== RAG Storage Migration Tool ===")
    print("This tool will migrate data from in-memory storage to persistent SQLite storage")
    print()
    
    # Initialize persistent storage
    print("Initializing persistent storage...")
    storage = init_storage("rag_database.db")
    
    # Get current database info
    db_info = storage.get_database_info()
    print(f"Database info: {json.dumps(db_info, indent=2)}")
    print()
    
    # Check if there's existing data in persistent storage
    existing_docs, _ = storage.get_all_documents()
    if existing_docs:
        print(f"⚠️  WARNING: Found {len(existing_docs)} existing documents in persistent storage")
        response = input("Do you want to continue? This might create duplicates. (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
        print()
    
    # Get documents from in-memory storage via API
    print("Fetching documents from in-memory storage...")
    try:
        response = requests.get("http://localhost:8001/documents", timeout=10)
        response.raise_for_status()
        in_memory_docs = response.json()
        print(f"Found {len(in_memory_docs)} documents in in-memory storage")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching documents from in-memory storage: {e}")
        print("Make sure the RAG server is running on port 8001")
        return
    
    if not in_memory_docs:
        print("No documents found in in-memory storage. Nothing to migrate.")
        return
    
    # Display documents to be migrated
    print("\nDocuments to migrate:")
    for i, doc in enumerate(in_memory_docs, 1):
        print(f"  {i}. {doc['title']} (User: {doc.get('user_id', 'unknown')})")
    print()
    
    # Confirm migration
    response = input(f"Migrate {len(in_memory_docs)} documents to persistent storage? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Perform migration
    print("\nStarting migration...")
    migrated_count = 0
    failed_count = 0
    
    for doc in in_memory_docs:
        try:
            # Generate a new document ID for the persistent storage
            import uuid
            new_doc_id = str(uuid.uuid4())
            
            # For migration, we'll need to regenerate embeddings
            # Since we don't have the original embeddings, we'll skip them for now
            # The documents will be re-embedded when they're first accessed
            
            print(f"  Migrating: {doc['title']}...")
            
            # Add document to persistent storage
            success = storage.add_document(
                doc_id=new_doc_id,
                url=doc['url'],
                title=doc['title'],
                content=doc['content'],
                user_id=doc.get('user_id', 'default_user'),
                embedding=[],  # Empty embedding - will be regenerated on first access
                timestamp=doc.get('timestamp')
            )
            
            if success:
                migrated_count += 1
                print(f"    ✅ Success")
            else:
                failed_count += 1
                print(f"    ❌ Failed")
                
        except Exception as e:
            failed_count += 1
            print(f"    ❌ Error: {e}")
    
    print(f"\n=== Migration Complete ===")
    print(f"✅ Successfully migrated: {migrated_count} documents")
    print(f"❌ Failed to migrate: {failed_count} documents")
    
    # Show final database info
    final_db_info = storage.get_database_info()
    print(f"\nFinal database info:")
    print(f"  Total documents: {final_db_info['total_documents']}")
    print(f"  Database size: {final_db_info['database_size_mb']} MB")
    print(f"  Unique users: {final_db_info['unique_users']}")

def backup_database():
    """Create a backup of the current database"""
    print("=== Database Backup ===")
    
    import os
    from datetime import datetime
    
    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"rag_database_backup_{timestamp}.db"
    
    print(f"Creating backup: {backup_filename}")
    
    storage = get_storage()
    success = storage.backup_database(backup_filename)
    
    if success:
        print(f"✅ Backup created successfully: {backup_filename}")
    else:
        print("❌ Backup failed")

def show_database_info():
    """Show detailed database information"""
    print("=== Database Information ===")
    
    storage = get_storage()
    db_info = storage.get_database_info()
    
    print(json.dumps(db_info, indent=2))
    
    # Show user statistics
    print("\n=== User Statistics ===")
    all_stats = storage.get_user_stats()
    print(json.dumps(all_stats, indent=2))
    
    # Show recent documents
    print("\n=== Recent Documents ===")
    recent_docs = storage.get_user_documents_list(limit=10)
    for i, doc in enumerate(recent_docs, 1):
        print(f"{i}. {doc['title']} (User: {doc['user_id']})")

def main():
    """Main migration script"""
    print("RAG Storage Migration Tool")
    print("1. Migrate from in-memory to persistent storage")
    print("2. Backup current database")
    print("3. Show database information")
    print("4. Exit")
    
    choice = input("\nSelect an option (1-4): ")
    
    if choice == "1":
        migrate_in_memory_data()
    elif choice == "2":
        backup_database()
    elif choice == "3":
        show_database_info()
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main() 