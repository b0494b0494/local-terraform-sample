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
def hello():
    logger.info(f"GET / - Request from {request.remote_addr}")
    return jsonify({
        'message': 'Hello from Sample App!',
        'status': 'running',
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'timestamp': datetime.utcnow().isoformat(),
        'cached': False  # キャッシュから取得された場合はTrueになる
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
    # ここでデータベース接続などの確認を行う
    logger.debug("Readiness check requested")
    return jsonify({
        'status': 'ready',
        'service': APP_NAME
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    # 本番環境ではdebug=Falseにすること
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} on port {port} (environment: {ENVIRONMENT})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
