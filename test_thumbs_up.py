"""
Test what happens when you click thumbs up on recommendations.
"""
import requests
import json

def test_thumbs_up_behavior():
    """Test the current thumbs up functionality."""
    print("👍 TESTING THUMBS UP BEHAVIOR")
    print("="*40)
    
    base_url = "http://localhost:8000"
    user_id = 635
    
    # Step 1: Get recommendations
    print(f"1. Getting recommendations for User {user_id}...")
    rec_response = requests.post(
        f"{base_url}/recommend",
        json={"user_id": user_id, "n_recommendations": 3},
        headers={"Content-Type": "application/json"}
    )
    
    if rec_response.status_code == 200:
        recommendations = rec_response.json()['recommendations']
        print("✅ Got recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['title'][:40]} (ID: {rec['item_id']})")
        
        # Step 2: Simulate clicking thumbs up on first recommendation
        first_movie = recommendations[0]
        print(f"\n2. Clicking 👍 on '{first_movie['title'][:30]}...'")
        
        event_data = {
            "user_id": user_id,
            "item_id": first_movie['item_id'],
            "event_type": "click"
        }
        
        event_response = requests.post(
            f"{base_url}/events",
            json=event_data,
            headers={"Content-Type": "application/json"}
        )
        
        if event_response.status_code == 200:
            result = event_response.json()
            print("✅ Thumbs up recorded!")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            print(f"   Event ID: {result['event_id']}")
        else:
            print(f"❌ Failed to record thumbs up: {event_response.status_code}")
        
        # Step 3: Get recommendations again to see if anything changed
        print(f"\n3. Getting recommendations again to check for changes...")
        rec_response2 = requests.post(
            f"{base_url}/recommend",
            json={"user_id": user_id, "n_recommendations": 3},
            headers={"Content-Type": "application/json"}
        )
        
        if rec_response2.status_code == 200:
            recommendations2 = rec_response2.json()['recommendations']
            print("✅ Got new recommendations:")
            for i, rec in enumerate(recommendations2, 1):
                print(f"   {i}. {rec['title'][:40]} (ID: {rec['item_id']})")
            
            # Compare recommendations
            old_titles = [r['title'] for r in recommendations]
            new_titles = [r['title'] for r in recommendations2]
            
            if old_titles == new_titles:
                print("\n📊 RESULT: Recommendations are IDENTICAL")
                print("   👍 Your click was recorded but didn't change recommendations")
                print("   🔮 This will change in future phases with real-time learning!")
            else:
                print("\n📊 RESULT: Recommendations CHANGED!")
                print("   🎉 Your feedback influenced the recommendations!")
        
    else:
        print(f"❌ Failed to get recommendations: {rec_response.status_code}")
    
    print("\n" + "="*40)
    print("📋 CURRENT THUMBS UP BEHAVIOR SUMMARY:")
    print("✅ Click is recorded by API")
    print("✅ Success message is shown")
    print("✅ Event gets a unique ID")
    print("❌ Event is not stored permanently")
    print("❌ Model is not updated")
    print("❌ Recommendations don't change")
    
    print("\n🚀 COMING IN FUTURE PHASES:")
    print("🔄 Real-time model updates")
    print("💾 Persistent event storage")
    print("🎯 Adaptive recommendations")
    print("📈 Learning from user behavior")

if __name__ == "__main__":
    test_thumbs_up_behavior()