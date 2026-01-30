import os
import secrets

class Config:
    """Application configuration class with security best practices."""
    
    # Security - Generate random secret key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/monitoring')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    # Set to None to allow cookies to work across localhost and IP addresses
    SESSION_COOKIE_SAMESITE = None
    # Don't restrict to specific domain - allows localhost and IP address access
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_NAME = 'server_monitoring_session'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    # Allow CSRF to work across localhost and IP addresses
    WTF_CSRF_SSL_STRICT = False
    
    # Pagination
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # SNMP Polling
    SNMP_POLL_INTERVAL_MINUTES = int(os.environ.get('SNMP_POLL_INTERVAL', 5))


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    DEBUG = False
    # Keep False unless using HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
