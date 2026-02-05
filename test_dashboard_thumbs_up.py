#!/usr/bin/env python3
"""
Instructions for testing the thumbs up button in the dashboard.
This script provides step-by-step instructions and verification steps.
"""

import requests
import time

API_BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8503"

def check_api_status():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except:
        return False

def get_user_activity_count(user_id):
    """Get current count of user events"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/activity?limit=50")
        if response.status_code == 200:
            data = response.json()
            return len(data.get('recent_events', []))
        return 0
    except:
        return 0

def main():
    print("🧪 Dashboard Thumbs Up Button Test Instructions")
    print("=" * 60)
    
    # Check prerequisites
    if not check_api_status():
        print("❌ API is not running on port 8000")
        print("   Start it with: uvicorn api.main:app --reload --port 8000")
        return
    
    print("✅ API is running on port 8000")
    
    # Test user
    test_user_id = 150
    
    # Get initial event count
    initial_count = get_user_activity_count(test_user_id)
    print(f"📊 User {test_user_id} currently has {initial_count} events")
    
    print()
    print("📋 MANUAL TEST STEPS:")
    print("=" * 30)
    print(f"1. Open your browser and go to: {DASHBOARD_URL}")
    print(f"2. In the sidebar, set User ID to: {test_user_id}")
    print("3. Click 'Get Recommendations' button")
    print("4. Wait for recommendations to load")
    print("5. Click the '👍 Like' button on ANY movie")
    print("6. Look for these SUCCESS indicators:")
    print("   ✅ 'Processing thumbs up for...' message appears")
    print("   ✅ 'Liked: [Movie Name]!' success message")
    print("   ✅ Balloons animation plays")
    print("   ✅ 'Check Real-Time tab → User Activity' info message")
    print()
    print("7. Go to the 'Real-Time' tab")
    print("8. In the User Activity section, set User ID to the same number")
    print("9. Click 'Get User Activity'")
    print("10. You should see your thumbs up event in the list")
    print()
    print("🔍 DEBUGGING TIPS:")
    print("=" * 20)
    print("- If button doesn't work, check the terminal running Streamlit")
    print("- Look for debug messages starting with '🚀 BUTTON CLICKED:'")
    print("- Look for debug messages starting with '🚨 SEND_EVENT CALLED:'")
    print("- If you see these messages, the button is working!")
    print("- If no messages appear, the button click isn't being detected")
    print()
    print("🛠️ TROUBLESHOOTING:")
    print("=" * 20)
    print("- Try clicking 'Clear All Likes' button to reset state")
    print("- Try refreshing the browser page")
    print("- Try a different User ID")
    print("- Check browser console (F12) for JavaScript errors")
    print()
    print("⏱️ VERIFICATION:")
    print("=" * 15)
    print("After clicking thumbs up, run this script again to see if event count increased")
    
    print()
    input("Press Enter after you've tested the thumbs up button...")
    
    # Check final count
    final_count = get_user_activity_count(test_user_id)
    print(f"📊 User {test_user_id} now has {final_count} events")
    
    if final_count > initial_count:
        print("✅ SUCCESS! Thumbs up button is working - event count increased!")
        print(f"   Events increased from {initial_count} to {final_count}")
    else:
        print("❌ ISSUE: Event count didn't increase")
        print("   This means the thumbs up button didn't send an event")
        print("   Check the debugging tips above")

if __name__ == "__main__":
    main()