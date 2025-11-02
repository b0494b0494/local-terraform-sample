#!/usr/bin/env python3
"""
Tests for authentication endpoints
"""
import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestAuthEndpoints(unittest.TestCase):
    """Test authentication endpoints"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_login_success_admin(self):
        """Test successful login with admin credentials"""
        response = self.app.post(
            '/auth/login',
            data=json.dumps({
                'username': 'admin',
                'password': 'admin123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('token', data)
        self.assertIn('api_key', data)
        self.assertEqual(data['user'], 'admin')
        self.assertIn('admin', data['roles'])

    def test_login_success_user(self):
        """Test successful login with user credentials"""
        response = self.app.post(
            '/auth/login',
            data=json.dumps({
                'username': 'user',
                'password': 'user123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['user'], 'user')
        self.assertIn('user', data['roles'])

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.app.post(
            '/auth/login',
            data=json.dumps({
                'username': 'invalid',
                'password': 'invalid'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid credentials')

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        response = self.app.post(
            '/auth/login',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

    def test_validate_token_valid(self):
        """Test token validation with valid token"""
        # First login to get token
        login_response = self.app.post(
            '/auth/login',
            data=json.dumps({
                'username': 'admin',
                'password': 'admin123'
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['token']

        # Validate token
        response = self.app.get(
            '/auth/validate',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'valid')
        self.assertEqual(data['user'], 'admin')


if __name__ == '__main__':
    unittest.main()
