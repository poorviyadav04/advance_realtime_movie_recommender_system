# 🚀 Quick Start Guide

Get your Real-Time Recommender System up and running in minutes!

## Prerequisites

- Python 3.8+ installed
- Git installed
- Internet connection for downloading dependencies and data

## 1. Clone and Setup

```bash
# Clone the repository (if from git)
git clone <your-repo-url>
cd realtime-recommender

# OR if you have the files locally, navigate to the directory
cd realtime-recommender
```

## 2. Automated Setup

Run the setup script to automatically configure everything:

```bash
python setup.py
```

This will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Test the installation
- ✅ Create configuration files

## 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv realtime-recommender-env

# Activate virtual environment
# Windows:
realtime-recommender-env\Scripts\activate
# Linux/Mac:
source realtime-recommender-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test setup
python test_setup.py
```

## 4. Download Sample Data

```bash
# Activate virtual environment first
python data/prepare_data.py
```

This downloads the MovieLens 1M dataset (~6MB) and prepares it for training.

## 5. Start the Services

### Terminal 1 - API Server
```bash
# Activate virtual environment
realtime-recommender-env\Scripts\activate  # Windows
# source realtime-recommender-env/bin/activate  # Linux/Mac

# Start API
uvicorn api.main:app --reload --port 8000
```

### Terminal 2 - Dashboard
```bash
# Activate virtual environment
realtime-recommender-env\Scripts\activate  # Windows
# source realtime-recommender-env/bin/activate  # Linux/Mac

# Start dashboard
streamlit run dashboard/app.py --server.port 8501
```

## 6. Access the Application

- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 7. Test the System

1. Open the dashboard at http://localhost:8501
2. Select a user ID (1-6040)
3. Click "Get Recommendations"
4. Simulate events by clicking the feedback buttons
5. Explore the analytics and metrics tabs

## Optional: Redis Setup

For real-time features, install Redis:

### Windows
1. Download Redis from https://redis.io/download
2. Install and start the Redis server
3. Or use Docker: `docker run -d -p 6379:6379 redis:alpine`

### Linux
```bash
sudo apt-get install redis-server
redis-server
```

### Mac
```bash
brew install redis
redis-server
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use different ports
   uvicorn api.main:app --reload --port 8001
   streamlit run dashboard/app.py --server.port 8502
   ```

2. **Virtual environment activation fails**
   ```bash
   # Windows: Use PowerShell or Command Prompt
   # Linux/Mac: Make sure you're using bash/zsh
   ```

3. **Package installation fails**
   ```bash
   # Upgrade pip first
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **API not responding**
   - Check if the API server is running
   - Verify the port (default: 8000)
   - Check firewall settings

### Getting Help

1. Run the test script: `python test_setup.py`
2. Check the logs in the terminal
3. Verify all services are running
4. Check the README.md for detailed documentation

## Next Steps

Once everything is running:

1. **Explore the Code**: Check out the project structure in README.md
2. **Add Real Data**: Replace sample data with your own
3. **Customize Models**: Modify the recommendation algorithms
4. **Deploy**: Use Docker for production deployment
5. **Scale**: Add more sophisticated real-time processing

## Development Workflow

```bash
# Activate environment
realtime-recommender-env\Scripts\activate

# Run tests
pytest

# Check code quality
python test_setup.py

# Start development servers
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

Happy coding! 🎉