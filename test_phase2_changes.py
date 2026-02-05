"""
Test script to show the differences between Phase 1 and Phase 2.
This demonstrates the personalization improvements.
"""
import requests
import json
import pandas as pd

def test_personalization_improvements():
    """Test the personalization improvements in Phase 2."""
    print("🎯 TESTING PHASE 2: PERSONALIZATION IMPROVEMENTS")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # Test with different users to show personalization
    test_users = [635, 1000, 2000]
    
    print("\n📊 COMPARING POPULARITY vs COLLABORATIVE FILTERING")
    print("="*60)
    
    for user_id in test_users:
        print(f"\n👤 USER {user_id}")
        print("-" * 40)
        
        try:
            # Get user profile first
            profile_response = requests.get(f"{base_url}/users/{user_id}/profile")
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print(f"Profile: {profile['total_interactions']} ratings, avg {profile['avg_rating']:.2f}")
                top_genres = list(profile['favorite_genres'].keys())[:3]
                print(f"Favorite genres: {top_genres}")
            
            # Test popularity model
            pop_request = {
                "user_id": user_id,
                "n_recommendations": 3,
                "model_type": "popularity"
            }
            
            pop_response = requests.post(
                f"{base_url}/recommend",
                json=pop_request,
                headers={"Content-Type": "application/json"}
            )
            
            # Test collaborative filtering
            collab_request = {
                "user_id": user_id,
                "n_recommendations": 3,
                "model_type": "collaborative"
            }
            
            collab_response = requests.post(
                f"{base_url}/recommend",
                json=collab_request,
                headers={"Content-Type": "application/json"}
            )
            
            if pop_response.status_code == 200 and collab_response.status_code == 200:
                pop_recs = pop_response.json()['recommendations']
                collab_recs = collab_response.json()['recommendations']
                
                print("\n🏆 POPULARITY MODEL (same for everyone):")
                for i, rec in enumerate(pop_recs, 1):
                    print(f"  {i}. {rec['title'][:45]} (score: {rec['score']:.3f})")
                
                print("\n🎯 COLLABORATIVE FILTERING (personalized):")
                for i, rec in enumerate(collab_recs, 1):
                    print(f"  {i}. {rec['title'][:45]} (rating: {rec['score']:.2f})")
                
                # Check if recommendations are different
                pop_titles = [r['title'] for r in pop_recs]
                collab_titles = [r['title'] for r in collab_recs]
                overlap = len(set(pop_titles) & set(collab_titles))
                
                print(f"\n📈 Personalization: {3-overlap}/3 recommendations are different!")
                
        except Exception as e:
            print(f"❌ Error testing user {user_id}: {e}")
    
    # Test the comparison endpoint
    print(f"\n🔄 TESTING MODEL COMPARISON ENDPOINT")
    print("-" * 40)
    
    try:
        comparison_response = requests.post(f"{base_url}/compare-models?user_id=635&n_recommendations=3")
        if comparison_response.status_code == 200:
            comparison = comparison_response.json()
            
            print("✅ Model comparison endpoint working!")
            print(f"Available models: {list(comparison['models'].keys())}")
            
            if 'popularity' in comparison['models'] and 'collaborative' in comparison['models']:
                pop_movies = [r['title'][:30] for r in comparison['models']['popularity']]
                collab_movies = [r['title'][:30] for r in comparison['models']['collaborative']]
                
                print(f"Popularity:     {pop_movies}")
                print(f"Collaborative:  {collab_movies}")
        
    except Exception as e:
        print(f"❌ Comparison endpoint error: {e}")
    
    # Test model metrics
    print(f"\n📊 TESTING MODEL METRICS")
    print("-" * 40)
    
    try:
        metrics_response = requests.get(f"{base_url}/metrics")
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            
            print("✅ Model metrics endpoint working!")
            print(f"Available models: {len(metrics['available_models'])}")
            
            for model in metrics['available_models']:
                print(f"  - {model['model_type']}: {model['status']}")
                if model['model_type'] == 'collaborative_filtering':
                    print(f"    Users: {model['n_users']:,}, Items: {model['n_items']:,}")
                    print(f"    Factors: {model['n_factors']}, Variance: {model['explained_variance']:.3f}")
        
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
    
    print("\n" + "="*60)
    print("🎉 PHASE 2 TESTING COMPLETE!")
    print("="*60)
    
    print("\n🚀 WHAT CHANGED ON YOUR LOCALHOST:")
    print("✅ Personalized recommendations (different for each user)")
    print("✅ Model selection (popularity vs collaborative)")
    print("✅ Model comparison endpoint")
    print("✅ Enhanced metrics with both models")
    print("✅ Real machine learning (matrix factorization)")
    
    print("\n🎯 NEXT PHASE PREVIEW:")
    print("- Content-based filtering (analyze movie genres/descriptions)")
    print("- Hybrid model (combine all approaches)")
    print("- Even better personalization!")

if __name__ == "__main__":
    test_personalization_improvements()