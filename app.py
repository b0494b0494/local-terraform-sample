#!/usr/bin/env python3
"""
Sample Application for Terraform and Kubernetes Practice
A simple HTTP server for local practice with observability, authentication, and caching features
"""
from flask import Flask, jsonify, request, g
import os
import logging
from datetime import datetime
import redis
import json
from functools import wraps
from psycopg2.extras import RealDictCursor  # For dict cursor
import auth
import metrics
import db_utils
import time
from collections import defaultdict

# Logging Configuration
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from ConfigMap (set as environment variables)
APP_NAME = os.getenv('APP_NAME', 'sample-app')
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

# Metrics module imported - see metrics.py

# Redis Connection Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_TTL = int(os.getenv('REDIS_TTL', 300))  # Default 5 minutes

# Redis Client Initialization
redis_client = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    # Test connection
    redis_client.ping()
    logger.info(f"Redis connected to {REDIS_HOST}:{REDIS_PORT}")
except (redis.ConnectionError, redis.TimeoutError) as e:
    logger.warning(f"Redis connection failed: {e}. Continuing without cache.")
    redis_client = None

# Database Connection Pool
db_pool = None
try:
    db_host = os.getenv('DATABASE_HOST')
    db_port = os.getenv('DATABASE_PORT', '5432')
    db_name = os.getenv('DATABASE_NAME')
    db_user = os.getenv('DATABASE_USER')
    db_password = os.getenv('DATABASE_PASSWORD')
    
    if db_host and db_name and db_user and db_password:
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        # Test connection
        test_conn = db_pool.getconn()
        db_pool.putconn(test_conn)
        logger.info(f"Database connected to {db_host}:{db_port}/{db_name}")
        # Share database pool with auth module
        auth.set_db_pool(db_pool)
    else:
        logger.info("Database credentials not set. Continuing without database.")
except Exception as e:
    logger.warning(f"Database connection failed: {e}. Continuing without database.")
    db_pool = None

def get_db_connection():
    """Get database connection from pool"""
    operation = "database.get_connection"
    start_time = time.time()
    
    if db_pool is None:
        return None
    try:
        conn = db_pool.getconn()
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_apm_operation(operation, duration_ms, success=True)
        return conn
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Failed to get database connection: {e}")
        metrics.increment_database_errors()
        metrics.record_apm_operation(operation, duration_ms, success=False, error=str(e))
        return None

def return_db_connection(conn):
    """Return connection to pool"""
    operation = "database.return_connection"
    start_time = time.time()
    
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
            duration_ms = (time.time() - start_time) * 1000
            _record_apm_operation(operation, duration_ms, success=True)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to return database connection: {e}")
            metrics.record_apm_operation(operation, duration_ms, success=False, error=str(e))

class DatabaseConnection:
    """Context manager for database connections"""
    def __init__(self):
        self.conn = None
    
    def __enter__(self):
        self.conn = get_db_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            return_db_connection(self.conn)
        return False

def cache_response(ttl=REDIS_TTL):
    """Decorator to cache Flask route responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if redis_client is None:
                # If Redis is not available, execute normally
                return f(*args, **kwargs)
            
            # Generate cache key from path and parameters
            cache_key = f"cache:{request.path}:{str(sorted(request.args.items()))}"
            
            # Try to get from cache
            try:
                start_time = time.time()
                cached = redis_client.get(cache_key)
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_apm_operation("cache.get", duration_ms, success=True)
                
                if cached:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return jsonify(json.loads(cached)), 200
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.warning(f"Cache read error: {e}")
                _record_apm_operation("cache.get", duration_ms, success=False, error=str(e))
            
            # Cache miss - execute normally
            logger.debug(f"Cache MISS: {cache_key}")
            response = f(*args, **kwargs)
            
            # Cache response (JSON responses only)
            try:
                if isinstance(response, tuple) and len(response) == 2:
                    data, status = response
                    if status == 200 and hasattr(data, 'get_json'):
                        start_time = time.time()
                        json_data = data.get_json()
                        redis_client.setex(
                            cache_key,
                            ttl,
                            json.dumps(json_data)
                        )
                        duration_ms = (time.time() - start_time) * 1000
                        metrics.record_apm_operation("cache.set", duration_ms, success=True)
                        logger.debug(f"Cached response for {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                logger.warning(f"Cache write error: {e}")
                metrics.record_apm_operation("cache.set", duration_ms, success=False, error=str(e))
            
            return response
        return decorated_function
    return decorator

@app.route('/')
@cache_response(ttl=60)  # Cache for 1 minute
@auth.rate_limit(max_requests=100, window_seconds=60)
def hello():
    logger.info(f"GET / - Request from {request.remote_addr}")
    return jsonify({
        'message': 'Hello from Sample App!',
        'status': 'running',
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'timestamp': datetime.utcnow().isoformat(),
        'cached': False,  # ???????????????True???
        'authenticated': getattr(g, 'authenticated', False)
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({
        'status': 'healthy',
        'service': APP_NAME,
        'version': APP_VERSION
    }), 200

@app.route('/ready')
def ready():
    """Readiness check endpoint"""
    # Check database connection if configured
    if db_utils.db_pool:
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
        'database_connected': db_utils.db_pool is not None
    }), 200

@app.route('/info')
@cache_response(ttl=300)  # Cache for 5 minutes
def info():
    """Return application information"""
    logger.info("Info endpoint requested")
    return jsonify({
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'host': request.host,
        'remote_addr': request.remote_addr,
        'redis_connected': redis_client is not None
    }), 200

@app.route('/cache/stats')
def cache_stats():
    """Return cache statistics"""
    if redis_client is None:
        return jsonify({
            'status': 'redis_not_available',
            'message': 'Redis is not connected'
        }), 503
    
    try:
        info = redis_client.info('stats')
        return jsonify({
            'status': 'connected',
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'total_keys': redis_client.dbsize(),
            'hit_rate': round(
                info.get('keyspace_hits', 0) / 
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100,
                2
            ) if (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) > 0 else 0
        }), 200
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/cache/clear', methods=['POST'])
def cache_clear():
    """?????????"""
    if redis_client is None:
        return jsonify({
            'status': 'redis_not_available',
            'message': 'Redis is not connected'
        }), 503
    
    try:
            # Delete all cache keys (pattern match)
        keys = redis_client.keys('cache:*')
        if keys:
            redis_client.delete(*keys)
        return jsonify({
            'status': 'cleared',
            'keys_deleted': len(keys)
        }), 200
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Global Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Resource not found',
        'path': request.path
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed',
        'method': request.method,
        'path': request.path
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

@app.before_request
def before_request_metrics():
    """Collect metrics and tracing at request start"""
    request.start_time = time.time()
    # Generate trace and span IDs (OpenTelemetry-style)
    trace_ids = metrics.generate_trace_ids()
    request.trace_id = trace_ids['trace_id']
    request.span_id = trace_ids['span_id']

@app.after_request
def after_request_metrics(response):
    """Collect metrics and tracing at request end"""
    duration = time.time() - request.start_time
    
    # Record HTTP request metrics
    path = request.path
    status = response.status_code
    user = getattr(g, 'current_user', None)
    
    metrics.record_http_request(path, request.method, status, duration, user)
    
    # Create trace span
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

@app.route('/metrics')
def metrics_endpoint():
    """Prometheus format metrics endpoint"""
    logger.debug("Metrics requested")
    output = metrics.get_prometheus_metrics(APP_NAME)
    return output, 200, {'Content-Type': 'text/plain; version=0.0.4'}

@app.route('/traces', methods=['GET'])
def get_traces():
    """Distributed traces endpoint (simplified)"""
    limit = request.args.get('limit', 50, type=int)
    trace_id = request.args.get('trace_id', None)
    
    traces = metrics.get_traces(limit=limit, trace_id=trace_id)
    
    return jsonify({
        'traces': traces,
        'total': len(metrics.get_traces())
    }), 200

@app.route('/apm/stats', methods=['GET'])
def apm_stats():
    """APM performance statistics endpoint"""
    stats = metrics.get_apm_stats()
    return jsonify(stats), 200

# _record_apm_operation is now metrics.record_apm_operation

@app.route('/db/status')
def db_status():
    """Database connection status"""
    if db_utils.db_pool is None:
        return jsonify({
            'status': 'not_configured',
            'message': 'Database not configured'
        }), 200
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get database connection'
        }), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        return_db_connection(conn)
        
        return jsonify({
            'status': 'connected',
            'version': version.split(',')[0]  # PostgreSQL version
        }), 200
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/db/query', methods=['POST'])
def db_query():
    """Execute a simple database query (for testing)"""
    if db_utils.db_pool is None:
        return jsonify({
            'status': 'error',
            'message': 'Database not configured'
        }), 503
    
    try:
        data = request.json or {}
        query = data.get('query', 'SELECT NOW() as current_time;')
        
        # Use context manager to ensure connection is returned
        with DatabaseConnection() as conn:
            if conn is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to get database connection'
                }), 500
            
            cur = conn.cursor(cursor_factory=RealDictCursor)
            try:
                cur.execute(query)
                results = cur.fetchall()
                cur.close()
                return jsonify({
                    'status': 'success',
                    'results': [dict(row) for row in results]
                }), 200
            except Exception as e:
                conn.rollback()
                cur.close()
                raise e
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Authentication Endpoints
@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint - returns JWT token"""
    try:
        data = request.json or {}
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Authenticate user with hashed password verification
        user_data = auth.authenticate_user(username, password)
        
        if user_data:
            # Authentication successful
            token = auth.create_jwt_token(username, roles=user_data['roles'])
            api_key = auth.register_api_key(username, roles=user_data['roles'])
            
            return jsonify({
                'status': 'success',
                'token': token,
                'api_key': api_key,
                'user': username,
                'roles': user_data['roles'],
                'expires_in': auth.JWT_EXPIRATION_HOURS * 3600
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/auth/validate', methods=['GET', 'POST'])
@auth.require_auth(jwt_required=True, api_key_required=False)
def validate_token():
    """Validate current authentication token"""
    return jsonify({
        'status': 'valid',
        'user': g.current_user,
        'roles': g.user_roles,
        'authenticated': True
    }), 200

@app.route('/auth/api-keys', methods=['GET'])
@auth.require_auth(jwt_required=True, roles=['admin'])
def list_api_keys():
    """List all API keys (admin only)"""
    keys = []
    for api_key, data in auth.API_KEYS.items():
        keys.append({
            'user': data['user'],
            'roles': data['roles'],
            'created_at': data['created_at'],
            'key_preview': api_key[:8] + '...'  # Don't expose full key
        })
    
    return jsonify({
        'status': 'success',
        'api_keys': keys,
        'total': len(keys)
    }), 200

# Protected Endpoint Examples
@app.route('/protected', methods=['GET'])
@auth.require_auth(jwt_required=True)
@auth.rate_limit(max_requests=30, window_seconds=60)
def protected_endpoint():
    """Example protected endpoint requiring JWT authentication"""
    return jsonify({
        'message': 'This is a protected endpoint',
        'user': g.current_user,
        'roles': g.user_roles,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/admin', methods=['GET'])
@auth.require_auth(jwt_required=True, roles=['admin'])
def admin_endpoint():
    """Example admin-only endpoint"""
    return jsonify({
        'message': 'This is an admin-only endpoint',
        'user': g.current_user,
        'roles': g.user_roles,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api-key-test', methods=['GET'])
@auth.require_auth(api_key_required=True)
def api_key_test():
    """Example endpoint using API key authentication"""
    return jsonify({
        'message': 'This endpoint uses API key authentication',
        'user': g.current_user,
        'roles': g.user_roles,
        'authenticated': True
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    # Default to False for security (set DEBUG=True explicitly for development)
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    
    if debug_mode and ENVIRONMENT != 'local':
        logger.warning(f"DEBUG mode enabled in {ENVIRONMENT} environment - this should only be used in development!")
    
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} on port {port} (environment: {ENVIRONMENT}, debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
