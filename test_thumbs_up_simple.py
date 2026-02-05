"""
Simple test to verify thumbs up functionality by directly testing the send_event function.
"""
import requests
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import the send_event function from dashboard
API_BASE_URL = "http://localhost:8000"

def send_event(user_id: int, item_id: int, event_type: str, rating: float = None):
    """Send an event to the API - copied from dashboard."""
    try:
        event_data = {
            "user_id": user_id,
            "item_id": item_id,
            "event_type": event_type,
            "source": "dashboard_test"
        }
        if rating is not None:
            event_data["rating"] = rating
        
        # Debug: Print what we're sending
        print(f"🔍 DEBUG: Sending event - User: {user_id}, Item: {item_id}, Type: {event_type}")
            
        response = requests.post(
            f"{API_BASE_URL}/events",
            json=event_data,
            timeout=5
        )
        
        # Debug: Print response
        print(f"🔍 DEBUG: Response status: {response.status_code}")
        if response.status_code == 200:
            print(f"🔍 DEBUG: Response: {response.json()}")
        else:
            print(f"🔍 DEBUG: Error response: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"🔍 DEBUG: Exception in send_event: {e}")
        return False

def test_thumbs_up():
    """Test the thumbs up functionality."""
    print("🧪 Testing Thumbs Up Functionality")
    print("="*50)
    
    user_id = 101
    item_id = 1
    
    print(f"Testing thumbs up for User {user_id}, Item {item_id}")
    
    # Test the send_event function directly
    success = send_event(user_id, item_id, "click")
    
    if success:
        print("✅ send_event function works correctly!")
        
        # Check if event was stored
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/activity?limit=10")
        if response.status_code == 200:
            activity = response.json()
            print(f"📊 User {user_id} now has {activity['total_events']} events")
            
            if activity['recent_events']:
                latest = activity['recent_events'][0]
                print(f"🎯 Latest event: {latest['event_type']} on item {latest['item_id']} at {latest['timestamp']}")
            
            return True
        else:
            print("❌ Failed to retrieve activity")
            return False
    else:
        print("❌ send_event function failed!")
        return False

def main():
    print("🔍 DEBUGGING THUMBS UP BUTTON")
    print("="*50)
    
    success = test_thumbs_up()
    
    if success:
        print("\n✅ The send_event function works correctly!")
        print("💡 The issue is that the thumbs up button in the dashboard is not calling send_event")
        print("\n🎯 Next steps:")
        print("1. Go to dashboard")
        print("2. Get recommendations for User 101")
        print("3. Click thumbs up")
        print("4. Check the Streamlit terminal for debug messages")
        print("5. If no debug messages appear, the button is not working")
    else:
        print("\n❌ The send_event function has issues")

if __name__ == "__main__":
    main()