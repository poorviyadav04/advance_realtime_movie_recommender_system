#!/usr/bin/env python3
"""
Test script to verify the thumbs up button fix is working.
This script will test the API endpoints that the thumbs up button calls.
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is not running: {e}")
        return False

def test_send_event(user_id, item_id, event_type="click"):
    """Test sending an event (what thumbs up button does)"""
    try:
        event_data = {
            "user_id": user_id,
            "item_id": item_id,
            "event_type": event_type,
            "source": "test_script"
        }
        
        print(f"🔄 Sending event: User {user_id}, Item {item_id}, Type {event_type}")
        response = requests.post(f"{API_BASE_URL}/events", json=event_data, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Event sent successfully! Event ID: {result.get('event_id')}")
            return True
        else:
            print(f"❌ Failed to send event: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending event: {e}")
        return False

def test_get_user_activity(user_id):
    """Test getting user activity (to verify event was recorded)"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/activity?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('recent_events', [])  # Fixed: use 'recent_events' not 'events'
            print(f"✅ User activity retrieved: {len(events)} events")
            
            # Show recent events
            if events:
                print("📋 Recent events:")
                for event in events[:3]:
                    print(f"   - Event {event['id']}: User {data['user_id']} → Item {event['item_id']} ({event['event_type']})")
            else:
                print("📋 No events found for this user")
            return True
        else:
            print(f"❌ Failed to get user activity: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting user activity: {e}")
        return False

def test_get_recommendations(user_id):
    """Test getting recommendations (to see what movies are available for thumbs up)"""
    try:
        # Use POST request with JSON body
        request_data = {
            "user_id": user_id,
            "n_recommendations": 3,
            "model_type": "hybrid"
        }
        
        response = requests.post(f"{API_BASE_URL}/recommend", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {len(data['recommendations'])} recommendations for user {user_id}")
            
            # Show recommendations
            print("🎬 Sample recommendations:")
            for i, rec in enumerate(data['recommendations'][:3], 1):
                print(f"   {i}. {rec['title']} (ID: {rec['item_id']}, Score: {rec['score']:.3f})")
            
            return data['recommendations']
        else:
            print(f"❌ Failed to get recommendations: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error getting recommendations: {e}")
        return []

def main():
    print("🧪 Testing Thumbs Up Button Fix")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ API is not running. Please start it with: uvicorn api.main:app --reload --port 8000")
        return
    
    print()
    
    # Test with a sample user
    test_user_id = 100
    
    # Get recommendations first
    print(f"1️⃣ Getting recommendations for user {test_user_id}...")
    recommendations = test_get_recommendations(test_user_id)
    
    if not recommendations:
        print("❌ No recommendations available for testing")
        return
    
    print()
    
    # Test sending an event (thumbs up)
    print("2️⃣ Testing thumbs up event...")
    test_item_id = recommendations[0]['item_id']  # Use first recommendation
    test_movie_title = recommendations[0]['title']
    
    print(f"   Simulating thumbs up for: {test_movie_title} (ID: {test_item_id})")
    
    if test_send_event(test_user_id, test_item_id, "click"):
        print("✅ Thumbs up event sent successfully!")
    else:
        print("❌ Failed to send thumbs up event")
        return
    
    print()
    
    # Wait a moment for event to be processed
    print("3️⃣ Waiting for event to be processed...")
    time.sleep(1)
    
    # Check user activity
    print("4️⃣ Checking user activity...")
    test_get_user_activity(test_user_id)
    
    print()
    print("🎉 Test completed!")
    print()
    print("📋 What to test in the dashboard:")
    print(f"   1. Go to http://localhost:8503")
    print(f"   2. Set User ID to {test_user_id}")
    print(f"   3. Click 'Get Recommendations'")
    print(f"   4. Click thumbs up on any movie")
    print(f"   5. Go to Real-Time tab → User Activity")
    print(f"   6. Check if the thumbs up event appears")
    print()
    print("🔧 If thumbs up still doesn't work:")
    print("   - Check browser console for JavaScript errors")
    print("   - Look for debug messages in the terminal running Streamlit")
    print("   - Try the 'Clear All Likes' button to reset state")

if __name__ == "__main__":
    main()