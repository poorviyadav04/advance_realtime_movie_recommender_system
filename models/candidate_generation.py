"""
Stage 1: Candidate Generation
Retrieves a broad set of relevant items from multiple sources for the Ranker.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Set
import logging
from collections import defaultdict

# Import existing models
from models.popularity import PopularityRecommender
from models.collaborative import CollaborativeFilteringRecommender
from models.content_based import ContentBasedRecommender

logger = logging.getLogger(__name__)

class CandidateGenerator:
    """
    Retrieves candidates from multiple recommendation sources.
    
    Sources:
    1. Collaborative Filtering (Personalized, serendipitous)
    2. Content-Based (Similar items to user history)
    3. Popularity (Fallback, trending items)
    """
    
    def __init__(self, 
                 popularity_model: PopularityRecommender,
                 collaborative_model: CollaborativeFilteringRecommender,
                 content_based_model: ContentBasedRecommender):
        """
        Initialize with pre-trained models.
        """
        self.pop_model = popularity_model
        self.cf_model = collaborative_model
        self.cb_model = content_based_model
        
    def get_candidates(self, user_id: int, n_candidates: int = 100, 
                      user_history: pd.DataFrame = None) -> List[Dict]:
        """
        Retrieve unique candidates from all sources.
        
        Args:
            user_id: User ID
            n_candidates: Total number of candidates to retrieve
            user_history: Optional user history for exclusion
            
        Returns:
            List of candidate dictionaries
        """
        candidates = {}  # Use dict for deduplication by item_id
        
        # 1. Collaborative Filtering (40% of candidates)
        n_cf = int(n_candidates * 0.4)
        if self.cf_model and self.cf_model.is_fitted:
            try:
                cf_recs = self.cf_model.predict(user_id, n_recommendations=n_cf)
                for rec in cf_recs:
                    item_id = rec['item_id']
                    if item_id not in candidates:
                        rec['source'] = 'collaborative'
                        rec['initial_score'] = rec['score']
                        candidates[item_id] = rec
            except Exception as e:
                logger.warning(f"CF Candidate generation failed: {e}")

        # 2. Content-Based (30% of candidates)
        n_cb = int(n_candidates * 0.3)
        if self.cb_model and self.cb_model.is_fitted:
            try:
                cb_recs = self.cb_model.predict(user_id, n_recommendations=n_cb)
                for rec in cb_recs:
                    item_id = rec['item_id']
                    if item_id not in candidates:
                        rec['source'] = 'content_based'
                        rec['initial_score'] = rec['score']
                        candidates[item_id] = rec
            except Exception as e:
                logger.warning(f"Content-Based Candidate generation failed: {e}")
                
        # 3. Popularity (Fill remaining or at least 30%)
        # Always fetch enough to fill the gap
        current_count = len(candidates)
        n_pop = max(int(n_candidates * 0.3), n_candidates - current_count)
        
        if self.pop_model and self.pop_model.is_fitted:
            try:
                pop_recs = self.pop_model.predict(user_id, n_recommendations=n_pop)
                for rec in pop_recs:
                    item_id = rec['item_id']
                    if item_id not in candidates:
                        rec['source'] = 'popularity'
                        rec['initial_score'] = rec['score']
                        candidates[item_id] = rec
            except Exception as e:
                logger.warning(f"Popularity Candidate generation failed: {e}")
                
        return list(candidates.values())
