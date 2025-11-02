#!/usr/bin/env python3
"""
シンプルなサンプルアプリケーション
ローカルで動作する簡単なHTTPサーバー
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        'message': 'Hello from Sample App!',
        'status': 'running',
        'environment': os.getenv('ENVIRONMENT', 'local')
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'sample-app'
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    # 本番環境ではdebug=Falseにすること
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
