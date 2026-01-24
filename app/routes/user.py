from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/dashboard')
@login_required
def user_dashboard():
    # Placeholder: user dashboard view
    return render_template('user_dashboard.html')
