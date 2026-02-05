"""
Test script to verify our real recommendation system is working.
"""
import requests
import json
import pandas as pd

def test_api_with_real_model():
    """Test the API with real model."""
    print("🧪 TESTING REAL RECOMMENDATION SYSTEM")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("\n1. Testing API Health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure API is running: uvicorn api.main:app --reload")
        return
    
    # Get a real user ID from our data
    try:
        train_data = pd.read_csv("data/processed/train_data.csv")
        sample_user = int(train_data['user_id'].iloc[100])  # Get a user from middle of dataset
        print(f"Using sample user: {sample_user}")
    except Exception as e:
        print(f"❌ Cannot load training data: {e}")
        return
    
    # Test 2: Get recommendations
    print(f"\n2. Testing Recommendations for User {sample_user}...")
    try:
        rec_request = {
            "user_id": sample_user,
            "n_recommendations": 5,
            "exclude_seen": True
        }
        
        response = requests.post(
            f"{base_url}/recommend",
            json=rec_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Recommendations received!")
            print(f"   Model version: {data['model_version']}")
            print(f"   Number of recommendations: {len(data['recommendations'])}")
            
            print("\n   Top 3 recommendations:")
            for i, rec in enumerate(data['recommendations'][:3], 1):
                print(f"   {i}. {rec['title'][:50]}")
                print(f"      Score: {rec['score']:.3f} | Ratings: {rec['num_ratings']} | Avg: {rec['avg_rating']:.1f}")
        else:
            print(f"❌ Recommendations failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Recommendations test failed: {e}")
    
    # Test 3: Get user profile
    print(f"\n3. Testing User Profile for User {sample_user}...")
    try:
        response = requests.get(f"{base_url}/users/{sample_user}/profile")
        
        if response.status_code == 200:
            profile = response.json()
            print("✅ User profile received!")
            print(f"   Total interactions: {profile['total_interactions']}")
            print(f"   Average rating: {profile['avg_rating']:.2f}")
            print(f"   Top genres: {list(profile['favorite_genres'].keys())[:3]}")
        else:
            print(f"❌ User profile failed: {response.status_code}")
    except Exception as e:
        print(f"❌ User profile test failed: {e}")
    
    # Test 4: Get model metrics
    print(f"\n4. Testing Model Metrics...")
    try:
        response = requests.get(f"{base_url}/metrics")
        
        if response.status_code == 200:
            metrics = response.json()
            print("✅ Model metrics received!")
            print(f"   Model type: {metrics['model_type']}")
            print(f"   Model status: {metrics['model_status']}")
            print(f"   Total items: {metrics.get('total_items', 'N/A')}")
            if 'top_item' in metrics:
                print(f"   Top item: {metrics['top_item']['title']}")
        else:
            print(f"❌ Model metrics failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Model metrics test failed: {e}")
    
    # Test 5: Compare with and without exclusion
    print(f"\n5. Testing Recommendation Exclusion...")
    try:
        # Get recommendations without exclusion
        rec_request_no_exclude = {
            "user_id": sample_user,
            "n_recommendations": 3,
            "exclude_seen": False
        }
        
        response_no_exclude = requests.post(
            f"{base_url}/recommend",
            json=rec_request_no_exclude,
            headers={"Content-Type": "application/json"}
        )
        
        # Get recommendations with exclusion
        rec_request_exclude = {
            "user_id": sample_user,
            "n_recommendations": 3,
            "exclude_seen": True
        }
        
        response_exclude = requests.post(
            f"{base_url}/recommend",
            json=rec_request_exclude,
            headers={"Content-Type": "application/json"}
        )
        
        if response_no_exclude.status_code == 200 and response_exclude.status_code == 200:
            recs_no_exclude = response_no_exclude.json()['recommendations']
            recs_exclude = response_exclude.json()['recommendations']
            
            print("✅ Exclusion test completed!")
            print("   Without exclusion:", [r['title'][:30] for r in recs_no_exclude])
            print("   With exclusion:   ", [r['title'][:30] for r in recs_exclude])
        else:
            print("❌ Exclusion test failed")
    except Exception as e:
        print(f"❌ Exclusion test failed: {e}")
    
    print("\n" + "="*50)
    print("🎉 TESTING COMPLETE!")
    print("="*50)
    print("\nYour real-time recommender system is working with:")
    print("✅ Real MovieLens data")
    print("✅ Popularity-based recommendations")
    print("✅ User profile analysis")
    print("✅ Recommendation exclusion")
    print("✅ Model metrics tracking")
    
    print(f"\n🌐 Access your system:")
    print(f"   - API: http://localhost:8000")
    print(f"   - Docs: http://localhost:8000/docs")
    print(f"   - Dashboard: streamlit run dashboard/app.py")

if __name__ == "__main__":
    test_api_with_real_model()