"""
Onboarding API endpoints for new users.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.database import get_db
from models.user import User
from models.cold_start import ColdStartRecommender
from middleware.auth_middleware import get_current_user

# Create router
router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# Load data for cold start recommender
try:
    movies_df = pd.read_csv("data/processed/movies_with_features.csv")
    ratings_df = pd.read_csv("data/processed/train_data.csv")
    cold_start_recommender = ColdStartRecommender(movies_df, ratings_df)
except Exception as e:
    print(f"Warning: Could not load data for cold start: {e}")
    cold_start_recommender = None


@router.get("/popular-movies")
async def get_popular_movies_for_onboarding(
    n: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get popular movies for new user onboarding.
    Users rate these to build initial profile.
    
    Args:
        n: Number of movies to return
        current_user: Authenticated user
        
    Returns:
        List of popular movies to rate
    """
    if cold_start_recommender is None:
        raise HTTPException(status_code=503, detail="Cold start system not available")
    
    items = cold_start_recommender.get_onboarding_items(n)
    
    return {
        "movies": items,
        "count": len(items),
        "message": "Rate at least 5 movies to get personalized recommendations"
    }


@router.get("/genres")
async def get_available_genres():
    """
    Get list of available genres for preference selection.
    
    Returns:
        List of genres
    """
    if cold_start_recommender is None or cold_start_recommender.movies_df is None:
        # Default genres
        genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", 
                  "Documentary", "Drama", "Fantasy", "Horror", "Mystery", 
                  "Romance", "Sci-Fi", "Thriller", "War", "Western"]
    else:
        # Extract genres from movies
        all_genres = set()
        for genres_str in cold_start_recommender.movies_df['genres'].dropna():
            all_genres.update(str(genres_str).split('|'))
        genres = sorted(list(all_genres))
    
    return {"genres": genres}


class PreferencesUpdate(BaseModel):
    """User preferences update model."""
    favorite_genres: List[str] = []
    onboarding_complete: bool = False


@router.post("/preferences")
async def update_preferences(
    preferences: PreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save user genre preferences.
    
    Args:
        preferences: User preferences
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated user info
    """
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update preferences
    user_prefs = user.preferences or {}
    user_prefs["favorite_genres"] = preferences.favorite_genres
    user_prefs["onboarding_complete"] = preferences.onboarding_complete
    user.preferences = user_prefs
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Preferences updated",
        "preferences": user_prefs
    }


@router.get("/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has completed onboarding.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Onboarding status
    """
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = user.preferences or {}
    onboarding_complete = preferences.get("onboarding_complete", False)
    
    # Also check if user has rated at least 5 items
    # (Would query user_events table in production)
    
    return {
        "onboarding_complete": onboarding_complete,
        "preferences": preferences
    }


if __name__ == "__main__":
    print("Onboarding API router defined")
    print("Endpoints:")
    print("  GET /onboarding/popular-movies - Get movies for rating")
    print("  GET /onboarding/genres - Get available genres")
    print("  POST /onboarding/preferences - Save preferences")
    print("  GET /onboarding/status - Check onboarding status")
