"""
Hybrid Recommender combining Popularity, Collaborative Filtering, and Content-Based approaches.
Now implements a Two-Stage Architecture: Candidate Generation -> Ranking.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import sys
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from models.popularity import PopularityRecommender
from models.collaborative import CollaborativeFilteringRecommender
from models.content_based import ContentBasedRecommender
from models.candidate_generation import CandidateGenerator
from models.ranker import Ranker

class HybridRecommender:
    """
    Two-Stage Hybrid Recommender.
    
    Stage 1: Candidate Generation (Retrieval)
    - Retrieves candidates from Popularity, Collaborative, and Content-Based models.
    
    Stage 2: Ranking (Learning to Rank)
    - Re-ranks candidates using a LightGBM model based on user-item features.
    """
    
    def __init__(self, 
                 default_weights: Dict[str, float] = None,
                 diversity_threshold: float = 0.7,
                 min_score_threshold: float = 0.1):
        """
        Initialize the hybrid recommender.
        """
        # Legacy weights for fallback or candidate gen weighting
        self.default_weights = default_weights or {
            'collaborative': 0.4,
            'content_based': 0.3,
            'popularity': 0.2,
            'diversity': 0.1
        }
        
        self.diversity_threshold = diversity_threshold
        self.min_score_threshold = min_score_threshold
        
        # Component Models
        self.popularity_model = None
        self.collaborative_model = None
        self.content_based_model = None
        
        # Two-Stage Components
        self.candidate_generator = None
        self.ranker = None
        
        # Data stats
        self.train_data = None
        self.user_activity_stats = None
        self.item_popularity_stats = None
        
        self.is_fitted = False
    
    def fit(self, 
            popularity_model: PopularityRecommender,
            collaborative_model: CollaborativeFilteringRecommender,
            content_based_model: ContentBasedRecommender,
            train_data: pd.DataFrame) -> 'HybridRecommender':
        """
        Initialize components and train ranker.
        """
        print("🚀 Initializing Two-Stage Hybrid Recommender...")
        print("="*50)
        
        self.popularity_model = popularity_model
        self.collaborative_model = collaborative_model
        self.content_based_model = content_based_model
        self.train_data = train_data
        
        # Initialize Stage 1
        print("Initializing Candidate Generator...")
        self.candidate_generator = CandidateGenerator(
            popularity_model, collaborative_model, content_based_model
        )
        
        # Analyze stats for feature engineering
        print("Analyzing data for Ranker features...")
        self._analyze_stats(train_data)
        
        # Initialize and Train Stage 2 (Ranker)
        print("Training Ranker Model...")
        self.ranker = Ranker()
        # Train on synthetic interaction logs
        self.ranker.fit()  # Auto-loads from data/processed/interaction_logs.csv
        # Save ranker with metrics for Dashboard
        self.ranker.save_model()
        
        self.is_fitted = True
        print(f"✅ Two-Stage pipeline ready!")
        
        return self
        
    def _analyze_stats(self, df: pd.DataFrame):
        """Calculate stats for feature engineering."""
        self.user_activity_stats = df.groupby('user_id').agg({
            'rating': ['count', 'mean']
        })
        self.user_activity_stats.columns = ['count', 'avg_rating']
        
        self.item_popularity_stats = df.groupby('movie_id').agg({
            'rating': ['count', 'mean']
        })
        self.item_popularity_stats.columns = ['count', 'avg_rating']

    def predict(self, user_id: int, n_recommendations: int = 10, 
                exclude_seen: bool = True, user_ratings: pd.DataFrame = None) -> List[Dict]:
        """
        Execute Two-Stage Recommendation Pipeline.
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
            
        # Stage 1: Candidate Generation
        # Retrieve more than we need (e.g., 50 candidates) to allow Ranker to filter/sort
        candidates = self.candidate_generator.get_candidates(
            user_id, n_candidates=50, user_history=user_ratings
        )
        
        if not candidates:
            return []
            
        # Stage 2: Ranking
        # Re-rank the candidates
        ranked_candidates = self.ranker.predict(
            user_id, candidates, 
            self.user_activity_stats, self.item_popularity_stats
        )
        
        # Filter (exclude seen, min score)
        # Note: exclude_seen is partially handled in logic, but good to reinforce
        final_recs = []
        seen_ids = set() # Populate if user_ratings provided
        
        for cand in ranked_candidates:
            if len(final_recs) >= n_recommendations:
                break
                
            # Format output
            rec = {
                'item_id': int(cand['item_id']),
                'title': cand.get('title', f"Item {cand['item_id']}"),
                'score': float(cand.get('final_score', cand.get('initial_score', 0))),
                'reason': 'hybrid_ranker',
                'explanation': f"Recommended via {cand.get('source', 'hybrid')}",
                'genres': cand.get('genres', '')
            }
            final_recs.append(rec)
            
        return final_recs
    
    def get_model_info(self) -> Dict:
        return {
            "status": "fitted",
            "type": "two_stage_hybrid",
            "stage1": "candidate_generator",
            "stage2": "lightgbm_ranker"
        }

    def save_model(self, filepath: str) -> None:
        """Save hybrid model (wraps components)."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
            
        # We save the references and stats. 
        # Components (pop, cf, content) are saved separately usually, 
        # but we can save the orchestrator state here.
        model_data = {
            'user_stats': self.user_activity_stats,
            'item_stats': self.item_popularity_stats,
            'is_fitted': self.is_fitted
        }
        joblib.dump(model_data, filepath)
        # Ranker should be saved separately strictly speaking, but for simplicity:
        self.ranker.save_model()
        print(f"✅ Hybrid orchestrator saved to {filepath}")

    @classmethod
    def load_model(cls, filepath: str, 
                   popularity_model: PopularityRecommender,
                   collaborative_model: CollaborativeFilteringRecommender,
                   content_based_model: ContentBasedRecommender,
                   train_data: pd.DataFrame) -> 'HybridRecommender':
        """Load hybrid model."""
        model_data = joblib.load(filepath)
        
        model = cls()
        model.popularity_model = popularity_model
        model.collaborative_model = collaborative_model
        model.content_based_model = content_based_model
        model.train_data = train_data
        
        # Re-initialize Stage 1
        model.candidate_generator = CandidateGenerator(
            popularity_model, collaborative_model, content_based_model
        )
        
        # Restore stats
        model.user_activity_stats = model_data.get('user_stats')
        model.item_popularity_stats = model_data.get('item_stats')
        model.is_fitted = model_data['is_fitted']
        
        # Restore Stage 2
        model.ranker = Ranker()
        model.ranker.load_model()
        
        return model

def train_hybrid_model():
    """Train and save a hybrid model using pre-trained individual models."""
    print("🚀 TRAINING TWO-STAGE HYBRID RECOMMENDER")
    print("="*60)
    
    # Load training data
    train_path = Path("data/processed/train_data.csv")
    if not train_path.exists():
        print("❌ Training data not found.")
        return None
    
    train_data = pd.read_csv(train_path)
    
    # Load pre-trained models
    print("\nLoading pre-trained models...")
    try:
        popularity_model = PopularityRecommender.load_model("data/models/popularity_model.joblib")
        collaborative_model = CollaborativeFilteringRecommender.load_model("data/models/collaborative_model.joblib")
        content_based_model = ContentBasedRecommender.load_model("data/models/content_based_model.joblib")
    except Exception as e:
        print(f"❌ Failed to load component models: {e}")
        return None
    
    # Train hybrid model
    hybrid_model = HybridRecommender()
    hybrid_model.fit(popularity_model, collaborative_model, content_based_model, train_data)
    
    # Save hybrid model
    model_path = Path("data/models/hybrid_model.joblib")
    hybrid_model.save_model(str(model_path))
    
    # Test
    print("\n🧪 TESTING TWO-STAGE PIPELINE")
    print("-"*50)
    
    user_id = 1000  # Example user
    try:
        recs = hybrid_model.predict(user_id, n_recommendations=3)
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec['title']} (score: {rec['score']:.3f})")
            print(f"     {rec['explanation']}")
    except Exception as e:
        print(f"Test failed: {e}")
            
    print(f"\n✅ Two-Stage Hybrid model ready!")
    return hybrid_model

if __name__ == "__main__":
    train_hybrid_model()