
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.server import Server, Component
from app.validators import (
    admin_required, validate_required, validate_ip_address, 
    validate_snmp_version, validate_brand, ValidationError
)
import logging

logger = logging.getLogger(__name__)

server_bp = Blueprint('server', __name__)

@server_bp.route('/admin/servers/edit/<int:server_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_server(server_id):
    server = Server.query.get_or_404(server_id)
    
    if request.method == 'POST':
        try:
            # Validate inputs
            name = validate_required(request.form.get('name'), 'Name')
            ip = validate_ip_address(request.form.get('ip'))
            brand = validate_brand(request.form.get('brand'))
            snmp_version = validate_snmp_version(request.form.get('snmp_version'))
            
            # SNMP v2c requires community string
            community = request.form.get('community', '').strip()
            if snmp_version == 'v2c' and not community:
                raise ValidationError('Community string is required for SNMP v2c', 'community')
            
            # SNMP v3 requires auth credentials
            snmp_auth_user = request.form.get('snmp_auth_user', '').strip()
            snmp_auth_pass = request.form.get('snmp_auth_pass', '').strip()
            if snmp_version == 'v3' and (not snmp_auth_user or not snmp_auth_pass):
                raise ValidationError('Auth user and password are required for SNMP v3', 'snmp_auth_user')
            
            # Update server
            server.name = name
            server.ip = ip
            server.community = community if snmp_version == 'v2c' else None
            server.brand = brand
            server.snmp_version = snmp_version
            server.snmp_auth_user = snmp_auth_user if snmp_version == 'v3' else None
            server.snmp_auth_pass = snmp_auth_pass if snmp_version == 'v3' else None
            server.snmp_priv_pass = request.form.get('snmp_priv_pass', '').strip() or None
            server.snmp_auth_proto = request.form.get('snmp_auth_proto', '').strip() or None
            server.snmp_priv_proto = request.form.get('snmp_priv_proto', '').strip() or None
            
            db.session.commit()
            logger.info(f'Server {server.id} ({server.name}) updated by {current_user.username}')
            flash('Server updated successfully!', 'success')
            return redirect(url_for('server.servers'))
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error updating server {server_id}: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating server {server_id}: {e}', exc_info=True)
            flash('An error occurred while updating the server.', 'danger')
    
    return render_template('edit_server.html', server=server)

@server_bp.route('/admin/servers/delete/<int:server_id>', methods=['POST'])
@login_required
@admin_required
def delete_server(server_id):
    try:
        server = Server.query.get_or_404(server_id)
        server_name = server.name
        db.session.delete(server)
        db.session.commit()
        logger.info(f'Server {server_id} ({server_name}) deleted by {current_user.username}')
        flash('Server deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting server {server_id}: {e}', exc_info=True)
        flash('An error occurred while deleting the server.', 'danger')
    
    return redirect(url_for('server.servers'))

@server_bp.route('/admin/servers')
@login_required
@admin_required
def servers():
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
        
        # Search parameter
        search_query = request.args.get('search', '').strip()
        
        # Filter parameters
        brand_filter = request.args.get('brand', '')
        snmp_filter = request.args.get('snmp_version', '')
        
        # Sort parameters
        sort_by = request.args.get('sort', 'name')
        sort_order = request.args.get('order', 'asc')
        
        # Build query
        query = Server.query
        
        # Apply search
        if search_query:
            query = query.filter(
                db.or_(
                    Server.name.ilike(f'%{search_query}%'),
                    Server.ip.ilike(f'%{search_query}%')
                )
            )
        
        # Apply filters
        if brand_filter:
            query = query.filter(Server.brand == brand_filter)
        if snmp_filter:
            query = query.filter(Server.snmp_version == snmp_filter)
        
        # Apply sorting
        sort_column = getattr(Server, sort_by, Server.name)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        servers = pagination.items
        
        # Get unique brands for filter dropdown
        brands = db.session.query(Server.brand).distinct().all()
        brands = [b[0] for b in brands]
        
        return render_template(
            'servers.html',
            servers=servers,
            pagination=pagination,
            search_query=search_query,
            brand_filter=brand_filter,
            snmp_filter=snmp_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            brands=brands
        )
    except Exception as e:
        logger.error(f'Error loading servers: {e}', exc_info=True)
        flash('An error occurred while loading servers.', 'danger')
        return render_template('servers.html', servers=[], pagination=None, 
                               search_query='', brand_filter='', snmp_filter='',
                               sort_by='name', sort_order='asc', brands=[])

@server_bp.route('/admin/servers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_server():
    if request.method == 'POST':
        try:
            # Validate inputs
            name = validate_required(request.form.get('name'), 'Name')
            ip = validate_ip_address(request.form.get('ip'))
            brand = validate_brand(request.form.get('brand'))
            snmp_version = validate_snmp_version(request.form.get('snmp_version'))
            
            # Check for duplicate IP
            existing_server = Server.query.filter_by(ip=ip).first()
            if existing_server:
                raise ValidationError(f'A server with IP {ip} already exists', 'ip')
            
            # SNMP v2c requires community string
            community = request.form.get('community', '').strip()
            if snmp_version == 'v2c' and not community:
                raise ValidationError('Community string is required for SNMP v2c', 'community')
            
            # SNMP v3 requires auth credentials
            snmp_auth_user = request.form.get('snmp_auth_user', '').strip()
            snmp_auth_pass = request.form.get('snmp_auth_pass', '').strip()
            if snmp_version == 'v3' and (not snmp_auth_user or not snmp_auth_pass):
                raise ValidationError('Auth user and password are required for SNMP v3', 'snmp_auth_user')
            
            server = Server(
                name=name,
                ip=ip,
                community=community if snmp_version == 'v2c' else None,
                brand=brand,
                snmp_version=snmp_version,
                snmp_auth_user=snmp_auth_user if snmp_version == 'v3' else None,
                snmp_auth_pass=snmp_auth_pass if snmp_version == 'v3' else None,
                snmp_priv_pass=request.form.get('snmp_priv_pass', '').strip() or None,
                snmp_auth_proto=request.form.get('snmp_auth_proto', '').strip() or None,
                snmp_priv_proto=request.form.get('snmp_priv_proto', '').strip() or None
            )
            db.session.add(server)
            db.session.commit()
            
            logger.info(f'Server {server.id} ({server.name}) created by {current_user.username}')
            flash('Server added successfully!', 'success')
            return redirect(url_for('server.servers'))
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error adding server: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding server: {e}', exc_info=True)
            flash('An error occurred while adding the server.', 'danger')
    
    return render_template('add_server.html')
