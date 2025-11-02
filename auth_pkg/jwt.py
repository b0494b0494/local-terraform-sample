"""
JWT token functions
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hmac
import hashlib
import base64
import json
import logging

from auth_pkg.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

logger = logging.getLogger(__name__)


def create_jwt_token(user: str, roles: Optional[List[str]] = None) -> str:
    """Create a JWT token (simplified implementation)"""
    # In production, use PyJWT library
    # This is a simplified demo version
    now = datetime.utcnow()
    exp_time = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        'user': user,
        'roles': roles or ['user'],
        'exp': exp_time.isoformat(),  # Convert to ISO string
        'iat': now.isoformat()
    }
    
    # Simple token encoding (not secure, for demo only)
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


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token (simplified implementation)"""
    if not token:
        return None
    
    try:
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
        exp_str = payload['exp']
        exp = datetime.fromisoformat(exp_str.replace('Z', '+00:00')) if isinstance(exp_str, str) else datetime.fromtimestamp(exp_str)
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
