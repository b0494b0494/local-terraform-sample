#!/usr/bin/env python3
"""
Authentication and Authorization module
Provides JWT token and API key authentication
"""
import os
import time
import hmac
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

# JWT Secret (in production, use strong random secret from environment)
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# API Keys (in production, store in database or secrets manager)
# Format: {api_key: {user: username, roles: [role1, role2], created_at: timestamp}}
API_KEYS = {}

def generate_api_key():
    """Generate a new API key"""
    return secrets.token_urlsafe(32)

def register_api_key(user, roles=None):
    """Register a new API key for a user"""
    api_key = generate_api_key()
    API_KEYS[api_key] = {
        'user': user,
        'roles': roles or ['user'],
        'created_at': datetime.utcnow().isoformat()
    }
    logger.info(f"API key registered for user: {user}")
    return api_key

def validate_api_key(api_key):
    """Validate an API key"""
    if not api_key:
        return None
    
    key_data = API_KEYS.get(api_key)
    if key_data:
        return {
            'user': key_data['user'],
            'roles': key_data['roles'],
            'authenticated': True
        }
    return None

def create_jwt_token(user, roles=None):
    """Create a JWT token (simplified implementation)"""
    # In production, use PyJWT library
    # This is a simplified demo version
    payload = {
        'user': user,
        'roles': roles or ['user'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    # Simple token encoding (not secure, for demo only)
    import base64
    import json
    header = {'alg': JWT_ALGORITHM, 'typ': 'JWT'}
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Create signature
    message = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        JWT_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
    return token

def verify_jwt_token(token):
    """Verify a JWT token (simplified implementation)"""
    if not token:
        return None
    
    try:
        import base64
        import json
        
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        encoded_payload = parts[1]
        # Add padding if needed
        padding = 4 - len(encoded_payload) % 4
        if padding != 4:
            encoded_payload += '=' * padding
        
        payload_json = base64.urlsafe_b64decode(encoded_payload)
        payload = json.loads(payload_json)
        
        # Check expiration
        exp = datetime.fromisoformat(payload['exp'])
        if datetime.utcnow() > exp:
            return None
        
        return {
            'user': payload.get('user'),
            'roles': payload.get('roles', ['user']),
            'authenticated': True
        }
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        return None

def require_auth(api_key_required=False, jwt_required=False, roles=None):
    """
    Decorator to require authentication
    
    Args:
        api_key_required: Require API key in X-API-Key header
        jwt_required: Require JWT token in Authorization header
        roles: List of required roles (any of these)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_info = None
            
            # Try API key authentication
            if api_key_required:
                api_key = request.headers.get('X-API-Key')
                auth_info = validate_api_key(api_key)
                if not auth_info:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'Valid API key required in X-API-Key header'
                    }), 401
            
            # Try JWT authentication
            if jwt_required and not auth_info:
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    auth_info = verify_jwt_token(token)
                    if not auth_info:
                        return jsonify({
                            'error': 'Authentication required',
                            'message': 'Valid JWT token required'
                        }), 401
                else:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'Bearer token required in Authorization header'
                    }), 401
            
            # If authentication required but not found
            if (api_key_required or jwt_required) and not auth_info:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'API key or JWT token required'
                }), 401
            
            # Check roles
            if roles and auth_info:
                user_roles = auth_info.get('roles', [])
                if not any(role in user_roles for role in roles):
                    return jsonify({
                        'error': 'Authorization failed',
                        'message': f'Required roles: {roles}, user roles: {user_roles}'
                    }), 403
            
            # Store auth info in Flask g for use in view
            g.current_user = auth_info.get('user') if auth_info else None
            g.user_roles = auth_info.get('roles', []) if auth_info else []
            g.authenticated = auth_info is not None
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rate limiting storage (in production, use Redis)
_rate_limit_storage = {}

def rate_limit(max_requests=60, window_seconds=60, key_func=None):
    """
    Simple rate limiting decorator
    
    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: IP address)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old entries
            _rate_limit_storage[key] = [
                ts for ts in _rate_limit_storage.get(key, [])
                if ts > window_start
            ]
            
            # Check rate limit
            request_count = len(_rate_limit_storage[key])
            if request_count >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window_seconds} seconds',
                    'retry_after': window_seconds
                }), 429
            
            # Record this request
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = []
            _rate_limit_storage[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
