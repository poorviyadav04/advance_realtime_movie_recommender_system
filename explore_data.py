"""
Explore the MovieLens dataset to understand what we're working with.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_data():
    """Load the processed data."""
    train_path = Path("data/processed/train_data.csv")
    test_path = Path("data/processed/test_data.csv")
    
    if not train_path.exists():
        print("Data not found. Run: python data/prepare_data.py")
        return None, None
    
    train_data = pd.read_csv(train_path)
    test_data = pd.read_csv(test_path)
    
    print(f"Train data: {len(train_data):,} ratings")
    print(f"Test data: {len(test_data):,} ratings")
    
    return train_data, test_data

def explore_basic_stats(data):
    """Show basic statistics about the data."""
    print("\n" + "="*50)
    print("BASIC DATASET STATISTICS")
    print("="*50)
    
    print(f"Total ratings: {len(data):,}")
    print(f"Unique users: {data['user_id'].nunique():,}")
    print(f"Unique movies: {data['movie_id'].nunique():,}")
    print(f"Rating range: {data['rating'].min()} - {data['rating'].max()}")
    print(f"Average rating: {data['rating'].mean():.2f}")
    print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

def explore_rating_distribution(data):
    """Show how ratings are distributed."""
    print("\n" + "="*50)
    print("RATING DISTRIBUTION")
    print("="*50)
    
    rating_counts = data['rating'].value_counts().sort_index()
    for rating, count in rating_counts.items():
        percentage = (count / len(data)) * 100
        print(f"Rating {rating}: {count:,} ({percentage:.1f}%)")

def explore_user_behavior(data):
    """Show user behavior patterns."""
    print("\n" + "="*50)
    print("USER BEHAVIOR PATTERNS")
    print("="*50)
    
    user_stats = data.groupby('user_id').agg({
        'rating': ['count', 'mean'],
        'movie_id': 'nunique'
    }).round(2)
    
    user_stats.columns = ['num_ratings', 'avg_rating', 'unique_movies']
    
    print("User activity statistics:")
    print(f"Average ratings per user: {user_stats['num_ratings'].mean():.1f}")
    print(f"Most active user rated: {user_stats['num_ratings'].max()} movies")
    print(f"Least active user rated: {user_stats['num_ratings'].min()} movies")
    print(f"Average user rating: {user_stats['avg_rating'].mean():.2f}")

def explore_movie_popularity(data):
    """Show movie popularity patterns."""
    print("\n" + "="*50)
    print("MOVIE POPULARITY PATTERNS")
    print("="*50)
    
    movie_stats = data.groupby(['movie_id', 'title']).agg({
        'rating': ['count', 'mean'],
        'user_id': 'nunique'
    }).round(2)
    
    movie_stats.columns = ['num_ratings', 'avg_rating', 'unique_users']
    movie_stats = movie_stats.sort_values('num_ratings', ascending=False)
    
    print("Top 10 most popular movies:")
    for i, (movie_info, stats) in enumerate(movie_stats.head(10).iterrows(), 1):
        movie_id, title = movie_info
        print(f"{i:2d}. {title[:50]:<50} ({stats['num_ratings']} ratings, {stats['avg_rating']:.1f} avg)")

def explore_genres(data):
    """Show genre distribution."""
    print("\n" + "="*50)
    print("GENRE ANALYSIS")
    print("="*50)
    
    # Split genres and count them
    all_genres = []
    for genres_str in data['genres'].dropna():
        genres = genres_str.split('|')
        all_genres.extend(genres)
    
    genre_counts = pd.Series(all_genres).value_counts()
    
    print("Top 10 genres by number of movies:")
    for i, (genre, count) in enumerate(genre_counts.head(10).items(), 1):
        print(f"{i:2d}. {genre:<15} {count:,} movies")

def show_sample_data(data):
    """Show sample of the actual data."""
    print("\n" + "="*50)
    print("SAMPLE DATA (First 10 rows)")
    print("="*50)
    
    sample = data[['user_id', 'movie_id', 'title', 'rating', 'genres']].head(10)
    for _, row in sample.iterrows():
        print(f"User {row['user_id']} rated '{row['title'][:30]}...' {row['rating']}/5")

def main():
    """Main exploration function."""
    print("🔍 EXPLORING MOVIELENS DATASET")
    print("="*60)
    
    # Load data
    train_data, test_data = load_data()
    if train_data is None:
        return
    
    # Use train data for exploration
    data = train_data
    
    # Run all explorations
    explore_basic_stats(data)
    explore_rating_distribution(data)
    explore_user_behavior(data)
    explore_movie_popularity(data)
    explore_genres(data)
    show_sample_data(data)
    
    print("\n" + "="*60)
    print("✅ DATA EXPLORATION COMPLETE!")
    print("="*60)
    print("\nKey Insights:")
    print("- We have real user ratings from 1-5 stars")
    print("- Users have different activity levels (some rate many movies)")
    print("- Movies have different popularity levels")
    print("- Multiple genres per movie")
    print("- Time-ordered data (older ratings in train, newer in test)")
    
    print("\n🚀 Ready to build recommender models!")

if __name__ == "__main__":
    main()