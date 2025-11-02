"""
User management functions
"""
from typing import Optional, Dict, Any
import bcrypt
import logging

from auth_pkg.config import JWT_EXPIRATION_HOURS

logger = logging.getLogger(__name__)

# Demo users with hashed passwords (in production, store in database)
# Format: {username: {password_hash: str, roles: [role1, role2]}}
DEMO_USERS = {}


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user data by username (in production, query database)"""
    return DEMO_USERS.get(username)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with username and password"""
    user = get_user(username)
    if not user:
        return None
    
    if verify_password(password, user['password_hash']):
        return {
            'username': username,
            'roles': user['roles']
        }
    return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def _init_demo_users() -> None:
    """Initialize demo users with hashed passwords"""
    DEMO_USERS['admin'] = {
        'password_hash': hash_password('admin123'),
        'roles': ['admin', 'user']
    }
    DEMO_USERS['user'] = {
        'password_hash': hash_password('user123'),
        'roles': ['user']
    }


# Initialize on module load
_init_demo_users()
