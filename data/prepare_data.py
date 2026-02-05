"""
Data preparation utilities for the recommender system.
"""
import os
import zipfile
from pathlib import Path
from typing import Tuple
import requests
import pandas as pd
from tqdm import tqdm

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import settings


def download_file(url: str, filepath: Path) -> None:
    """Download a file from URL with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filepath, 'wb') as file, tqdm(
        desc=filepath.name,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            size = file.write(chunk)
            pbar.update(size)


def download_movielens(dataset_size: str = "1m") -> None:
    """
    Download MovieLens dataset.
    
    Args:
        dataset_size: Size of dataset to download ('100k', '1m', '10m', '25m')
    """
    urls = {
        "100k": "https://files.grouplens.org/datasets/movielens/ml-100k.zip",
        "1m": "https://files.grouplens.org/datasets/movielens/ml-1m.zip",
        "10m": "https://files.grouplens.org/datasets/movielens/ml-10m.zip",
        "25m": "https://files.grouplens.org/datasets/movielens/ml-25m.zip"
    }
    
    if dataset_size not in urls:
        raise ValueError(f"Dataset size must be one of {list(urls.keys())}")
    
    url = urls[dataset_size]
    zip_path = settings.RAW_DATA_DIR / f"ml-{dataset_size}.zip"
    extract_path = settings.RAW_DATA_DIR / f"ml-{dataset_size}"
    
    # Download if not exists
    if not zip_path.exists():
        print(f"Downloading MovieLens {dataset_size} dataset...")
        download_file(url, zip_path)
        print("Download completed!")
    
    # Extract if not exists
    if not extract_path.exists():
        print("Extracting dataset...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(settings.RAW_DATA_DIR)
        print("Extraction completed!")
    
    return extract_path


def load_movielens_1m() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load MovieLens 1M dataset.
    
    Returns:
        Tuple of (ratings, movies, users) DataFrames
    """
    data_path = settings.RAW_DATA_DIR / "ml-1m"
    
    if not data_path.exists():
        print("MovieLens 1M dataset not found. Downloading...")
        download_movielens("1m")
    
    # Load ratings
    ratings = pd.read_csv(
        data_path / "ratings.dat",
        sep="::",
        names=["user_id", "movie_id", "rating", "timestamp"],
        engine="python"
    )
    
    # Load movies
    movies = pd.read_csv(
        data_path / "movies.dat",
        sep="::",
        names=["movie_id", "title", "genres"],
        engine="python",
        encoding="latin-1"
    )
    
    # Load users
    users = pd.read_csv(
        data_path / "users.dat",
        sep="::",
        names=["user_id", "gender", "age", "occupation", "zip_code"],
        engine="python"
    )
    
    return ratings, movies, users


def preprocess_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Preprocess the MovieLens data for training.
    
    Returns:
        Tuple of (train_data, test_data) DataFrames
    """
    print("Loading MovieLens 1M dataset...")
    ratings, movies, users = load_movielens_1m()
    
    # Merge ratings with movie information
    data = ratings.merge(movies, on="movie_id", how="left")
    data = data.merge(users, on="user_id", how="left")
    
    # Convert timestamp to datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')
    
    # Sort by timestamp for time-aware split
    data = data.sort_values('timestamp')
    
    # Time-aware train/test split (80/20)
    split_idx = int(len(data) * 0.8)
    train_data = data.iloc[:split_idx].copy()
    test_data = data.iloc[split_idx:].copy()
    
    # Save processed data
    train_path = settings.PROCESSED_DATA_DIR / "train_data.csv"
    test_path = settings.PROCESSED_DATA_DIR / "test_data.csv"
    
    train_data.to_csv(train_path, index=False)
    test_data.to_csv(test_path, index=False)
    
    print(f"Processed data saved:")
    print(f"  Train: {train_path} ({len(train_data):,} ratings)")
    print(f"  Test: {test_path} ({len(test_data):,} ratings)")
    
    return train_data, test_data


if __name__ == "__main__":
    # Prepare the data
    train_data, test_data = preprocess_data()
    
    print("\nDataset Statistics:")
    print(f"Total users: {train_data['user_id'].nunique():,}")
    print(f"Total movies: {train_data['movie_id'].nunique():,}")
    print(f"Total ratings: {len(train_data):,}")
    print(f"Rating range: {train_data['rating'].min()} - {train_data['rating'].max()}")
    print(f"Average rating: {train_data['rating'].mean():.2f}")