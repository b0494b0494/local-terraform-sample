#!/usr/bin/env python3
"""
シンプルなサンプルアプリケーション
ローカルで動作する簡単なHTTPサーバー
"""
from flask import Flask, jsonify, request
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

# ロギング設定
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ConfigMapから読み込む設定値（環境変数として設定される）
APP_NAME = os.getenv('APP_NAME', 'sample-app')
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

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

# Database connection pool
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
    if db_pool is None:
        return None
    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        return None

def return_db_connection(conn):
    """Return connection to pool"""
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to return database connection: {e}")

def cache_response(ttl=REDIS_TTL):
    """レスポンスをキャッシュするデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if redis_client is None:
                # Redisが利用できない場合は通常通り実行
                return f(*args, **kwargs)
            
            # キャッシュキー生成（パスとパラメータから）
            cache_key = f"cache:{request.path}:{str(sorted(request.args.items()))}"
            
            # キャッシュから取得を試みる
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return jsonify(json.loads(cached)), 200
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # キャッシュがない場合は通常実行
            logger.debug(f"Cache MISS: {cache_key}")
            response = f(*args, **kwargs)
            
            # レスポンスをキャッシュ（JSONレスポンスのみ）
            try:
                if isinstance(response, tuple) and len(response) == 2:
                    data, status = response
                    if status == 200 and hasattr(data, 'get_json'):
                        json_data = data.get_json()
                        redis_client.setex(
                            cache_key,
                            ttl,
                            json.dumps(json_data)
                        )
                        logger.debug(f"Cached response for {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return response
        return decorated_function
    return decorator

@app.route('/')
@cache_response(ttl=60)  # 1分間キャッシュ
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
    # データベース接続確認
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
@cache_response(ttl=300)  # 5分間キャッシュ
def info():
    """アプリケーション情報を返す"""
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
    """キャッシュ統計情報を返す"""
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
        # キャッシュキーをすべて削除（パターンマッチ）
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

@app.route('/metrics')
def metrics():
    """メトリクスエンドポイント（簡易版）"""
    logger.debug("Metrics requested")
    # 実際には Prometheus 形式のメトリクスを返す
    return jsonify({
        'requests': {
            'total': 0,  # 実際にはカウンターを実装
        }
    }), 200

@app.route('/db/status')
def db_status():
    """データベース接続ステータス"""
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
