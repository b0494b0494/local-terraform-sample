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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
