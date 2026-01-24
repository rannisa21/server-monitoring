"""Custom validators for form validation."""
import re
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_required(value, field_name):
    """Validate that a field is not empty."""
    if not value or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f'{field_name} is required', field_name)
    return value.strip() if isinstance(value, str) else value


def validate_ip_address(ip):
    """Validate IP address format."""
    if not ip:
        raise ValidationError('IP address is required', 'ip')
    
    # Simple IPv4 validation
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        raise ValidationError('Invalid IP address format', 'ip')
    
    # Check each octet is 0-255
    octets = ip.split('.')
    for octet in octets:
        if not 0 <= int(octet) <= 255:
            raise ValidationError('Invalid IP address: octets must be 0-255', 'ip')
    
    return ip


def validate_oid(oid):
    """Validate SNMP OID format."""
    if not oid:
        raise ValidationError('OID is required', 'oid')
    
    # OID should start with a dot or number and contain only dots and numbers
    pattern = r'^\.?(\d+\.)*\d+$'
    if not re.match(pattern, oid.strip()):
        raise ValidationError('Invalid OID format (e.g., 1.3.6.1.2.1.1.1.0)', 'oid')
    
    return oid.strip()


def validate_username(username):
    """Validate username format."""
    if not username:
        raise ValidationError('Username is required', 'username')
    
    username = username.strip()
    if len(username) < 3:
        raise ValidationError('Username must be at least 3 characters', 'username')
    if len(username) > 64:
        raise ValidationError('Username must be at most 64 characters', 'username')
    
    # Allow alphanumeric and underscore
    pattern = r'^[a-zA-Z0-9_]+$'
    if not re.match(pattern, username):
        raise ValidationError('Username can only contain letters, numbers, and underscores', 'username')
    
    return username


def validate_password(password, min_length=8):
    """Validate password strength."""
    if not password:
        raise ValidationError('Password is required', 'password')
    
    if len(password) < min_length:
        raise ValidationError(f'Password must be at least {min_length} characters', 'password')
    
    return password


def validate_snmp_version(version):
    """Validate SNMP version."""
    if version not in ('v2c', 'v3'):
        raise ValidationError('SNMP version must be v2c or v3', 'snmp_version')
    return version


def validate_category(category):
    """Validate component category."""
    valid_categories = ('fan', 'PSU', 'harddisk', 'suhu')
    if category not in valid_categories:
        raise ValidationError(f'Category must be one of: {", ".join(valid_categories)}', 'category')
    return category


def validate_brand(brand):
    """Validate server brand."""
    valid_brands = ('HPE', 'Dell', 'supermicro', 'custom')
    if brand not in valid_brands:
        raise ValidationError(f'Brand must be one of: {", ".join(valid_brands)}', 'brand')
    return brand


def validate_role(role):
    """Validate user role."""
    valid_roles = ('admin', 'user')
    if role not in valid_roles:
        raise ValidationError(f'Role must be one of: {", ".join(valid_roles)}', 'role')
    return role


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role.value != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def validate_month_year(month, year):
    """Validate month and year for reports."""
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        raise ValidationError('Invalid month or year format')
    
    if not 1 <= month <= 12:
        raise ValidationError('Month must be between 1 and 12', 'month')
    if not 2000 <= year <= 2100:
        raise ValidationError('Year must be between 2000 and 2100', 'year')
    
    return month, year
