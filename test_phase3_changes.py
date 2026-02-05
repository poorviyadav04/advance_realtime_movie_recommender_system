"""
Test script to demonstrate Phase 3 improvements: Content-Based Filtering.
This shows the new explainable recommendations and content-based logic.
"""
import requests
import json
import pandas as pd

def test_phase3_improvements():
    """Test the Phase 3 content-based filtering improvements."""
    print("🎬 TESTING PHASE 3: CONTENT-BASED FILTERING")
    print("="*60)
    
    base_url = "http://localhost:8000"
    test_user = 635
    
    print(f"\n📊 COMPARING ALL THREE MODELS FOR USER {test_user}")
    print("="*60)
    
    # Test all three models
    models = ["popularity", "collaborative", "content_based"]
    results = {}
    
    for model_type in models:
        try:
            response = requests.post(
                f"{base_url}/recommend",
                json={
                    "user_id": test_user,
                    "n_recommendations": 3,
                    "model_type": model_type
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results[model_type] = data['recommendations']
                
                print(f"\n🎯 {model_type.upper()} MODEL:")
                for i, rec in enumerate(data['recommendations'], 1):
                    print(f"  {i}. {rec['title'][:45]} (score: {rec['score']:.3f})")
                    if 'explanation' in rec:
                        print(f"     💡 {rec['explanation']}")
                    elif 'reason' in rec:
                        print(f"     📝 Reason: {rec['reason']}")
            else:
                print(f"❌ {model_type} model failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing {model_type}: {e}")
    
    # Test the new similar movies endpoint
    print(f"\n🔍 TESTING SIMILAR MOVIES FEATURE")
    print("-" * 40)
    
    try:
        # Get a movie ID from user's history
        train_data = pd.read_csv("data/processed/train_data.csv")
        user_ratings = train_data[train_data['user_id'] == test_user]
        
        if len(user_ratings) > 0:
            sample_movie = user_ratings.iloc[0]
            movie_id = sample_movie['movie_id']
            movie_title = sample_movie['title']
            
            print(f"Finding movies similar to: {movie_title}")
            
            similar_response = requests.get(f"{base_url}/movies/{movie_id}/similar?n_similar=3")
            
            if similar_response.status_code == 200:
                similar_data = similar_response.json()
                print("✅ Similar movies found:")
                
                for movie in similar_data['similar_movies']:
                    print(f"  • {movie['title'][:40]} (similarity: {movie['similarity']:.3f})")
                    print(f"    Genres: {movie['genres']}")
            else:
                print(f"❌ Similar movies failed: {similar_response.status_code}")
    
    except Exception as e:
        print(f"❌ Similar movies test failed: {e}")
    
    # Test the explanation endpoint
    print(f"\n💡 TESTING RECOMMENDATION EXPLANATIONS")
    print("-" * 40)
    
    try:
        explain_response = requests.get(f"{base_url}/users/{test_user}/explain?model_type=content_based")
        
        if explain_response.status_code == 200:
            explanation = explain_response.json()
            print("✅ Explanation generated:")
            print(f"  User has {explanation['total_ratings']} total ratings")
            print(f"  Liked {explanation['liked_movies']} movies (4+ stars)")
            print(f"  {explanation['explanation']}")
            
            if explanation['recommendations_based_on']:
                print("\n  📚 Recommendations based on:")
                for item in explanation['recommendations_based_on'][:2]:  # Show first 2
                    liked = item['liked_movie']
                    print(f"    🎬 {liked['title'][:35]} (rated {liked['rating']}/5)")
                    print(f"       Genres: {liked['genres']}")
                    print(f"       Similar movies:")
                    for sim in item['similar_movies'][:2]:
                        print(f"         → {sim['title'][:30]} ({sim['similarity']:.3f})")
        else:
            print(f"❌ Explanation failed: {explain_response.status_code}")
    
    except Exception as e:
        print(f"❌ Explanation test failed: {e}")
    
    # Test model comparison endpoint
    print(f"\n🔄 TESTING MODEL COMPARISON")
    print("-" * 40)
    
    try:
        comparison_response = requests.post(f"{base_url}/compare-models?user_id={test_user}&n_recommendations=2")
        
        if comparison_response.status_code == 200:
            comparison = comparison_response.json()
            print("✅ Model comparison successful:")
            
            for model_name, recommendations in comparison['models'].items():
                print(f"  {model_name.upper()}:")
                for rec in recommendations:
                    print(f"    • {rec['title'][:35]} ({rec['score']:.3f})")
        else:
            print(f"❌ Model comparison failed: {comparison_response.status_code}")
    
    except Exception as e:
        print(f"❌ Model comparison test failed: {e}")
    
    # Test enhanced metrics
    print(f"\n📊 TESTING ENHANCED METRICS")
    print("-" * 40)
    
    try:
        metrics_response = requests.get(f"{base_url}/metrics")
        
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            print("✅ Enhanced metrics available:")
            print(f"  Available models: {len(metrics['available_models'])}")
            
            for model in metrics['available_models']:
                print(f"  📈 {model['model_type'].upper()}:")
                if model['model_type'] == 'content_based':
                    print(f"      Movies: {model['n_movies']:,}")
                    print(f"      Features: {model['n_features']:,}")
                    print(f"      Avg similarity: {model['avg_similarity']:.3f}")
                elif model['model_type'] == 'collaborative_filtering':
                    print(f"      Users: {model['n_users']:,}")
                    print(f"      Items: {model['n_items']:,}")
                    print(f"      Factors: {model['n_factors']}")
                elif model['model_type'] == 'popularity':
                    print(f"      Items: {model['total_items']:,}")
        else:
            print(f"❌ Metrics failed: {metrics_response.status_code}")
    
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
    
    print("\n" + "="*60)
    print("🎉 PHASE 3 TESTING COMPLETE!")
    print("="*60)
    
    print("\n🚀 NEW FEATURES IN PHASE 3:")
    print("✅ Content-based filtering with TF-IDF and cosine similarity")
    print("✅ Explainable recommendations with reasons")
    print("✅ Similar movies endpoint (/movies/{id}/similar)")
    print("✅ Recommendation explanations (/users/{id}/explain)")
    print("✅ Three-model comparison (popularity, collaborative, content)")
    print("✅ Genre-based similarity analysis")
    print("✅ Enhanced API documentation")
    
    print("\n🎯 WHAT YOU CAN SEE ON LOCALHOST:")
    print("🌐 API Docs: http://localhost:8000/docs")
    print("   - New endpoints for similar movies and explanations")
    print("   - Model selection parameter in recommendations")
    print("   - Enhanced response formats with explanations")
    
    print("\n📈 IMPROVEMENTS OVER PHASE 2:")
    print("• Explainable AI: Know WHY movies are recommended")
    print("• Cold-start handling: Works for new movies immediately")
    print("• Genre consistency: Similar movies have similar themes")
    print("• Content analysis: Uses actual movie characteristics")
    print("• API expansion: More endpoints for better UX")
    
    print("\n🔮 COMING IN PHASE 4:")
    print("• Hybrid model combining all three approaches")
    print("• Weighted ensemble for optimal recommendations")
    print("• Dynamic model selection based on user/item characteristics")

if __name__ == "__main__":
    test_phase3_improvements()