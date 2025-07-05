#!/usr/bin/env python3
"""
Add Sample Data Script
Adds sample documents to the RAG database for testing and demonstration
"""

import requests
import json
from datetime import datetime

# API base URL
API_BASE = "http://localhost:8001"

# Sample documents for different users
SAMPLE_DOCUMENTS = [
    # Restaurant user documents
    {
        "url": "https://restaurant.com/menu",
        "title": "Italian Restaurant Menu",
        "content": "Our restaurant serves authentic Italian cuisine including pasta, pizza, and tiramisu. We use fresh ingredients imported from Italy. Our signature dishes include Spaghetti Carbonara, Margherita Pizza, and homemade Tiramisu. We also offer a selection of fine Italian wines.",
        "user_id": "restaurant_user"
    },
    {
        "url": "https://restaurant.com/hours",
        "title": "Restaurant Hours and Location",
        "content": "We are open Monday through Friday from 11:00 AM to 10:00 PM, and Saturday through Sunday from 12:00 PM to 11:00 PM. We are located at 123 Main Street, Downtown. Reservations are recommended for dinner service.",
        "user_id": "restaurant_user"
    },
    {
        "url": "https://restaurant.com/specials",
        "title": "Weekly Specials",
        "content": "This week's specials include: Monday - 20% off all pasta dishes, Tuesday - Wine pairing dinner, Wednesday - Family night with kids eat free, Thursday - Date night special with dessert included, Friday - Happy hour from 4-7 PM.",
        "user_id": "restaurant_user"
    },
    
    # Travel agency documents
    {
        "url": "https://travel.com/packages",
        "title": "Travel Packages to Europe",
        "content": "We offer comprehensive travel packages to Italy, France, and Spain. Our packages include flight booking, hotel reservations, guided tours, and transportation. Popular destinations include Rome, Paris, Barcelona, Florence, and Madrid. All packages come with 24/7 travel support.",
        "user_id": "travel_user"
    },
    {
        "url": "https://travel.com/booking",
        "title": "Booking Information",
        "content": "To book your travel package, please call us at 1-800-TRAVEL or visit our website. We require a 20% deposit to confirm your booking. Full payment is due 30 days before departure. Cancellation policies vary by package type.",
        "user_id": "travel_user"
    },
    {
        "url": "https://travel.com/insurance",
        "title": "Travel Insurance Options",
        "content": "We offer comprehensive travel insurance covering medical emergencies, trip cancellation, lost luggage, and flight delays. Basic coverage starts at $50 per person, premium coverage at $100 per person. Insurance must be purchased within 14 days of booking.",
        "user_id": "travel_user"
    },
    
    # Tech support documents
    {
        "url": "https://tech.com/password-reset",
        "title": "Password Reset Guide",
        "content": "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your email. If you don't receive the email, check your spam folder. Contact IT support if you continue to have issues.",
        "user_id": "tech_user"
    },
    {
        "url": "https://tech.com/network-troubleshooting",
        "title": "Network Troubleshooting",
        "content": "If you're experiencing network issues, first try restarting your router and modem. Check that all cables are properly connected. If the problem persists, run the network diagnostic tool or contact IT support. Common issues include DNS problems and firewall settings.",
        "user_id": "tech_user"
    },
    {
        "url": "https://tech.com/software-installation",
        "title": "Software Installation Guide",
        "content": "To install new software, download the installer from the approved software repository. Run the installer as administrator and follow the setup wizard. Make sure to restart your computer after installation. Contact IT if you encounter any errors during installation.",
        "user_id": "tech_user"
    },
    
    # General company documents
    {
        "url": "https://company.com/about",
        "title": "About Our Company",
        "content": "We are a leading technology company specializing in innovative solutions for businesses. Founded in 2010, we have served over 1000 clients worldwide. Our mission is to help businesses grow through technology. We offer consulting, development, and support services.",
        "user_id": "company_user"
    },
    {
        "url": "https://company.com/contact",
        "title": "Contact Information",
        "content": "You can reach us at info@company.com or call us at 1-800-COMPANY. Our office hours are Monday through Friday, 9 AM to 6 PM EST. For urgent support, call our 24/7 hotline at 1-800-SUPPORT. We're located at 456 Business Ave, Tech City.",
        "user_id": "company_user"
    }
]

def add_document(doc):
    """Add a single document to the database"""
    try:
        response = requests.post(
            f"{API_BASE}/add-document",
            json=doc,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            print(f"✅ Added: {doc['title']} (User: {doc['user_id']})")
            return True
        else:
            print(f"❌ Failed to add: {doc['title']} - {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error adding {doc['title']}: {e}")
        return False

def main():
    """Main function to add sample data"""
    print("🚀 Adding Sample Data to RAG Database")
    print(f"API Base: {API_BASE}")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server is running")
            print(f"Storage type: {health.get('storage', 'Unknown')}")
            print()
        else:
            print("❌ Server is not responding properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the RAG server is running on http://localhost:8001")
        return
    
    # Get current stats
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"Current documents: {stats.get('document_count', 0)}")
            print(f"Current users: {stats.get('unique_users', 0)}")
            print()
    except Exception as e:
        print(f"Warning: Could not get current stats: {e}")
    
    # Add documents
    print("📄 Adding sample documents...")
    success_count = 0
    failed_count = 0
    
    for doc in SAMPLE_DOCUMENTS:
        if add_document(doc):
            success_count += 1
        else:
            failed_count += 1
    
    print()
    print(f"=== Summary ===")
    print(f"✅ Successfully added: {success_count} documents")
    print(f"❌ Failed to add: {failed_count} documents")
    
    # Get final stats
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\nFinal database state:")
            print(f"Total documents: {stats.get('document_count', 0)}")
            print(f"Unique users: {stats.get('unique_users', 0)}")
    except Exception as e:
        print(f"Warning: Could not get final stats: {e}")
    
    print()
    print("🎉 Sample data addition complete!")
    print("You can now use the database manager at: http://localhost:8001/db-manager.html")

if __name__ == "__main__":
    main() 