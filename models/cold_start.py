"""
Cold start recommendation system for new users.
Provides initial recommendations before sufficient user data is collected.
"""
import pandas as pd
from typing import List, Dict
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class ColdStartRecommender:
    """
    Handles cold start problem for new users.
    
    Strategies:
    1. Popularity-based recommendations
    2. Genre-based recommendations
    3. Gradual personalization as user rates items
    """
    
    def __init__(self, movies_df: pd.DataFrame = None, ratings_df: pd.DataFrame = None):
        """
        Initialize cold start recommender.
        
        Args:
            movies_df: Movies dataset with genres
            ratings_df: Historical ratings for popularity calculation
        """
        self.movies_df = movies_df
        self.ratings_df = ratings_df
        self.popular_items = None
        self.genre_popular_items = {}
        
        if movies_df is not None and ratings_df is not None:
            self._compute_popularity()
    
    def _compute_popularity(self):
        """Compute overall and genre-specific popularity."""
        if self.ratings_df is None or self.movies_df is None:
            return
        
        # Calculate average rating and rating count for each movie
        popularity_stats = self.ratings_df.groupby('item_id').agg({
            'rating': ['mean', 'count']
        }).reset_index()
        popularity_stats.columns = ['item_id', 'avg_rating', 'rating_count']
        
        # Merge with movie info
        popular_df = popularity_stats.merge(self.movies_df, on='item_id', how='left')
        
        # Weighted score: combines average rating and popularity
        # Items with very few ratings are downweighted
        min_ratings = 10
        popular_df['popularity_score'] = (
            popular_df['avg_rating'] * (popular_df['rating_count'] / (popular_df['rating_count'] + min_ratings))
        )
        
        # Store overall popular items
        self.popular_items = popular_df.nlargest(100, 'popularity_score')
        
        # Compute genre-specific popularity
        if 'genres' in self.movies_df.columns:
            for _, row in self.movies_df.iterrows():
                genres = str(row['genres']).split('|')
                for genre in genres:
                    if genre not in self.genre_popular_items:
                        self.genre_popular_items[genre] = []
        
        # For each genre, get top items
        for genre in self.genre_popular_items.keys():
            genre_movies = popular_df[popular_df['genres'].str.contains(genre, case=False, na=False)]
            self.genre_popular_items[genre] = genre_movies.nlargest(50, 'popularity_score')
    
    def get_popular_recommendations(self, n: int = 10, exclude_items: List[int] = None) -> List[Dict]:
        """
        Get popular items for a new user.
        
        Args:
            n: Number of recommendations
            exclude_items: Items to exclude (already rated)
            
        Returns:
            List of recommended items
        """
        if self.popular_items is None:
            return []
        
        exclude_items = exclude_items or []
        filtered = self.popular_items[~self.popular_items['item_id'].isin(exclude_items)]
        
        recommendations = []
        for _, row in filtered.head(n).iterrows():
            recommendations.append({
                'item_id': int(row['item_id']),
                'title': row.get('title', f"Movie {row['item_id']}"),
                'genres': row.get('genres', ''),
                'predicted_rating': float(row

['avg_rating']),
                'popularity_score': float(row['popularity_score']),
                'reason': 'popular'
            })
        
        return recommendations
    
    def get_genre_recommendations(self, genres: List[str], n: int = 10, exclude_items: List[int] = None) -> List[Dict]:
        """
        Get recommendations based on genre preferences.
        
        Args:
            genres: List of preferred genres
            n: Number of recommendations
            exclude_items: Items to exclude
            
        Returns:
            List of recommended items
        """
        if not genres:
            return self.get_popular_recommendations(n, exclude_items)
        
        exclude_items = exclude_items or []
        recommendations = []
        items_per_genre = max(1, n // len(genres))
        
        for genre in genres:
            if genre in self.genre_popular_items:
                genre_items = self.genre_popular_items[genre]
                filtered = genre_items[~genre_items['item_id'].isin(exclude_items)]
                
                for _, row in filtered.head(items_per_genre).iterrows():
                    if row['item_id'] not in [r['item_id'] for r in recommendations]:
                        recommendations.append({
                            'item_id': int(row['item_id']),
                            'title': row.get('title', f"Movie {row['item_id']}"),
                            'genres': row.get('genres', ''),
                            'predicted_rating': float(row['avg_rating']),
                            'popularity_score': float(row['popularity_score']),
                            'reason': f'popular_{genre}'
                        })
                        
                        if len(recommendations) >= n:
                            break
            
            if len(recommendations) >= n:
                break
        
        # Fill remaining slots with popular items if needed
        if len(recommendations) < n:
            popular = self.get_popular_recommendations(
                n - len(recommendations),
                exclude_items + [r['item_id'] for r in recommendations]
            )
            recommendations.extend(popular)
        
        return recommendations[:n]
    
    def should_use_cold_start(self, user_id: int, user_rating_count: int = 0) -> bool:
        """
        Determine if cold start strategy should be used.
        
        Args:
            user_id: User ID
            user_rating_count: Number of ratings user has given
            
        Returns:
            True if cold start should be used
        """
        # Use cold start for:
        # 1. New users (user_id >= 1000000)
        # 2. Users with fewer than 5 ratings
        return user_id >= 1000000 or user_rating_count < 5
    
    def get_onboarding_items(self, n: int = 10) -> List[Dict]:
        """
        Get diverse popular items for onboarding.
        Users are asked to rate these to build initial profile.
        
        Args:
            n: Number of items to return
            
        Returns:
            List of diverse popular items
        """
        if self.popular_items is None:
            return []
        
        # Get items from different genres
        onboarding_items = []
        genres_covered = set()
        
        for _, row in self.popular_items.iterrows():
            item_genres = str(row.get('genres', '')).split('|')
            
            # Prefer items with genres we haven't shown yet
            if not any(g in genres_covered for g in item_genres):
                onboarding_items.append({
                    'item_id': int(row['item_id']),
                    'title': row.get('title', f"Movie {row['item_id']}"),
                    'genres': row.get('genres', ''),
                    'avg_rating': float(row['avg_rating'])
                })
                genres_covered.update(item_genres)
                
                if len(onboarding_items) >= n:
                    break
        
        # Fill with popular items if needed
        if len(onboarding_items) < n:
            for _, row in self.popular_items.iterrows():
                if row['item_id'] not in [i['item_id'] for i in onboarding_items]:
                    onboarding_items.append({
                        'item_id': int(row['item_id']),
                        'title': row.get('title', f"Movie {row['item_id']}"),
                        'genres': row.get('genres', ''),
                        'avg_rating': float(row['avg_rating'])
                    })
                    
                    if len(onboarding_items) >= n:
                        break
        
        return onboarding_items


if __name__ == "__main__":
    print("Cold Start Recommender module loaded")
    print("Provides recommendations for new users before personalization")
