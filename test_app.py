#!/usr/bin/env python3
"""
???????????????
"""
import requests
import time
import sys

def test_health_endpoint(base_url="http://localhost:8080"):
    """??????????????????"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("? Health check passed")
        return True
    except Exception as e:
        print(f"? Health check failed: {e}")
        return False

def test_root_endpoint(base_url="http://localhost:8080"):
    """??????????????"""
    try:
        response = requests.get(base_url, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'status' in data
        print("? Root endpoint passed")
        return True
    except Exception as e:
        print(f"? Root endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing sample app...")
    print("-" * 40)
    
    # ??????????????
    time.sleep(1)
    
    results = []
    results.append(test_health_endpoint())
    results.append(test_root_endpoint())
    
    print("-" * 40)
    if all(results):
        print("All tests passed! ?")
        sys.exit(0)
    else:
        print("Some tests failed ?")
        sys.exit(1)
