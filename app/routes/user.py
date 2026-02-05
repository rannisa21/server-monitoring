from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.user import User
from app import db
from app.validators import validate_username, validate_password, ValidationError
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/dashboard')
@login_required
def user_dashboard():
    # Placeholder: user dashboard view
    return render_template('user_dashboard.html')


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Allow users to edit their own profile (username and password)."""
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            
            if action == 'update_username':
                new_username = validate_username(request.form.get('username'))
                
                # Check for duplicate username
                existing = User.query.filter(
                    User.username == new_username,
                    User.id != current_user.id
                ).first()
                if existing:
                    raise ValidationError('Username sudah digunakan', 'username')
                
                old_username = current_user.username
                current_user.username = new_username
                db.session.commit()
                
                logger.info(f'User {current_user.id} changed username from {old_username} to {new_username}')
                flash('Username berhasil diubah!', 'success')
                
            elif action == 'update_password':
                current_password = request.form.get('current_password', '').strip()
                new_password = request.form.get('new_password', '').strip()
                confirm_password = request.form.get('confirm_password', '').strip()
                
                if not current_password:
                    raise ValidationError('Password saat ini harus diisi', 'current_password')
                
                # Verify current password
                from app import bcrypt
                if not bcrypt.check_password_hash(current_user.password_hash, current_password):
                    raise ValidationError('Password saat ini salah', 'current_password')
                
                # Validate new password
                validate_password(new_password)
                
                if new_password != confirm_password:
                    raise ValidationError('Password baru dan konfirmasi tidak sama', 'confirm_password')
                
                # Update password
                current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                
                logger.info(f'User {current_user.id} ({current_user.username}) changed password')
                flash('Password berhasil diubah!', 'success')
                
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error in profile update for user {current_user.id}: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating profile for user {current_user.id}: {e}', exc_info=True)
            flash('Terjadi kesalahan saat mengupdate profil.', 'danger')
    
    return render_template('profile.html')
