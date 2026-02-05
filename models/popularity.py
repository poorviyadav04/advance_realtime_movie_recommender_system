"""
Popularity-based recommender model.
This is the simplest baseline: recommend the most popular movies.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from typing import List, Dict, Tuple

class PopularityRecommender:
    """
    Popularity-based recommender that recommends the most popular items.
    
    This is a simple baseline model that:
    1. Calculates popularity based on number of ratings and average rating
    2. Recommends the same popular items to all users
    3. Serves as a baseline to compare other models against
    """
    
    def __init__(self, popularity_weight: float = 0.7):
        """
        Initialize the popularity recommender.
        
        Args:
            popularity_weight: Weight for number of ratings vs average rating
                              (0.7 means 70% weight on count, 30% on average)
        """
        self.popularity_weight = popularity_weight
        self.popular_items = None
        self.item_stats = None
        self.is_fitted = False
        
    def fit(self, ratings_df: pd.DataFrame) -> 'PopularityRecommender':
        """
        Train the popularity model.
        
        Args:
            ratings_df: DataFrame with columns ['user_id', 'movie_id', 'rating', 'title']
            
        Returns:
            self: The fitted model
        """
        print("Training Popularity Recommender...")
        
        # Calculate statistics for each movie
        self.item_stats = ratings_df.groupby(['movie_id', 'title']).agg({
            'rating': ['count', 'mean', 'std'],
            'user_id': 'nunique'
        }).round(3)
        
        # Flatten column names
        self.item_stats.columns = ['num_ratings', 'avg_rating', 'rating_std', 'unique_users']
        self.item_stats = self.item_stats.reset_index()
        
        # Calculate popularity score
        # Normalize number of ratings to 0-1 scale
        max_ratings = self.item_stats['num_ratings'].max()
        normalized_count = self.item_stats['num_ratings'] / max_ratings
        
        # Normalize average rating to 0-1 scale (assuming 1-5 rating scale)
        normalized_avg = (self.item_stats['avg_rating'] - 1) / 4
        
        # Combine count and average with weights
        self.item_stats['popularity_score'] = (
            self.popularity_weight * normalized_count + 
            (1 - self.popularity_weight) * normalized_avg
        )
        
        # Sort by popularity score
        self.popular_items = self.item_stats.sort_values(
            'popularity_score', ascending=False
        ).reset_index(drop=True)
        
        self.is_fitted = True
        
        print(f"✅ Model trained on {len(ratings_df):,} ratings")
        print(f"   - {self.item_stats['movie_id'].nunique()} unique movies")
        print(f"   - Top movie: {self.popular_items.iloc[0]['title']}")
        print(f"   - Popularity score range: {self.popular_items['popularity_score'].min():.3f} - {self.popular_items['popularity_score'].max():.3f}")
        
        return self
    
    def predict(self, user_id: int, n_recommendations: int = 10, 
                exclude_seen: bool = True, user_ratings: pd.DataFrame = None) -> List[Dict]:
        """
        Get recommendations for a user.
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations to return
            exclude_seen: Whether to exclude movies the user has already rated
            user_ratings: DataFrame of user's previous ratings (for exclusion)
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Start with all popular items
        recommendations = self.popular_items.copy()
        
        # Exclude items the user has already seen
        if exclude_seen and user_ratings is not None:
            seen_movies = set(user_ratings[user_ratings['user_id'] == user_id]['movie_id'])
            recommendations = recommendations[~recommendations['movie_id'].isin(seen_movies)]
        
        # Get top N recommendations
        top_recommendations = recommendations.head(n_recommendations)
        
        # Format as list of dictionaries
        result = []
        for _, row in top_recommendations.iterrows():
            result.append({
                'item_id': int(row['movie_id']),
                'title': row['title'],
                'score': float(row['popularity_score']),
                'reason': 'popularity',
                'num_ratings': int(row['num_ratings']),
                'avg_rating': float(row['avg_rating'])
            })
        
        return result
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model."""
        if not self.is_fitted:
            return {"status": "not_fitted"}
        
        return {
            "status": "fitted",
            "model_type": "popularity",
            "total_items": len(self.item_stats),
            "popularity_weight": self.popularity_weight,
            "top_item": {
                "title": self.popular_items.iloc[0]['title'],
                "score": float(self.popular_items.iloc[0]['popularity_score'])
            }
        }
    
    def save_model(self, filepath: str) -> None:
        """Save the trained model to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        model_data = {
            'popular_items': self.popular_items,
            'item_stats': self.item_stats,
            'popularity_weight': self.popularity_weight,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, filepath)
        print(f"✅ Model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str) -> 'PopularityRecommender':
        """Load a trained model from disk."""
        model_data = joblib.load(filepath)
        
        model = cls(popularity_weight=model_data['popularity_weight'])
        model.popular_items = model_data['popular_items']
        model.item_stats = model_data['item_stats']
        model.is_fitted = model_data['is_fitted']
        
        print(f"✅ Model loaded from {filepath}")
        return model

def train_popularity_model():
    """Train and save a popularity model."""
    print("🚀 TRAINING POPULARITY RECOMMENDER")
    print("="*50)
    
    # Load training data
    train_path = Path("data/processed/train_data.csv")
    if not train_path.exists():
        print("❌ Training data not found. Run: python data/prepare_data.py")
        return None
    
    train_data = pd.read_csv(train_path)
    print(f"Loaded {len(train_data):,} training ratings")
    
    # Train model
    model = PopularityRecommender(popularity_weight=0.7)
    model.fit(train_data)
    
    # Save model
    model_path = Path("data/models/popularity_model.joblib")
    model_path.parent.mkdir(exist_ok=True)
    model.save_model(str(model_path))
    
    # Test the model
    print("\n🧪 TESTING MODEL")
    print("-"*30)
    
    # Get recommendations for a sample user
    sample_user = train_data['user_id'].iloc[0]
    recommendations = model.predict(
        user_id=sample_user, 
        n_recommendations=5,
        exclude_seen=True,
        user_ratings=train_data
    )
    
    print(f"Top 5 recommendations for User {sample_user}:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['title'][:50]} (score: {rec['score']:.3f}, {rec['num_ratings']} ratings)")
    
    print(f"\n✅ Popularity model ready!")
    print(f"Model saved at: {model_path}")
    
    return model

if __name__ == "__main__":
    train_popularity_model()