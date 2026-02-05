"""
ADVANCED Synthetic Data Generation with Latent Factor Model

This creates CAUSALLY MEANINGFUL data where:
- User preferences are represented as embeddings
- Item characteristics are represented as embeddings  
- Interaction probability = f(user_embedding · item_embedding, popularity, recency)
- Features are PREDICTIVE of labels (not random)

Expected AUC: 0.70-0.80+
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ============================================================================
# LATENT FACTOR MODEL CONFIGURATION
# ============================================================================
EMBEDDING_DIM = 5  # Latent factors (genre preferences, quality, etc.)
N_USERS = 1000
N_INTERACTIONS = 100000

def load_movie_data():
    """Load movie data from train_data.csv"""
    train_path = "data/processed/train_data.csv"
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"{train_path} not found. Run data/prepare_data.py first.")
    
    df = pd.read_csv(train_path)
    # Get unique movies
    movies = df[['movie_id', 'title', 'genres']].drop_duplicates('movie_id')
    return movies

def create_embeddings(n_users, movies):
    """
    Create latent factor embeddings for users and items.
    
    Embeddings capture:
    - Genre preferences (action, comedy, drama)
    - Quality sensitivity (prefers high-rated vs any content)
    - Recency bias (prefers new vs old movies)
    - Mainstream vs niche preferences
    """
    print("Creating latent factor embeddings...")
    
    # User embeddings: each dimension represents a latent preference
    # Dimensions: [genre_action, genre_drama, quality_sensitivity, recency_bias, mainstream]
    user_embeddings = np.random.randn(n_users, EMBEDDING_DIM) * 0.5
    
    # Item embeddings: learned from movie metadata
    n_movies = len(movies)
    item_embeddings = {}
    
    for idx, row in movies.iterrows():
        movie_id = row['movie_id']
        genres = str(row['genres']).lower()
        
        # Construct embedding based on movie characteristics
        emb = np.random.randn(EMBEDDING_DIM) * 0.3
        
        # Dimension 0-2: Genre signals
        if 'action' in genres or 'thriller' in genres:
            emb[0] += 0.8
        if 'drama' in genres or 'romance' in genres:
            emb[1] += 0.8
        if 'comedy' in genres:
            emb[2] += 0.8
            
        # Dimension 3: Quality (simulated from movie ID - lower IDs = classics)
        emb[3] = -movie_id / 5000.0  # Classics have negative values
        
        # Dimension 4: Mainstream vs niche (based on genre diversity)
        emb[4] = len(genres.split('|')) * 0.3  # More genres = mainstream
        
        item_embeddings[movie_id] = emb
    
    return user_embeddings, item_embeddings

def sigmoid(x):
    """Sigmoid activation: maps (-inf, inf) to (0, 1)"""
    return 1 / (1 + np.exp(-np.clip(x, -10, 10)))

def compute_interaction_probability(user_emb, item_emb, item_popularity, item_recency):
    """
    Causal model: p(interaction | user, item)
    
    Combines:
    1. User-item similarity (dot product)
    2. Item popularity
    3. Item recency
    """
    # Core signal: embedding similarity
    similarity = np.dot(user_emb, item_emb)
    
    # Popularity boost (popular items get more interactions)
    popularity_score = np.log1p(item_popularity) * 0.3
    
    # Recency boost (newer items get more attention)
    recency_score = item_recency * 0.2
    
    # Combine signals
    logit = similarity + popularity_score + recency_score
    
    # Convert to probability
    return sigmoid(logit)

def generate_interactions_with_latent_factors(user_embeddings, item_embeddings, movies, n_interactions):
    """
    Generate interactions using latent factor model.
    
    Key insight: Labels are CAUSED by features!
    - High user-item similarity → high rating → positive label
    - Low similarity → low rating → negative label
    """
    print(f"Generating {n_interactions:,} interactions with latent factors...")
    
    n_users = len(user_embeddings)
    movie_ids = list(item_embeddings.keys())
    
    # Assign popularity scores (simulate view counts)
    item_popularity = {mid: np.random.exponential(50) for mid in movie_ids}
    
    # Assign recency scores (0-1, based on release year)
    item_recency = {}
    for _, row in movies.iterrows():
        # Extract year from title
        import re
        match = re.search(r'\((\d{4})\)', str(row['title']))
        year = int(match.group(1)) if match else 2000
        item_recency[row['movie_id']] = (year - 1900) / 100.0  # Normalize
    
    interactions = []
    
    for _ in range(n_interactions):
        # Sample user
        user_id = np.random.randint(0, n_users)
        user_emb = user_embeddings[user_id]
        
        # Sample item (biased by similarity)
        # First, pick a candidate set
        if np.random.rand() < 0.7:
            # 70%: Sample proportional to user-item affinity
            scores = []
            for mid in np.random.choice(movie_ids, size=min(100, len(movie_ids)), replace=False):
                item_emb = item_embeddings[mid]
                pop = item_popularity.get(mid, 1)
                rec = item_recency.get(mid, 0.5)
                score = compute_interaction_probability(user_emb, item_emb, pop, rec)
                scores.append((mid, score))
            
            # Sample from top candidates
            scores.sort(key=lambda x: x[1], reverse=True)
            item_id = scores[0][0] if scores else movie_ids[0]
        else:
            # 30%: Random exploration
            item_id = np.random.choice(movie_ids)
        
        item_emb = item_embeddings[item_id]
        pop = item_popularity.get(item_id, 1)
        rec = item_recency.get(item_id, 0.5)
        
        # Compute interaction parameters
        affinity_score = np.dot(user_emb, item_emb)
        interaction_prob = compute_interaction_probability(user_emb, item_emb, pop, rec)
        
        # Determine event type
        event_type = 'rate' if np.random.rand() < 0.3 else 'click'
        
        if event_type == 'rate':
            # Rating is based on affinity
            # High affinity → high rating
            base_rating = 3.0 + affinity_score * 1.5  # Maps affinity to rating scale
            rating = int(np.clip(np.round(base_rating + np.random.normal(0, 0.4)), 1, 5))
            
            # Label: high ratings + high affinity = positive
            if rating >= 4 and affinity_score > 0:
                label = 1
            elif rating >= 4:
                label = 1 if np.random.rand() < 0.7 else 0
            elif rating == 3 and affinity_score > 0.5:
                label = 1 if np.random.rand() < 0.5 else 0
            else:
                label = 0
        else:
            # Click
            rating = 0
            # Clicks convert based on affinity
            label = 1 if interaction_prob > 0.6 else 0
        
        # Timestamp
        timestamp = datetime.now() - timedelta(days=np.random.randint(1, 90))
        
        interactions.append({
            'user_id': user_id,
            'item_id': item_id,
            'event_type': event_type,
            'rating': rating,
            'label': label,
            'timestamp': timestamp,
            'affinity_score': affinity_score,  # Hidden ground truth (for debugging)
            'item_popularity': pop,
            'item_recency': rec
        })
    
    return pd.DataFrame(interactions)

def compute_features(interactions_df, movies):
    """
    Compute features from interactions.
    These features are CAUSED BY the latent factors, making them predictive!
    """
    print("Computing features...")
    
    # User stats
    user_stats = interactions_df[interactions_df['rating'] > 0].groupby('user_id').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    user_stats.columns = ['user_id', 'user_rating_avg', 'user_rating_count']
    
    # Item stats
    item_stats = interactions_df[interactions_df['rating'] > 0].groupby('item_id').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    item_stats.columns = ['item_id', 'item_rating_avg', 'item_rating_count']
    
    # Release years
    def extract_year(title):
        import re
        match = re.search(r'\((\d{4})\)', str(title))
        return int(match.group(1)) if match else 2000
    
    movie_years = movies[['movie_id', 'title']].drop_duplicates('movie_id')
    movie_years['release_year'] = movie_years['title'].apply(extract_year)
    movie_years = movie_years[['movie_id', 'release_year']].rename(columns={'movie_id': 'item_id'})
    
    # Merge features
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
    print("=" * 70)
    print("LATENT FACTOR SYNTHETIC DATA GENERATION")
    print("=" * 70)
    print("\n📐 Creating causally meaningful data where features → labels")
    
    # Load movies
    print("\n1. Loading movie data...")
    movies = load_movie_data()
    print(f"   Loaded {len(movies):,} unique movies")
    
    # Create embeddings
    print(f"\n2. Creating {EMBEDDING_DIM}D latent embeddings...")
    user_embeddings, item_embeddings = create_embeddings(N_USERS, movies)
    print(f"   Created embeddings for {N_USERS:,} users and {len(item_embeddings):,} items")
    
    # Generate interactions
    print(f"\n3. Generating interactions via latent factor model...")
    interactions = generate_interactions_with_latent_factors(
        user_embeddings, item_embeddings, movies, N_INTERACTIONS
    )
    print(f"   Generated {len(interactions):,} interactions")
    
    # Compute features
    print("\n4. Computing features...")
    enriched = compute_features(interactions, movies)
    
    # Verify causal structure
    print("\n✅ CAUSAL STRUCTURE VERIFICATION:")
    print(f"   Affinity Score ↔ Label correlation: {enriched['affinity_score'].corr(enriched['label']):+.4f}")
    print(f"   User Rating Avg ↔ Label: {enriched['user_rating_avg'].corr(enriched['label']):+.4f}")
    print(f"   Item Rating Avg ↔ Label: {enriched['item_rating_avg'].corr(enriched['label']):+.4f}")
    
    # Drop debugging columns
    enriched = enriched.drop(columns=['affinity_score', 'item_popularity', 'item_recency'])
    
    # Save
    output_path = "data/processed/interaction_logs.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    enriched.to_csv(output_path, index=False)
    
    print(f"\n✅ Saved {len(enriched):,} interactions to {output_path}")
    print(f"📊 Positive rate: {enriched['label'].mean():.2%}")
    print("\nSample data:")
    print(enriched[['user_id', 'item_id', 'rating', 'label', 
                     'user_rating_avg', 'item_rating_avg']].head())
    
    print("\n" + "=" * 70)
    print("🎯 Expected AUC with this data: 0.70-0.80")
    print("=" * 70)

if __name__ == "__main__":
    main()
