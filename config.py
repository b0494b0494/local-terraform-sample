#!/usr/bin/env python3
"""
Configuration Module
Handles environment variable loading and validation
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """Application configuration from environment variables"""
    
    # Application settings
    APP_NAME: str = "sample-app"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"
    PORT: int = 8080
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database settings
    DATABASE_HOST: Optional[str] = None
    DATABASE_PORT: int = 5432
    DATABASE_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_TTL: int = 300  # Default 5 minutes
    
    # JWT settings
    JWT_SECRET: Optional[str] = None
    JWT_EXPIRATION_HOURS: int = 24
    
    # Security settings
    RATE_LIMIT_ENABLED: bool = True
    
    @classmethod
    def load(cls) -> None:
        """Load configuration from environment variables"""
        # Application settings
        cls.APP_NAME = cls._get_env('APP_NAME', cls.APP_NAME)
        cls.APP_VERSION = cls._get_env('APP_VERSION', cls.APP_VERSION)
        cls.ENVIRONMENT = cls._get_env('ENVIRONMENT', cls.ENVIRONMENT)
        cls.PORT = cls._get_env_int('PORT', cls.PORT)
        cls.DEBUG = cls._get_env_bool('DEBUG', cls.DEBUG)
        cls.LOG_LEVEL = cls._get_env('LOG_LEVEL', cls.LOG_LEVEL).upper()
        
        # Database settings
        cls.DATABASE_HOST = cls._get_env('DATABASE_HOST', None)
        cls.DATABASE_PORT = cls._get_env_int('DATABASE_PORT', cls.DATABASE_PORT)
        cls.DATABASE_NAME = cls._get_env('DATABASE_NAME', None)
        cls.DATABASE_USER = cls._get_env('DATABASE_USER', None)
        cls.DATABASE_PASSWORD = cls._get_env('DATABASE_PASSWORD', None)
        
        # Redis settings
        cls.REDIS_HOST = cls._get_env('REDIS_HOST', cls.REDIS_HOST)
        cls.REDIS_PORT = cls._get_env_int('REDIS_PORT', cls.REDIS_PORT)
        cls.REDIS_TTL = cls._get_env_int('REDIS_TTL', cls.REDIS_TTL)
        
        # JWT settings
        cls.JWT_SECRET = cls._get_env('JWT_SECRET', None)
        cls.JWT_EXPIRATION_HOURS = cls._get_env_int('JWT_EXPIRATION_HOURS', cls.JWT_EXPIRATION_HOURS)
        
        # Security settings
        cls.RATE_LIMIT_ENABLED = cls._get_env_bool('RATE_LIMIT_ENABLED', cls.RATE_LIMIT_ENABLED)
        
        # Validate configuration
        cls._validate()
        
        logger.info(f"Configuration loaded: environment={cls.ENVIRONMENT}, port={cls.PORT}, debug={cls.DEBUG}")
    
    @classmethod
    def _get_env(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable as string
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Optional[str]: Environment variable value or default
        """
        value = os.getenv(key, default)
        return value
    
    @classmethod
    def _get_env_int(cls, key: str, default: int) -> int:
        """Get environment variable as integer
        
        Args:
            key: Environment variable name
            default: Default value if not set or invalid
            
        Returns:
            int: Environment variable value as integer or default
        """
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
            return default
    
    @classmethod
    def _get_env_bool(cls, key: str, default: bool) -> bool:
        """Get environment variable as boolean
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            bool: Environment variable value as boolean or default
        """
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @classmethod
    def _validate(cls) -> None:
        """Validate configuration values
        
        Raises:
            ValueError: If configuration validation fails
        """
        errors = []
        
        # Validate PORT
        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append(f"Invalid PORT: {cls.PORT} (must be 1-65535)")
        
        # Validate ENVIRONMENT
        valid_environments = ['local', 'development', 'staging', 'production']
        if cls.ENVIRONMENT not in valid_environments:
            errors.append(f"Invalid ENVIRONMENT: {cls.ENVIRONMENT} (must be one of {valid_environments})")
        
        # Validate LOG_LEVEL
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL not in valid_log_levels:
            errors.append(f"Invalid LOG_LEVEL: {cls.LOG_LEVEL} (must be one of {valid_log_levels})")
        
        # Validate database configuration (if any database setting is provided)
        db_settings = [
            cls.DATABASE_HOST,
            cls.DATABASE_NAME,
            cls.DATABASE_USER,
            cls.DATABASE_PASSWORD
        ]
        if any(db_settings) and not all(db_settings):
            errors.append("Database configuration incomplete: all of DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD must be set together")
        
        # Validate DATABASE_PORT
        if cls.DATABASE_PORT < 1 or cls.DATABASE_PORT > 65535:
            errors.append(f"Invalid DATABASE_PORT: {cls.DATABASE_PORT} (must be 1-65535)")
        
        # Validate REDIS_PORT
        if cls.REDIS_PORT < 1 or cls.REDIS_PORT > 65535:
            errors.append(f"Invalid REDIS_PORT: {cls.REDIS_PORT} (must be 1-65535)")
        
        # Validate REDIS_TTL
        if cls.REDIS_TTL < 0:
            errors.append(f"Invalid REDIS_TTL: {cls.REDIS_TTL} (must be >= 0)")
        
        # Validate JWT settings
        if cls.JWT_EXPIRATION_HOURS < 1:
            errors.append(f"Invalid JWT_EXPIRATION_HOURS: {cls.JWT_EXPIRATION_HOURS} (must be >= 1)")
        
        # Security warnings for production
        if cls.ENVIRONMENT == 'production':
            if cls.DEBUG:
                logger.warning("??  DEBUG mode is enabled in production environment!")
            if not cls.JWT_SECRET:
                logger.warning("??  JWT_SECRET is not set in production environment!")
            if cls.JWT_SECRET and len(cls.JWT_SECRET) < 32:
                logger.warning("??  JWT_SECRET is too short (recommended: at least 32 characters)")
        
        # Log errors and raise exception if critical
        if errors:
            error_msg = "Configuration validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @classmethod
    def is_database_configured(cls) -> bool:
        """Check if database is fully configured"""
        return all([
            cls.DATABASE_HOST,
            cls.DATABASE_NAME,
            cls.DATABASE_USER,
            cls.DATABASE_PASSWORD
        ])
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary (excluding sensitive data)"""
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'environment': cls.ENVIRONMENT,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'log_level': cls.LOG_LEVEL,
            'database_configured': cls.is_database_configured(),
            'database_host': cls.DATABASE_HOST if cls.DATABASE_HOST else None,
            'database_port': cls.DATABASE_PORT,
            'database_name': cls.DATABASE_NAME if cls.DATABASE_NAME else None,
            'redis_host': cls.REDIS_HOST,
            'redis_port': cls.REDIS_PORT,
            'redis_ttl': cls.REDIS_TTL,
            'jwt_expiration_hours': cls.JWT_EXPIRATION_HOURS,
            'rate_limit_enabled': cls.RATE_LIMIT_ENABLED,
        }


# Load configuration on module import
Config.load()
