"""
API key management functions
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import secrets
import logging

logger = logging.getLogger(__name__)

# Database connection pool (set by set_db_pool)
_db_pool = None

# API Keys (in production, store in database or secrets manager)
# Format: {api_key: {user: username, roles: [role1, role2], created_at: timestamp}}
API_KEYS = {}


def set_db_pool(db_pool: Any) -> None:
    """Set database connection pool (called from app.py)"""
    global _db_pool
    _db_pool = db_pool


def generate_api_key() -> str:
    """Generate a new API key"""
    return secrets.token_urlsafe(32)


def store_api_key_in_db(api_key: str, user: str, roles: Optional[List[str]] = None) -> bool:
    """Store API key in database"""
    if not _db_pool:
        return False
    
    try:
        conn = _db_pool.getconn()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO api_keys (api_key, user_name, roles, created_at, is_active)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, TRUE)
            ON CONFLICT (api_key) DO NOTHING
        """, (api_key, user, roles or ['user']))
        conn.commit()
        cur.close()
        _db_pool.putconn(conn)
        return True
    except Exception as e:
        logger.error(f"Failed to store API key in database: {e}")
        if conn:
            conn.rollback()
            _db_pool.putconn(conn)
        return False


def get_api_key_from_db(api_key: str) -> Optional[Dict[str, Any]]:
    """Get API key data from database"""
    if not _db_pool:
        return None
    
    try:
        conn = _db_pool.getconn()
        if not conn:
            return None
        
        cur = conn.cursor()
        cur.execute("""
            SELECT api_key, user_name, roles, is_active, expires_at, last_used_at
            FROM api_keys
            WHERE api_key = %s
        """, (api_key,))
        row = cur.fetchone()
        cur.close()
        _db_pool.putconn(conn)
        
        if row and row[3]:  # is_active
            return {
                'api_key': row[0],
                'user': row[1],
                'roles': row[2],
                'is_active': row[3],
                'expires_at': row[4],
                'last_used_at': row[5]
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get API key from database: {e}")
        if conn:
            _db_pool.putconn(conn)
        return None


def update_api_key_last_used(api_key: str) -> bool:
    """Update last_used_at timestamp for API key"""
    if not _db_pool:
        return False
    
    try:
        conn = _db_pool.getconn()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("""
            UPDATE api_keys
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE api_key = %s
        """, (api_key,))
        conn.commit()
        cur.close()
        _db_pool.putconn(conn)
        return True
    except Exception as e:
        logger.error(f"Failed to update API key last used: {e}")
        if conn:
            conn.rollback()
            _db_pool.putconn(conn)
        return False


def register_api_key(user: str, roles: Optional[List[str]] = None) -> str:
    """Register a new API key for a user"""
    api_key = generate_api_key()
    
    # Store in memory (backward compatibility)
    API_KEYS[api_key] = {
        'user': user,
        'roles': roles or ['user'],
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Also store in database if available
    if _db_pool:
        store_api_key_in_db(api_key, user, roles)
    
    logger.info(f"API key registered for user: {user}")
    return api_key


def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate an API key"""
    if not api_key:
        return None
    
    # Check in-memory storage first (backward compatibility)
    key_data = API_KEYS.get(api_key)
    if key_data:
        return {
            'user': key_data['user'],
            'roles': key_data['roles'],
            'authenticated': True
        }
    
    # Check database if available
    if _db_pool:
        key_data = get_api_key_from_db(api_key)
        if key_data and key_data.get('is_active'):
            # Check expiration
            if key_data.get('expires_at'):
                expires_at = datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                    logger.warning(f"API key expired: {api_key[:10]}...")
                    return None
            
            # Update last used timestamp
            update_api_key_last_used(api_key)
            
            return {
                'user': key_data['user'],
                'roles': key_data['roles'],
                'authenticated': True
            }
    
    return None
