#!/usr/bin/env python3
"""
シンプルなサンプルアプリケーション
ローカルで動作する簡単なHTTPサーバー
"""
from flask import Flask, jsonify, request
import os
import logging
from datetime import datetime

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

@app.route('/')
def hello():
    logger.info(f"GET / - Request from {request.remote_addr}")
    return jsonify({
        'message': 'Hello from Sample App!',
        'status': 'running',
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'timestamp': datetime.utcnow().isoformat()
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
def info():
    """アプリケーション情報を返す"""
    logger.info("Info endpoint requested")
    return jsonify({
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'host': request.host,
        'remote_addr': request.remote_addr
    }), 200

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
