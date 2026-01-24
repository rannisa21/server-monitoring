from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app.models.user import User, RoleEnum
from app import db
from app.validators import (
    admin_required, validate_required, validate_username, 
    validate_password, validate_role, ValidationError
)
import logging

logger = logging.getLogger(__name__)

# Blueprint harus dideklarasikan sebelum digunakan
user_management_bp = Blueprint('user_management', __name__)

@user_management_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'], endpoint='edit_user')
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent editing self to non-admin
    if user.id == current_user.id:
        flash('You cannot edit your own account from here.', 'warning')
        return redirect(url_for('user_management.user_management'))
    
    if request.method == 'POST':
        try:
            username = validate_username(request.form.get('username'))
            role = validate_role(request.form.get('role'))
            password = request.form.get('password', '').strip()
            
            # Check for duplicate username (excluding current user)
            existing = User.query.filter(
                User.username == username,
                User.id != user.id
            ).first()
            if existing:
                raise ValidationError('Username already exists', 'username')
            
            user.username = username
            user.role = RoleEnum(role)
            
            # Only update password if provided
            if password:
                validate_password(password, min_length=6)
                from app import bcrypt
                user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            db.session.commit()
            logger.info(f'User {user.id} ({user.username}) updated by {current_user.username}')
            flash('User berhasil diupdate!', 'success')
            return redirect(url_for('user_management.user_management'))
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error updating user {user_id}: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating user {user_id}: {e}', exc_info=True)
            flash('An error occurred while updating the user.', 'danger')
    
    return render_template('edit_user.html', user=user)

@user_management_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'], endpoint='delete_user')
@login_required
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent self-deletion
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('user_management.user_management'))
        
        # Prevent deleting the last admin
        if user.role == RoleEnum.admin:
            admin_count = User.query.filter_by(role=RoleEnum.admin).count()
            if admin_count <= 1:
                flash('Cannot delete the last admin user.', 'danger')
                return redirect(url_for('user_management.user_management'))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f'User {user_id} ({username}) deleted by {current_user.username}')
        flash('User berhasil dihapus!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting user {user_id}: {e}', exc_info=True)
        flash('An error occurred while deleting the user.', 'danger')
    
    return redirect(url_for('user_management.user_management'))


@user_management_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def user_management():
    if request.method == 'POST':
        try:
            username = validate_username(request.form.get('username'))
            password = validate_password(request.form.get('password'), min_length=6)
            role = validate_role(request.form.get('role'))
            
            # Check for duplicate username
            if User.query.filter_by(username=username).first():
                raise ValidationError('Username sudah terdaftar!', 'username')
            
            from app import bcrypt
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, password_hash=password_hash, role=RoleEnum(role))
            db.session.add(user)
            db.session.commit()
            
            logger.info(f'User {user.id} ({user.username}) created by {current_user.username}')
            flash('User berhasil ditambahkan!', 'success')
            return redirect(url_for('user_management.user_management'))
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error adding user: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding user: {e}', exc_info=True)
            flash('An error occurred while adding the user.', 'danger')
    
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
        
        # Search parameter
        search_query = request.args.get('search', '').strip()
        
        # Filter parameters
        role_filter = request.args.get('role', '')
        
        # Sort parameters
        sort_by = request.args.get('sort', 'username')
        sort_order = request.args.get('order', 'asc')
        
        # Build query
        query = User.query
        
        # Apply search
        if search_query:
            query = query.filter(User.username.ilike(f'%{search_query}%'))
        
        # Apply filters
        if role_filter:
            query = query.filter(User.role == RoleEnum(role_filter))
        
        # Apply sorting
        if sort_by == 'username':
            sort_column = User.username
        elif sort_by == 'role':
            sort_column = User.role
        else:
            sort_column = User.username
            
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        return render_template(
            'user_management.html',
            users=users,
            pagination=pagination,
            search_query=search_query,
            role_filter=role_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        logger.error(f'Error loading users: {e}', exc_info=True)
        flash('An error occurred while loading users.', 'danger')
        return render_template('user_management.html', users=[], pagination=None,
                               search_query='', role_filter='', sort_by='username', sort_order='asc')
