"""
Online Learning Module for Incremental Model Updates.
Allows models to learn from new user feedback without full retraining.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OnlineLearner:
    """
    Manages incremental learning from user feedback.
    
    Features:
    - Buffers feedback events for batch updates
    - Triggers model retraining when buffer reaches threshold
    - Maintains update history and metrics
    """
    
    def __init__(self, 
                 buffer_size: int = 10,
                 auto_update: bool = True,
                 update_interval_minutes: int = 60):
        """
        Initialize the online learner.
        
        Args:
            buffer_size: Number of events to buffer before updating
            auto_update: Whether to automatically trigger updates
            update_interval_minutes: Minimum minutes between updates
        """
        self.buffer_size = buffer_size
        self.auto_update = auto_update
        self.update_interval_minutes = update_interval_minutes
        
        self.feedback_buffer = []
        self.last_update_time = None
        self.update_count = 0
        self.total_feedback_processed = 0
        
        logger.info(f"OnlineLearner initialized with buffer_size={buffer_size}")
    
    def add_feedback(self, user_id: int, item_id: int, rating: float, 
                    timestamp: Optional[datetime] = None) -> Dict:
        """
        Add a new feedback event to the buffer.
        
        Args:
            user_id: User ID
            item_id: Item ID
            rating: User rating
            timestamp: Event timestamp
            
        Returns:
            Status dictionary with buffer info
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        feedback = {
            'user_id': user_id,
            'item_id': item_id,
            'rating': rating,
            'timestamp': timestamp
        }
        
        self.feedback_buffer.append(feedback)
        logger.info(f"Feedback added: user={user_id}, item={item_id}, rating={rating}")
        
        # Check if we should trigger an update
        should_update = False
        reason = None
        
        if self.auto_update:
            # Check buffer size
            if len(self.feedback_buffer) >= self.buffer_size:
                should_update = True
                reason = f"Buffer size reached ({len(self.feedback_buffer)}/{self.buffer_size})"
            
            # Check time interval
            elif self.last_update_time is not None:
                minutes_since_update = (datetime.now() - self.last_update_time).seconds / 60
                if minutes_since_update >= self.update_interval_minutes:
                    should_update = True
                    reason = f"Time interval reached ({minutes_since_update:.1f} minutes)"
        
        return {
            'buffer_size': len(self.feedback_buffer),
            'should_update': should_update,
            'reason': reason,
            'total_processed': self.total_feedback_processed
        }
    
    def get_buffered_feedback(self) -> pd.DataFrame:
        """
        Get buffered feedback as a DataFrame.
        
        Returns:
            DataFrame with feedback events
        """
        if not self.feedback_buffer:
            return pd.DataFrame()
        
        return pd.DataFrame(self.feedback_buffer)
    
    def clear_buffer(self):
        """Clear the feedback buffer after processing."""
        buffer_size = len(self.feedback_buffer)
        self.total_feedback_processed += buffer_size
        self.feedback_buffer = []
        self.last_update_time = datetime.now()
        self.update_count += 1
        
        logger.info(f"Buffer cleared. Processed {buffer_size} events. Total: {self.total_feedback_processed}")
    
    def partial_update_collaborative(self, model, new_ratings: pd.DataFrame):
        """
        Perform incremental update for collaborative filtering model.
        
        Strategy: Retrain on recent data window (old + new)
        
        Args:
            model: Collaborative filtering model
            new_ratings: New ratings to incorporate
        """
        logger.info(f"Performing partial update with {len(new_ratings)} new ratings")
        
        # Get existing training data
        if hasattr(model, 'training_data') and model.training_data is not None:
            # Combine old and new data
            # Keep a sliding window (e.g., last 10000 ratings)
            max_history = 10000
            combined_data = pd.concat([model.training_data, new_ratings])
            
            # Sort by timestamp if available
            if 'timestamp' in combined_data.columns:
                combined_data = combined_data.sort_values('timestamp', ascending=False)
            
            # Keep most recent
            combined_data = combined_data.head(max_history)
            
            # Retrain on combined data
            model.fit(combined_data)
            model.training_data = combined_data
        else:
            # First time - just train on new data
            model.fit(new_ratings)
            model.training_data = new_ratings
        
        logger.info(f"Model updated successfully")
    
    def partial_update_hybrid(self, hybrid_model, pop_model, cf_model, 
                             content_model, new_ratings: pd.DataFrame):
        """
        Perform incremental update for hybrid model.
        
        Args:
            hybrid_model: Hybrid model
            pop_model: Popularity model
            cf_model: Collaborative filtering model
            content_model: Content-based model
            new_ratings: New ratings
        """
        logger.info(f"Updating hybrid model components with {len(new_ratings)} new ratings")
        
        # Update collaborative filtering (most important for personalization)
        self.partial_update_collaborative(cf_model, new_ratings)
        
        # Update popularity counts
        if hasattr(pop_model, 'rating_counts') and pop_model.rating_counts is not None:
            for _, row in new_ratings.iterrows():
                item_id = row['movie_id'] if 'movie_id' in row else row['item_id']
                if item_id in pop_model.rating_counts:
                    pop_model.rating_counts[item_id] += 1
                else:
                    pop_model.rating_counts[item_id] = 1
        
        # Re-fit hybrid model with updated components
        if hasattr(hybrid_model, 'train_data'):
            hybrid_model.fit(pop_model, cf_model, content_model, hybrid_model.train_data)
        
        logger.info("Hybrid model update complete")
    
    def trigger_update(self, models: Dict) -> Dict:
        """
        Trigger an update for all registered models.
        
        Args:
            models: Dictionary of models to update
                   e.g., {'collaborative': cf_model, 'hybrid': hybrid_model, ...}
        
        Returns:
            Update statistics
        """
        if not self.feedback_buffer:
            logger.warning("No feedback in buffer, skipping update")
            return {
                'updated': False,
                'reason': 'Empty buffer'
            }
        
        # Get buffered feedback
        new_ratings = self.get_buffered_feedback()
        
        # Prepare ratings DataFrame
        # Ensure it has required columns
        if 'movie_id' not in new_ratings.columns and 'item_id' in new_ratings.columns:
            new_ratings['movie_id'] = new_ratings['item_id']
        
        start_time = datetime.now()
        
        # Update each model
        updated_models = []
        for model_name, model in models.items():
            try:
                if 'collaborative' in model_name.lower():
                    self.partial_update_collaborative(model, new_ratings)
                    updated_models.append(model_name)
                elif 'hybrid' in model_name.lower():
                    # For hybrid, we need access to component models
                    if hasattr(model, 'popularity_model'):
                        self.partial_update_hybrid(
                            model, 
                            model.popularity_model,
                            model.collaborative_model,
                            model.content_based_model,
                            new_ratings
                        )
                        updated_models.append(model_name)
            except Exception as e:
                logger.error(f"Error updating {model_name}: {e}")
        
        # Clear buffer
        buffer_size = len(self.feedback_buffer)
        self.clear_buffer()
        
        update_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Update complete. {len(updated_models)} models updated in {update_time:.2f}s")
        
        return {
            'updated': True,
            'models_updated': updated_models,
            'feedback_count': buffer_size,
            'update_time_seconds': update_time,
            'total_updates': self.update_count
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about the online learner."""
        return {
            'buffer_size': len(self.feedback_buffer),
            'buffer_capacity': self.buffer_size,
            'total_processed': self.total_feedback_processed,
            'update_count': self.update_count,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'auto_update': self.auto_update
        }


if __name__ == "__main__":
    # Example usage
    learner = OnlineLearner(buffer_size=5)
    
    # Add some feedback
    for i in range(3):
        status = learner.add_feedback(
            user_id=100 + i,
            item_id=1000 + i,
            rating=4.5
        )
        print(f"Status: {status}")
    
    print(f"\nLearner stats: {learner.get_stats()}")
    print(f"Buffered feedback:\n{learner.get_buffered_feedback()}")
