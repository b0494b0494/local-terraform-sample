#!/usr/bin/env python3
"""
FastAPI (ASGI) Application for Terraform and Kubernetes Practice
Gradual migration from Flask to FastAPI + Uvicorn
"""
from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Optional

from app import config, database, cache

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
async def root():
    """Root endpoint - FastAPI version"""
    logger.info("GET / - FastAPI endpoint")
    return {
        "message": "Hello from FastAPI App!",
        "status": "running",
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "framework": "FastAPI/ASGI"
    }


@app.get("/health")
async def health():
    """Health check endpoint - FastAPI version"""
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
