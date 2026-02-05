"""
Main FastAPI application for the real-time recommender system.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uvicorn
import pandas as pd
from pathlib import Path
import sys
from sqlalchemy.orm import Session


def _utc_now_iso() -> str:
    """Return current UTC time in ISO format for API responses."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import settings
from config.database import get_db, get_redis, create_all_tables  # Added create_all_tables
from models.popularity import PopularityRecommender
from models.collaborative import CollaborativeFilteringRecommender
from models.content_based import ContentBasedRecommender
from models.hybrid import HybridRecommender
from models.online_learner import OnlineLearner  # NEW IN PHASE 6!
from evaluation.ab_testing import ExperimentManager  # NEW IN PHASE 6!
from ingestion.event_processor import event_processor, create_tables
from feature_store.recommendation_cache import recommendation_cache, cache_metrics
from api.auth import router as auth_router  # NEW IN PHASE 7!
from api.onboarding import router as onboarding_router  # NEW IN PHASE 7!

# Create FastAPI app
app = FastAPI(
    title="Real-Time Recommender System",
    description="A production-grade real-time recommender system with hybrid approaches",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

 # Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NEW IN PHASE 7: Include authentication router
app.include_router(auth_router)
app.include_router(onboarding_router)

# Global variables for models and data
popularity_model = None
collaborative_model = None
content_based_model = None
hybrid_model = None
train_data = None

# NEW IN PHASE 6: Online Learning and A/B Testing
online_learner = None
experiment_manager = None

def load_model_and_data():
    """Load the trained model and training data."""
    global popularity_model, collaborative_model, content_based_model, hybrid_model, train_data
    
    try:
        # Load training data first (needed for hybrid model)
        train_path = Path("data/processed/train_data.csv")
        if train_path.exists():
            train_data = pd.read_csv(train_path)
            print(f"✅ Training data loaded ({len(train_data):,} ratings)")
        else:
            print("⚠️ No training data found.")
        
        # Load popularity model
        popularity_path = Path("data/models/popularity_model.joblib")
        if popularity_path.exists():
            popularity_model = PopularityRecommender.load_model(str(popularity_path))
            print("✅ Popularity model loaded")
        else:
            print("⚠️ No popularity model found.")
        
        # Load collaborative filtering model
        collaborative_path = Path("data/models/collaborative_model.joblib")
        if collaborative_path.exists():
            collaborative_model = CollaborativeFilteringRecommender.load_model(str(collaborative_path))
            print("✅ Collaborative filtering model loaded")
        else:
            print("⚠️ No collaborative filtering model found.")
        
        # Load content-based model
        content_based_path = Path("data/models/content_based_model.joblib")
        if content_based_path.exists():
            content_based_model = ContentBasedRecommender.load_model(str(content_based_path))
            print("✅ Content-based model loaded")
        else:
            print("⚠️ No content-based model found.")
        
        # Load hybrid model (NEW IN PHASE 4!)
        hybrid_path = Path("data/models/hybrid_model.joblib")
        if (hybrid_path.exists() and 
            popularity_model and collaborative_model and content_based_model and train_data is not None):
            try:
                hybrid_model = HybridRecommender.load_model(
                    str(hybrid_path),
                    popularity_model,
                    collaborative_model,
                    content_based_model,
                    train_data
                )
                print("✅ Hybrid model loaded")
            except Exception as e:
                print(f"⚠️ Failed to load hybrid model: {e}")
        else:
            print("⚠️ Hybrid model not available (missing dependencies)")
            
    except Exception as e:
        print(f"❌ Error loading model/data: {e}")

# Load model and data on startup
@app.on_event("startup")
async def startup_event():
    global online_learner, experiment_manager
    
    # Create database tables
    create_tables()
    
    # NEW IN PHASE 7: Create authentication tables
    create_all_tables()
    
    # Load ML models
    load_model_and_data()
    
    # Initialize Online Learner (NEW IN PHASE 6!)
    online_learner = OnlineLearner(
        buffer_size=10,  # Update after 10 feedback events
        auto_update=True,
        update_interval_minutes=60  # Or update every 60 minutes
    )
    
    # Initialize A/B Testing (NEW IN PHASE 6!)
    experiment_manager = ExperimentManager()
    # Create a default experiment: Hybrid vs Collaborative
    experiment_manager.create_experiment(
        experiment_id="model_comparison",
        name="Hybrid vs Collaborative Filtering",
        groups={
            "control": {"model": "collaborative", "weight": 0.5},
            "treatment": {"model": "hybrid", "weight": 0.5}
        },
        description="Compare hybrid model against collaborative filtering"
    )
    
    print("🚀 Phase 6: Online Learning & A/B Testing ready!")
    print("🔐 Phase 7: User Authentication ready!")
    print("✅ Database tables created")
    print("✅ Authentication tables created")
    print("✅ Event processing system initialized")
    print("✅ Recommendation caching system ready")
    print("✅ Online learner initialized")
    print("✅ A/B testing framework ready")

# Pydantic models for API
class UserEvent(BaseModel):
    """User event model for real-time ingestion."""
    user_id: int
    item_id: int
    event_type: str  # 'view', 'click', 'rate', 'purchase'
    rating: Optional[float] = None
    timestamp: Optional[str] = None
    session_id: Optional[str] = None
    source: Optional[str] = "web"
    metadata: Optional[dict] = None

class RecommendationRequest(BaseModel):
    """Recommendation request model."""
    user_id: int
    n_recommendations: int = 10
    exclude_seen: bool = True
    model_type: str = "hybrid"  # "popularity", "collaborative", "content_based", or "hybrid"

class RecommendationResponse(BaseModel):
    """Recommendation response model."""
    user_id: int
    recommendations: List[dict]
    model_version: str
    timestamp: str

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "recommender-api",
        "version": "1.0.0"
    }

# Event ingestion endpoint (ENHANCED IN PHASE 5, AGAIN IN PHASE 6!)
@app.post("/events")
async def ingest_event(event: UserEvent, db: Session = Depends(get_db)):
    """
    Ingest a user event for real-time processing.
    
    NEW IN PHASE 6: Feeds rating events to online learner for incremental updates.
    
    Args:
        event: User event data
        db: Database session
        
    Returns:
        Success confirmation with event processing details
    """
    try:
        # Convert Pydantic model to dict
        event_data = event.dict()
        
        # Process the event using our event processor
        result = await event_processor.process_event(event_data, db)
        
        # NEW IN PHASE 6: Feed rating events to online learner
        if (event.event_type == "rate" and event.rating is not None and 
            online_learner is not None):
            feedback_status = online_learner.add_feedback(
                user_id=event.user_id,
                item_id=event.item_id,
                rating=event.rating
            )
            result["online_learning"] = feedback_status
            
            # Trigger update if needed
            if feedback_status.get("should_update"):
                models_to_update = {}
                if collaborative_model:
                    models_to_update["collaborative"] = collaborative_model
                if hybrid_model:
                    models_to_update["hybrid"] = hybrid_model
                
                update_result = online_learner.trigger_update(models_to_update)
                result["model_update"] = update_result
        
        # Record cache metrics
        if result["status"] == "success":
            cache_metrics.record_miss()  # New event means cache needs refresh
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest event: {str(e)}")

# Recommendation endpoint (ENHANCED WITH CACHING IN PHASE 5, A/B TESTING IN PHASE 6!)
@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get recommendations for a user with intelligent caching and A/B testing.
    
    NEW IN PHASE 6: Automatically participates in active A/B experiments.
    
    Args:
        request: Recommendation request
        
    Returns:
        List of recommended items (cached when possible)
    """
    try:
        # NEW IN PHASE 6: Check for active experiments
        actual_model_type = request.model_type
        experiment_group = None
        
        if experiment_manager is not None:
            active_experiments = experiment_manager.get_active_experiments()
            if "model_comparison" in active_experiments:
                group_config = experiment_manager.get_group_config(
                    request.user_id, "model_comparison"
                )
                if group_config:
                    actual_model_type = group_config["model"]
                    experiment_group = group_config["group_name"]
        
        # Try to get from cache first
        cached_recommendations = recommendation_cache.get_recommendations(
            user_id=request.user_id,
            model_type=actual_model_type,
            n_recommendations=request.n_recommendations
        )
        
        if cached_recommendations:
            cache_metrics.record_hit()
            return RecommendationResponse(
                user_id=request.user_id,
                recommendations=cached_recommendations,
                model_version=f"{request.model_type}_v1.0_cached",
                timestamp=_utc_now_iso()
            )
        
        # Cache miss - generate new recommendations
        cache_metrics.record_miss()
        
        # Choose model based on request (same logic as before)
        if request.model_type == "hybrid" and hybrid_model and hybrid_model.is_fitted:
            # Use hybrid model (NEW IN PHASE 4!)
            recommendations = hybrid_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "hybrid_v1.0"
            
        elif request.model_type == "content_based" and content_based_model and content_based_model.is_fitted:
            # Use content-based filtering
            recommendations = content_based_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "content_based_v1.0"
            
        elif request.model_type == "collaborative" and collaborative_model and collaborative_model.is_fitted:
            # Use collaborative filtering
            recommendations = collaborative_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "collaborative_v1.0"
            
        elif request.model_type == "popularity" and popularity_model and popularity_model.is_fitted:
            # Use popularity model
            recommendations = popularity_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "popularity_v1.0"
            
        elif hybrid_model and hybrid_model.is_fitted:
            # Default to hybrid if available (NEW IN PHASE 4!)
            recommendations = hybrid_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "hybrid_v1.0"
            
        elif content_based_model and content_based_model.is_fitted:
            # Default to content-based if available
            recommendations = content_based_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "content_based_v1.0"
            
        elif collaborative_model and collaborative_model.is_fitted:
            # Default to collaborative if available
            recommendations = collaborative_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "collaborative_v1.0"
            
        elif popularity_model and popularity_model.is_fitted:
            # Fallback to popularity
            recommendations = popularity_model.predict(
                user_id=request.user_id,
                n_recommendations=request.n_recommendations,
                exclude_seen=request.exclude_seen,
                user_ratings=train_data
            )
            model_version = "popularity_v1.0"
            
        else:
            # Final fallback to dummy recommendations
            recommendations = [
                {
                    "item_id": i,
                    "title": f"Movie {i}",
                    "score": 0.9 - (i * 0.1),
                    "reason": "dummy_fallback"
                }
                for i in range(1, request.n_recommendations + 1)
            ]
            model_version = "dummy_v1.0"
        
        # Cache the recommendations for future requests
        recommendation_cache.set_recommendations(
            user_id=request.user_id,
            model_type=request.model_type,
            recommendations=recommendations,
            n_recommendations=request.n_recommendations
        )
        
        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            model_version=model_version,
            timestamp=_utc_now_iso()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

# User profile endpoint
@app.get("/users/{user_id}/profile")
async def get_user_profile(user_id: int):
    """
    Get user profile and interaction history.
    
    Args:
        user_id: User ID
        
    Returns:
        User profile data
    """
    try:
        if train_data is not None:
            # Get real user data
            user_ratings = train_data[train_data['user_id'] == user_id]
            
            if len(user_ratings) > 0:
                profile = {
                    "user_id": user_id,
                    "total_interactions": len(user_ratings),
                    "favorite_genres": user_ratings['genres'].str.split('|').explode().value_counts().head(3).to_dict(),
                    "avg_rating": float(user_ratings['rating'].mean()),
                    "last_activity": user_ratings['timestamp'].max(),
                    "rating_distribution": user_ratings['rating'].value_counts().to_dict()
                }
            else:
                profile = {
                    "user_id": user_id,
                    "total_interactions": 0,
                    "favorite_genres": {},
                    "avg_rating": 0.0,
                    "last_activity": None,
                    "rating_distribution": {}
                }
        else:
            # Fallback to dummy data
            profile = {
                "user_id": user_id,
                "total_interactions": 0,
                "favorite_genres": [],
                "avg_rating": 0.0,
                "last_activity": None
            }
        
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

# Model metrics endpoint
@app.get("/metrics")
async def get_model_metrics():
    """
    Get current model performance metrics.
    
    Returns:
        Model performance metrics
    """
    try:
        metrics = {
            "available_models": [],
            "default_model": "collaborative",
            "last_updated": _utc_now_iso()
        }
        
        if popularity_model and popularity_model.is_fitted:
            pop_info = popularity_model.get_model_info()
            metrics["available_models"].append({
                "model_type": "popularity",
                "status": "ready",
                "total_items": pop_info["total_items"],
                "top_item": pop_info["top_item"]
            })
        
        if collaborative_model and collaborative_model.is_fitted:
            collab_info = collaborative_model.get_model_info()
            metrics["available_models"].append({
                "model_type": "collaborative_filtering",
                "status": "ready",
                "n_users": collab_info["n_users"],
                "n_items": collab_info["n_items"],
                "n_factors": collab_info["n_factors"],
                "explained_variance": collab_info["explained_variance"]
            })
        
        if content_based_model and content_based_model.is_fitted:
            content_info = content_based_model.get_model_info()
            metrics["available_models"].append({
                "model_type": "content_based",
                "status": "ready",
                "n_movies": content_info["n_movies"],
                "n_features": content_info["n_features"],
                "avg_similarity": content_info["avg_similarity"]
            })
        
        if hybrid_model and hybrid_model.is_fitted:
            hybrid_info = hybrid_model.get_model_info()
            metrics["available_models"].append({
                "model_type": "hybrid",
                "status": "ready",
                "component_models": hybrid_info["component_models"],
                "default_weights": hybrid_info["default_weights"],
                "n_users_analyzed": hybrid_info["n_users_analyzed"],
                "n_items_analyzed": hybrid_info["n_items_analyzed"]
            })
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Model comparison endpoint
@app.post("/compare-models")
async def compare_models(user_id: int, n_recommendations: int = 5):
    """
    Compare recommendations from different models for the same user.
    
    Args:
        user_id: User ID to get recommendations for
        n_recommendations: Number of recommendations per model
        
    Returns:
        Recommendations from all available models
    """
    try:
        comparison = {
            "user_id": user_id,
            "models": {}
        }
        
        # Get recommendations from popularity model
        if popularity_model and popularity_model.is_fitted:
            pop_recs = popularity_model.predict(
                user_id=user_id,
                n_recommendations=n_recommendations,
                exclude_seen=True,
                user_ratings=train_data
            )
            comparison["models"]["popularity"] = pop_recs
        
        # Get recommendations from collaborative filtering
        if collaborative_model and collaborative_model.is_fitted:
            collab_recs = collaborative_model.predict(
                user_id=user_id,
                n_recommendations=n_recommendations,
                exclude_seen=True,
                user_ratings=train_data
            )
            comparison["models"]["collaborative"] = collab_recs
        
        # Get recommendations from content-based filtering
        if content_based_model and content_based_model.is_fitted:
            content_recs = content_based_model.predict(
                user_id=user_id,
                n_recommendations=n_recommendations,
                exclude_seen=True,
                user_ratings=train_data
            )
            comparison["models"]["content_based"] = content_recs
        
        # Get recommendations from hybrid model (NEW IN PHASE 4!)
        if hybrid_model and hybrid_model.is_fitted:
            hybrid_recs = hybrid_model.predict(
                user_id=user_id,
                n_recommendations=n_recommendations,
                exclude_seen=True,
                user_ratings=train_data
            )
            comparison["models"]["hybrid"] = hybrid_recs
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare models: {str(e)}")

# Similar movies endpoint
@app.get("/movies/{movie_id}/similar")
async def get_similar_movies(movie_id: int, n_similar: int = 5):
    """
    Get movies similar to a given movie using content-based filtering.
    
    Args:
        movie_id: Movie ID to find similar movies for
        n_similar: Number of similar movies to return
        
    Returns:
        List of similar movies with similarity scores
    """
    try:
        if not content_based_model or not content_based_model.is_fitted:
            raise HTTPException(status_code=503, detail="Content-based model not available")
        
        similar_movies = content_based_model.get_similar_movies(movie_id, n_similar)
        
        if not similar_movies:
            raise HTTPException(status_code=404, detail=f"Movie {movie_id} not found")
        
        return {
            "movie_id": movie_id,
            "similar_movies": similar_movies
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get similar movies: {str(e)}")

# Get movie details endpoint
@app.get("/movies/{movie_id}")
async def get_movie_details(movie_id: int):
    """
    Get details for a specific movie.
    
    Args:
        movie_id: Movie ID
        
    Returns:
        Movie details (title, genres)
    """
    try:
        # Try to get from content-based model first (fastest)
        if content_based_model and content_based_model.is_fitted:
            if movie_id in content_based_model.movie_info:
                info = content_based_model.movie_info[movie_id]
                return {
                    "movie_id": movie_id,
                    "title": info['title'],
                    "genres": info['genres']
                }
        
        # Fallback: check other models or return basic info
        return {
            "movie_id": movie_id,
            "title": f"Movie {movie_id}",
            "genres": "Unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get movie details: {str(e)}")

# Recommendation explanation endpoint
@app.get("/users/{user_id}/explain")
async def explain_recommendations(user_id: int, model_type: str = "content_based"):
    """
    Explain why certain movies were recommended to a user.
    
    Args:
        user_id: User ID to explain recommendations for
        model_type: Type of model to use for explanation
        
    Returns:
        Detailed explanation of recommendations
    """
    try:
        if model_type == "content_based" and content_based_model and content_based_model.is_fitted:
            # Get user's rating history
            if train_data is None:
                raise HTTPException(status_code=503, detail="Training data not available")
            
            user_ratings = train_data[train_data['user_id'] == user_id]
            
            if len(user_ratings) == 0:
                return {
                    "user_id": user_id,
                    "explanation": "New user - no rating history available",
                    "recommendations_based_on": []
                }
            
            # Get liked movies (rating >= 4)
            liked_movies = user_ratings[user_ratings['rating'] >= 4.0]
            
            explanation = {
                "user_id": user_id,
                "total_ratings": len(user_ratings),
                "liked_movies": len(liked_movies),
                "explanation": f"Recommendations based on {len(liked_movies)} movies you rated 4+ stars",
                "recommendations_based_on": []
            }
            
            for _, movie in liked_movies.head(5).iterrows():  # Show top 5 liked movies
                similar_movies = content_based_model.get_similar_movies(movie['movie_id'], n_similar=3)
                explanation["recommendations_based_on"].append({
                    "liked_movie": {
                        "title": movie['title'],
                        "rating": movie['rating'],
                        "genres": movie['genres']
                    },
                    "similar_movies": similar_movies
                })
            
            return explanation
        else:
            raise HTTPException(status_code=503, detail=f"Model {model_type} not available")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain recommendations: {str(e)}")

# NEW PHASE 5 ENDPOINTS

# User activity endpoint
@app.get("/users/{user_id}/activity")
async def get_user_activity(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get recent activity for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of events to return
        db: Database session
        
    Returns:
        List of recent user events
    """
    try:
        events = event_processor.get_user_recent_events(user_id, limit, db)
        return {
            "user_id": user_id,
            "recent_events": events,
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")

# Item activity endpoint
@app.get("/items/{item_id}/activity")
async def get_item_activity(item_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get recent activity for an item.
    
    Args:
        item_id: Item ID
        limit: Maximum number of events to return
        db: Database session
        
    Returns:
        List of recent item events
    """
    try:
        events = event_processor.get_item_recent_events(item_id, limit, db)
        return {
            "item_id": item_id,
            "recent_events": events,
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get item activity: {str(e)}")

# Cache management endpoints
@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics."""
    try:
        cache_stats = recommendation_cache.get_cache_stats()
        metrics_stats = cache_metrics.get_stats()
        
        return {
            "cache_system": cache_stats,
            "performance_metrics": metrics_stats,
            "timestamp": _utc_now_iso()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@app.post("/cache/invalidate/{user_id}")
async def invalidate_user_cache(user_id: int):
    """Invalidate cached recommendations for a specific user."""
    try:
        success = recommendation_cache.invalidate_user_cache(user_id)
        if success:
            return {"status": "success", "message": f"Cache invalidated for user {user_id}"}
        else:
            return {"status": "error", "message": "Failed to invalidate cache"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

# Real-time metrics endpoint
@app.get("/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time system metrics."""
    try:
        system_metrics = event_processor.get_system_metrics()
        cache_stats = recommendation_cache.get_cache_stats()
        
        return {
            "event_metrics": system_metrics,
            "cache_metrics": cache_stats,
            "timestamp": _utc_now_iso()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metrics: {str(e)}")

# NEW PHASE 6 ENDPOINTS

# Online Learning endpoints
@app.get("/learning/stats")
async def get_online_learning_stats():
    """Get online learning statistics."""
    try:
        if online_learner is None:
            raise HTTPException(status_code=503, detail="Online learner not initialized")
        
        stats = online_learner.get_stats()
        return {
            "online_learning": stats,
            "timestamp": _utc_now_iso()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning stats: {str(e)}")

@app.post("/learning/trigger-update")
async def trigger_model_update():
    """Manually trigger a model update from buffered feedback."""
    try:
        if online_learner is None:
            raise HTTPException(status_code=503, detail="Online learner not initialized")
        
        models_to_update = {}
        if collaborative_model:
            models_to_update["collaborative"] = collaborative_model
        if hybrid_model:
            models_to_update["hybrid"] = hybrid_model
        
        result = online_learner.trigger_update(models_to_update)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger update: {str(e)}")

# A/B Testing endpoints
@app.get("/experiments")
async def get_experiments():
    """Get all A/B experiments."""
    try:
        if experiment_manager is None:
            raise HTTPException(status_code=503, detail="Experiment manager not initialized")
        
        experiments = experiment_manager.get_all_experiments_info()
        return {
            "experiments": experiments,
            "total_experiments": len(experiments),
            "timestamp": _utc_now_iso()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get experiments: {str(e)}")

@app.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get information about a specific experiment."""
    try:
        if experiment_manager is None:
            raise HTTPException(status_code=503, detail="Experiment manager not initialized")
        
        experiment_info = experiment_manager.get_experiment_info(experiment_id)
        if experiment_info is None:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
        
        return experiment_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get experiment: {str(e)}")

@app.get("/users/{user_id}/experiment-group")
async def get_user_experiment_group(user_id: int, experiment_id: str = "model_comparison"):
    """Get the experiment group assignment for a specific user."""
    try:
        if experiment_manager is None:
            raise HTTPException(status_code=503, detail="Experiment manager not initialized")
        
        group_config = experiment_manager.get_group_config(user_id, experiment_id)
        if group_config is None:
            return {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "assigned_group": None,
                "message": "Experiment not active or not found"
            }
        
        return {
            "user_id": user_id,
            **group_config
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get experiment group: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )