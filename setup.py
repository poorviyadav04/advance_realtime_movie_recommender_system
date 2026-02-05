"""
Setup script for the Real-Time Recommender System.
This script helps you get started quickly with the project.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[FAIL] Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"[OK] Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def setup_environment():
    """Set up the virtual environment and install dependencies."""
    print("Setting up Real-Time Recommender System")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("realtime-recommender-env")
    if not venv_path.exists():
        if not run_command("python -m venv realtime-recommender-env", "Creating virtual environment"):
            return False
    else:
        print("[OK] Virtual environment already exists")
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = "realtime-recommender-env\\Scripts\\activate"
        python_exe = "realtime-recommender-env\\Scripts\\python.exe"
        pip_exe = "realtime-recommender-env\\Scripts\\pip.exe"
    else:  # Unix/Linux/Mac
        activate_script = "source realtime-recommender-env/bin/activate"
        python_exe = "realtime-recommender-env/bin/python"
        pip_exe = "realtime-recommender-env/bin/pip"
    
    # Upgrade pip
    if not run_command(f"{python_exe} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_exe} install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Test the setup
    if not run_command(f"{python_exe} test_setup.py", "Testing setup"):
        return False
    
    return True

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\n[INFO] Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("[OK] .env file created")
    else:
        print("[OK] .env file already exists")

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    
    print("\nNext Steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("   realtime-recommender-env\\Scripts\\activate")
    else:  # Unix/Linux/Mac
        print("   source realtime-recommender-env/bin/activate")
    
    print("\n2. Download sample data:")
    print("   python data/prepare_data.py")
    
    print("\n3. Start the API server:")
    print("   uvicorn api.main:app --reload --port 8000")
    
    print("\n4. In a new terminal, start the dashboard:")
    print("   streamlit run dashboard/app.py --server.port 8501")
    
    print("\n5. Access the application:")
    print("   - API: http://localhost:8000")
    print("   - Dashboard: http://localhost:8501")
    print("   - API Docs: http://localhost:8000/docs")
    
    print("\n📚 Optional: Install Redis for real-time features")
    print("   - Windows: Download from https://redis.io/download")
    print("   - Linux: sudo apt-get install redis-server")
    print("   - Mac: brew install redis")
    print("   - Start: redis-server")
    
    print("\nDevelopment:")
    print("   - Run tests: pytest")
    print("   - Check setup: python test_setup.py")
    print("   - View project structure in README.md")

def main():
    """Main setup function."""
    try:
        # Setup environment
        if not setup_environment():
            print("\n[FAIL] Setup failed. Please check the errors above.")
            return 1
        
        # Create .env file
        create_env_file()
        
        # Print next steps
        print_next_steps()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[WARN] Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Unexpected error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())