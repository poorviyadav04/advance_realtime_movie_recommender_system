"""
Database models for storing user events and interactions.
Phase 5: Real-time event ingestion.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime
from typing import Optional

class UserEvent(Base):
    """
    Model for storing user interaction events.
    This captures all user behavior in real-time.
    """
    __tablename__ = "user_events"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    user_id = Column(Integer, nullable=False, index=True)
    item_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # 'view', 'click', 'rate', 'purchase'
    
    # Optional rating (for rating events)
    rating = Column(Float, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Additional context
    session_id = Column(String(100), nullable=True, index=True)
    source = Column(String(50), default="web", nullable=False)  # 'web', 'mobile', 'api'
    
    # Metadata
    metadata_json = Column(Text, nullable=True)  # JSON string for additional data
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_item_timestamp', 'item_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<UserEvent(user_id={self.user_id}, item_id={self.item_id}, event_type='{self.event_type}')>"

class UserProfile(Base):
    """
    Model for storing user profile information.
    This gets updated based on user behavior patterns.
    """
    __tablename__ = "user_profiles"
    
    # Primary key
    user_id = Column(Integer, primary_key=True, index=True)
    
    # Profile data
    total_interactions = Column(Integer, default=0, nullable=False)
    total_ratings = Column(Integer, default=0, nullable=False)
    avg_rating = Column(Float, nullable=True)
    
    # Preferences (JSON strings)
    favorite_genres = Column(Text, nullable=True)  # JSON array
    preferred_decades = Column(Text, nullable=True)  # JSON array
    
    # Activity patterns
    first_interaction = Column(DateTime(timezone=True), nullable=True)
    last_interaction = Column(DateTime(timezone=True), nullable=True)
    most_active_hour = Column(Integer, nullable=True)  # 0-23
    
    # Recommendation preferences
    prefers_popular = Column(Boolean, default=False, nullable=False)
    prefers_niche = Column(Boolean, default=False, nullable=False)
    exploration_factor = Column(Float, default=0.5, nullable=False)  # 0-1, how much they like new things
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, total_interactions={self.total_interactions})>"

class RecommendationLog(Base):
    """
    Model for logging recommendations served to users.
    This helps track recommendation performance and user responses.
    """
    __tablename__ = "recommendation_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Recommendation details
    user_id = Column(Integer, nullable=False, index=True)
    item_id = Column(Integer, nullable=False, index=True)
    model_type = Column(String(50), nullable=False, index=True)  # 'hybrid', 'collaborative', etc.
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)  # Position in recommendation list (1, 2, 3...)
    
    # Context
    session_id = Column(String(100), nullable=True, index=True)
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # User response tracking
    was_clicked = Column(Boolean, default=False, nullable=False)
    was_rated = Column(Boolean, default=False, nullable=False)
    click_timestamp = Column(DateTime(timezone=True), nullable=True)
    rating_given = Column(Float, nullable=True)
    
    # Model explanation
    explanation = Column(Text, nullable=True)
    model_weights = Column(Text, nullable=True)  # JSON string of model weights used
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_request_timestamp', 'user_id', 'request_timestamp'),
        Index('idx_model_timestamp', 'model_type', 'request_timestamp'),
    )
    
    def __repr__(self):
        return f"<RecommendationLog(user_id={self.user_id}, item_id={self.item_id}, model_type='{self.model_type}')>"

class SystemMetrics(Base):
    """
    Model for storing system performance metrics.
    This helps monitor the health and performance of the recommendation system.
    """
    __tablename__ = "system_metrics"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'counter', 'gauge', 'histogram'
    
    # Context
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # 'api', 'model', 'system'
    
    # Additional data
    tags = Column(Text, nullable=True)  # JSON string for tags/labels
    
    # Indexes
    __table_args__ = (
        Index('idx_metric_timestamp', 'metric_name', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SystemMetrics(metric_name='{self.metric_name}', value={self.metric_value})>"