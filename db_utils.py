#!/usr/bin/env python3
"""
Database Utilities Module
Handles database connection pool and context manager
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import logging
import time
import metrics
import config

logger = logging.getLogger(__name__)

# Database Connection Pool
db_pool = None


def initialize_db_pool():
    """Initialize database connection pool"""
    global db_pool
    
    # Use config module for database settings
    if not config.Config.is_database_configured():
        logger.info("Database credentials not set. Continuing without database.")
        return None
    
    try:
        db_host = config.Config.DATABASE_HOST
        db_port = config.Config.DATABASE_PORT
        db_name = config.Config.DATABASE_NAME
        db_user = config.Config.DATABASE_USER
        db_password = config.Config.DATABASE_PASSWORD
        
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
        return db_pool
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Continuing without database.")
        return None


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
            metrics.record_apm_operation(operation, duration_ms, success=True)
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


def get_pool():
    """Get database pool (for sharing with auth module)"""
    return db_pool
