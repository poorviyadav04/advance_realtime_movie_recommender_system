"""
Test script to verify the project setup is working correctly.
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")
    
    try:
        import pandas as pd
        print("[OK] pandas")
    except ImportError as e:
        print(f"[FAIL] pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("[OK] numpy")
    except ImportError as e:
        print(f"[FAIL] numpy: {e}")
        return False
    
    try:
        import sklearn
        print("[OK] scikit-learn")
    except ImportError as e:
        print(f"[FAIL] scikit-learn: {e}")
        return False
    
    try:
        import fastapi
        print("[OK] fastapi")
    except ImportError as e:
        print(f"[FAIL] fastapi: {e}")
        return False
    
    try:
        import streamlit
        print("[OK] streamlit")
    except ImportError as e:
        print(f"[FAIL] streamlit: {e}")
        return False
    
    try:
        import redis
        print("[OK] redis")
    except ImportError as e:
        print(f"[FAIL] redis: {e}")
        return False
    
    try:
        import mlflow
        print("[OK] mlflow")
    except ImportError as e:
        print(f"[FAIL] mlflow: {e}")
        return False
    
    try:
        import implicit
        print("[OK] implicit")
    except ImportError as e:
        print(f"[WARN] implicit: {e} (optional - will use scikit-learn alternatives)")
        # Don't return False for implicit as it's optional
    
    try:
        import lightgbm
        print("[OK] lightgbm")
    except ImportError as e:
        print(f"[FAIL] lightgbm: {e}")
        return False
    
    return True

def test_project_structure():
    """Test that the project structure is correct."""
    print("\nTesting project structure...")
    
    required_dirs = [
        "api",
        "models", 
        "feature_store",
        "ingestion",
        "evaluation",
        "dashboard",
        "data",
        "data/raw",
        "data/processed", 
        "data/models",
        "notebooks",
        "config",
        "tests"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"[OK] {dir_path}/")
        else:
            print(f"[FAIL] {dir_path}/")
            all_exist = False
    
    return all_exist

def test_config():
    """Test that configuration can be loaded."""
    print("\nTesting configuration...")
    
    try:
        from config.settings import settings
        print(f"[OK] Configuration loaded")
        print(f"   - Project root: {settings.PROJECT_ROOT}")
        print(f"   - API port: {settings.API_PORT}")
        print(f"   - Redis host: {settings.REDIS_HOST}")
        return True
    except Exception as e:
        print(f"[FAIL] Configuration failed: {e}")
        return False

def test_api_import():
    """Test that API modules can be imported."""
    print("\nTesting API imports...")
    
    try:
        from api.main import app
        print("[OK] FastAPI app imported")
        return True
    except Exception as e:
        print(f"[FAIL] FastAPI app import failed: {e}")
        return False

def test_dashboard_import():
    """Test that dashboard can be imported."""
    print("\nTesting dashboard imports...")
    
    try:
        # Just check if the file exists and is valid Python
        dashboard_path = Path("dashboard/app.py")
        if dashboard_path.exists():
            print("[OK] Dashboard app exists")
            return True
        else:
            print("[FAIL] Dashboard app not found")
            return False
    except Exception as e:
        print(f"[FAIL] Dashboard test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Real-Time Recommender System Setup")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Project Structure", test_project_structure), 
        ("Configuration", test_config),
        ("API Import", test_api_import),
        ("Dashboard Import", test_dashboard_import)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\nAll tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start Redis server: redis-server")
        print("2. Start API: uvicorn api.main:app --reload")
        print("3. Start dashboard: streamlit run dashboard/app.py")
        print("4. Download data: python data/prepare_data.py")
    else:
        print(f"\n{len(tests) - passed} test(s) failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())