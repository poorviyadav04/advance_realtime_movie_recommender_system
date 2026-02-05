"""
Test the API activity endpoint directly to debug the dashboard issue.
"""
import requests

API_BASE_URL = "http://localhost:8000"

def test_activity_endpoint():
    """Test the activity endpoint for different users."""
    print("🧪 Testing API Activity Endpoint")
    print("="*50)
    
    test_users = [100, 150, 653, 700]
    
    for user_id in test_users:
        print(f"\n👤 Testing User {user_id}:")
        
        try:
            # Test the endpoint
            url = f"{API_BASE_URL}/users/{user_id}/activity?limit=10"
            print(f"   URL: {url}")
            
            response = requests.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Total events: {data['total_events']}")
                print(f"   Recent events: {len(data['recent_events'])}")
                
                if data['recent_events']:
                    latest = data['recent_events'][0]
                    print(f"   Latest: {latest['event_type']} item {latest['item_id']} at {latest['timestamp']}")
                else:
                    print("   No events found")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   Exception: {e}")
    
    print(f"\n🎯 Dashboard Test:")
    print(f"1. Go to Real-Time tab")
    print(f"2. Set User ID to 150 in Activity Viewer")
    print(f"3. Click 'Get User Activity'")
    print(f"4. Check the Streamlit terminal for debug output")

if __name__ == "__main__":
    test_activity_endpoint()