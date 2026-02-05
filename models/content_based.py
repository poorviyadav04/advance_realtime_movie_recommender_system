"""
Content-Based Filtering using TF-IDF and Cosine Similarity.
This recommends items similar to what the user has liked before.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class ContentBasedRecommender:
    """
    Content-Based recommender using TF-IDF vectorization and cosine similarity.
    
    This model:
    1. Analyzes movie features (genres, cast, director, keywords)
    2. Creates TF-IDF vectors for each movie
    3. Calculates similarity between movies
    4. Recommends movies similar to ones the user liked
    """
    
    def __init__(self, min_rating_threshold: float = 4.0):
        """
        Initialize the content-based recommender.
        
        Args:
            min_rating_threshold: Minimum rating to consider a movie "liked"
        """
        self.min_rating_threshold = min_rating_threshold
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2
        )
        
        # Model components
        self.movie_features = None
        self.similarity_matrix = None
        self.movie_to_idx = None
        self.idx_to_movie = None
        self.movie_info = None
        self.feature_names = None
        self.is_fitted = False
        
    def _extract_movie_features(self, movies_df: pd.DataFrame) -> pd.Series:
        """Extract and combine movie features for TF-IDF."""
        print("Extracting movie features...")
        
        # Combine multiple features into a single text representation
        features = []
        
        for _, movie in movies_df.iterrows():
            feature_text = []
            
            # Add genres (most important feature)
            if pd.notna(movie['genres']):
                genres = movie['genres'].replace('|', ' ')
                feature_text.append(genres)
                # Give genres more weight by repeating them
                feature_text.append(genres)
            
            # Add title words (for keyword matching)
            if pd.notna(movie['title']):
                # Extract year and clean title
                title = movie['title']
                if '(' in title and ')' in title:
                    title = title.split('(')[0].strip()
                feature_text.append(title)
            
            # Combine all features
            combined_features = ' '.join(feature_text)
            features.append(combined_features)
        
        return pd.Series(features, index=movies_df.index)
    
    def fit(self, ratings_df: pd.DataFrame) -> 'ContentBasedRecommender':
        """
        Train the content-based model.
        
        Args:
            ratings_df: DataFrame with columns ['user_id', 'movie_id', 'rating', 'title', 'genres']
            
        Returns:
            self: The fitted model
        """
        print("🚀 Training Content-Based Filtering Model...")
        print("="*50)
        
        # Get unique movies with their features
        movies_df = ratings_df[['movie_id', 'title', 'genres']].drop_duplicates()
        movies_df = movies_df.reset_index(drop=True)
        
        print(f"Processing {len(movies_df):,} unique movies...")
        
        # Store movie information
        self.movie_info = movies_df.set_index('movie_id')[['title', 'genres']].to_dict('index')
        
        # Create mappings
        self.movie_to_idx = {movie_id: idx for idx, movie_id in enumerate(movies_df['movie_id'])}
        self.idx_to_movie = {idx: movie_id for movie_id, idx in self.movie_to_idx.items()}
        
        # Extract features for TF-IDF
        movie_features_text = self._extract_movie_features(movies_df)
        
        # Create TF-IDF vectors
        print("Creating TF-IDF vectors...")
        self.movie_features = self.tfidf_vectorizer.fit_transform(movie_features_text)
        self.feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        # Calculate similarity matrix
        print("Calculating movie similarity matrix...")
        self.similarity_matrix = cosine_similarity(self.movie_features)
        
        self.is_fitted = True
        
        print(f"✅ Content-based model trained successfully!")
        print(f"   Movies processed: {len(movies_df):,}")
        print(f"   Features extracted: {len(self.feature_names):,}")
        print(f"   Similarity matrix: {self.similarity_matrix.shape}")
        print(f"   Average similarity: {self.similarity_matrix.mean():.3f}")
        
        return self
    
    def get_similar_movies(self, movie_id: int, n_similar: int = 10) -> List[Dict]:
        """
        Get movies similar to a given movie.
        
        Args:
            movie_id: Movie ID to find similar movies for
            n_similar: Number of similar movies to return
            
        Returns:
            List of similar movies with similarity scores
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before finding similar movies")
        
        if movie_id not in self.movie_to_idx:
            return []
        
        movie_idx = self.movie_to_idx[movie_id]
        similarity_scores = self.similarity_matrix[movie_idx]
        
        # Get indices of most similar movies (excluding the movie itself)
        similar_indices = np.argsort(similarity_scores)[::-1][1:n_similar+1]
        
        similar_movies = []
        for idx in similar_indices:
            similar_movie_id = self.idx_to_movie[idx]
            similarity_score = similarity_scores[idx]
            
            movie_info = self.movie_info.get(similar_movie_id, {})
            
            similar_movies.append({
                'item_id': int(similar_movie_id),
                'title': movie_info.get('title', f'Movie {similar_movie_id}'),
                'similarity': float(similarity_score),
                'genres': movie_info.get('genres', 'Unknown')
            })
        
        return similar_movies
    
    def _explain_similarity(self, movie_id1: int, movie_id2: int) -> str:
        """Explain why two movies are similar."""
        if movie_id1 not in self.movie_to_idx or movie_id2 not in self.movie_to_idx:
            return "Unknown similarity"
        
        movie1_info = self.movie_info.get(movie_id1, {})
        movie2_info = self.movie_info.get(movie_id2, {})
        
        # Find common genres
        genres1 = set(movie1_info.get('genres', '').split('|'))
        genres2 = set(movie2_info.get('genres', '').split('|'))
        common_genres = genres1 & genres2
        
        if common_genres:
            return f"Similar genres: {', '.join(common_genres)}"
        else:
            return "Similar themes and style"
    
    def predict(self, user_id: int, n_recommendations: int = 10, 
                exclude_seen: bool = True, user_ratings: pd.DataFrame = None) -> List[Dict]:
        """
        Get content-based recommendations for a user.
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations to return
            exclude_seen: Whether to exclude movies the user has already rated
            user_ratings: DataFrame of user's previous ratings
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        if user_ratings is None:
            return []
        
        # Get user's ratings
        user_data = user_ratings[user_ratings['user_id'] == user_id]
        
        if len(user_data) == 0:
            # For new users, recommend popular movies from different genres
            return self._get_diverse_popular_movies(n_recommendations)
        
        # Find movies the user liked (rating >= threshold)
        liked_movies = user_data[user_data['rating'] >= self.min_rating_threshold]
        
        if len(liked_movies) == 0:
            # If user hasn't liked anything highly, use all their ratings
            liked_movies = user_data
        
        # Get movies to exclude
        seen_movies = set(user_data['movie_id']) if exclude_seen else set()
        
        # Collect recommendations based on liked movies
        recommendations_dict = {}
        
        for _, liked_movie in liked_movies.iterrows():
            movie_id = liked_movie['movie_id']
            user_rating = liked_movie['rating']
            
            # Get similar movies
            similar_movies = self.get_similar_movies(movie_id, n_similar=20)
            
            for similar_movie in similar_movies:
                similar_id = similar_movie['item_id']
                
                # Skip if already seen
                if similar_id in seen_movies:
                    continue
                
                # Calculate weighted score based on user's rating and similarity
                weighted_score = (user_rating / 5.0) * similar_movie['similarity']
                
                if similar_id in recommendations_dict:
                    # If movie already recommended, take the higher score
                    if weighted_score > recommendations_dict[similar_id]['score']:
                        recommendations_dict[similar_id] = {
                            'item_id': similar_id,
                            'title': similar_movie['title'],
                            'score': weighted_score,
                            'reason': 'content_based',
                            'explanation': f"Similar to {liked_movie['title']} ({self._explain_similarity(movie_id, similar_id)})",
                            'genres': similar_movie['genres'],
                            'similarity': similar_movie['similarity'],
                            'based_on': liked_movie['title']
                        }
                else:
                    recommendations_dict[similar_id] = {
                        'item_id': similar_id,
                        'title': similar_movie['title'],
                        'score': weighted_score,
                        'reason': 'content_based',
                        'explanation': f"Similar to {liked_movie['title']} ({self._explain_similarity(movie_id, similar_id)})",
                        'genres': similar_movie['genres'],
                        'similarity': similar_movie['similarity'],
                        'based_on': liked_movie['title']
                    }
        
        # Sort by score and return top N
        recommendations = list(recommendations_dict.values())
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:n_recommendations]
    
    def _get_diverse_popular_movies(self, n_recommendations: int) -> List[Dict]:
        """Get diverse popular movies for new users."""
        # This is a fallback for users with no rating history
        # In a real system, you'd use popularity data
        popular_movies = []
        
        # Get a sample of movies from different genres
        sample_movies = list(self.movie_info.keys())[:n_recommendations*2]
        
        for movie_id in sample_movies[:n_recommendations]:
            movie_info = self.movie_info[movie_id]
            popular_movies.append({
                'item_id': int(movie_id),
                'title': movie_info['title'],
                'score': 0.5,  # Neutral score
                'reason': 'content_based_popular',
                'explanation': 'Popular movie for new users',
                'genres': movie_info['genres']
            })
        
        return popular_movies
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model."""
        if not self.is_fitted:
            return {"status": "not_fitted"}
        
        return {
            "status": "fitted",
            "model_type": "content_based",
            "n_movies": len(self.movie_to_idx),
            "n_features": len(self.feature_names),
            "min_rating_threshold": self.min_rating_threshold,
            "avg_similarity": float(self.similarity_matrix.mean()),
            "similarity_matrix_shape": self.similarity_matrix.shape
        }
    
    def save_model(self, filepath: str) -> None:
        """Save the trained model to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'movie_features': self.movie_features,
            'similarity_matrix': self.similarity_matrix,
            'movie_to_idx': self.movie_to_idx,
            'idx_to_movie': self.idx_to_movie,
            'movie_info': self.movie_info,
            'feature_names': self.feature_names,
            'min_rating_threshold': self.min_rating_threshold,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, filepath)
        print(f"✅ Content-based model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str) -> 'ContentBasedRecommender':
        """Load a trained model from disk."""
        model_data = joblib.load(filepath)
        
        model = cls(min_rating_threshold=model_data['min_rating_threshold'])
        
        # Restore all model components
        model.tfidf_vectorizer = model_data['tfidf_vectorizer']
        model.movie_features = model_data['movie_features']
        model.similarity_matrix = model_data['similarity_matrix']
        model.movie_to_idx = model_data['movie_to_idx']
        model.idx_to_movie = model_data['idx_to_movie']
        model.movie_info = model_data['movie_info']
        model.feature_names = model_data['feature_names']
        model.is_fitted = model_data['is_fitted']
        
        print(f"✅ Content-based model loaded from {filepath}")
        return model

def train_content_based_model():
    """Train and save a content-based model."""
    print("🚀 TRAINING CONTENT-BASED FILTERING MODEL")
    print("="*60)
    
    # Load training data
    train_path = Path("data/processed/train_data.csv")
    if not train_path.exists():
        print("❌ Training data not found. Run: python data/prepare_data.py")
        return None
    
    train_data = pd.read_csv(train_path)
    print(f"Loaded {len(train_data):,} training ratings")
    
    # Train model
    model = ContentBasedRecommender(min_rating_threshold=4.0)
    model.fit(train_data)
    
    # Save model
    model_path = Path("data/models/content_based_model.joblib")
    model_path.parent.mkdir(exist_ok=True)
    model.save_model(str(model_path))
    
    # Test the model
    print("\n🧪 TESTING CONTENT-BASED MODEL")
    print("-"*50)
    
    # Test with different users to show content-based recommendations
    test_users = [635, 1000, 2000]
    
    for user_id in test_users:
        print(f"\n👤 User {user_id} Content-Based Recommendations:")
        try:
            recommendations = model.predict(
                user_id=user_id,
                n_recommendations=3,
                exclude_seen=True,
                user_ratings=train_data
            )
            
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['title'][:40]} (score: {rec['score']:.3f})")
                print(f"     {rec['explanation']}")
            
            # Test similarity function
            user_ratings = train_data[train_data['user_id'] == user_id]
            if len(user_ratings) > 0:
                sample_movie = user_ratings.iloc[0]['movie_id']
                similar_movies = model.get_similar_movies(sample_movie, n_similar=2)
                if similar_movies:
                    print(f"     Movies similar to {user_ratings.iloc[0]['title'][:30]}:")
                    for sim_movie in similar_movies:
                        print(f"       - {sim_movie['title'][:35]} (similarity: {sim_movie['similarity']:.3f})")
                
        except Exception as e:
            print(f"  Error for user {user_id}: {e}")
    
    print(f"\n✅ Content-based model ready!")
    print(f"Model saved at: {model_path}")
    
    return model

if __name__ == "__main__":
    train_content_based_model()