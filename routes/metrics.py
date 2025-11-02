"""
Metrics and observability endpoints
"""
from flask import Blueprint, jsonify, request, g
from typing import Tuple
from flask import Response
import logging

from app import metrics, config

logger = logging.getLogger(__name__)

APP_NAME = config.Config.APP_NAME

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/metrics')
def metrics_endpoint() -> Response:
    """Prometheus format metrics endpoint"""
    logger.debug("Metrics requested")
    output = metrics.get_prometheus_metrics(APP_NAME)
    return output, 200, {'Content-Type': 'text/plain; version=0.0.4'}


@metrics_bp.route('/traces', methods=['GET'])
def get_traces() -> Tuple[Response, int]:
    """Distributed traces endpoint (simplified)"""
    limit = request.args.get('limit', 50, type=int)
    trace_id = request.args.get('trace_id', None)
    
    traces = metrics.get_traces(limit=limit, trace_id=trace_id)
    
    return jsonify({
        'traces': traces,
        'total': len(metrics.get_traces())
    }), 200


@metrics_bp.route('/apm/stats', methods=['GET'])
def apm_stats() -> Tuple[Response, int]:
    """APM performance statistics endpoint"""
    stats = metrics.get_apm_stats()
    return jsonify(stats), 200
