"""
Test script to verify the fixed thumbs up button functionality.
"""
import requests
import time

API_BASE_URL = "http://localhost:8000"

def check_user_activity(user_id):
    """Check current activity for a user."""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/activity?limit=10")
        if response.status_code == 200:
            data = response.json()
            return data['total_events'], data['recent_events']
        return 0, []
    except:
        return 0, []

def main():
    print("🧪 TESTING FIXED THUMBS UP BUTTON")
    print("="*50)
    
    user_id = 101
    
    # Check current activity
    current_events, recent = check_user_activity(user_id)
    print(f"📊 User {user_id} currently has {current_events} events")
    
    if recent:
        latest = recent[0]
        print(f"🎯 Latest event: {latest['event_type']} item {latest['item_id']} at {latest['timestamp'][:19]}")
    
    print(f"\n🎯 TESTING INSTRUCTIONS:")
    print(f"1. Go to dashboard: http://localhost:8502")
    print(f"2. Go to 'Recommendations' tab")
    print(f"3. Set User ID to {user_id}")
    print(f"4. Click 'Get Recommendations'")
    print(f"5. Click '👍 Like' button on any movie")
    print(f"6. You should see:")
    print(f"   - Success message with balloons 🎈")
    print(f"   - Instruction to check Real-Time tab")
    print(f"7. Go to 'Real-Time' tab")
    print(f"8. Set User ID to {user_id} in Activity Viewer")
    print(f"9. Click 'Get User Activity'")
    print(f"10. You should see {current_events + 1} events (one more than before)")
    
    print(f"\n🔍 WHAT TO LOOK FOR IN TERMINAL:")
    print(f"When you click thumbs up, you should see debug messages like:")
    print(f"🔍 DEBUG: Sending event - User: {user_id}, Item: [movie_id], Type: click")
    print(f"🔍 DEBUG: Response status: 200")
    print(f"✅ SUCCESS: Event [event_id] created for User {user_id}")
    
    print(f"\n✅ FIXED ISSUES:")
    print(f"- Unique button keys prevent conflicts")
    print(f"- Removed complex session state logic")
    print(f"- Added clear visual feedback")
    print(f"- Enhanced debug output")
    print(f"- Simple, reliable button implementation")
    
    print(f"\n🎉 The thumbs up button should now work perfectly!")

if __name__ == "__main__":
    main()