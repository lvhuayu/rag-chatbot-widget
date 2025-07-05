# 🧪 Multi-Tenant RAG Chatbot - Testing Instructions

## 🚀 Quick Start Testing

### Step 1: Start the Backend Server

```bash
# Start the RAG backend server
python backend/rag_server_simple.py
```

### Step 2: Run the Interactive Test Script

```bash
# Run the comprehensive test script
python test_multi_tenant_interactions.py
```

This script will:
- ✅ Insert mock data for 4 different users
- ✅ Test user-specific searches
- ✅ Verify data isolation
- ✅ Show statistics for each user

## 📊 Test Users and Their Knowledge

The test script creates 4 different users with unique knowledge bases:

### 1. 🏢 Software Company (`company_abc_123`)
**Knowledge Base:**
- About Company ABC (software development expertise)
- Our Services (web apps, mobile apps, cloud solutions)
- Technologies We Use (React, Node.js, Python, AWS)
- Pricing Information (project-based pricing)

**Test Queries:**
- "What services do you offer?"
- "What technologies do you use?"
- "How much do your projects cost?"

### 2. 🍝 Italian Restaurant (`restaurant_xyz`)
**Knowledge Base:**
- Our Menu (Italian cuisine, signature dishes)
- Location and Hours (downtown location, hours)
- Our Chef (Chef Marco Rossi, 20 years experience)
- Private Events (weddings, corporate dinners)

**Test Queries:**
- "What food do you serve?"
- "What are your opening hours?"
- "Can you host private events?"

### 3. 💪 Fitness Center (`fitness_center_456`)
**Knowledge Base:**
- Our Facilities (equipment, pool, sauna, spa)
- Group Classes (yoga, Pilates, spinning, Zumba)
- Personal Training (customized plans, nutrition)
- Membership Options (flexible plans, discounts)

**Test Queries:**
- "What facilities do you have?"
- "What classes do you offer?"
- "How much does personal training cost?"

### 4. ✈️ Travel Agency (`travel_agency_789`)
**Knowledge Base:**
- Popular Destinations (Bali, Maldives, Santorini)
- Travel Services (flights, hotels, insurance)
- Cruise Packages (Caribbean, Mediterranean, Alaska)

**Test Queries:**
- "What destinations do you offer?"
- "Do you provide cruise packages?"
- "What travel services do you have?"

## 🔍 Manual Testing

### Test 1: User-Specific Searches

```bash
# Test software company
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What services do you offer?",
    "user_id": "company_abc_123"
  }'

# Test restaurant
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What food do you serve?",
    "user_id": "restaurant_xyz"
  }'

# Test fitness center
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What facilities do you have?",
    "user_id": "fitness_center_456"
  }'
```

### Test 2: Data Isolation

```bash
# Software company searching for restaurant info (should find nothing)
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Italian food",
    "user_id": "company_abc_123"
  }'

# Restaurant searching for software info (should find nothing)
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "software development",
    "user_id": "restaurant_xyz"
  }'
```

### Test 3: User Statistics

```bash
# Get stats for each user
curl "http://localhost:8001/stats?user_id=company_abc_123"
curl "http://localhost:8001/stats?user_id=restaurant_xyz"
curl "http://localhost:8001/stats?user_id=fitness_center_456"
curl "http://localhost:8001/stats?user_id=travel_agency_789"

# Get overall stats
curl "http://localhost:8001/stats"
```

### Test 4: User Documents

```bash
# List documents for each user
curl "http://localhost:8001/documents?user_id=company_abc_123"
curl "http://localhost:8001/documents?user_id=restaurant_xyz"
curl "http://localhost:8001/documents?user_id=fitness_center_456"
curl "http://localhost:8001/documents?user_id=travel_agency_789"
```

## 🌐 Frontend Testing

### Test with Interactive Demo

1. Open `public/multi-tenant-example.html` in your browser
2. Try different user IDs:
   - `company_abc_123`
   - `restaurant_xyz`
   - `fitness_center_456`
   - `travel_agency_789`
3. Ask questions relevant to each business
4. Verify that responses are specific to each user's knowledge

### Test with Function Test Page

1. Open `public/test-multi-tenant.html` in your browser
2. Test all 4 methods of setting userId
3. Verify that each method works correctly

## ✅ Expected Results

### User-Specific Responses

Each user should only get responses based on their own knowledge:

- **company_abc_123**: Software development, web apps, pricing
- **restaurant_xyz**: Italian food, dining hours, chef info
- **fitness_center_456**: Gym facilities, classes, training
- **travel_agency_789**: Travel destinations, cruises, services

### Data Isolation

Cross-user searches should return no results:
- Software company searching for "Italian food" → No results
- Restaurant searching for "software development" → No results
- Fitness center searching for "travel packages" → No results

### Statistics

Each user should show correct document counts:
- company_abc_123: 4 documents
- restaurant_xyz: 4 documents
- fitness_center_456: 4 documents
- travel_agency_789: 3 documents
- Overall: 15 documents

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check if port 8001 is available
netstat -an | findstr :8001

# Kill process if needed
taskkill /F /PID <process_id>
```

### No Search Results
- Ensure backend is running
- Check that mock data was inserted
- Verify user_id is correct
- Check backend logs for errors

### Cross-User Data Leakage
- This indicates a bug in the filtering logic
- Check the search endpoint implementation
- Verify user_id filtering is working

## 📈 Performance Testing

### Load Testing
```bash
# Test multiple concurrent searches
for i in {1..10}; do
  curl -X POST "http://localhost:8001/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query", "user_id": "company_abc_123"}' &
done
wait
```

### Memory Usage
- Monitor memory usage during testing
- Check for memory leaks with large document sets
- Verify efficient vector storage

## 🎯 Success Criteria

✅ **Multi-tenant isolation working**
- Each user only sees their own documents
- No cross-user data access

✅ **Search functionality working**
- Relevant results for user-specific queries
- No results for irrelevant queries

✅ **Statistics accurate**
- Correct document counts per user
- Overall statistics match expectations

✅ **Frontend integration working**
- Different user IDs show different responses
- All 4 configuration methods work

✅ **Performance acceptable**
- Fast search responses
- Efficient memory usage
- No memory leaks

## 🚀 Next Steps

After successful testing:

1. **Deploy to production** with real user data
2. **Add persistent storage** (database instead of in-memory)
3. **Implement user authentication** and authorization
4. **Add monitoring and analytics**
5. **Scale for multiple users**

---

**Happy Testing! 🎉** 