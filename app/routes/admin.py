from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.validators import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Admin dashboard view - only accessible by admins
    return render_template('admin_dashboard.html')
