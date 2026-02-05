"""
Real-time event processing system for Phase 5.
This handles ingestion, processing, and storage of user events.
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import redis
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.database import get_db, get_redis, db_config
from models.database_models import UserEvent, UserProfile, RecommendationLog, SystemMetrics
from feature_store.recommendation_cache import recommendation_cache

class EventProcessor:
    """
    Real-time event processor that handles user interactions.
    
    This class:
    1. Ingests user events (clicks, ratings, views)
    2. Updates user profiles in real-time
    3. Invalidates cached recommendations when needed
    4. Tracks system metrics
    """
    
    def __init__(self):
        self.redis_client = get_redis()
        self.in_memory_cache = {}  # Fallback if Redis not available
        
    async def process_event(self, event_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Process a single user event.
        
        Args:
            event_data: Event data dictionary
            db: Database session
            
        Returns:
            Processing result
        """
        try:
            # Validate event data
            required_fields = ['user_id', 'item_id', 'event_type']
            for field in required_fields:
                if field not in event_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create event record
            event = UserEvent(
                user_id=event_data['user_id'],
                item_id=event_data['item_id'],
                event_type=event_data['event_type'],
                rating=event_data.get('rating'),
                session_id=event_data.get('session_id'),
                source=event_data.get('source', 'web'),
                metadata_json=json.dumps(event_data.get('metadata', {}))
            )
            
            # Save to database
            db.add(event)
            db.commit()
            
            # Update user profile asynchronously
            await self._update_user_profile(event_data['user_id'], event_data, db)
            
            # Invalidate cached recommendations for this user
            await self._invalidate_user_cache(event_data['user_id'])
            
            # Update system metrics
            await self._update_metrics(event_data['event_type'])
            
            return {
                "status": "success",
                "event_id": event.id,
                "message": "Event processed successfully"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"Failed to process event: {str(e)}"
            }
    
    async def _update_user_profile(self, user_id: int, event_data: Dict, db: Session):
        """Update user profile based on new event."""
        try:
            # Get or create user profile
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                profile = UserProfile(
                    user_id=user_id,
                    first_interaction=datetime.utcnow()
                )
                db.add(profile)
            
            # Update interaction counts
            profile.total_interactions += 1
            profile.last_interaction = datetime.utcnow()
            
            # Update rating statistics if this is a rating event
            if event_data['event_type'] == 'rate' and event_data.get('rating'):
                profile.total_ratings += 1
                
                # Recalculate average rating
                user_ratings = db.query(UserEvent).filter(
                    UserEvent.user_id == user_id,
                    UserEvent.event_type == 'rate',
                    UserEvent.rating.isnot(None)
                ).all()
                
                if user_ratings:
                    avg_rating = sum(event.rating for event in user_ratings) / len(user_ratings)
                    profile.avg_rating = avg_rating
            
            # Update activity hour
            current_hour = datetime.utcnow().hour
            profile.most_active_hour = current_hour
            
            db.commit()
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            db.rollback()
    
    async def _invalidate_user_cache(self, user_id: int):
        """Invalidate cached recommendations for a user (uses same key pattern as recommendation_cache)."""
        try:
            recommendation_cache.invalidate_user_cache(user_id)
        except Exception as e:
            print(f"Error invalidating cache: {e}")
    
    async def _update_metrics(self, event_type: str):
        """Update system metrics."""
        try:
            # Use Redis for real-time counters
            if self.redis_client:
                # Increment event type counter
                self.redis_client.incr(f"metrics:events:{event_type}:count")
                
                # Update hourly metrics
                current_hour = datetime.utcnow().strftime("%Y-%m-%d:%H")
                self.redis_client.incr(f"metrics:events:{event_type}:hourly:{current_hour}")
                
                # Set expiration for hourly metrics (keep for 7 days)
                self.redis_client.expire(f"metrics:events:{event_type}:hourly:{current_hour}", 7 * 24 * 3600)
                
        except Exception as e:
            print(f"Error updating metrics: {e}")
    
    def get_user_recent_events(self, user_id: int, limit: int = 50, db: Session = None) -> List[Dict]:
        """Get recent events for a user."""
        if not db:
            db = next(get_db())
        
        try:
            events = db.query(UserEvent).filter(
                UserEvent.user_id == user_id
            ).order_by(desc(UserEvent.timestamp)).limit(limit).all()
            
            return [
                {
                    "id": event.id,
                    "item_id": event.item_id,
                    "event_type": event.event_type,
                    "rating": event.rating,
                    "timestamp": event.timestamp.isoformat(),
                    "source": event.source
                }
                for event in events
            ]
            
        except Exception as e:
            print(f"Error getting user events: {e}")
            return []
    
    def get_item_recent_events(self, item_id: int, limit: int = 100, db: Session = None) -> List[Dict]:
        """Get recent events for an item."""
        if not db:
            db = next(get_db())
        
        try:
            events = db.query(UserEvent).filter(
                UserEvent.item_id == item_id
            ).order_by(desc(UserEvent.timestamp)).limit(limit).all()
            
            return [
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "rating": event.rating,
                    "timestamp": event.timestamp.isoformat(),
                    "source": event.source
                }
                for event in events
            ]
            
        except Exception as e:
            print(f"Error getting item events: {e}")
            return []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        metrics = {}
        
        try:
            if self.redis_client:
                # Get event counts
                for event_type in ['view', 'click', 'rate', 'purchase']:
                    count = self.redis_client.get(f"metrics:events:{event_type}:count")
                    metrics[f"{event_type}_count"] = int(count) if count else 0
                
                # Get recent activity (last hour)
                current_hour = datetime.utcnow().strftime("%Y-%m-%d:%H")
                for event_type in ['view', 'click', 'rate', 'purchase']:
                    hourly_count = self.redis_client.get(f"metrics:events:{event_type}:hourly:{current_hour}")
                    metrics[f"{event_type}_last_hour"] = int(hourly_count) if hourly_count else 0
            
            return metrics
            
        except Exception as e:
            print(f"Error getting system metrics: {e}")
            return {}

# Global event processor instance
event_processor = EventProcessor()

def create_tables():
    """Create database tables if they don't exist."""
    try:
        engine = db_config.get_engine()
        if engine:
            from config.database import Base
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully")
        else:
            print("❌ No database engine available")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    # Create tables when run directly
    create_tables()