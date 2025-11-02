#!/usr/bin/env python3
"""
Sample Application for Terraform and Kubernetes Practice
Refactored to use routes/ package structure for better modularity
"""
from flask import Flask, jsonify, request, g, Response
from typing import Tuple
import logging
import time

from app import metrics, database, cache, config
import auth  # Keep using auth.py for now, will migrate to auth_pkg later

# Logging Configuration
logging.basicConfig(
    level=config.Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
APP_NAME = config.Config.APP_NAME
APP_VERSION = config.Config.APP_VERSION
ENVIRONMENT = config.Config.ENVIRONMENT

# Initialize database pool
db_pool = database.initialize_db_pool()
if database.db_pool:
    set_db_pool(database.db_pool)

# Import database utilities
get_db_connection = database.get_db_connection
return_db_connection = database.return_db_connection
DatabaseConnection = database.DatabaseConnection

# Cache decorator
cache_response = cache.cache_response

# Register blueprints
from routes import health, cache as cache_routes, metrics as metrics_routes, db, auth_routes, protected
from auth_pkg import rate_limit

# Health endpoints - register blueprint
# Apply decorators to root endpoint
from app import cache as app_cache
health.health_bp.route('/')(
    app_cache.cache_response(ttl=60)(
        rate_limit(max_requests=100, window_seconds=60)(
            health.hello
        )
    )
)
# Apply cache to info endpoint
health.health_bp.route('/info')(
    app_cache.cache_response(ttl=300)(
        health.info
    )
)
app.register_blueprint(health.health_bp)

app.register_blueprint(cache_routes.cache_bp)
app.register_blueprint(metrics_routes.metrics_bp)
app.register_blueprint(db.db_bp)

# Auth routes - register blueprint
# Decorators will be applied via @decorator syntax in route files
app.register_blueprint(auth_routes.auth_routes_bp)

# Protected routes - register blueprint
app.register_blueprint(protected.protected_bp)

# Global Error Handlers
@app.errorhandler(404)
def not_found(error: Exception) -> Tuple[Response, int]:
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Resource not found',
        'path': request.path
    }), 404


@app.errorhandler(405)
def method_not_allowed(error: Exception) -> Tuple[Response, int]:
    """Handle 405 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed',
        'method': request.method,
        'path': request.path
    }), 405


@app.errorhandler(500)
def internal_error(error: Exception) -> Tuple[Response, int]:
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


@app.before_request
def before_request_metrics() -> None:
    """Collect metrics and tracing at request start"""
    request.start_time = time.time()
    trace_ids = metrics.generate_trace_ids()
    request.trace_id = trace_ids['trace_id']
    request.span_id = trace_ids['span_id']


@app.after_request
def after_request_metrics(response: Response) -> Response:
    """Collect metrics and tracing at request end"""
    duration = time.time() - request.start_time
    
    path = request.path
    status = response.status_code
    user = getattr(g, 'current_user', None)
    
    metrics.record_http_request(path, request.method, status, duration, user)
    
    metrics.create_trace_span(
        trace_id=getattr(request, 'trace_id', 'unknown'),
        span_id=getattr(request, 'span_id', 'unknown'),
        operation_name=f"{request.method} {path}",
        duration_ms=duration * 1000,
        status_code=status,
        method=request.method,
        path=path,
        user_agent=request.headers.get('User-Agent', 'unknown'),
        service_name=APP_NAME,
        user=user
    )
    
    return response


if __name__ == '__main__':
    port = config.Config.PORT
    debug_mode = config.Config.DEBUG
    
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} on port {port} (environment: {ENVIRONMENT}, debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
