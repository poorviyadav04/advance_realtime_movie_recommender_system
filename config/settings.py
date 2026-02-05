"""
Configuration settings for the real-time recommender system.
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = DATA_DIR / "models"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./recommender.db"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # MLflow settings
    MLFLOW_TRACKING_URI: str = "sqlite:///./mlflow.db"
    MLFLOW_EXPERIMENT_NAME: str = "recommender-system"
    
    # Model settings
    COLLABORATIVE_FACTORS: int = 50
    CONTENT_SIMILARITY_THRESHOLD: float = 0.1
    HYBRID_ALPHA: float = 0.7  # Weight for collaborative filtering
    HYBRID_BETA: float = 0.3   # Weight for content-based
    
    # Recommendation settings
    DEFAULT_N_RECOMMENDATIONS: int = 10
    CANDIDATE_POOL_SIZE: int = 100
    
    # Real-time settings
    EVENT_BATCH_SIZE: int = 100
    FEATURE_UPDATE_INTERVAL: int = 300  # seconds
    
    # Evaluation settings
    TEST_SIZE: float = 0.2
    RANDOM_STATE: int = 42
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.RAW_DATA_DIR.mkdir(exist_ok=True)
settings.PROCESSED_DATA_DIR.mkdir(exist_ok=True)
settings.MODELS_DIR.mkdir(exist_ok=True)