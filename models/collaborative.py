"""
Collaborative Filtering using Matrix Factorization.
This finds users with similar tastes and recommends items they liked.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from typing import List, Dict, Tuple
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class CollaborativeFilteringRecommender:
    """
    Collaborative Filtering recommender using Matrix Factorization (SVD).
    
    This model:
    1. Creates a user-item rating matrix
    2. Uses SVD to find latent factors (hidden patterns)
    3. Predicts ratings for unseen items
    4. Recommends items with highest predicted ratings
    """
    
    def __init__(self, n_factors: int = 50, random_state: int = 42):
        """
        Initialize the collaborative filtering model.
        
        Args:
            n_factors: Number of latent factors to learn
            random_state: Random seed for reproducibility
        """
        self.n_factors = n_factors
        self.random_state = random_state
        self.svd = TruncatedSVD(n_components=n_factors, random_state=random_state)
        
        # Model components
        self.user_item_matrix = None
        self.user_factors = None
        self.item_factors = None
        self.user_to_idx = None
        self.idx_to_user = None
        self.item_to_idx = None
        self.idx_to_item = None
        self.item_info = None
        self.global_mean = None
        self.user_means = None
        self.item_means = None
        self.item_biases_arr = None  # Precomputed item biases for fast predict
        self.is_fitted = False
        
    def _create_user_item_matrix(self, ratings_df: pd.DataFrame) -> csr_matrix:
        """Create sparse user-item rating matrix."""
        print("Creating user-item matrix...")
        
        # Create mappings
        unique_users = sorted(ratings_df['user_id'].unique())
        unique_items = sorted(ratings_df['movie_id'].unique())
        
        self.user_to_idx = {user: idx for idx, user in enumerate(unique_users)}
        self.idx_to_user = {idx: user for user, idx in self.user_to_idx.items()}
        self.item_to_idx = {item: idx for idx, item in enumerate(unique_items)}
        self.idx_to_item = {idx: item for item, idx in self.item_to_idx.items()}
        
        # Create matrix
        n_users = len(unique_users)
        n_items = len(unique_items)
        
        # Map ratings to matrix indices
        user_indices = ratings_df['user_id'].map(self.user_to_idx)
        item_indices = ratings_df['movie_id'].map(self.item_to_idx)
        ratings = ratings_df['rating'].values
        
        # Create sparse matrix
        matrix = csr_matrix(
            (ratings, (user_indices, item_indices)),
            shape=(n_users, n_items)
        )
        
        print(f"✅ Matrix created: {n_users:,} users × {n_items:,} items")
        print(f"   Sparsity: {(1 - matrix.nnz / (n_users * n_items)) * 100:.2f}%")
        
        return matrix
    
    def fit(self, ratings_df: pd.DataFrame) -> 'CollaborativeFilteringRecommender':
        """
        Train the collaborative filtering model.
        
        Args:
            ratings_df: DataFrame with columns ['user_id', 'movie_id', 'rating', 'title']
            
        Returns:
            self: The fitted model
        """
        print("🚀 Training Collaborative Filtering Model...")
        print("="*50)
        
        # Store item information for recommendations
        self.item_info = ratings_df[['movie_id', 'title']].drop_duplicates()
        self.item_info = self.item_info.set_index('movie_id')['title'].to_dict()
        
        # Create user-item matrix
        self.user_item_matrix = self._create_user_item_matrix(ratings_df)
        
        # Calculate global and user/item means for better predictions
        self.global_mean = ratings_df['rating'].mean()
        self.user_means = ratings_df.groupby('user_id')['rating'].mean().to_dict()
        self.item_means = ratings_df.groupby('movie_id')['rating'].mean().to_dict()
        # Precompute item bias array for fast vectorized predict
        n_items = len(self.item_to_idx)
        self.item_biases_arr = np.array([
            self.item_means.get(self.idx_to_item[i], self.global_mean) - self.global_mean
            for i in range(n_items)
        ], dtype=np.float64)
        
        # Apply SVD matrix factorization
        print("Applying SVD matrix factorization...")
        self.user_factors = self.svd.fit_transform(self.user_item_matrix)
        self.item_factors = self.svd.components_.T
        
        # Calculate explained variance
        explained_variance = self.svd.explained_variance_ratio_.sum()
        
        self.is_fitted = True
        
        print(f"✅ Model trained successfully!")
        print(f"   Latent factors: {self.n_factors}")
        print(f"   Explained variance: {explained_variance:.3f}")
        print(f"   Global mean rating: {self.global_mean:.2f}")
        
        return self
    
    def _predict_rating(self, user_id: int, item_id: int) -> float:
        """Predict rating for a user-item pair."""
        if user_id not in self.user_to_idx or item_id not in self.item_to_idx:
            # Fallback to global mean for unknown users/items
            return self.global_mean
        
        user_idx = self.user_to_idx[user_id]
        item_idx = self.item_to_idx[item_id]
        
        # Matrix factorization prediction
        predicted = np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        
        # Add bias terms for better accuracy
        user_bias = self.user_means.get(user_id, self.global_mean) - self.global_mean
        item_bias = self.item_means.get(item_id, self.global_mean) - self.global_mean
        
        final_prediction = self.global_mean + user_bias + item_bias + predicted
        
        # Clip to valid rating range
        return np.clip(final_prediction, 1.0, 5.0)
    
    def predict(self, user_id: int, n_recommendations: int = 10, 
                exclude_seen: bool = True, user_ratings: pd.DataFrame = None) -> List[Dict]:
        """
        Get recommendations for a user (vectorized for performance).
        
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
        
        n_items = len(self.item_to_idx)
        
        # Unknown user: fallback to global mean and return top by item bias + factor norm
        if user_id not in self.user_to_idx:
            scores = self.global_mean + self.item_biases_arr + np.mean(self.item_factors, axis=1)
            seen_items = set()
        else:
            user_idx = self.user_to_idx[user_id]
            user_bias = self.user_means.get(user_id, self.global_mean) - self.global_mean
            # Vectorized: one dot product for all items
            scores = (
                self.global_mean
                + user_bias
                + self.item_biases_arr
                + (self.user_factors[user_idx] @ self.item_factors.T)
            )
            scores = np.clip(scores, 1.0, 5.0)
            
            if exclude_seen and user_ratings is not None:
                seen_items = set(user_ratings[user_ratings['user_id'] == user_id]['movie_id'])
            else:
                seen_items = set()
        
        # Mask out seen items
        for item_id in seen_items:
            if item_id in self.item_to_idx:
                scores[self.item_to_idx[item_id]] = -np.inf
        
        # Top N indices (vectorized)
        top_indices = np.argsort(scores)[::-1][:n_recommendations]
        
        recommendations = []
        for idx in top_indices:
            if scores[idx] == -np.inf:
                break
            item_id = self.idx_to_item[idx]
            predicted_rating = float(scores[idx])
            title = self.item_info.get(item_id, f"Movie {item_id}")
            recommendations.append({
                'item_id': int(item_id),
                'title': title,
                'score': predicted_rating,
                'reason': 'collaborative_filtering',
                'predicted_rating': predicted_rating
            })
        
        return recommendations
    
    def get_similar_users(self, user_id: int, n_similar: int = 5) -> List[Dict]:
        """Find users with similar preferences."""
        if not self.is_fitted or user_id not in self.user_to_idx:
            return []
        
        user_idx = self.user_to_idx[user_id]
        user_vector = self.user_factors[user_idx].reshape(1, -1)
        
        # Calculate similarity with all other users
        similarities = cosine_similarity(user_vector, self.user_factors)[0]
        
        # Get top similar users (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar+1]
        
        similar_users = []
        for idx in similar_indices:
            similar_user_id = self.idx_to_user[idx]
            similarity_score = similarities[idx]
            
            similar_users.append({
                'user_id': int(similar_user_id),
                'similarity': float(similarity_score)
            })
        
        return similar_users
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model."""
        if not self.is_fitted:
            return {"status": "not_fitted"}
        
        return {
            "status": "fitted",
            "model_type": "collaborative_filtering",
            "n_factors": self.n_factors,
            "n_users": len(self.user_to_idx),
            "n_items": len(self.item_to_idx),
            "global_mean_rating": float(self.global_mean),
            "explained_variance": float(self.svd.explained_variance_ratio_.sum())
        }
    
    def save_model(self, filepath: str) -> None:
        """Save the trained model to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        model_data = {
            'svd': self.svd,
            'user_factors': self.user_factors,
            'item_factors': self.item_factors,
            'user_to_idx': self.user_to_idx,
            'idx_to_user': self.idx_to_user,
            'item_to_idx': self.item_to_idx,
            'idx_to_item': self.idx_to_item,
            'item_info': self.item_info,
            'global_mean': self.global_mean,
            'user_means': self.user_means,
            'item_means': self.item_means,
            'item_biases_arr': self.item_biases_arr,
            'n_factors': self.n_factors,
            'random_state': self.random_state,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, filepath)
        print(f"✅ Collaborative filtering model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str) -> 'CollaborativeFilteringRecommender':
        """Load a trained model from disk."""
        model_data = joblib.load(filepath)
        
        model = cls(
            n_factors=model_data['n_factors'],
            random_state=model_data['random_state']
        )
        
        # Restore all model components
        model.svd = model_data['svd']
        model.user_factors = model_data['user_factors']
        model.item_factors = model_data['item_factors']
        model.user_to_idx = model_data['user_to_idx']
        model.idx_to_user = model_data['idx_to_user']
        model.item_to_idx = model_data['item_to_idx']
        model.idx_to_item = model_data['idx_to_item']
        model.item_info = model_data['item_info']
        model.global_mean = model_data['global_mean']
        model.user_means = model_data['user_means']
        model.item_means = model_data['item_means']
        model.item_biases_arr = model_data.get('item_biases_arr')
        if model.item_biases_arr is None:
            # Backfill for models saved before item_biases_arr was added
            n_items = len(model.item_to_idx)
            model.item_biases_arr = np.array([
                model.item_means.get(model.idx_to_item[i], model.global_mean) - model.global_mean
                for i in range(n_items)
            ], dtype=np.float64)
        model.is_fitted = model_data['is_fitted']
        
        print(f"✅ Collaborative filtering model loaded from {filepath}")
        return model

def train_collaborative_model():
    """Train and save a collaborative filtering model."""
    print("🚀 TRAINING COLLABORATIVE FILTERING MODEL")
    print("="*60)
    
    # Load training data
    train_path = Path("data/processed/train_data.csv")
    if not train_path.exists():
        print("❌ Training data not found. Run: python data/prepare_data.py")
        return None
    
    train_data = pd.read_csv(train_path)
    print(f"Loaded {len(train_data):,} training ratings")
    
    # Train model
    model = CollaborativeFilteringRecommender(n_factors=50, random_state=42)
    model.fit(train_data)
    
    # Save model
    model_path = Path("data/models/collaborative_model.joblib")
    model_path.parent.mkdir(exist_ok=True)
    model.save_model(str(model_path))
    
    # Test the model
    print("\n🧪 TESTING COLLABORATIVE FILTERING MODEL")
    print("-"*50)
    
    # Test with different users to show personalization
    test_users = [635, 1000, 2000]  # Different users with different tastes
    
    for user_id in test_users:
        print(f"\n👤 User {user_id} Recommendations:")
        try:
            recommendations = model.predict(
                user_id=user_id,
                n_recommendations=3,
                exclude_seen=True,
                user_ratings=train_data
            )
            
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['title'][:45]} (predicted rating: {rec['score']:.2f})")
            
            # Show similar users
            similar_users = model.get_similar_users(user_id, n_similar=3)
            if similar_users:
                print(f"     Similar users: {[u['user_id'] for u in similar_users]}")
                
        except Exception as e:
            print(f"  Error for user {user_id}: {e}")
    
    print(f"\n✅ Collaborative filtering model ready!")
    print(f"Model saved at: {model_path}")
    
    return model

if __name__ == "__main__":
    train_collaborative_model()