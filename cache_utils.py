#!/usr/bin/env python3
"""
Cache Utilities Module
Handles Redis connection and caching functionality
"""
import redis
from functools import wraps
from typing import Optional, Dict, Any, Callable
from flask import request, jsonify, Response
import logging
import config

logger = logging.getLogger(__name__)

# Redis Connection Configuration (from config module)
REDIS_HOST: str = config.Config.REDIS_HOST
REDIS_PORT: int = config.Config.REDIS_PORT
REDIS_TTL: int = config.Config.REDIS_TTL

# Redis Client Initialization
redis_client: Optional[redis.Redis] = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    # Test connection
    redis_client.ping()
    logger.info(f"Redis connected to {REDIS_HOST}:{REDIS_PORT}")
except (redis.ConnectionError, redis.TimeoutError) as e:
    logger.warning(f"Redis connection failed: {e}. Continuing without cache.")
    redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance
    
    Returns:
        Optional[redis.Redis]: Redis client if connected, None otherwise
    """
    return redis_client


def cache_response(ttl: int = REDIS_TTL) -> Callable:
    """Decorator to cache Flask route responses
    
    Args:
        ttl: Time to live for cached responses in seconds
        
    Returns:
        Callable: Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Response:
            # Skip caching if Redis is not available
            if redis_client is None:
                return f(*args, **kwargs)
            
            # Generate cache key from request
            cache_key = f"cache:{request.path}:{str(sorted(request.args.items()))}"
            
            try:
                # Try to get cached response
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return jsonify(eval(cached)), 200
                
                # Cache miss - execute function
                logger.debug(f"Cache miss: {cache_key}")
                response = f(*args, **kwargs)
                
                # Cache the response (only if status code is 200)
                if isinstance(response, tuple) and len(response) == 2:
                    status_code = response[1]
                    data = response[0]
                    
                    if status_code == 200 and isinstance(data, dict):
                        # Cache JSON responses
                        try:
                            redis_client.setex(
                                cache_key,
                                ttl,
                                str(data)
                            )
                            logger.debug(f"Cached response: {cache_key} (TTL: {ttl}s)")
                        except Exception as e:
                            logger.warning(f"Failed to cache response: {e}")
                
                return response
                
            except Exception as e:
                logger.error(f"Cache error: {e}")
                # On error, just execute function without caching
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def clear_cache():
    """Clear all cache entries"""
    if redis_client is None:
        return False
    
    try:
        # Flush all keys (use with caution in production)
        redis_client.flushdb()
        logger.info("Cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return False


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics
    
    Returns:
        Dict[str, Any]: Cache statistics dictionary
    """
    if redis_client is None:
        return {
            'status': 'not_configured',
            'message': 'Redis not configured'
        }
    
    try:
        info = redis_client.info()
        return {
            'status': 'connected',
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'keys': redis_client.dbsize(),
            'hit_rate': round(
                info.get('keyspace_hits', 0) / 
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 
                2
            )
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
