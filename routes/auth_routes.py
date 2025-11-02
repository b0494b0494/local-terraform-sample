"""
Authentication endpoints
"""
from flask import Blueprint, jsonify, request, g
from typing import Tuple
from flask import Response
import logging

# Import auth functions - will be updated after auth_pkg is created
# For now, we'll import from auth module
import auth

logger = logging.getLogger(__name__)

auth_routes_bp = Blueprint('auth_routes', __name__)


@auth_routes_bp.route('/auth/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """Login endpoint - returns JWT token"""
    try:
        data = request.json or {}
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Authenticate user with hashed password verification
        user_data = auth.authenticate_user(username, password)
        
        if user_data:
            # Authentication successful
            token = auth.create_jwt_token(username, roles=user_data['roles'])
            api_key = auth.register_api_key(username, roles=user_data['roles'])
            
            return jsonify({
                'status': 'success',
                'token': token,
                'api_key': api_key,
                'user': username,
                'roles': user_data['roles'],
                'expires_in': auth.JWT_EXPIRATION_HOURS * 3600
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@auth_routes_bp.route('/auth/validate', methods=['GET', 'POST'])
@require_auth(jwt_required=True, api_key_required=False)
def validate_token() -> Tuple[Response, int]:
    """Validate current authentication token"""
    return jsonify({
        'status': 'valid',
        'user': g.current_user,
        'roles': g.user_roles,
        'authenticated': True
    }), 200


@auth_routes_bp.route('/auth/api-keys', methods=['GET'])
@require_auth(jwt_required=True, roles=['admin'])
def list_api_keys() -> Tuple[Response, int]:
    """List all API keys (admin only)"""
    keys = []
    for api_key, data in API_KEYS.items():
        keys.append({
            'user': data['user'],
            'roles': data['roles'],
            'created_at': data['created_at'],
            'key_preview': api_key[:8] + '...'  # Don't expose full key
        })
    
    return jsonify({
        'status': 'success',
        'api_keys': keys,
        'total': len(keys)
    }), 200
