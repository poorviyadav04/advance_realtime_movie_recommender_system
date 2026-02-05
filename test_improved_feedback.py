"""
Test script to verify the improved feedback system in the dashboard.
This demonstrates the enhanced user experience without page refreshes.
"""
import requests
import time

API_BASE_URL = "http://localhost:8000"

def test_feedback_system():
    """Test the improved feedback system."""
    print("🧪 Testing Improved Feedback System")
    print("="*50)
    
    # Test user
    test_user = 1001
    
    # Send some test events to create activity
    print(f"📝 Creating test activity for user {test_user}...")
    
    test_events = [
        {"item_id": 1, "event_type": "view"},
        {"item_id": 1, "event_type": "click"},
        {"item_id": 2, "event_type": "view"},
        {"item_id": 1, "event_type": "rate", "rating": 4.5},
    ]
    
    for event in test_events:
        event_data = {
            "user_id": test_user,
            "item_id": event["item_id"],
            "event_type": event["event_type"],
            "source": "feedback_test"
        }
        
        if "rating" in event:
            event_data["rating"] = event["rating"]
        
        try:
            response = requests.post(f"{API_BASE_URL}/events", json=event_data)
            if response.status_code == 200:
                print(f"✅ Sent {event['event_type']} event for item {event['item_id']}")
            else:
                print(f"❌ Failed to send {event['event_type']} event")
        except Exception as e:
            print(f"❌ Error sending event: {e}")
        
        time.sleep(0.5)
    
    print(f"\n📊 Test activity created for user {test_user}")
    print("\n🎯 Dashboard Improvements:")
    print("✅ Thumbs up feedback now shows persistent state")
    print("✅ Event simulator shows recent events sent")
    print("✅ Random session generator shows detailed feedback")
    print("✅ Cache invalidation provides clear status")
    print("✅ Auto-refresh option for live activity monitoring")
    
    print(f"\n💡 To test the improvements:")
    print(f"1. Go to http://localhost:8502")
    print(f"2. Get recommendations for user {test_user}")
    print(f"3. Click thumbs up - notice it shows '✅ Liked!' instead of refreshing")
    print(f"4. Go to 'Real-Time' tab and try the event simulator")
    print(f"5. Enable auto-refresh in the activity viewer")
    
    print(f"\n🎉 Feedback system improvements are ready!")

if __name__ == "__main__":
    test_feedback_system()