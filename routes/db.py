"""
Database endpoints
"""
from flask import Blueprint, jsonify, request
from typing import Tuple
from flask import Response
from psycopg2.extras import RealDictCursor
import logging

from app import database

logger = logging.getLogger(__name__)

# Get database utilities
get_db_connection = database.get_db_connection
return_db_connection = database.return_db_connection
DatabaseConnection = database.DatabaseConnection

db_bp = Blueprint('db', __name__)


@db_bp.route('/db/status')
def db_status() -> Tuple[Response, int]:
    """Database connection status"""
    if database.db_pool is None:
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


@db_bp.route('/db/query', methods=['POST'])
def db_query() -> Tuple[Response, int]:
    """Execute a simple database query (for testing)"""
    if database.db_pool is None:
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
