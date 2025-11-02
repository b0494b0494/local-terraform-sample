"""
Health check and info endpoints
"""
from flask import Blueprint, jsonify, request, g
from typing import Tuple
from flask import Response
from datetime import datetime
import logging

from app import database, cache, config

logger = logging.getLogger(__name__)

# Get database utilities from database module
get_db_connection = database.get_db_connection
return_db_connection = database.return_db_connection

# Configuration
APP_NAME = config.Config.APP_NAME
APP_VERSION = config.Config.APP_VERSION
ENVIRONMENT = config.Config.ENVIRONMENT

# Create blueprint
health_bp = Blueprint('health', __name__)


@health_bp.route('/')
def hello():
    """Root endpoint"""
    logger.info(f"GET / - Request from {request.remote_addr}")
    # Note: Cache and rate limit decorators should be applied in app.py when registering blueprint
    return jsonify({
        'message': 'Hello from Sample App!',
        'status': 'running',
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'timestamp': datetime.utcnow().isoformat(),
        'cached': False,  # Will be True if served from cache
        'authenticated': getattr(g, 'authenticated', False)
    })


@health_bp.route('/health')
def health() -> Tuple[Response, int]:
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({
        'status': 'healthy',
        'service': APP_NAME,
        'version': APP_VERSION
    }), 200


@health_bp.route('/ready')
def ready() -> Tuple[Response, int]:
    """Readiness check endpoint"""
    # Check database connection if configured
    if database.db_pool:
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return_db_connection(conn)
                logger.debug("Database connection verified")
            except Exception as e:
                logger.warning(f"Database check failed: {e}")
                return jsonify({
                    'status': 'not_ready',
                    'service': APP_NAME,
                    'reason': 'database_check_failed'
                }), 503
    
    logger.debug("Readiness check requested")
    return jsonify({
        'status': 'ready',
        'service': APP_NAME,
        'database_connected': database.db_pool is not None
    }), 200


@health_bp.route('/info')
def info() -> Tuple[Response, int]:
    """Return application information"""
    logger.info("Info endpoint requested")
    info_data = config.Config.get_summary()
    info_data.update({
        'host': request.host,
        'remote_addr': request.remote_addr,
        'redis_connected': cache.redis_client is not None
    })
    return jsonify(info_data), 200
