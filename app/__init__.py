from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

import os
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def setup_logging(app):
    """Configure application logging."""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/server_monitoring.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.setLevel(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.info('Server Monitoring application starting...')


def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize logging
    setup_logging(app)
    
    # Initialize CORS with security settings
    CORS(app, resources={r"/api/*": {"origins": os.environ.get('CORS_ORIGINS', '*')}})

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = 'Please log in to access this page.'
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Register error handlers
    register_error_handlers(app)

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.user import user_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.server import server_bp
    from app.routes.component import component_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(dashboard_bp)
    from app.routes.report import report_bp
    from app.routes.user_management import user_management_bp
    app.register_blueprint(server_bp)
    app.register_blueprint(component_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(user_management_bp)

    from app.scheduler.monitor import start_scheduler
    if os.environ.get('ENABLE_SCHEDULER', 'true').lower() == 'true':
        start_scheduler(app)
    
    app.logger.info('Application initialized successfully')
    return app


def register_error_handlers(app):
    """Register error handlers for the application."""
    from flask import render_template, jsonify, request, flash, redirect, url_for
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'Bad request: {error}')
        if request.is_json:
            return jsonify({'error': 'Bad request', 'message': str(error)}), 400
        flash('Bad request. Please check your input.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning(f'Forbidden access attempt: {error}')
        if request.is_json:
            return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
        flash('You do not have permission to access this resource.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f'Page not found: {request.url}')
        if request.is_json:
            return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
        flash('The requested page was not found.', 'warning')
        return redirect(url_for('dashboard.dashboard'))
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}', exc_info=True)
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
        flash('An unexpected error occurred. Please try again later.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
