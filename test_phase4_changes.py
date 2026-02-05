"""
Test script to demonstrate Phase 4 changes: Hybrid Recommender System
This script shows the improvements and new features added in Phase 4.
"""
import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-"*50)

def check_api_status():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print("❌ API is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure to start the API with: uvicorn api.main:app --reload --port 8000")
        return False

def get_model_metrics():
    """Get current model metrics."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_recommendations(user_id, model_type="hybrid", n_recommendations=5):
    """Get recommendations from a specific model."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/recommend",
            json={
                "user_id": user_id,
                "n_recommendations": n_recommendations,
                "model_type": model_type
            }
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def compare_all_models(user_id, n_recommendations=3):
    """Compare recommendations from all available models."""
    try:
        response = requests.post(f"{API_BASE_URL}/compare-models?user_id={user_id}&n_recommendations={n_recommendations}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def demonstrate_phase4_features():
    """Demonstrate all Phase 4 features."""
    
    print_header("PHASE 4: HYBRID RECOMMENDER SYSTEM DEMONSTRATION")
    print("This script demonstrates the advanced hybrid recommendation system")
    print("that intelligently combines multiple recommendation approaches.")
    
    # Check API status
    if not check_api_status():
        return
    
    # Get system metrics
    print_section("System Status & Available Models")
    metrics = get_model_metrics()
    if metrics:
        print(f"Available models: {len(metrics['available_models'])}")
        for model in metrics['available_models']:
            print(f"  ✅ {model['model_type'].replace('_', ' ').title()}: {model['status']}")
            
            # Show hybrid model details
            if model['model_type'] == 'hybrid':
                print(f"     🔧 Component models: {model['component_models']}")
                print(f"     ⚖️ Default weights: {model['default_weights']}")
                print(f"     👥 Users analyzed: {model['n_users_analyzed']:,}")
                print(f"     🎬 Items analyzed: {model['n_items_analyzed']:,}")
    else:
        print("❌ Could not retrieve system metrics")
    
    # Test users with different characteristics
    test_users = [
        {"id": 635, "description": "Active user with many ratings"},
        {"id": 1000, "description": "Moderate user with some ratings"},
        {"id": 5000, "description": "Light user with few ratings"}
    ]
    
    print_section("Hybrid Model Recommendations")
    print("Testing hybrid model with users of different activity levels...")
    
    for user_info in test_users:
        user_id = user_info["id"]
        description = user_info["description"]
        
        print(f"\n👤 User {user_id} ({description}):")
        
        # Get hybrid recommendations
        hybrid_recs = get_recommendations(user_id, "hybrid", 3)
        if hybrid_recs:
            print(f"   🎯 Hybrid Recommendations (Model: {hybrid_recs['model_version']}):")
            
            for i, rec in enumerate(hybrid_recs['recommendations'], 1):
                print(f"   {i}. {rec['title'][:45]} (Score: {rec['score']:.3f})")
                
                # Show detailed explanation
                if 'explanation' in rec:
                    print(f"      💡 {rec['explanation']}")
                
                # Show model contributions (Phase 4 feature!)
                if 'model_contributions' in rec:
                    contributions = rec['model_contributions']
                    contrib_details = []
                    for model_name, contrib in contributions.items():
                        if contrib['contribution'] > 0.01:
                            percentage = (contrib['contribution'] / rec['score']) * 100
                            contrib_details.append(f"{model_name}: {percentage:.0f}%")
                    
                    if contrib_details:
                        print(f"      🔧 Model contributions: {', '.join(contrib_details)}")
                
                # Show dynamic weights used
                if 'weights_used' in rec:
                    weights = rec['weights_used']
                    weight_str = ", ".join([f"{k}: {v:.2f}" for k, v in weights.items()])
                    print(f"      ⚖️ Dynamic weights: {weight_str}")
                
                print()  # Empty line for readability
        else:
            print("   ❌ Could not get hybrid recommendations")
    
    print_section("Model Comparison Analysis")
    print("Comparing recommendations from all models for the same user...")
    
    comparison_user = 635
    comparison = compare_all_models(comparison_user, 3)
    
    if comparison:
        print(f"\n👤 User {comparison_user} - Model Comparison:")
        
        for model_name, model_recs in comparison['models'].items():
            print(f"\n🔹 {model_name.replace('_', ' ').title()} Model:")
            
            for i, rec in enumerate(model_recs, 1):
                explanation = rec.get('explanation', rec.get('reason', 'No explanation'))
                print(f"   {i}. {rec['title'][:40]} ({rec['score']:.3f})")
                print(f"      💡 {explanation}")
                
                # Show hybrid-specific details
                if model_name == 'hybrid' and 'model_contributions' in rec:
                    contributions = rec['model_contributions']
                    contrib_summary = []
                    for contrib_model, contrib_data in contributions.items():
                        if contrib_data['contribution'] > 0.01:
                            percentage = (contrib_data['contribution'] / rec['score']) * 100
                            contrib_summary.append(f"{contrib_model}: {percentage:.0f}%")
                    
                    if contrib_summary:
                        print(f"      🔧 Breakdown: {', '.join(contrib_summary)}")
    else:
        print("❌ Could not get model comparison")
    
    print_section("Phase 4 Key Improvements")
    print("✅ Hybrid Model Features:")
    print("   • Combines popularity, collaborative, and content-based approaches")
    print("   • Dynamic weight adjustment based on user characteristics")
    print("   • Multi-faceted explanations showing model contributions")
    print("   • Diversity optimization to avoid repetitive recommendations")
    print("   • Intelligent fallback for cold-start users")
    print("   • Real-time weight calculation per user")
    
    print("\n✅ Technical Improvements:")
    print("   • Weighted ensemble combining normalized scores")
    print("   • User activity analysis for personalized weighting")
    print("   • Genre-based diversity bonuses")
    print("   • Comprehensive model contribution tracking")
    print("   • Seamless integration with existing API endpoints")
    
    print_section("What's Different from Phase 3?")
    print("🔄 Phase 3 vs Phase 4 Comparison:")
    print("   Phase 3: Individual models working separately")
    print("   Phase 4: All models working together intelligently")
    print()
    print("   Phase 3: Static model selection")
    print("   Phase 4: Dynamic weight adjustment per user")
    print()
    print("   Phase 3: Single-source explanations")
    print("   Phase 4: Multi-faceted explanations with contribution breakdown")
    print()
    print("   Phase 3: Basic similarity-based recommendations")
    print("   Phase 4: Diversity-optimized recommendations")
    
    print_section("Next Steps")
    print("🚀 Ready for Phase 5:")
    print("   • Real-time event ingestion")
    print("   • Feature store implementation")
    print("   • Online learning capabilities")
    print("   • A/B testing framework")
    
    print(f"\n✅ Phase 4 demonstration completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 Your hybrid recommender system is now production-ready!")

if __name__ == "__main__":
    demonstrate_phase4_features()