"""
Enhanced data simulation with proper feature engineering.
Generates interaction logs WITH user and item statistics for model training.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

def load_movie_data():
    """Load movie data from train_data.csv"""
    train_path = "data/processed/train_data.csv"
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"{train_path} not found. Run data/prepare_data.py first.")
    
    df = pd.read_csv(train_path)
    return df

def generate_user_profiles(n_users=1000):
    """Generate user genre preferences"""
    genres = ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Thriller', 'Romance', 'Horror']
    
    profiles = []
    for user_id in range(1, n_users + 1):
        # Each user prefers 2-3 genres
        preferred_genres = random.sample(genres, k=random.randint(2, 3))
        profiles.append({
            'user_id': user_id,
            'preferred_genres': preferred_genres,
            'avg_rating_tendency': np.random.normal(3.5, 0.5)  # How generous they rate
        })
    
    return pd.DataFrame(profiles)

def simulate_interactions(movie_df, user_profiles, n_interactions=50000):
    """Generate synthetic interactions with realistic patterns"""
    interactions = []
    
    # Get unique movie info
    movies = movie_df[['movie_id', 'title', 'genres']].drop_duplicates('movie_id')
    
    for _ in range(n_interactions):
        # Pick random user
        user = user_profiles.sample(1).iloc[0]
        user_id = user['user_id']
        
        # Pick movie (biased towards user's preferred genres)
        if random.random() < 0.7:  # 70% of time, pick from preferred genres
            genre_filter = movies['genres'].apply(
                lambda x: any(g in x for g in user['preferred_genres']) if isinstance(x, str) else False
            )
            candidate_movies = movies[genre_filter]
            if len(candidate_movies) == 0:
                candidate_movies = movies
        else:
            candidate_movies = movies
        
        movie = candidate_movies.sample(1).iloc[0]
        item_id = movie['movie_id']
        
        # Determine interaction type
        event_type = random.choices(['click', 'rate'], weights=[0.7, 0.3])[0]
        
        if event_type == 'rate':
            # Generate rating (biased by user tendency and genre match)
            base_rating = user['avg_rating_tendency']
            genre_match = any(g in movie['genres'] for g in user['preferred_genres'])
            
            if genre_match:
                base_rating += 0.5  # Boost for preferred genre
            
            rating = int(np.clip(np.round(base_rating + np.random.normal(0, 0.5)), 1, 5))
            
            # IMPROVED LABEL LOGIC: Consider both rating AND genre match
            # This makes labels more predictable from features
            if rating >= 4 and genre_match:
                label = 1  # High rating + genre match = definitely positive
            elif rating >= 4 and not genre_match:
                label = 1 if random.random() < 0.7 else 0  # Some false positives
            elif rating == 3 and genre_match:
                label = 1 if random.random() < 0.4 else 0  # Neutral can be positive
            else:
                label = 0  # Low rating or no match = negative
        else:
            rating = 0
            # Clicks also consider genre match
            genre_match = any(g in movie['genres'] for g in user['preferred_genres'])
            if genre_match:
                label = 1 if random.random() < 0.25 else 0  # Higher click-through for matched genres
            else:
                label = 1 if random.random() < 0.10 else 0  # Lower for non-matched
        
        # Generate timestamp
        timestamp = datetime.now() - timedelta(days=random.randint(1, 90))
        
        interactions.append({
            'user_id': user_id,
            'item_id': item_id,
            'event_type': event_type,
            'rating': rating,
            'label': label,
            'timestamp': timestamp
        })
    
    return pd.DataFrame(interactions)

def compute_features(interactions_df, movie_df):
    """
    Compute user and item statistics - THIS IS THE KEY FIX!
    """
    print("Computing user statistics...")
    # User features
    user_stats = interactions_df[interactions_df['rating'] > 0].groupby('user_id').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    user_stats.columns = ['user_id', 'user_rating_avg', 'user_rating_count']  # Match Ranker names!
    
    print("Computing item statistics...")
    # Item features  
    item_stats = interactions_df[interactions_df['rating'] > 0].groupby('item_id').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    item_stats.columns = ['item_id', 'item_rating_avg', 'item_rating_count']  # Match Ranker names!
    
    print("Extracting release years...")
    # Extract release year from movie titles
    def extract_year(title):
        import re
        match = re.search(r'\((\d{4})\)', str(title))
        return int(match.group(1)) if match else 2000
    
    movie_years = movie_df[['movie_id', 'title']].drop_duplicates('movie_id')
    movie_years['release_year'] = movie_years['title'].apply(extract_year)
    movie_years = movie_years[['movie_id', 'release_year']].rename(columns={'movie_id': 'item_id'})
    
    print("Merging features...")
    # Merge features into interactions
    enriched = interactions_df.copy()
    enriched = enriched.merge(user_stats, on='user_id', how='left')
    enriched = enriched.merge(item_stats, on='item_id', how='left')
    enriched = enriched.merge(movie_years, on='item_id', how='left')
    
    # Fill missing values
    enriched['user_rating_avg'] = enriched['user_rating_avg'].fillna(3.0)
    enriched['user_rating_count'] = enriched['user_rating_count'].fillna(0)
    enriched['item_rating_avg'] = enriched['item_rating_avg'].fillna(3.0)
    enriched['item_rating_count'] = enriched['item_rating_count'].fillna(0)
    enriched['release_year'] = enriched['release_year'].fillna(2000)
    
    return enriched

def main():
    print("=" * 60)
    print("GENERATING REALISTIC INTERACTION DATA WITH FEATURES")
    print("=" * 60)
    
    # Load movies
    print("\n1. Loading movie data...")
    movie_df = load_movie_data()
    print(f"   Loaded {len(movie_df)} movie records")
    
    # Generate users
    print("\n2. Generating user profiles...")
    user_profiles = generate_user_profiles(n_users=1000)
    print(f"   Created {len(user_profiles)} users")
    
    # Generate interactions
    print("\n3. Simulating interactions...")
    interactions = simulate_interactions(movie_df, user_profiles, n_interactions=100000)  # Doubled!
    print(f"   Generated {len(interactions)} interactions")
    
    # Compute features (THE CRITICAL STEP!)
    print("\n4. Computing features...")
    enriched_interactions = compute_features(interactions, movie_df)
    
    # Verify features exist
    print("\n✅ FEATURE VERIFICATION:")
    required_features = ['user_rating_avg', 'user_rating_count', 'item_rating_avg', 
                         'item_rating_count', 'release_year']
    for feat in required_features:
        if feat in enriched_interactions.columns:
            print(f"   ✓ {feat}: mean={enriched_interactions[feat].mean():.2f}")
        else:
            print(f"   ✗ {feat}: MISSING!")
    
    # Save
    output_path = "data/processed/interaction_logs.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    enriched_interactions.to_csv(output_path, index=False)
    
    print(f"\n✅ Saved {len(enriched_interactions)} interactions to {output_path}")
    print(f"📊 Positive rate: {enriched_interactions['label'].mean():.2%}")
    print("\nSample data:")
    print(enriched_interactions[['user_id', 'item_id', 'rating', 'label', 
                                   'user_rating_avg', 'item_rating_avg']].head())

if __name__ == "__main__":
    main()
