"""
Protected endpoints examples
"""
from flask import Blueprint, jsonify, g
from typing import Tuple
from flask import Response
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

protected_bp = Blueprint('protected', __name__)


@protected_bp.route('/protected', methods=['GET'])
def protected_endpoint() -> Tuple[Response, int]:
    """Example protected endpoint requiring JWT authentication"""
    return jsonify({
        'message': 'This is a protected endpoint',
        'user': g.current_user,
        'roles': g.user_roles,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@protected_bp.route('/admin', methods=['GET'])
@require_auth(jwt_required=True, roles=['admin'])
def admin_endpoint() -> Tuple[Response, int]:
    """Example admin-only endpoint"""
    return jsonify({
        'message': 'This is an admin-only endpoint',
        'user': g.current_user,
        'roles': g.user_roles,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@protected_bp.route('/api-key-test', methods=['GET'])
@require_auth(api_key_required=True)
def api_key_test() -> Tuple[Response, int]:
    """Example endpoint using API key authentication"""
    return jsonify({
        'message': 'This endpoint uses API key authentication',
        'user': g.current_user,
        'roles': g.user_roles,
        'authenticated': True
    }), 200
