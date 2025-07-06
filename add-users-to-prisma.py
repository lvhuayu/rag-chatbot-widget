#!/usr/bin/env python3
"""
Add Users to Prisma Database
Adds sample users to the Prisma database for testing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the upload portal server directory to the path to access Prisma client
upload_server_path = Path("upload_portal/rag-document-uploader/server")
if upload_server_path.exists():
    sys.path.insert(0, str(upload_server_path))

try:
    from prisma import Prisma
except ImportError:
    print("❌ Prisma client not found. Please run 'npx prisma generate' first.")
    sys.exit(1)

# Sample users data
SAMPLE_USERS = [
    {
        "username": "john_doe",
        "password": "password123",
        "publicKey": "pk_test_john_123"
    },
    {
        "username": "jane_smith", 
        "password": "password456",
        "publicKey": "pk_test_jane_456"
    },
    {
        "username": "admin_user",
        "password": "admin123", 
        "publicKey": "pk_test_admin_789"
    },
    {
        "username": "demo_user",
        "password": "demo123",
        "publicKey": "pk_test_demo_101"
    },
    {
        "username": "test_user",
        "password": "test123",
        "publicKey": "pk_test_test_202"
    }
]

async def add_users():
    """Add sample users to the database"""
    prisma = Prisma()
    
    try:
        await prisma.connect()
        print("✅ Connected to Prisma database")
        
        added_count = 0
        skipped_count = 0
        
        for user_data in SAMPLE_USERS:
            try:
                # Check if user already exists
                existing_user = await prisma.user.find_unique(
                    where={"username": user_data["username"]}
                )
                
                if existing_user:
                    print(f"⏭️  User '{user_data['username']}' already exists, skipping...")
                    skipped_count += 1
                    continue
                
                # Create new user
                user = await prisma.user.create(data=user_data)
                print(f"✅ Added user: {user.username} (ID: {user.id})")
                added_count += 1
                
            except Exception as e:
                print(f"❌ Error adding user '{user_data['username']}': {e}")
        
        print(f"\n📊 Summary:")
        print(f"✅ Users added: {added_count}")
        print(f"⏭️  Users skipped (already exist): {skipped_count}")
        
        # Get total user count
        total_users = await prisma.user.count()
        print(f"📈 Total users in database: {total_users}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        await prisma.disconnect()

def main():
    """Main function"""
    print("🚀 Adding Sample Users to Prisma Database")
    print("==========================================")
    
    # Check if we're in the right directory
    if not Path("prisma/schema.prisma").exists():
        print("❌ Error: prisma/schema.prisma not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Run the async function
    asyncio.run(add_users())
    
    print("\n🎉 User addition complete!")
    print("You can now:")
    print("1. Use these usernames to test the upload portal")
    print("2. Add documents for these users via the RAG API")
    print("3. Test multi-tenant functionality")

if __name__ == "__main__":
    main() 