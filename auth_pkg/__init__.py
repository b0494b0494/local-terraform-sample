"""
Authentication and Authorization package
Reorganized from auth.py for better modularity
"""

# Import main functions for backward compatibility
from auth_pkg.users import get_user, authenticate_user, hash_password, verify_password
from auth_pkg.jwt import create_jwt_token, verify_jwt_token
from auth_pkg.api_keys import (
    generate_api_key,
    store_api_key_in_db,
    get_api_key_from_db,
    update_api_key_last_used,
    validate_api_key,
    register_api_key,
    set_db_pool,
    API_KEYS
)
from auth_pkg.decorators import require_auth, rate_limit
from auth_pkg.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

# Export for backward compatibility
__all__ = [
    'get_user',
    'authenticate_user',
    'hash_password',
    'verify_password',
    'create_jwt_token',
    'verify_jwt_token',
    'generate_api_key',
    'store_api_key_in_db',
    'get_api_key_from_db',
    'update_api_key_last_used',
    'validate_api_key',
    'register_api_key',
    'set_db_pool',
    'require_auth',
    'rate_limit',
    'API_KEYS',
    'JWT_SECRET',
    'JWT_ALGORITHM',
    'JWT_EXPIRATION_HOURS',
]
