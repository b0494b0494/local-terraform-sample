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
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import auth
import time
import uuid
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

# Prometheus metrics storage
_metrics = {
    'http_requests_total': defaultdict(lambda: defaultdict(int)),  # path -> status -> count
    'http_request_duration_seconds': [],  # List of durations
    'app_database_connection_errors_total': 0,
    'app_redis_connection_errors_total': 0,
}

# Distributed tracing storage (simplified OpenTelemetry-style)
_traces = []  # List of trace spans
_MAX_TRACES = 100  # Keep last 100 traces

# APM (Application Performance Monitoring) hooks
_apm_data = {
    'operation_stats': defaultdict(lambda: {
        'count': 0,
        'total_duration_ms': 0.0,
        'min_duration_ms': float('inf'),
        'max_duration_ms': 0.0,
        'errors': 0,
        'last_executed': None
    }),
    'slow_operations': [],  # Operations taking > 1 second
    'error_operations': []  # Operations that failed
}
_MAX_SLOW_OPS = 50
_MAX_ERROR_OPS = 50

# Redis接続設定
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_TTL = int(os.getenv('REDIS_TTL', 300))  # デフォルト5分

# Redisクライアント初期化
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
    # 接続テスト
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
        _record_apm_operation(operation, duration_ms, success=True)
        return conn
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Failed to get database connection: {e}")
        _metrics['app_database_connection_errors_total'] += 1
        _record_apm_operation(operation, duration_ms, success=False, error=str(e))
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
            _record_apm_operation(operation, duration_ms, success=False, error=str(e))

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
                _record_apm_operation("cache.get", duration_ms, success=True)
                
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
                        _record_apm_operation("cache.set", duration_ms, success=True)
                        logger.debug(f"Cached response for {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                start_time = time.time()
                duration_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                logger.warning(f"Cache write error: {e}")
                _record_apm_operation("cache.set", duration_ms, success=False, error=str(e))
            
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
        'cached': False,  # キャッシュから取得された場合はTrueになる
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
    if db_pool:
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
        'database_connected': db_pool is not None
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
    """キャッシュをクリア"""
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

@app.before_request
def before_request_metrics():
    """Collect metrics and tracing at request start"""
    request.start_time = time.time()
    # Generate trace and span IDs (OpenTelemetry-style)
    request.trace_id = uuid.uuid4().hex[:16]  # 16-char trace ID
    request.span_id = uuid.uuid4().hex[:8]    # 8-char span ID

@app.after_request
def after_request_metrics(response):
    """Request終了時のメトリクス収集とトレーシング"""
    duration = time.time() - request.start_time
    
    # HTTP requests total (by path and status)
    path = request.path
    status = response.status_code
    _metrics['http_requests_total'][path][status] += 1
    
    # Request duration
    _metrics['http_request_duration_seconds'].append({
        'path': path,
        'method': request.method,
        'duration': duration,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Keep only last 100 entries
    if len(_metrics['http_request_duration_seconds']) > 100:
        _metrics['http_request_duration_seconds'] = _metrics['http_request_duration_seconds'][-100:]
    
    # Distributed tracing: Create span
    span = {
        'trace_id': getattr(request, 'trace_id', 'unknown'),
        'span_id': getattr(request, 'span_id', 'unknown'),
        'parent_span_id': None,  # Root span
        'operation_name': f"{request.method} {path}",
        'service_name': APP_NAME,
        'start_time': datetime.utcnow().isoformat(),
        'duration_ms': duration * 1000,
        'status_code': status,
        'attributes': {
            'http.method': request.method,
            'http.path': path,
            'http.status_code': status,
            'http.user_agent': request.headers.get('User-Agent', 'unknown'),
        }
    }
    
    # Add authentication info if available
    if hasattr(g, 'current_user') and g.current_user:
        span['attributes']['user'] = g.current_user
    
    _traces.append(span)
    
    # Keep only last MAX_TRACES
    if len(_traces) > _MAX_TRACES:
        _traces[:] = _traces[-_MAX_TRACES:]
    
    return response

@app.route('/metrics')
def metrics():
    """Prometheus format metrics endpoint"""
    logger.debug("Metrics requested")
    
    output = []
    
    # HTTP requests total (Prometheus format)
    for path, status_counts in _metrics['http_requests_total'].items():
        for status, count in status_counts.items():
            output.append(
                f'http_requests_total{{path="{path}",status="{status}",service="{APP_NAME}"}} {count}'
            )
    
    # Request duration (simplified histogram format)
    if _metrics['http_request_duration_seconds']:
        durations = [d['duration'] for d in _metrics['http_request_duration_seconds']]
        
        # Buckets (seconds): 0.1, 0.5, 1.0, 2.0, 5.0, +Inf
        buckets = [0.1, 0.5, 1.0, 2.0, 5.0, float('inf')]
        bucket_counts = [0] * len(buckets)
        
        for duration in durations:
            for i, bucket in enumerate(buckets):
                if duration <= bucket:
                    bucket_counts[i] += 1
                    break
        
        for i, (bucket, count) in enumerate(zip(buckets, bucket_counts)):
            le = bucket if bucket != float('inf') else '+Inf'
            output.append(
                f'http_request_duration_seconds_bucket{{le="{le}",service="{APP_NAME}"}} {count}'
            )
        
        # Summary statistics
        avg_duration = sum(durations) / len(durations) if durations else 0
        output.append(f'http_request_duration_seconds_avg{{service="{APP_NAME}"}} {avg_duration}')
        output.append(f'http_request_duration_seconds_count{{service="{APP_NAME}"}} {len(durations)}')
    
    # データベース接続エラー
    output.append(
        f'app_database_connection_errors_total{{service="{APP_NAME}"}} {_metrics["app_database_connection_errors_total"]}'
    )
    
    # Redis接続エラー
    output.append(
        f'app_redis_connection_errors_total{{service="{APP_NAME}"}} {_metrics["app_redis_connection_errors_total"]}'
    )
    
    return '\n'.join(output) + '\n', 200, {'Content-Type': 'text/plain; version=0.0.4'}

@app.route('/traces', methods=['GET'])
def get_traces():
    """Distributed traces endpoint (simplified)"""
    limit = request.args.get('limit', 50, type=int)
    trace_id = request.args.get('trace_id', None)
    
    filtered_traces = _traces
    
    # Filter by trace_id if provided
    if trace_id:
        filtered_traces = [t for t in _traces if t['trace_id'] == trace_id]
    
    # Return latest traces
    traces_to_return = filtered_traces[-limit:] if len(filtered_traces) > limit else filtered_traces
    
    return jsonify({
        'traces': traces_to_return,
        'total': len(filtered_traces),
        'returned': len(traces_to_return)
    }), 200

@app.route('/apm/stats', methods=['GET'])
def apm_stats():
    """APM performance statistics endpoint"""
    # Calculate averages
    stats_summary = {}
    for operation, stats in _apm_data['operation_stats'].items():
        avg_duration = stats['total_duration_ms'] / stats['count'] if stats['count'] > 0 else 0
        error_rate = stats['errors'] / stats['count'] if stats['count'] > 0 else 0
        
        stats_summary[operation] = {
            'count': stats['count'],
            'avg_duration_ms': round(avg_duration, 2),
            'min_duration_ms': round(stats['min_duration_ms'], 2) if stats['min_duration_ms'] != float('inf') else 0,
            'max_duration_ms': round(stats['max_duration_ms'], 2),
            'total_duration_ms': round(stats['total_duration_ms'], 2),
            'errors': stats['errors'],
            'error_rate': round(error_rate * 100, 2),  # Percentage
            'last_executed': stats['last_executed']
        }
    
    return jsonify({
        'operation_stats': stats_summary,
        'slow_operations': _apm_data['slow_operations'][-10:],  # Last 10 slow operations
        'recent_errors': _apm_data['error_operations'][-10:],  # Last 10 errors
        'summary': {
            'total_operations': sum(s['count'] for s in _apm_data['operation_stats'].values()),
            'total_errors': sum(s['errors'] for s in _apm_data['operation_stats'].values()),
            'total_slow_operations': len(_apm_data['slow_operations'])
        }
    }), 200

def _record_apm_operation(operation, duration_ms, success=True, error=None):
    """Record APM metrics for an operation"""
    stats = _apm_data['operation_stats'][operation]
    
    stats['count'] += 1
    stats['total_duration_ms'] += duration_ms
    stats['min_duration_ms'] = min(stats['min_duration_ms'], duration_ms)
    stats['max_duration_ms'] = max(stats['max_duration_ms'], duration_ms)
    stats['last_executed'] = datetime.utcnow().isoformat()
    
    if not success:
        stats['errors'] += 1
        error_record = {
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat(),
            'error': error or 'Unknown error',
            'duration_ms': duration_ms
        }
        _apm_data['error_operations'].append(error_record)
        if len(_apm_data['error_operations']) > _MAX_ERROR_OPS:
            _apm_data['error_operations'] = _apm_data['error_operations'][-_MAX_ERROR_OPS:]
    
    # Track slow operations (> 1 second)
    if duration_ms > 1000:
        slow_record = {
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': duration_ms
        }
        _apm_data['slow_operations'].append(slow_record)
        if len(_apm_data['slow_operations']) > _MAX_SLOW_OPS:
            _apm_data['slow_operations'] = _apm_data['slow_operations'][-_MAX_SLOW_OPS:]

@app.route('/db/status')
def db_status():
    """Database connection status"""
    if db_pool is None:
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
    if db_pool is None:
        return jsonify({
            'error': 'Database not configured'
        }), 503
    
    try:
        query = request.json.get('query', 'SELECT NOW() as current_time;')
        conn = get_db_connection()
        if conn is None:
            return jsonify({
                'error': 'Failed to get database connection'
            }), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        return_db_connection(conn)
        
        return jsonify({
            'status': 'success',
            'results': [dict(row) for row in results]
        }), 200
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return jsonify({
            'error': str(e)
        }), 500

# Authentication Endpoints
@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint - returns JWT token"""
    try:
        data = request.json or {}
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Simple demo authentication (in production, check against database)
        # Demo credentials: user: admin, password: admin123
        if username == 'admin' and password == 'admin123':
            token = auth.create_jwt_token(username, roles=['admin', 'user'])
            api_key = auth.register_api_key(username, roles=['admin', 'user'])
            
            return jsonify({
                'status': 'success',
                'token': token,
                'api_key': api_key,
                'user': username,
                'roles': ['admin', 'user'],
                'expires_in': auth.JWT_EXPIRATION_HOURS * 3600
            }), 200
        elif username == 'user' and password == 'user123':
            token = auth.create_jwt_token(username, roles=['user'])
            api_key = auth.register_api_key(username, roles=['user'])
            
            return jsonify({
                'status': 'success',
                'token': token,
                'api_key': api_key,
                'user': username,
                'roles': ['user'],
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
    # 本番環境ではdebug=Falseにすること
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} on port {port} (environment: {ENVIRONMENT})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
