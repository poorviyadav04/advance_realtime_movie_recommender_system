"""
Offline Evaluation Metrics for Recommender Systems.
Implements industry-standard metrics: Precision@K, Recall@K, NDCG.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def precision_at_k(actual: List[int], predicted: List[int], k: int = 10) -> float:
    """
    Calculate Precision@K.
    
    Precision@K = (# of recommended items @K that are relevant) / K
    
    Args:
        actual: List of relevant item IDs
        predicted: List of predicted item IDs (ranked)
        k: Number of top predictions to consider
        
    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if not predicted or k == 0:
        return 0.0
    
    predicted_k = predicted[:k]
    relevant_count = len(set(actual) & set(predicted_k))
    
    return relevant_count / k


def recall_at_k(actual: List[int], predicted: List[int], k: int = 10) -> float:
    """
    Calculate Recall@K.
    
    Recall@K = (# of recommended items @K that are relevant) / (total # of relevant items)
    
    Args:
        actual: List of relevant item IDs
        predicted: List of predicted item IDs (ranked)
        k: Number of top predictions to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not actual:
        return 0.0
    
    predicted_k = predicted[:k]
    relevant_count = len(set(actual) & set(predicted_k))
    
    return relevant_count / len(actual)


def ndcg_at_k(actual: List[int], predicted: List[int], k: int = 10) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG)@K.
    
    NDCG considers both relevance AND ranking position.
    Higher-ranked relevant items contribute more to the score.
    
    Args:
        actual: List of relevant item IDs
        predicted: List of predicted item IDs (ranked)
        k: Number of top predictions to consider
        
    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    if not predicted or not actual:
        return 0.0
    
    predicted_k = predicted[:k]
    
    # Calculate DCG (Discounted Cumulative Gain)
    dcg = 0.0
    for i, item_id in enumerate(predicted_k):
        if item_id in actual:
            # Relevance = 1 for relevant items, 0 for irrelevant
  # Position discount: log2(i+2) because positions start at 1
            dcg += 1.0 / np.log2(i + 2)
    
    # Calculate IDCG (Ideal DCG - best possible ranking)
    idcg = 0.0
    for i in range(min(len(actual), k)):
        idcg += 1.0 / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def evaluate_recommendations(
    user_actual: Dict[int, List[int]], 
    user_predicted: Dict[int, List[int]], 
    k_values: List[int] = [5, 10, 20]
) -> Dict[str, float]:
    """
    Evaluate recommendations across all users.
    
    Args:
        user_actual: Dict mapping user_id -> list of relevant item IDs
        user_predicted: Dict mapping user_id -> list of predicted item IDs (ranked)
        k_values: List of K values to evaluate
        
    Returns:
        Dictionary of average metrics across all users
    """
    results = {f'precision@{k}': [] for k in k_values}
    results.update({f'recall@{k}': [] for k in k_values})
    results.update({f'ndcg@{k}': [] for k in k_values})
    
    common_users = set(user_actual.keys()) & set(user_predicted.keys())
    
    for user_id in common_users:
        actual = user_actual[user_id]
        predicted = user_predicted[user_id]
        
        for k in k_values:
            results[f'precision@{k}'].append(precision_at_k(actual, predicted, k))
            results[f'recall@{k}'].append(recall_at_k(actual, predicted, k))
            results[f'ndcg@{k}'].append(ndcg_at_k(actual, predicted, k))
    
    # Calculate averages
    avg_results = {}
    for metric, values in results.items():
        avg_results[metric] = np.mean(values) if values else 0.0
    
    return avg_results
