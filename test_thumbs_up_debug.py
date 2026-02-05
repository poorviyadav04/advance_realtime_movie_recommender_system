"""
Debug script to test the thumbs up functionality.
"""
import requests
import time

API_BASE_URL = "http://localhost:8000"

def test_thumbs_up_for_user(user_id, item_id):
    """Test sending a thumbs up event for a specific user."""
    print(f"🧪 Testing thumbs up for User {user_id}, Item {item_id}")
    
    # Send the event
    event_data = {
        "user_id": user_id,
        "item_id": item_id,
        "event_type": "click",
        "source": "thumbs_up_test"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/events", json=event_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Event sent successfully! Event ID: {result.get('event_id')}")
            
            # Wait a moment for processing
            time.sleep(1)
            
            # Check if we can retrieve it
            activity_response = requests.get(f"{API_BASE_URL}/users/{user_id}/activity?limit=5")
            if activity_response.status_code == 200:
                activity = activity_response.json()
                print(f"📊 User {user_id} now has {activity['total_events']} events")
                
                if activity['recent_events']:
                    latest_event = activity['recent_events'][0]
                    print(f"🎯 Latest event: {latest_event['event_type']} on item {latest_event['item_id']} at {latest_event['timestamp']}")
                    return True
                else:
                    print("❌ No events found in activity")
                    return False
            else:
                print(f"❌ Failed to get activity: {activity_response.status_code}")
                return False
        else:
            print(f"❌ Failed to send event: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 DEBUGGING THUMBS UP FUNCTIONALITY")
    print("="*50)
    
    # Test for user 653 (the one you were testing)
    success1 = test_thumbs_up_for_user(653, 1)
    
    print("\n" + "-"*30)
    
    # Test for user 700 (the one from earlier)
    success2 = test_thumbs_up_for_user(700, 2)
    
    print("\n" + "="*50)
    if success1 and success2:
        print("✅ Thumbs up functionality is working correctly!")
        print("💡 The issue might be in the dashboard UI refresh")
    else:
        print("❌ There's an issue with the thumbs up functionality")
    
    print("\n🎯 To test in dashboard:")
    print("1. Go to Real-Time tab")
    print("2. Set User ID to 653 in Activity Viewer")
    print("3. Click 'Get User Activity'")
    print("4. You should see the test events above")

if __name__ == "__main__":
    main()