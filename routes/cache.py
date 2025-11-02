"""
Cache management endpoints
"""
from flask import Blueprint, jsonify
from typing import Tuple
from flask import Response
import logging

from app import cache

logger = logging.getLogger(__name__)

cache_bp = Blueprint('cache', __name__)


@cache_bp.route('/cache/stats')
def cache_stats() -> Tuple[Response, int]:
    """Return cache statistics"""
    stats = cache.get_cache_stats()
    status_code = 200 if stats.get('status') != 'error' else 500
    return jsonify(stats), status_code


@cache_bp.route('/cache/clear', methods=['POST'])
def cache_clear() -> Tuple[Response, int]:
    """Clear cache endpoint"""
    if cache.redis_client is None:
        return jsonify({
            'status': 'error',
            'message': 'Redis not configured'
        }), 503
    
    success = cache.clear_cache()
    if success:
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared'
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to clear cache'
        }), 500
