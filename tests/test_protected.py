#!/usr/bin/env python3
"""
Tests for protected endpoints
"""
import unittest
import json
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import app from app.py (not from app/ package)
import app as app_module
app = app_module.app


class TestProtectedEndpoints(unittest.TestCase):
    """Test protected endpoints"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def get_auth_token(self, username='admin', password='admin123'):
        """Helper to get authentication token"""
        response = self.app.post(
            '/auth/login',
            data=json.dumps({
                'username': username,
                'password': password
            }),
            content_type='application/json'
        )
        if response.status_code == 200:
            return json.loads(response.data)['token']
        return None

    def test_protected_without_auth(self):
        """Test protected endpoint without authentication"""
        response = self.app.get('/protected')
        self.assertEqual(response.status_code, 401)

    def test_protected_with_valid_token(self):
        """Test protected endpoint with valid token"""
        token = self.get_auth_token()
        self.assertIsNotNone(token)

        response = self.app.get(
            '/protected',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'This is a protected endpoint')

    def test_admin_without_auth(self):
        """Test admin endpoint without authentication"""
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 401)

    def test_admin_with_user_token(self):
        """Test admin endpoint with user token (should fail)"""
        token = self.get_auth_token('user', 'user123')
        self.assertIsNotNone(token)

        response = self.app.get(
            '/admin',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_with_admin_token(self):
        """Test admin endpoint with admin token"""
        token = self.get_auth_token('admin', 'admin123')
        self.assertIsNotNone(token)

        response = self.app.get(
            '/admin',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('admin', data.get('roles', []))


if __name__ == '__main__':
    unittest.main()
