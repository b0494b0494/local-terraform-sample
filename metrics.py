#!/usr/bin/env python3
"""
Metrics and Observability Module
Handles Prometheus metrics, distributed tracing, and APM data
"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import time
import uuid


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


def generate_trace_ids() -> Dict[str, str]:
    """Generate trace and span IDs for distributed tracing
    
    Returns:
        Dict[str, str]: Dictionary with 'trace_id' and 'span_id'
    """
    return {
        'trace_id': uuid.uuid4().hex[:16],  # 16-char trace ID
        'span_id': uuid.uuid4().hex[:8]     # 8-char span ID
    }


def record_http_request(path: str, method: str, status: int, duration: float, user: Optional[str] = None) -> None:
    """Record HTTP request metrics
    
    Args:
        path: Request path
        method: HTTP method
        status: HTTP status code
        duration: Request duration in seconds
        user: Optional user identifier
    """
    # HTTP requests total (by path and status)
    _metrics['http_requests_total'][path][status] += 1
    
    # Request duration
    _metrics['http_request_duration_seconds'].append({
        'path': path,
        'method': method,
        'duration': duration,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Keep only last 100 entries
    if len(_metrics['http_request_duration_seconds']) > 100:
        _metrics['http_request_duration_seconds'] = _metrics['http_request_duration_seconds'][-100:]


def create_trace_span(trace_id, span_id, operation_name, duration_ms, status_code, method, path, user_agent, service_name='sample-app', user=None):
    """Create a trace span"""
    span = {
        'trace_id': trace_id,
        'span_id': span_id,
        'parent_span_id': None,  # Root span
        'operation_name': operation_name,
        'service_name': service_name,
        'start_time': datetime.utcnow().isoformat(),
        'duration_ms': duration_ms,
        'status_code': status_code,
        'attributes': {
            'http.method': method,
            'http.path': path,
            'http.status_code': status_code,
            'http.user_agent': user_agent or 'unknown',
        }
    }
    
    # Add authentication info if available
    if user:
        span['attributes']['user'] = user
    
    _traces.append(span)
    
    # Keep only last MAX_TRACES
    if len(_traces) > _MAX_TRACES:
        _traces[:] = _traces[-_MAX_TRACES:]
    
    return span


def record_apm_operation(
    operation: str,
    duration_ms: float,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """Record APM metrics for an operation
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        success: Whether the operation succeeded
        error: Optional error message
    """
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


def increment_database_errors():
    """Increment database connection error counter"""
    _metrics['app_database_connection_errors_total'] += 1


def increment_redis_errors():
    """Increment Redis connection error counter"""
    _metrics['app_redis_connection_errors_total'] += 1


def get_prometheus_metrics(app_name):
    """Format metrics in Prometheus text format"""
    output = []
    
    # HTTP requests total (Prometheus format)
    for path, status_counts in _metrics['http_requests_total'].items():
        for status, count in status_counts.items():
            output.append(
                f'http_requests_total{{path="{path}",status="{status}",service="{app_name}"}} {count}'
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
                f'http_request_duration_seconds_bucket{{le="{le}",service="{app_name}"}} {count}'
            )
        
        # Summary statistics
        avg_duration = sum(durations) / len(durations) if durations else 0
        output.append(f'http_request_duration_seconds_avg{{service="{app_name}"}} {avg_duration}')
        output.append(f'http_request_duration_seconds_count{{service="{app_name}"}} {len(durations)}')
    
    # Database connection errors
    output.append(
        f'app_database_connection_errors_total{{service="{app_name}"}} {_metrics["app_database_connection_errors_total"]}'
    )
    
    # Redis connection errors
    output.append(
        f'app_redis_connection_errors_total{{service="{app_name}"}} {_metrics["app_redis_connection_errors_total"]}'
    )
    
    return '\n'.join(output) + '\n'


def get_traces(limit=None, trace_id=None):
    """Get stored traces"""
    traces = _traces
    
    if trace_id:
        traces = [t for t in traces if t.get('trace_id') == trace_id]
    
    if limit:
        traces = traces[-limit:]
    
    return list(reversed(traces))  # Most recent first


def get_apm_stats() -> Dict[str, Any]:
    """Get APM performance statistics
    
    Returns:
        Dict[str, Any]: APM statistics dictionary
    """
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
    
    return {
        'operation_stats': stats_summary,
        'slow_operations': _apm_data['slow_operations'][-10:],  # Last 10 slow operations
        'recent_errors': _apm_data['error_operations'][-10:],  # Last 10 errors
        'summary': {
            'total_operations': sum(s['count'] for s in _apm_data['operation_stats'].values()),
            'total_errors': sum(s['errors'] for s in _apm_data['operation_stats'].values()),
            'total_slow_operations': len(_apm_data['slow_operations'])
        }
    }
