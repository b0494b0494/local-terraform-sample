#!/usr/bin/env python3
"""
FastAPI (ASGI) Application for Terraform and Kubernetes Practice
Gradual migration from Flask to FastAPI + Uvicorn
"""
from fastapi import FastAPI, Request, status, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import logging
import time
from typing import Optional

from app import config, database, cache, metrics
from auth_pkg import users, jwt, api_keys, decorators

# Logging Configuration
logging.basicConfig(
    level=config.Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=config.Config.APP_NAME,
    version=config.Config.APP_VERSION,
    description="Sample Application for Terraform and Kubernetes Practice (FastAPI/ASGI)"
)

# Configuration
APP_NAME = config.Config.APP_NAME
APP_VERSION = config.Config.APP_VERSION
ENVIRONMENT = config.Config.ENVIRONMENT

# Initialize database pool
db_pool = database.initialize_db_pool()


@app.get("/")
async def root(request: Request):
    """Root endpoint - FastAPI version"""
    logger.info(f"GET / - FastAPI endpoint from {request.client.host if request.client else 'unknown'}")
    
    # Try to use cache decorator pattern
    cache_key = f"root:{request.url}"
    cached = False
    
    if cache_client:
        try:
            cached_data = cache_client.get(cache_key)
            if cached_data:
                import json
                data = json.loads(cached_data)
                data["cached"] = True
                return data
        except Exception as e:
            logger.debug(f"Cache read error: {e}")
    
    data = {
        "message": "Hello from FastAPI App!",
        "status": "running",
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "framework": "FastAPI/ASGI",
        "cached": cached
    }
    
    # Cache the response
    if cache_client:
        try:
            import json
            cache_client.setex(cache_key, 60, json.dumps(data))
        except Exception as e:
            logger.debug(f"Cache write error: {e}")
    
    return data


@app.get("/health")
async def health():
    """Health check endpoint - FastAPI version"""
    metrics.record_request_metric("GET", "/health", 200)
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "framework": "FastAPI/ASGI"
    }


@app.get("/ready")
async def ready():
    """Readiness check endpoint - FastAPI version"""
    # Check database connection if configured
    db_connected = False
    if database.db_pool:
        try:
            conn = database.get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT 1")
                    cur.close()
                    database.return_db_connection(conn)
                    db_connected = True
                    logger.debug("Database connection verified")
                except Exception as e:
                    logger.warning(f"Database check failed: {e}")
                    return JSONResponse(
                        status_code=503,
                        content={
                            "status": "not_ready",
                            "service": APP_NAME,
                            "reason": "database_check_failed",
                            "framework": "FastAPI/ASGI"
                        }
                    )
        except Exception as e:
            logger.warning(f"Database connection error: {e}")
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": db_connected,
        "framework": "FastAPI/ASGI"
    }


@app.get("/info")
async def info(request: Request):
    """Application info endpoint - FastAPI version"""
    info_data = config.Config.get_summary()
    info_data.update({
        "host": request.url.hostname,
        "remote_addr": request.client.host if request.client else None,
        "redis_connected": cache.redis_client is not None if cache.redis_client else False,
        "framework": "FastAPI/ASGI",
        "timestamp": datetime.utcnow().isoformat()
    })
    return info_data


@app.get("/db/status")
async def db_status():
    """Database status endpoint - FastAPI version"""
    if not database.db_pool:
        return {
            "status": "not_configured",
            "database": "not_configured",
            "framework": "FastAPI/ASGI"
        }
    
    try:
        conn = database.get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT version()")
                db_version = cur.fetchone()[0]
                cur.close()
                database.return_db_connection(conn)
                return {
                    "status": "connected",
                    "database": "postgresql",
                    "version": db_version,
                    "framework": "FastAPI/ASGI"
                }
            except Exception as e:
                logger.error(f"Database query error: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": str(e),
                        "framework": "FastAPI/ASGI"
                    }
                )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "message": "Could not get database connection",
                    "framework": "FastAPI/ASGI"
                }
            )
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": str(e),
                "framework": "FastAPI/ASGI"
            }
        )


@app.get("/cache/stats")
async def cache_stats():
    """Cache statistics endpoint - FastAPI version"""
    try:
        stats = cache.get_cache_stats()
        return {
            "status": "success",
            "stats": stats,
            "framework": "FastAPI/ASGI"
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "framework": "FastAPI/ASGI"
            }
        )


@app.post("/cache/clear")
async def cache_clear():
    """Clear cache endpoint - FastAPI version"""
    try:
        cleared = cache.clear_cache()
        return {
            "status": "success",
            "message": f"Cache cleared. Keys removed: {cleared}",
            "framework": "FastAPI/ASGI"
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "framework": "FastAPI/ASGI"
            }
        )


@app.post("/auth/login")
async def login(request: Request):
    """Login endpoint - FastAPI version"""
    try:
        body = await request.json()
        username = body.get("username", "")
        password = body.get("password", "")
        
        # Authenticate user
        user_data = users.authenticate_user(username, password)
        
        if user_data:
            # Generate JWT token
            token = jwt.create_jwt_token(username, roles=user_data["roles"])
            # Register API key
            api_key = api_keys.register_api_key(username, roles=user_data["roles"])
            
            return {
                "status": "success",
                "token": token,
                "api_key": api_key,
                "user": username,
                "roles": user_data["roles"],
                "expires_in": jwt.JWT_EXPIRATION_HOURS * 3600,
                "framework": "FastAPI/ASGI"
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/auth/validate")
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token - FastAPI version"""
    try:
        token = credentials.credentials
        payload = jwt.verify_jwt_token(token)
        
        if payload:
            return {
                "status": "valid",
                "user": payload.get("user") or payload.get("username"),
                "roles": payload.get("roles", []),
                "authenticated": True,
                "framework": "FastAPI/ASGI"
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token validation failed"
        )


@app.get("/auth/api-keys")
async def list_api_keys(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List API keys (admin only) - FastAPI version"""
    try:
        token = credentials.credentials
        payload = jwt.verify_jwt_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if user is admin
        user_roles = payload.get("roles", [])
        if "admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get all API keys
        all_keys = api_keys.API_KEYS.copy()
        if db_pool:
            # Also get from database if configured
            db_keys = api_keys.get_all_api_keys_from_db()
            if db_keys:
                all_keys.update(db_keys)
        
        # Format response
        keys_list = []
        for key, info in all_keys.items():
            keys_list.append({
                "user": info.get("user", "unknown"),
                "roles": info.get("roles", []),
                "created_at": info.get("created_at", ""),
                "key_preview": key[:8] + "..." if len(key) > 8 else key
            })
        
        return {
            "status": "success",
            "api_keys": keys_list,
            "total": len(keys_list),
            "framework": "FastAPI/ASGI"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API keys list error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api-key-test")
async def api_key_test(x_api_key: Optional[str] = Header(None)):
    """Test API key authentication - FastAPI version"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Verify API key
    key_info = api_keys.get_api_key_from_db(x_api_key) if db_pool else api_keys.API_KEYS.get(x_api_key)
    
    if key_info:
        # Update last used
        if db_pool:
            api_keys.update_api_key_last_used(x_api_key)
        
        return {
            "status": "success",
            "authenticated": True,
            "user": key_info.get("user"),
            "roles": key_info.get("roles", []),
            "message": "API key authentication successful",
            "framework": "FastAPI/ASGI"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint - FastAPI version"""
    try:
        metrics_text = metrics.get_prometheus_metrics(APP_NAME)
        from fastapi.responses import Response
        return Response(content=metrics_text, media_type="text/plain")
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/traces")
async def get_traces():
    """Distributed tracing data endpoint - FastAPI version"""
    try:
        traces_data = metrics.get_traces()
        return {
            "status": "success",
            "traces": traces_data,
            "framework": "FastAPI/ASGI"
        }
    except Exception as e:
        logger.error(f"Traces error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/apm/stats")
async def get_apm_stats():
    """APM performance statistics endpoint - FastAPI version"""
    try:
        apm_stats = metrics.get_apm_stats()
        return {
            "status": "success",
            "stats": apm_stats,
            "framework": "FastAPI/ASGI"
        }
    except Exception as e:
        logger.error(f"APM stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
            "framework": "FastAPI/ASGI"
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = config.Config.PORT
    logger.info(f"Starting FastAPI app on port {port} (environment: {ENVIRONMENT})")
    uvicorn.run(app, host="0.0.0.0", port=port)
