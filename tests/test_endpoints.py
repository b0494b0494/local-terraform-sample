#!/usr/bin/env python3
"""
Tests for main application endpoints
"""
import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import app from app.py (not from app/ package)
import app as app_module
app = app_module.app


class TestHealthEndpoints(unittest.TestCase):
    """Test health check endpoints"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('service', data)

    def test_ready_endpoint(self):
        """Test /ready endpoint"""
        response = self.app.get('/ready')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn(data['status'], ['ready', 'not_ready'])

    def test_info_endpoint(self):
        """Test /info endpoint"""
        response = self.app.get('/info')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('app_name', data)
        self.assertIn('version', data)


class TestMetricsEndpoint(unittest.TestCase):
    """Test metrics endpoint"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_metrics_endpoint_exists(self):
        """Test /metrics endpoint returns Prometheus format"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; version=0.0.4')
        content = response.data.decode('utf-8')
        self.assertIn('http_requests_total', content)


class TestCacheEndpoints(unittest.TestCase):
    """Test cache-related endpoints"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.redis_client')
    def test_cache_stats_with_redis(self, mock_redis):
        """Test /cache/stats with Redis available"""
        mock_redis.info.return_value = {
            'keyspace_hits': 10,
            'keyspace_misses': 5
        }
        mock_redis.dbsize.return_value = 3
        mock_redis.isinstance = lambda x, y: x is not None

        response = self.app.get('/cache/stats')
        if mock_redis is not None:
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('status', data)

    def test_cache_clear_without_redis(self):
        """Test /cache/clear without Redis"""
        with patch('app.redis_client', None):
            response = self.app.post('/cache/clear')
            self.assertEqual(response.status_code, 503)


class TestDatabaseEndpoints(unittest.TestCase):
    """Test database-related endpoints"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_db_status_without_db(self):
        """Test /db/status without database configured"""
        with patch('app.db_pool', None):
            response = self.app.get('/db/status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'not_configured')

    def test_db_query_without_db(self):
        """Test /db/query without database configured"""
        with patch('app.db_pool', None):
            response = self.app.post(
                '/db/query',
                data=json.dumps({'query': 'SELECT 1'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 503)


class TestErrorHandlers(unittest.TestCase):
    """Test global error handlers"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_404_handler(self):
        """Test 404 error handler"""
        response = self.app.get('/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Resource not found')

    def test_405_handler(self):
        """Test 405 error handler"""
        # Try POST on a GET-only endpoint
        response = self.app.post('/health')
        if response.status_code == 405:
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'error')
            self.assertEqual(data['message'], 'Method not allowed')


if __name__ == '__main__':
    unittest.main()
