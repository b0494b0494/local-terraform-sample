"""
Authentication and rate limiting decorators
"""
from typing import Optional, List, Callable
from functools import wraps
import time
import logging

from flask import request, jsonify, g

from auth_pkg.api_keys import validate_api_key
from auth_pkg.jwt import verify_jwt_token

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
_rate_limit_storage = {}


def require_auth(api_key_required: bool = False, jwt_required: bool = False, roles: Optional[List[str]] = None) -> Callable:
    """
    Decorator to require authentication
    
    Args:
        api_key_required: Require API key in X-API-Key header
        jwt_required: Require JWT token in Authorization header
        roles: List of required roles (any of these)
    """
    def decorator(f: Callable) -> Callable:
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


def rate_limit(max_requests: int = 60, window_seconds: int = 60, key_func: Optional[Callable[[], str]] = None) -> Callable:
    """
    Simple rate limiting decorator
    
    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: IP address)
    """
    def decorator(f: Callable) -> Callable:
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
