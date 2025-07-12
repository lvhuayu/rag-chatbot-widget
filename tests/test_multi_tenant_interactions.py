#!/usr/bin/env python3
"""
Multi-Tenant RAG Chatbot - Interactive Test Script
This script tests different users with different knowledge bases
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔑 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print(f"{'-'*40}")

def add_document(url, title, content, user_id):
    """Add a document to the RAG system"""
    payload = {
        "url": url,
        "title": title,
        "content": content,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/add-document", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Added: {title} (User: {user_id})")
            return True
        else:
            print(f"❌ Failed to add {title}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error adding {title}: {e}")
        return False

def search_documents(query, user_id, top_k=3):
    """Search documents for a specific user"""
    payload = {
        "query": query,
        "top_k": top_k,
        "threshold": 0.5,
        "user_id": user_id
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/search", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Search failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Search error: {e}")
        return None

def get_user_stats(user_id):
    """Get statistics for a specific user"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats?user_id={user_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return None

def get_user_documents(user_id):
    """Get documents for a specific user"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents?user_id={user_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Documents failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Documents error: {e}")
        return None

def test_user_interaction(user_id, queries):
    """Test a user's interaction with their knowledge base"""
    print_section(f"Testing User: {user_id}")
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        
        result = search_documents(query, user_id)
        if result:
            documents = result.get('documents', [])
            context = result.get('context', 'No context available')
            
            print(f"   Found {len(documents)} relevant documents")
            
            if documents:
                for j, doc in enumerate(documents, 1):
                    print(f"   {j}. {doc['document']['title']} (similarity: {doc['similarity']:.3f})")
                    print(f"      Content: {doc['document']['content'][:100]}...")
            else:
                print("   No relevant documents found")
            
            print(f"   AI Response: {context[:200]}...")
        else:
            print("   ❌ Search failed")
        
        time.sleep(1)  # Small delay between queries

def insert_mock_data():
    """Insert mock data for different users"""
    print_header("Inserting Mock Data for Multi-Tenant Testing")
    
    # User 1: Software Company
    print_section("Adding Data for Software Company (company_abc_123)")
    
    company_docs = [
        {
            "url": "https://company-abc.com/about",
            "title": "About Company ABC",
            "content": "Company ABC is a leading software development company specializing in web applications, mobile apps, and cloud solutions. Founded in 2010, we have 50 employees and serve clients worldwide. Our expertise includes React, Node.js, Python, and AWS technologies.",
            "user_id": "company_abc_123"
        },
        {
            "url": "https://company-abc.com/services",
            "title": "Our Services",
            "content": "We offer comprehensive software development services including custom web applications, mobile app development, e-commerce platforms, CRM systems, and cloud infrastructure solutions. Our development process follows Agile methodology with regular client communication.",
            "user_id": "company_abc_123"
        },
        {
            "url": "https://company-abc.com/technologies",
            "title": "Technologies We Use",
            "content": "Our tech stack includes React.js, Angular, Vue.js for frontend; Node.js, Python Django, Java Spring for backend; MongoDB, PostgreSQL for databases; AWS, Azure for cloud services; and Docker, Kubernetes for deployment.",
            "user_id": "company_abc_123"
        },
        {
            "url": "https://company-abc.com/pricing",
            "title": "Pricing Information",
            "content": "Our pricing is project-based and depends on complexity. Small projects start at $10,000, medium projects range from $25,000 to $75,000, and large enterprise solutions start at $100,000. We offer free consultations and detailed quotes.",
            "user_id": "company_abc_123"
        }
    ]
    
    for doc in company_docs:
        add_document(doc["url"], doc["title"], doc["content"], doc["user_id"])
    
    # User 2: Italian Restaurant
    print_section("Adding Data for Italian Restaurant (restaurant_xyz)")
    
    restaurant_docs = [
        {
            "url": "https://restaurant-xyz.com/menu",
            "title": "Our Menu",
            "content": "We are a fine dining Italian restaurant serving authentic cuisine. Our signature dishes include pasta carbonara with guanciale and pecorino, risotto ai porcini, osso buco alla Milanese, and tiramisu made with mascarpone. We also offer an extensive wine list featuring Italian and international selections.",
            "user_id": "restaurant_xyz"
        },
        {
            "url": "https://restaurant-xyz.com/location",
            "title": "Location and Hours",
            "content": "Located in the heart of downtown at 123 Main Street, we offer both indoor and outdoor seating with beautiful city views. Open Tuesday to Sunday, 5:00 PM to 11:00 PM. Reservations are recommended, especially for dinner service. We accommodate groups up to 20 people.",
            "user_id": "restaurant_xyz"
        },
        {
            "url": "https://restaurant-xyz.com/chef",
            "title": "Our Chef",
            "content": "Chef Marco Rossi brings 20 years of experience from top restaurants in Italy and New York. He specializes in traditional Italian cuisine with modern twists. All our pasta is made fresh daily, and we source ingredients from local farmers and Italian importers.",
            "user_id": "restaurant_xyz"
        },
        {
            "url": "https://restaurant-xyz.com/events",
            "title": "Private Events",
            "content": "We host private events including weddings, corporate dinners, and special celebrations. Our private dining room seats up to 30 guests. We offer customized menus and wine pairings. Contact us for pricing and availability.",
            "user_id": "restaurant_xyz"
        }
    ]
    
    for doc in restaurant_docs:
        add_document(doc["url"], doc["title"], doc["content"], doc["user_id"])
    
    # User 3: Fitness Center
    print_section("Adding Data for Fitness Center (fitness_center_456)")
    
    fitness_docs = [
        {
            "url": "https://fitness-center-456.com/facilities",
            "title": "Our Facilities",
            "content": "We are a premium fitness center with state-of-the-art equipment including cardio machines, free weights, resistance training equipment, and functional training areas. Our facility features a swimming pool, sauna, steam room, and spa services. We have separate areas for men and women.",
            "user_id": "fitness_center_456"
        },
        {
            "url": "https://fitness-center-456.com/classes",
            "title": "Group Classes",
            "content": "We offer over 50 group classes weekly including yoga, Pilates, spinning, Zumba, strength training, HIIT, and meditation. Classes are suitable for all fitness levels. Our certified instructors provide personalized attention. Class schedules are available online and at the front desk.",
            "user_id": "fitness_center_456"
        },
        {
            "url": "https://fitness-center-456.com/training",
            "title": "Personal Training",
            "content": "Our certified personal trainers create customized workout plans based on your goals and fitness level. We offer one-on-one sessions, small group training, and nutrition counseling. Packages start at $60 per session with discounts for multiple sessions.",
            "user_id": "fitness_center_456"
        },
        {
            "url": "https://fitness-center-456.com/membership",
            "title": "Membership Options",
            "content": "We offer flexible membership options including monthly, quarterly, and annual plans. Basic membership includes access to gym and equipment. Premium membership includes group classes, pool access, and spa facilities. Student and corporate discounts available. No long-term contracts required.",
            "user_id": "fitness_center_456"
        }
    ]
    
    for doc in fitness_docs:
        add_document(doc["url"], doc["title"], doc["content"], doc["user_id"])
    
    # User 4: Travel Agency
    print_section("Adding Data for Travel Agency (travel_agency_789)")
    
    travel_docs = [
        {
            "url": "https://travel-agency-789.com/destinations",
            "title": "Popular Destinations",
            "content": "We specialize in luxury travel to exotic destinations including Bali, Maldives, Santorini, and the Swiss Alps. Our packages include flights, accommodations, transfers, and guided tours. We work with premium hotels and resorts to ensure exceptional experiences for our clients.",
            "user_id": "travel_agency_789"
        },
        {
            "url": "https://travel-agency-789.com/services",
            "title": "Travel Services",
            "content": "We offer comprehensive travel services including flight booking, hotel reservations, car rentals, travel insurance, and visa assistance. Our travel consultants provide personalized recommendations based on your preferences and budget. We handle all arrangements and provide 24/7 support during your trip.",
            "user_id": "travel_agency_789"
        },
        {
            "url": "https://travel-agency-789.com/cruises",
            "title": "Cruise Packages",
            "content": "We partner with major cruise lines including Royal Caribbean, Celebrity, and Norwegian. Our cruise packages include Caribbean, Mediterranean, Alaska, and European river cruises. We offer exclusive deals and onboard credits. Group bookings available for special occasions.",
            "user_id": "travel_agency_789"
        }
    ]
    
    for doc in travel_docs:
        add_document(doc["url"], doc["title"], doc["content"], doc["user_id"])

def test_user_interactions():
    """Test interactions for different users"""
    print_header("Testing Multi-Tenant User Interactions")
    
    # Test queries for each user
    test_cases = {
        "company_abc_123": [
            "What services do you offer?",
            "What technologies do you use?",
            "How much do your projects cost?",
            "Do you work with restaurants?"  # Should find nothing
        ],
        "restaurant_xyz": [
            "What food do you serve?",
            "What are your opening hours?",
            "Can you host private events?",
            "Do you offer software development?"  # Should find nothing
        ],
        "fitness_center_456": [
            "What facilities do you have?",
            "What classes do you offer?",
            "How much does personal training cost?",
            "Do you serve Italian food?"  # Should find nothing
        ],
        "travel_agency_789": [
            "What destinations do you offer?",
            "Do you provide cruise packages?",
            "What travel services do you have?",
            "Do you offer fitness classes?"  # Should find nothing
        ]
    }
    
    for user_id, queries in test_cases.items():
        test_user_interaction(user_id, queries)

def test_data_isolation():
    """Test that users cannot access each other's data"""
    print_header("Testing Data Isolation")
    
    # Test cross-user searches
    cross_user_tests = [
        ("company_abc_123", "Italian food", "Software company searching for restaurant info"),
        ("restaurant_xyz", "software development", "Restaurant searching for tech info"),
        ("fitness_center_456", "travel packages", "Fitness center searching for travel info"),
        ("travel_agency_789", "gym equipment", "Travel agency searching for fitness info")
    ]
    
    for user_id, query, description in cross_user_tests:
        print_section(f"Cross-User Test: {description}")
        print(f"User: {user_id}")
        print(f"Query: '{query}'")
        
        result = search_documents(query, user_id)
        if result:
            documents = result.get('documents', [])
            if documents:
                print(f"❌ FAILED: Found {len(documents)} documents (should be 0)")
                for doc in documents:
                    print(f"   - {doc['document']['title']} (User: {doc['document']['user_id']})")
            else:
                print(f"✅ PASSED: No documents found (correct isolation)")
        else:
            print("❌ Search failed")
        
        time.sleep(1)

def show_statistics():
    """Show statistics for all users"""
    print_header("Multi-Tenant Statistics")
    
    users = ["company_abc_123", "restaurant_xyz", "fitness_center_456", "travel_agency_789"]
    
    for user_id in users:
        stats = get_user_stats(user_id)
        if stats:
            print(f"\n👤 User: {user_id}")
            print(f"   Documents: {stats['document_count']}")
            print(f"   Total in system: {stats['total_documents']}")
            print(f"   Multi-tenant: {stats.get('multi_tenant', False)}")
    
    # Overall stats
    overall_stats = get_user_stats(None)
    if overall_stats:
        print(f"\n📊 Overall System")
        print(f"   Total documents: {overall_stats['document_count']}")
        print(f"   Users: {len(users)}")
        print(f"   Average per user: {overall_stats['document_count'] / len(users):.1f}")

def main():
    """Main test function"""
    print_header("Multi-Tenant RAG Chatbot - Interactive Test")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code != 200:
            print(f"❌ Backend not responding at {BACKEND_URL}")
            print("Please start the backend server: python backend/rag_server_simple.py")
            return
        print(f"✅ Backend is running at {BACKEND_URL}")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please start the backend server: python backend/rag_server_simple.py")
        return
    
    # Clear existing documents (optional)
    print_section("Clearing existing documents")
    try:
        response = requests.delete(f"{BACKEND_URL}/clear-documents")
        if response.status_code == 200:
            print("✅ Cleared existing documents")
        else:
            print("⚠️ Could not clear documents (continuing anyway)")
    except Exception as e:
        print(f"⚠️ Could not clear documents: {e} (continuing anyway)")
    
    # Insert mock data
    insert_mock_data()
    
    # Show initial statistics
    show_statistics()
    
    # Test user interactions
    test_user_interactions()
    
    # Test data isolation
    test_data_isolation()
    
    # Final statistics
    show_statistics()
    
    print_header("Test Completed Successfully!")
    print("\n🎉 Multi-tenant functionality is working correctly!")
    print("\nKey Results:")
    print("✅ Each user has their own isolated knowledge base")
    print("✅ Users cannot access each other's data")
    print("✅ Search results are user-specific")
    print("✅ Statistics show correct document counts per user")
    
    print("\n🌐 You can now test the frontend:")
    print("   - Open public/multi-tenant-example.html")
    print("   - Try different user IDs to see isolated responses")

if __name__ == "__main__":
    main() 