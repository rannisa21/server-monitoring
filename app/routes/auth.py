from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db, bcrypt, login_manager
from app.validators import validate_required, validate_username, ValidationError
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f'Error loading user {user_id}: {e}')
        return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            # Validate inputs
            if not username or not password:
                flash('Username and password are required.', 'danger')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and bcrypt.check_password_hash(user.password_hash, password):
                login_user(user)
                logger.info(f'User {username} logged in successfully')
                
                # Redirect to next page if available
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard.dashboard'))
            
            logger.warning(f'Failed login attempt for username: {username}')
            flash('Invalid username or password.', 'danger')
            
        except Exception as e:
            logger.error(f'Login error: {e}', exc_info=True)
            flash('An error occurred during login. Please try again.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f'User {username} logged out')
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
