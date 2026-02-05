"""
Launch MLflow UI to view experiment tracking results.

Usage:
    python scripts/mlflow_ui.py

Then navigate to: http://localhost:5000
"""
import subprocess
import os

if __name__ == "__main__":
    # Ensure we're in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    print("🚀 Starting MLflow UI...")
    print("📊 Navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()
    
    # Launch MLflow UI
    subprocess.run(["mlflow", "ui", "--port", "5000"])
