"""
Test script to demonstrate Phase 5 changes: Real-Time Event Ingestion & Caching
This script shows the new real-time capabilities and database integration.
"""
import requests
import json
import time
import random
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

def send_event(user_id, item_id, event_type, rating=None, session_id=None):
    """Send a user event to the API."""
    try:
        event_data = {
            "user_id": user_id,
            "item_id": item_id,
            "event_type": event_type,
            "source": "test_script"
        }
        
        if rating is not None:
            event_data["rating"] = rating
        if session_id is not None:
            event_data["session_id"] = session_id
            
        response = requests.post(f"{API_BASE_URL}/events", json=event_data)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error sending event: {e}")
        return None

def get_recommendations(user_id, model_type="hybrid", n_recommendations=5):
    """Get recommendations from the API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/recommend",
            json={
                "user_id": user_id,
                "n_recommendations": n_recommendations,
                "model_type": model_type
            }
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return None

def get_user_activity(user_id, limit=10):
    """Get user activity from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/activity?limit={limit}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error getting user activity: {e}")
        return None

def get_cache_stats():
    """Get cache statistics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/cache/stats")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return None

def get_realtime_metrics():
    """Get real-time metrics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics/realtime")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error getting real-time metrics: {e}")
        return None

def invalidate_user_cache(user_id):
    """Invalidate cache for a user."""
    try:
        response = requests.post(f"{API_BASE_URL}/cache/invalidate/{user_id}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error invalidating cache: {e}")
        return None

def demonstrate_phase5_features():
    """Demonstrate all Phase 5 features."""
    
    print_header("PHASE 5: REAL-TIME EVENT INGESTION & CACHING DEMONSTRATION")
    print("This script demonstrates the new real-time capabilities:")
    print("• Real-time event ingestion and storage")
    print("• Lightning-fast recommendation caching")
    print("• User activity tracking")
    print("• System performance monitoring")
    
    # Check API status
    if not check_api_status():
        return
    
    print_section("1. Real-Time Event Ingestion")
    print("Simulating real user interactions...")
    
    test_user = 1001
    session_id = f"session_{int(time.time())}"
    
    # Simulate a user session with multiple interactions
    events_to_send = [
        {"item_id": 1, "event_type": "view"},
        {"item_id": 1, "event_type": "click"},
        {"item_id": 2, "event_type": "view"},
        {"item_id": 3, "event_type": "view"},
        {"item_id": 1, "event_type": "rate", "rating": 4.5},
        {"item_id": 2, "event_type": "click"},
        {"item_id": 4, "event_type": "view"},
        {"item_id": 2, "event_type": "rate", "rating": 3.5},
    ]
    
    print(f"👤 Simulating user {test_user} session: {session_id}")
    
    for i, event in enumerate(events_to_send, 1):
        print(f"   {i}. Sending {event['event_type']} event for item {event['item_id']}", end="")
        if 'rating' in event:
            print(f" (rating: {event['rating']})", end="")
        
        result = send_event(
            user_id=test_user,
            item_id=event['item_id'],
            event_type=event['event_type'],
            rating=event.get('rating'),
            session_id=session_id
        )
        
        if result and result.get('status') == 'success':
            print(" ✅")
        else:
            print(" ❌")
        
        time.sleep(0.5)  # Small delay to simulate real user behavior
    
    print_section("2. User Activity Tracking")
    print("Retrieving stored user activity...")
    
    activity = get_user_activity(test_user, limit=20)
    if activity:
        print(f"👤 User {test_user} recent activity:")
        print(f"   Total events recorded: {activity['total_events']}")
        
        for event in activity['recent_events'][:5]:  # Show last 5 events
            timestamp = event['timestamp'][:19]  # Remove microseconds
            rating_info = f" (rating: {event['rating']})" if event['rating'] else ""
            print(f"   • {timestamp}: {event['event_type']} item {event['item_id']}{rating_info}")
    else:
        print("❌ Could not retrieve user activity")
    
    print_section("3. Recommendation Caching Performance")
    print("Testing recommendation caching system...")
    
    # First request (cache miss)
    print("🔄 First recommendation request (cache miss):")
    start_time = time.time()
    recommendations1 = get_recommendations(test_user, "hybrid", 5)
    first_request_time = time.time() - start_time
    
    if recommendations1:
        print(f"   ⏱️ Response time: {first_request_time:.3f} seconds")
        print(f"   📊 Model version: {recommendations1['model_version']}")
        print("   🎬 Recommendations:")
        for i, rec in enumerate(recommendations1['recommendations'][:3], 1):
            print(f"      {i}. {rec['title'][:40]} (score: {rec['score']:.3f})")
    
    # Second request (cache hit)
    print("\n🚀 Second recommendation request (cache hit):")
    start_time = time.time()
    recommendations2 = get_recommendations(test_user, "hybrid", 5)
    second_request_time = time.time() - start_time
    
    if recommendations2:
        print(f"   ⏱️ Response time: {second_request_time:.3f} seconds")
        print(f"   📊 Model version: {recommendations2['model_version']}")
        
        # Calculate speedup
        if first_request_time > 0:
            speedup = first_request_time / second_request_time
            print(f"   🚀 Cache speedup: {speedup:.1f}x faster!")
    
    print_section("4. Cache Management")
    print("Demonstrating cache invalidation...")
    
    # Get cache stats before invalidation
    cache_stats = get_cache_stats()
    if cache_stats:
        print("📊 Cache statistics before invalidation:")
        perf_metrics = cache_stats.get('performance_metrics', {})
        print(f"   • Total requests: {perf_metrics.get('total_requests', 0)}")
        print(f"   • Cache hits: {perf_metrics.get('hits', 0)}")
        print(f"   • Cache misses: {perf_metrics.get('misses', 0)}")
        print(f"   • Hit rate: {perf_metrics.get('hit_rate', 0):.2%}")
    
    # Invalidate cache for the user
    print(f"\n🗑️ Invalidating cache for user {test_user}...")
    invalidation_result = invalidate_user_cache(test_user)
    if invalidation_result and invalidation_result.get('status') == 'success':
        print("   ✅ Cache invalidated successfully")
    else:
        print("   ❌ Cache invalidation failed")
    
    # Third request (cache miss again after invalidation)
    print("\n🔄 Third recommendation request (after cache invalidation):")
    start_time = time.time()
    recommendations3 = get_recommendations(test_user, "hybrid", 5)
    third_request_time = time.time() - start_time
    
    if recommendations3:
        print(f"   ⏱️ Response time: {third_request_time:.3f} seconds")
        print(f"   📊 Model version: {recommendations3['model_version']}")
        print("   💡 Notice: Cache miss after invalidation (slower response)")
    
    print_section("5. Real-Time System Metrics")
    print("Monitoring system performance...")
    
    metrics = get_realtime_metrics()
    if metrics:
        event_metrics = metrics.get('event_metrics', {})
        cache_metrics = metrics.get('cache_metrics', {})
        
        print("📈 Event Processing Metrics:")
        for event_type in ['view', 'click', 'rate', 'purchase']:
            total_count = event_metrics.get(f'{event_type}_count', 0)
            hourly_count = event_metrics.get(f'{event_type}_last_hour', 0)
            print(f"   • {event_type.title()} events: {total_count} total, {hourly_count} last hour")
        
        print("\n💾 Cache System Metrics:")
        print(f"   • Redis available: {cache_metrics.get('redis_available', False)}")
        print(f"   • Memory cache size: {cache_metrics.get('memory_cache_size', 0)}")
        if cache_metrics.get('redis_available'):
            print(f"   • Redis memory used: {cache_metrics.get('redis_memory_used', 'N/A')}")
            print(f"   • Redis cached items: {cache_metrics.get('redis_cached_recommendations', 0)}")
    
    print_section("6. Multi-User Simulation")
    print("Simulating multiple users for realistic load testing...")
    
    # Simulate multiple users
    users_to_simulate = [2001, 2002, 2003, 2004, 2005]
    
    for user_id in users_to_simulate:
        # Send some random events
        for _ in range(random.randint(2, 5)):
            item_id = random.randint(1, 100)
            event_type = random.choice(['view', 'click', 'rate'])
            rating = random.uniform(1.0, 5.0) if event_type == 'rate' else None
            
            send_event(user_id, item_id, event_type, rating)
        
        # Get recommendations (this will populate cache)
        get_recommendations(user_id, "hybrid", 3)
    
    print(f"✅ Simulated activity for {len(users_to_simulate)} users")
    
    # Final cache stats
    final_cache_stats = get_cache_stats()
    if final_cache_stats:
        final_perf_metrics = final_cache_stats.get('performance_metrics', {})
        print(f"\n📊 Final cache performance:")
        print(f"   • Total requests: {final_perf_metrics.get('total_requests', 0)}")
        print(f"   • Hit rate: {final_perf_metrics.get('hit_rate', 0):.2%}")
    
    print_section("Phase 5 Key Improvements")
    print("✅ Real-Time Event Processing:")
    print("   • Live user interaction capture and storage")
    print("   • Automatic user profile updates")
    print("   • Event-driven cache invalidation")
    print("   • Comprehensive activity tracking")
    
    print("\n✅ High-Performance Caching:")
    print("   • Redis-based recommendation caching")
    print("   • Sub-second response times for cached requests")
    print("   • Intelligent cache invalidation")
    print("   • Fallback to in-memory cache")
    
    print("\n✅ Production-Ready Architecture:")
    print("   • SQLite database for development (PostgreSQL ready)")
    print("   • Real-time metrics and monitoring")
    print("   • Scalable event processing pipeline")
    print("   • API-first design for microservices")
    
    print_section("What's Different from Phase 4?")
    print("🔄 Phase 4 vs Phase 5 Comparison:")
    print("   Phase 4: Static recommendations from files")
    print("   Phase 5: Dynamic recommendations with real-time updates")
    print()
    print("   Phase 4: No user behavior tracking")
    print("   Phase 5: Complete user activity monitoring")
    print()
    print("   Phase 4: Slow recommendation generation")
    print("   Phase 5: Lightning-fast cached recommendations")
    print()
    print("   Phase 4: No persistence of user interactions")
    print("   Phase 5: Full database storage and event processing")
    
    print_section("Next Steps")
    print("🚀 Ready for Phase 6:")
    print("   • Online learning and model updates")
    print("   • A/B testing framework")
    print("   • Advanced feature engineering")
    print("   • Production deployment with Docker")
    
    print(f"\n✅ Phase 5 demonstration completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 Your real-time recommender system is now enterprise-ready!")

if __name__ == "__main__":
    demonstrate_phase5_features()