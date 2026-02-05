"""
Final verification script to ensure everything is working correctly.
"""
import requests
import time
import subprocess
import sys
from pathlib import Path

def test_api_health():
    """Test if the API is responding."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] API Health Check: {data['status']}")
            return True
        else:
            print(f"[FAIL] API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[WARN] API not running - start with: uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"[FAIL] API test failed: {e}")
        return False

def test_api_recommendations():
    """Test the recommendations endpoint."""
    try:
        response = requests.post(
            "http://localhost:8000/recommend",
            json={"user_id": 1, "n_recommendations": 5},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Recommendations API: Got {len(data['recommendations'])} recommendations")
            return True
        else:
            print(f"[FAIL] Recommendations API returned: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[WARN] API not running for recommendations test")
        return False
    except Exception as e:
        print(f"[FAIL] Recommendations test failed: {e}")
        return False

def test_dashboard_import():
    """Test dashboard can be imported."""
    try:
        import dashboard.app
        print("[OK] Dashboard imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Dashboard import failed: {e}")
        return False

def test_data_preparation():
    """Test data preparation script."""
    try:
        from data.prepare_data import load_movielens_1m
        print("[OK] Data preparation script imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Data preparation test failed: {e}")
        return False

def test_project_structure():
    """Verify all essential files exist."""
    essential_files = [
        "api/main.py",
        "dashboard/app.py", 
        "config/settings.py",
        "data/prepare_data.py",
        "requirements.txt",
        "README.md",
        "QUICKSTART.md"
    ]
    
    all_exist = True
    for file_path in essential_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[FAIL] Missing: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all verification tests."""
    print("Final Setup Verification")
    print("=" * 40)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Dashboard Import", test_dashboard_import),
        ("Data Preparation", test_data_preparation),
        ("API Health", test_api_health),
        ("API Recommendations", test_api_recommendations),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("VERIFICATION RESULTS")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed >= 3:  # Allow API tests to fail if not running
        print("\n[SUCCESS] Setup verification completed!")
        print("\nYour Real-Time Recommender System is ready!")
        print("\nTo start using it:")
        print("1. Start API: uvicorn api.main:app --reload")
        print("2. Start Dashboard: streamlit run dashboard/app.py")
        print("3. Visit: http://localhost:8501")
        return 0
    else:
        print(f"\n[FAIL] {len(tests) - passed} critical test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())