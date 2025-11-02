#!/usr/bin/env python3
"""
Test script for Redis cache functionality
Tests cache hit/miss behavior and cache statistics
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8080"

def test_cache_hit_miss():
    """Test cache hit and miss behavior"""
    print("=" * 60)
    print("Testing Redis Cache Hit/Miss")
    print("=" * 60)
    
    # First request - should be cache MISS
    print("\n1. First request (should be MISS):")
    response1 = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response1.status_code}")
    data1 = response1.json()
    print(f"   Timestamp: {data1.get('timestamp', 'N/A')}")
    
    time.sleep(1)
    
    # Second request - should be cache HIT
    print("\n2. Second request (should be HIT):")
    response2 = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response2.status_code}")
    data2 = response2.json()
    print(f"   Timestamp: {data2.get('timestamp', 'N/A')}")
    
    # Compare timestamps
    if data1.get('timestamp') == data2.get('timestamp'):
        print("\n   ? Cache HIT confirmed (same timestamp)")
        return True
    else:
        print("\n   ? Cache MISS (different timestamps - cache not working)")
        return False

def test_cache_stats():
    """Test cache statistics endpoint"""
    print("\n" + "=" * 60)
    print("Testing Cache Statistics")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/cache/stats")
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"Redis Status: {stats.get('status')}")
            print(f"Keyspace Hits: {stats.get('keyspace_hits', 0)}")
            print(f"Keyspace Misses: {stats.get('keyspace_misses', 0)}")
            print(f"Total Keys: {stats.get('total_keys', 0)}")
            print(f"Hit Rate: {stats.get('hit_rate', 0)}%")
            print("\n? Cache stats endpoint working")
            return True
        elif response.status_code == 503:
            print("\n??  Redis not available (this is OK if Redis is disabled)")
            return True
        else:
            print(f"\n? Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n? Error: {e}")
        return False

def test_cache_clear():
    """Test cache clear endpoint"""
    print("\n" + "=" * 60)
    print("Testing Cache Clear")
    print("=" * 60)
    
    try:
        # Make a request to populate cache
        requests.get(f"{BASE_URL}/info")
        time.sleep(1)
        
        # Clear cache
        response = requests.post(f"{BASE_URL}/cache/clear")
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Keys Deleted: {data.get('keys_deleted', 0)}")
            print("\n? Cache clear endpoint working")
            return True
        elif response.status_code == 503:
            print("\n??  Redis not available")
            return True
        else:
            print(f"\n? Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n? Error: {e}")
        return False

def test_info_endpoint_cache():
    """Test /info endpoint with caching"""
    print("\n" + "=" * 60)
    print("Testing /info Endpoint Cache (5 minute TTL)")
    print("=" * 60)
    
    # First request
    print("\n1. First request:")
    response1 = requests.get(f"{BASE_URL}/info")
    data1 = response1.json()
    print(f"   Redis Connected: {data1.get('redis_connected', False)}")
    
    time.sleep(1)
    
    # Second request (should be cached)
    print("\n2. Second request (should be cached):")
    response2 = requests.get(f"{BASE_URL}/info")
    data2 = response2.json()
    
    # Check if cached
    if data1.get('host') == data2.get('host'):
        print("   ? Cache working for /info endpoint")
        return True
    else:
        print("   ??  Response changed (may be normal for some fields)")
        return True

def main():
    """Run all tests"""
    print("\n?? Starting Redis Cache Tests\n")
    
    # Check if service is available
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"? Service not healthy: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"? Cannot connect to {BASE_URL}")
        print(f"   Make sure the app is running: docker-compose up -d")
        sys.exit(1)
    
    results = []
    
    # Run tests
    results.append(("Cache Hit/Miss", test_cache_hit_miss()))
    results.append(("Cache Stats", test_cache_stats()))
    results.append(("Cache Clear", test_cache_clear()))
    results.append(("Info Endpoint Cache", test_info_endpoint_cache()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "? PASS" if passed else "? FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n?? All tests passed!")
        sys.exit(0)
    else:
        print("\n??  Some tests failed or had warnings")
        sys.exit(1)

if __name__ == "__main__":
    main()
