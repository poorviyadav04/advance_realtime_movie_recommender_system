"""
Stage 2: Ranker
Uses machine learning (LightGBM) to re-rank candidates provided by the CandidateGenerator.
"""
import pandas as pd
import numpy as np
import logging
import joblib
from typing import List, Dict, Optional, Tuple
import os
import lightgbm as lgb
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class Ranker:
    """
    Learning to Rank model using LightGBM.
    Re-ranks candidates based on likelihood of interaction (rating >= 4.0 or click).
    """
    
    def __init__(self, model_path: str = "data/models/ranker_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.features = [
            # User features
            'user_rating_avg', 'user_rating_count', 
            # Item features
            'item_rating_avg', 'item_rating_count', 'release_year',
            # Interaction features
            'initial_score', 'source_weight',
            # Context features
            'hour_of_day', 'is_weekend'
        ]
        
    def _extract_features(self, user_id: int, candidates: List[Dict], 
                         user_stats: pd.DataFrame, item_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features for user-item pairs.
        """
        features_list = []
        
        # Get user stats
        u_stat = {'avg_rating': 3.5, 'count': 0}
        if user_stats is not None and user_id in user_stats.index:
            try:
                u_stat = user_stats.loc[user_id]
            except:
                pass
                
        now = datetime.now()
        hour = now.hour
        is_weekend = 1 if now.weekday() >= 5 else 0
        
        for cand in candidates:
            item_id = cand['item_id']
            
            # Get item stats
            i_stat = {'avg_rating': 3.5, 'count': 0}
            if item_stats is not None and item_id in item_stats.index:
                try:
                    i_stat = item_stats.loc[item_id]
                except:
                    pass
            
            # Source weight mapping
            source = cand.get('source', 'unknown')
            source_weight = 1.0
            if source == 'collaborative': source_weight = 1.5
            elif source == 'content_based': source_weight = 1.2
            elif source == 'popularity': source_weight = 0.8
            
            feat = {
                'user_rating_avg': float(u_stat.get('avg_rating', 3.5)),
                'user_rating_count': int(u_stat.get('count', 0)),
                'item_rating_avg': float(i_stat.get('avg_rating', 3.5)),
                'item_rating_count': int(i_stat.get('count', 0)),
                'release_year': 2000, # Placeholder/Default
                'initial_score': float(cand.get('initial_score', 0.5)),
                'source_weight': source_weight,
                'hour_of_day': hour,
                'is_weekend': is_weekend
            }
            features_list.append(feat)
            
        return pd.DataFrame(features_list)

    def fit(self, train_df: pd.DataFrame = None, enable_mlflow: bool = True):
        """
        Train the ranking model with MLflow tracking and offline evaluation.
        Args:
            train_df: Optional DataFrame. If None, loads from data/processed/interaction_logs.csv
            enable_mlflow: Whether to log to MLflow
        """
        logger.info("Training Ranker (LightGBM)...")
        
        # Initialize MLflow
        if enable_mlflow:
            try:
                import mlflow
                mlflow.set_experiment("recommender_ranker")
                mlflow.start_run()
            except Exception as e:
                logger.warning(f"MLflow not available: {e}")
                enable_mlflow = False
        
        # Load training data if not provided
        if train_df is None:
            log_path = Path("data/processed/interaction_logs.csv")
            if not log_path.exists():
                logger.error("No training data found. Run data/data_simulation.py first.")
                return
            train_df = pd.read_csv(log_path)
            
        # Train/Test Split (80/20) for offline evaluation
        from sklearn.model_selection import train_test_split
        train_data, test_data = train_test_split(train_df, test_size=0.2, random_state=42)
        logger.info(f"Split: {len(train_data)} train, {len(test_data)} test samples")
        
        # Feature Engineering
        for df in [train_data, test_data]:
            if 'hour_of_day' not in df.columns:
                df['hour_of_day'] = 12
            if 'is_weekend' not in df.columns:
                df['is_weekend'] = 0
            for col in self.features:
                if col not in df.columns:
                    df[col] = 0
        
        # Prepare training data
        X_train = train_data[self.features]
        y_train = train_data['label']
        X_test = test_data[self.features]
        y_test = test_data['label']
        
        # Hyperparameters (BALANCED: Performance + Regularization)
        params = {
            'n_estimators': 200,          # Moderate number of trees
            'learning_rate': 0.1,         # Faster convergence
            'num_leaves': 45,             # Moderate complexity (between 31-63)
            'max_depth': 7,               # Moderate depth
            'min_child_samples': 25,      # Stronger regularization (was 15)
            'subsample': 0.75,            # Use 75% of samples per tree
            'colsample_bytree': 0.75,     # Use 75% of features per tree
            'reg_alpha': 0.1,             # L1 regularization (NEW!)
            'reg_lambda': 0.1,            # L2 regularization (NEW!)
            'random_state': 42
        }
        
        # Log hyperparameters to MLflow
        if enable_mlflow:
            mlflow.log_params(params)
        
        # Train Model
        self.model = lgb.LGBMClassifier(**params)
        self.model.fit(X_train, y_train)
        
        # Training Metrics
        train_pred = self.model.predict_proba(X_train)[:, 1]
        from sklearn.metrics import roc_auc_score, log_loss
        train_auc = roc_auc_score(y_train, train_pred)
        train_loss = log_loss(y_train, train_pred)
        
        # Test Metrics (Offline Evaluation)
        test_pred = self.model.predict_proba(X_test)[:, 1]
        test_auc = roc_auc_score(y_test, test_pred)
        test_loss = log_loss(y_test, test_pred)
        
        # Ranking Metrics (Precision@K, NDCG@K)
        # For ranking evaluation, we need user-level predictions
        # Simplification: Evaluate average precision across all predictions
        from sklearn.metrics import average_precision_score
        test_ap = average_precision_score(y_test, test_pred)
        
        # Log metrics to MLflow
        if enable_mlflow:
            mlflow.log_metrics({
                'train_auc': train_auc,
                'train_logloss': train_loss,
                'test_auc': test_auc,
                'test_logloss': test_loss,
                'test_avg_precision': test_ap
            })
            
            # Log feature importances
            for feat, imp in zip(self.features, self.model.feature_importances_):
                mlflow.log_metric(f"importance_{feat}", float(imp))
        
        logger.info(f"✅ Ranker trained successfully.")
        logger.info(f"📊 Training Metrics: AUC={train_auc:.4f}, LogLoss={train_loss:.4f}")
        logger.info(f"📊 Test Metrics: AUC={test_auc:.4f}, LogLoss={test_loss:.4f}, AP={test_ap:.4f}")
        logger.info(f"Feature Importances: {dict(zip(self.features, self.model.feature_importances_))}")
        
        # End MLflow run
        if enable_mlflow:
            mlflow.end_run()
        
        # Store metrics for later access
        self.metrics = {
            'train_auc': train_auc,
            'test_auc': test_auc,
            'test_logloss': test_loss,
            'test_avg_precision': test_ap
        }
        
    def predict(self, user_id: int, candidates: List[Dict], 
               user_stats: pd.DataFrame = None, item_stats: pd.DataFrame = None) -> List[Dict]:
        """
        Re-rank a list of candidates.
        """
        if not candidates:
            return []
            
        # If model is not trained, fallback to sorting by initial score
        if self.model is None:
            return sorted(candidates, key=lambda x: x.get('initial_score', 0), reverse=True)
            
        try:
            # Extract features
            X_pred = self._extract_features(user_id, candidates, user_stats, item_stats)
            
            # Predict probabilities
            scores = self.model.predict_proba(X_pred)[:, 1]
            
            # Update scores
            for i, candidate in enumerate(candidates):
                candidate['final_score'] = float(scores[i])
                candidate['ranker_contribution'] = float(scores[i]) - candidate.get('initial_score', 0)
                
            return sorted(candidates, key=lambda x: x.get('final_score', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Ranking failed: {e}")
            # Fallback
            return sorted(candidates, key=lambda x: x.get('initial_score', 0), reverse=True)

    def save_model(self):
        """Save the entire Ranker object including metrics."""
        if self.model:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            # Save the entire Ranker object to preserve metrics
            joblib.dump(self, self.model_path)
            logger.info(f"Ranker (with metrics) saved to {self.model_path}")
    
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info(f"Ranker loaded from {self.model_path}")
        else:
            logger.warning("Ranker model file not found")
