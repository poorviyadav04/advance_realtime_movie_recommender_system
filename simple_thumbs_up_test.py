"""
Simple Streamlit app to test thumbs up functionality in isolation.
This will help us debug the issue without the complex dashboard.
"""
import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"

def send_event(user_id: int, item_id: int, event_type: str):
    """Send an event to the API."""
    try:
        event_data = {
            "user_id": user_id,
            "item_id": item_id,
            "event_type": event_type,
            "source": "simple_test"
        }
        
        print(f"🔍 SIMPLE TEST: Sending event - User: {user_id}, Item: {item_id}, Type: {event_type}")
        
        response = requests.post(f"{API_BASE_URL}/events", json=event_data, timeout=5)
        
        print(f"🔍 SIMPLE TEST: Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 SIMPLE TEST: Success! Event ID: {result.get('event_id')}")
            return True
        else:
            print(f"🔍 SIMPLE TEST: Error: {response.text}")
            return False
    except Exception as e:
        print(f"🔍 SIMPLE TEST: Exception: {e}")
        return False

def main():
    st.title("🧪 Simple Thumbs Up Test")
    
    st.write("This is a minimal test to verify thumbs up functionality works.")
    
    user_id = st.number_input("User ID", value=170, min_value=1, max_value=6040)
    
    st.write("**Test Movies:**")
    
    # Simple movie list for testing
    movies = [
        {"id": 1, "title": "Toy Story (1995)"},
        {"id": 2, "title": "Jumanji (1995)"},
        {"id": 3, "title": "Grumpier Old Men (1995)"}
    ]
    
    for movie in movies:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{movie['title']}**")
        
        with col2:
            # Simple thumbs up button
            button_key = f"like_{movie['id']}"
            
            if st.button("👍 Like", key=button_key):
                st.write(f"Clicked thumbs up for {movie['title']}")
                
                success = send_event(user_id, movie['id'], "click")
                
                if success:
                    st.success(f"✅ Liked {movie['title']}!")
                    st.balloons()
                else:
                    st.error("❌ Failed to send event")
    
    st.write("---")
    st.write("**Instructions:**")
    st.write("1. Click any '👍 Like' button above")
    st.write("2. Check the terminal for debug messages")
    st.write("3. Go to Real-Time tab in main dashboard to verify event was stored")

if __name__ == "__main__":
    main()