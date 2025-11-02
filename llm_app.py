#!/usr/bin/env python3
"""
LLM???????????????????????
???????????API????????????????????
"""
from flask import Flask, jsonify, request
import os
import logging
import json
import time
import uuid
from datetime import datetime
from collections import defaultdict
from functools import wraps

# ???????
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(message)s',  # JSON?????message??
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ConfigMap?????????
APP_NAME = os.getenv('APP_NAME', 'llm-app')
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

# ???????????????Prometheus??????
metrics = {
    'requests_total': defaultdict(int),
    'request_duration_seconds': [],
    'tokens_generated': 0,
    'errors_total': 0,
}

# ????????????OpenTelemetry??????
traces = []

def log_structured(level, message, **kwargs):
    """????????"""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'service': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'message': message,
        **kwargs
    }
    logger.log(getattr(logging, level.upper()), json.dumps(log_data))

def trace_span(operation_name):
    """?????????????????"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_id = str(uuid.uuid4())
            span_id = str(uuid.uuid4())
            start_time = time.time()
            
            log_structured('INFO', f'Trace started: {operation_name}', 
                          trace_id=trace_id, span_id=span_id, operation=operation_name)
            
            try:
                result = func(*args, **kwargs, trace_id=trace_id)
                duration = time.time() - start_time
                
                log_structured('INFO', f'Trace completed: {operation_name}',
                              trace_id=trace_id, span_id=span_id, 
                              operation=operation_name, duration_ms=duration * 1000)
                
                traces.append({
                    'trace_id': trace_id,
                    'span_id': span_id,
                    'operation': operation_name,
                    'duration_ms': duration * 1000,
                    'status': 'success',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics['errors_total'] += 1
                
                log_structured('ERROR', f'Trace failed: {operation_name}',
                              trace_id=trace_id, span_id=span_id,
                              operation=operation_name, duration_ms=duration * 1000,
                              error=str(e))
                
                traces.append({
                    'trace_id': trace_id,
                    'span_id': span_id,
                    'operation': operation_name,
                    'duration_ms': duration * 1000,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                raise
        
        return wrapper
    return decorator

@app.before_request
def before_request():
    """?????????????????"""
    request.start_time = time.time()
    metrics['requests_total'][request.path] += 1

@app.after_request
def after_request(response):
    """?????????????????"""
    duration = time.time() - request.start_time
    metrics['request_duration_seconds'].append({
        'path': request.path,
        'method': request.method,
        'duration': duration,
        'status_code': response.status_code,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # ??100?????
    if len(metrics['request_duration_seconds']) > 100:
        metrics['request_duration_seconds'] = metrics['request_duration_seconds'][-100:]
    
    return response

@app.route('/')
def hello():
    """??????????"""
    log_structured('INFO', 'Root endpoint accessed', 
                  path='/', remote_addr=request.remote_addr)
    return jsonify({
        'message': 'LLM App with Observability',
        'status': 'running',
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'environment': ENVIRONMENT,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/chat', methods=['POST'])
@trace_span('chat_completion')
def chat(trace_id):
    """LLM?????API?????"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            log_structured('WARN', 'Empty message received', trace_id=trace_id)
            return jsonify({'error': 'message is required'}), 400
        
        log_structured('INFO', 'Chat request received',
                      trace_id=trace_id, user_message_length=len(user_message))
        
        # ???????????????LLM?????
        response_message = f"Echo: {user_message}"
        tokens = len(response_message.split())
        metrics['tokens_generated'] += tokens
        
        log_structured('INFO', 'Chat response generated',
                      trace_id=trace_id, tokens=tokens)
        
        return jsonify({
            'message': response_message,
            'tokens': tokens,
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        log_structured('ERROR', 'Chat request failed',
                      trace_id=trace_id, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def prometheus_metrics():
    """Prometheus???????????????"""
    log_structured('DEBUG', 'Metrics endpoint accessed')
    
    # Prometheus?????
    output = []
    
    # ??????
    for path, count in metrics['requests_total'].items():
        output.append(f'llm_requests_total{{path="{path}",service="{APP_NAME}"}} {count}')
    
    # ??????????
    if metrics['request_duration_seconds']:
        avg_duration = sum(d['duration'] for d in metrics['request_duration_seconds']) / len(metrics['request_duration_seconds'])
        output.append(f'llm_request_duration_seconds_avg{{service="{APP_NAME}"}} {avg_duration}')
    
    # ?????
    output.append(f'llm_tokens_generated_total{{service="{APP_NAME}"}} {metrics["tokens_generated"]}')
    
    # ????
    output.append(f'llm_errors_total{{service="{APP_NAME}"}} {metrics["errors_total"]}')
    
    return '\n'.join(output) + '\n', 200, {'Content-Type': 'text/plain'}

@app.route('/traces')
def get_traces():
    """????????????"""
    log_structured('INFO', 'Traces endpoint accessed')
    return jsonify({
        'traces': traces[-50:],  # ??50?
        'total': len(traces)
    })

@app.route('/logs')
def get_logs():
    """???????????"""
    log_structured('INFO', 'Logs endpoint accessed')
    # ???????????????????????
    return jsonify({
        'message': 'Logs are streamed to stdout/stderr',
        'format': 'JSON structured logs',
        'service': APP_NAME
    })

@app.route('/health')
def health():
    """Health check"""
    log_structured('DEBUG', 'Health check requested')
    return jsonify({
        'status': 'healthy',
        'service': APP_NAME,
        'version': APP_VERSION
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    
    log_structured('INFO', f'Starting {APP_NAME} v{APP_VERSION}',
                  port=port, environment=ENVIRONMENT)
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
