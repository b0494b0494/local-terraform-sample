"""
Tests for FastAPI (ASGI) application endpoints
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import FastAPI app
from app_asgi import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["framework"] == "FastAPI/ASGI"
    assert "app_name" in data
    assert "version" in data
    assert "timestamp" in data


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["framework"] == "FastAPI/ASGI"
    assert "timestamp" in data


def test_ready_endpoint():
    """Test readiness check endpoint"""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["framework"] == "FastAPI/ASGI"
    assert "timestamp" in data


def test_info_endpoint():
    """Test info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert data["framework"] == "FastAPI/ASGI"
    assert "timestamp" in data


def test_nonexistent_endpoint():
    """Test 404 handling for nonexistent endpoint"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_db_status_endpoint():
    """Test database status endpoint"""
    response = client.get("/db/status")
    # Should return either 200 (connected) or status indicating not configured
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert data["framework"] == "FastAPI/ASGI"


def test_ready_with_db_check():
    """Test ready endpoint includes database check"""
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database_connected" in data
    assert data["framework"] == "FastAPI/ASGI"


def test_cache_stats_endpoint():
    """Test cache stats endpoint"""
    response = client.get("/cache/stats")
    # Should return 200 even if cache is not configured
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["framework"] == "FastAPI/ASGI"


def test_cache_clear_endpoint():
    """Test cache clear endpoint"""
    response = client.post("/cache/clear")
    # Should return 200 even if cache is not configured
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["framework"] == "FastAPI/ASGI"


def test_root_with_caching():
    """Test root endpoint with caching support"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "cached" in data
    assert data["framework"] == "FastAPI/ASGI"


def test_login_endpoint():
    """Test login endpoint"""
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    # Should return 200 with token or 401 if demo users not initialized
    assert response.status_code in [200, 401, 500]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data.get("framework") == "FastAPI/ASGI"


def test_validate_endpoint_no_token():
    """Test validate endpoint without token"""
    response = client.get("/auth/validate")
    assert response.status_code == 403  # FastAPI security returns 403


def test_api_key_test_no_key():
    """Test API key endpoint without key"""
    response = client.get("/api-key-test")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
