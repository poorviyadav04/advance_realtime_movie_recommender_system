# Real-Time Advanced Recommender System
A **production-style end-to-end recommender system** built using **realistic synthetic user–item interaction data**, advanced **feature engineering**, and **LightGBM-based ranking models**.

This project focuses on understanding **why recommender systems work (or fail)** by emphasizing **data realism, feature–label alignment, and system design**, rather than only model tuning.

---

## 🎯 Project Overview

This project implements a **real-time inspired recommender system pipeline** that simulates user interactions, generates recommendations using multiple strategies, and evaluates them offline.

The system was intentionally built using **synthetic data with controlled structure** to:
- experiment safely without relying on private user data
- understand recommender system fundamentals
- study the impact of **data quality vs model complexity**


## 🏗️ Architecture

```
User Interactions
│
▼
Data Simulation & Ingestion
│
▼
Feature Engineering
│
▼
Candidate Generation
│
▼
Learning-to-Rank (LightGBM)
│
▼
Offline Evaluation & Analysis
```

> This architecture mirrors how real-world recommender systems are designed, while keeping the implementation lightweight and learnable.

---

## 🚀 Key Features

- **Realistic Synthetic Data Generation**
  - Latent user preferences
  - Item characteristics
  - Probabilistic interaction labeling
  - Avoids random/noisy simulation pitfalls

- **Multiple Recommendation Strategies**
  - Popularity-based recommender
  - Collaborative filtering
  - Content-based filtering
  - Hybrid recommender

- **Two-Stage Recommendation Design**
  - Candidate generation
  - Ranking with LightGBM

- **Feature Engineering**
  - User-level features
  - Item-level features
  - User–item interaction features
  - Temporal & behavioral signals

- **Offline Evaluation**
  - AUC
  - Ranking-oriented analysis
  - Controlled experiments to study model behavior

- **Production-Oriented Code Structure**
  - Modular design
  - Clear separation of concerns
  - Experiment tracking with MLflow
  - API-ready structure using FastAPI

---

## 🛠️ Tech Stack

### Core
- **Python 3.8+**
- **FastAPI** – API layer
- **SQLite** – Lightweight persistence
- **Streamlit** – Dashboard & visualization

### Machine Learning
- **Pandas, NumPy**
- **Scikit-learn**
- **LightGBM** – Learning-to-rank model
- **MLflow** – Experiment tracking

### Infrastructure & Tooling
- **Docker / Docker Compose**
- **Git**

---


## 📁 Project Structure

```
advance_realtime_movie_recommender_system/
├── api/ # FastAPI endpoints
├── models/ # Recommender models
├── feature_store/ # Feature caching utilities
├── ingestion/ # Event processing logic
├── evaluation/ # Metrics & evaluation
├── dashboard/ # Streamlit dashboard
├── data/ # Data simulation & preparation (no raw data committed)
├── scripts/ # Diagnostics & utilities
├── tests/ # Tests
├── config/ # Configuration
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md

## 🚦 Getting Started

### Prerequisites
- Python 3.8+
- Git

### Setup

```bash
git clone https://github.com/poorviyadav04/advance_realtime_movie_recommender_system.git
cd advance_realtime_movie_recommender_system

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

🧪 Running the Project

# Generate synthetic interaction data
python data/data_simulation_v2.py

# Train and evaluate models
python scripts/reality_check.py

# Start API server
uvicorn api.main:app --reload

📊 Evaluation & Results

Initial experiments showed poor model performance despite correct modeling choices.
After redesigning the synthetic data generation process to include latent user–item preferences, performance improved significantly.

This validated a key real-world ML lesson:

Good models cannot compensate for weak or unrealistic data.

🧠 Key Learnings

Data generation quality matters more than hyperparameter tuning

Feature–label alignment is critical for learnable patterns

Recommender systems are ranking problems, not just classification tasks

System design and evaluation strategy are as important as model choice

📝 License

MIT License

Built with ❤️ to learn how real recommender systems actually work
