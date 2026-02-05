"""
Redis-based recommendation caching system for Phase 5.
This provides lightning-fast recommendation serving.
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.database import get_redis

class RecommendationCache:
    """
    High-performance recommendation caching system using Redis.
    
    This class:
    1. Caches recommendations for fast serving
    2. Manages cache expiration and invalidation
    3. Provides fallback to in-memory cache
    4. Tracks cache performance metrics
    """
    
    def __init__(self):
        self.redis_client = get_redis()
        self.in_memory_cache = {}  # Fallback cache
        self.cache_ttl = 3600  # 1 hour default TTL
        self.max_memory_cache_size = 1000  # Max items in memory cache
        
    def get_recommendations(self, user_id: int, model_type: str = "hybrid", 
                          n_recommendations: int = 10) -> Optional[List[Dict]]:
        """
        Get cached recommendations for a user.
        
        Args:
            user_id: User ID
            model_type: Type of model used
            n_recommendations: Number of recommendations
            
        Returns:
            Cached recommendations or None if not found
        """
        cache_key = self._get_cache_key(user_id, model_type, n_recommendations)
        
        try:
            # Try Redis first
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    # Check if cache is still valid
                    if self._is_cache_valid(data):
                        return data['recommendations']
            
            # Fallback to in-memory cache
            if cache_key in self.in_memory_cache:
                data = self.in_memory_cache[cache_key]
                if self._is_cache_valid(data):
                    return data['recommendations']
                else:
                    # Remove expired cache
                    del self.in_memory_cache[cache_key]
            
            return None
            
        except Exception as e:
            print(f"Error getting cached recommendations: {e}")
            return None
    
    def set_recommendations(self, user_id: int, model_type: str, 
                          recommendations: List[Dict], n_recommendations: int = 10,
                          ttl: Optional[int] = None) -> bool:
        """
        Cache recommendations for a user.
        
        Args:
            user_id: User ID
            model_type: Type of model used
            recommendations: List of recommendation dictionaries
            n_recommendations: Number of recommendations
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successfully cached
        """
        cache_key = self._get_cache_key(user_id, model_type, n_recommendations)
        ttl = ttl or self.cache_ttl
        
        cache_data = {
            'recommendations': recommendations,
            'cached_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
            'model_type': model_type,
            'user_id': user_id
        }
        
        try:
            # Store in Redis
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(cache_data, default=str)
                )
            
            # Store in memory cache (with size limit)
            if len(self.in_memory_cache) >= self.max_memory_cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.in_memory_cache))
                del self.in_memory_cache[oldest_key]
            
            self.in_memory_cache[cache_key] = cache_data
            
            return True
            
        except Exception as e:
            print(f"Error caching recommendations: {e}")
            return False
    
    def invalidate_user_cache(self, user_id: int) -> bool:
        """
        Invalidate all cached recommendations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successfully invalidated
        """
        try:
            # Pattern for all user caches
            pattern = f"rec:user:{user_id}:*"
            
            if self.redis_client:
                # Get all keys matching pattern
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            # Remove from memory cache
            keys_to_remove = [key for key in self.in_memory_cache.keys() 
                            if key.startswith(f"rec:user:{user_id}:")]
            for key in keys_to_remove:
                del self.in_memory_cache[key]
            
            return True
            
        except Exception as e:
            print(f"Error invalidating user cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        stats = {
            'redis_available': self.redis_client is not None,
            'memory_cache_size': len(self.in_memory_cache),
            'max_memory_cache_size': self.max_memory_cache_size,
            'default_ttl': self.cache_ttl
        }
        
        try:
            if self.redis_client:
                # Get Redis info
                redis_info = self.redis_client.info()
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                    'redis_connected_clients': redis_info.get('connected_clients', 0),
                    'redis_total_commands': redis_info.get('total_commands_processed', 0)
                })
                
                # Count recommendation keys
                rec_keys = self.redis_client.keys("rec:*")
                stats['redis_cached_recommendations'] = len(rec_keys)
        
        except Exception as e:
            print(f"Error getting cache stats: {e}")
        
        return stats
    
    def warm_cache_for_user(self, user_id: int, recommendations_func, 
                           model_types: List[str] = None) -> Dict[str, bool]:
        """
        Pre-warm cache for a user with recommendations from multiple models.
        
        Args:
            user_id: User ID
            recommendations_func: Function to generate recommendations
            model_types: List of model types to cache
            
        Returns:
            Dictionary of model_type -> success status
        """
        model_types = model_types or ['hybrid', 'collaborative', 'content_based', 'popularity']
        results = {}
        
        for model_type in model_types:
            try:
                # Generate recommendations
                recommendations = recommendations_func(user_id, model_type)
                
                if recommendations:
                    # Cache the recommendations
                    success = self.set_recommendations(user_id, model_type, recommendations)
                    results[model_type] = success
                else:
                    results[model_type] = False
                    
            except Exception as e:
                print(f"Error warming cache for {model_type}: {e}")
                results[model_type] = False
        
        return results
    
    def _get_cache_key(self, user_id: int, model_type: str, n_recommendations: int) -> str:
        """Generate cache key for recommendations."""
        return f"rec:user:{user_id}:model:{model_type}:n:{n_recommendations}"
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """Check if cached data is still valid."""
        try:
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            return datetime.utcnow() < expires_at
        except:
            return False
    
    def clear_all_cache(self) -> bool:
        """Clear all cached recommendations (use with caution)."""
        try:
            if self.redis_client:
                # Clear all recommendation keys
                keys = self.redis_client.keys("rec:*")
                if keys:
                    self.redis_client.delete(*keys)
            
            # Clear memory cache
            self.in_memory_cache.clear()
            
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

# Global cache instance
recommendation_cache = RecommendationCache()

class CacheMetrics:
    """Track cache performance metrics."""
    
    def __init__(self):
        self.redis_client = get_redis()
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
    
    def record_hit(self):
        """Record a cache hit."""
        self.hits += 1
        self.total_requests += 1
        
        if self.redis_client:
            self.redis_client.incr("cache:hits")
            self.redis_client.incr("cache:total_requests")
    
    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1
        self.total_requests += 1
        
        if self.redis_client:
            self.redis_client.incr("cache:misses")
            self.redis_client.incr("cache:total_requests")
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        stats = {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': self.total_requests,
            'hit_rate': self.get_hit_rate()
        }
        
        if self.redis_client:
            try:
                redis_hits = self.redis_client.get("cache:hits")
                redis_misses = self.redis_client.get("cache:misses")
                redis_total = self.redis_client.get("cache:total_requests")
                
                if redis_total and int(redis_total) > 0:
                    stats.update({
                        'redis_hits': int(redis_hits) if redis_hits else 0,
                        'redis_misses': int(redis_misses) if redis_misses else 0,
                        'redis_total_requests': int(redis_total),
                        'redis_hit_rate': int(redis_hits) / int(redis_total) if redis_hits and redis_total else 0.0
                    })
            except Exception as e:
                print(f"Error getting Redis cache stats: {e}")
        
        return stats

# Global cache metrics instance
cache_metrics = CacheMetrics()