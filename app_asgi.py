#!/usr/bin/env python3
"""
FastAPI (ASGI) Application for Terraform and Kubernetes Practice
Gradual migration from Flask to FastAPI + Uvicorn
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from app import config

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
    # TODO: Add actual readiness checks (database, Redis, etc.)
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "framework": "FastAPI/ASGI"
    }


@app.get("/info")
async def info():
    """Application info endpoint - FastAPI version"""
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "framework": "FastAPI/ASGI",
        "timestamp": datetime.utcnow().isoformat()
    }


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
