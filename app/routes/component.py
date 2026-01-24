from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.server import Server, Component
from app.validators import (
    admin_required, validate_required, validate_oid, 
    validate_category, ValidationError
)
import logging

logger = logging.getLogger(__name__)

component_bp = Blueprint('component', __name__)


@component_bp.route('/admin/components', methods=['GET'])
@login_required
@admin_required
def all_components():
    """Show all components from all servers."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
        
        # Get filter parameters
        server_filter = request.args.get('server_id', type=int)
        category_filter = request.args.get('category', '')
        search_query = request.args.get('search', '').strip()
        
        # Build query
        query = db.session.query(Component).join(Server)
        
        if server_filter:
            query = query.filter(Component.server_id == server_filter)
        if category_filter:
            query = query.filter(Component.category == category_filter)
        if search_query:
            query = query.filter(
                db.or_(
                    Component.name.ilike(f'%{search_query}%'),
                    Component.oid.ilike(f'%{search_query}%')
                )
            )
        
        query = query.order_by(Server.name, Component.name)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        components = pagination.items
        
        # Get all servers for filter dropdown
        servers = Server.query.order_by(Server.name).all()
        
        # Get unique categories for filter
        categories = db.session.query(Component.category).distinct().all()
        categories = [c[0] for c in categories]
        
        return render_template(
            'all_components.html',
            components=components,
            pagination=pagination,
            servers=servers,
            server_filter=server_filter,
            category_filter=category_filter,
            search_query=search_query,
            categories=categories
        )
    except Exception as e:
        logger.error(f'Error loading all components: {e}', exc_info=True)
        flash('An error occurred while loading components.', 'danger')
        return redirect(url_for('dashboard.dashboard'))


@component_bp.route('/admin/server/<int:server_id>/components', methods=['GET'])
@login_required
@admin_required
def components(server_id):
    try:
        server = Server.query.get_or_404(server_id)
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
        
        pagination = Component.query.filter_by(server_id=server_id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        components = pagination.items
        
        return render_template(
            'components.html',
            server=server,
            components=components,
            pagination=pagination
        )
    except Exception as e:
        logger.error(f'Error loading components for server {server_id}: {e}', exc_info=True)
        flash('An error occurred while loading components.', 'danger')
        return redirect(url_for('server.servers'))

@component_bp.route('/admin/server/<int:server_id>/components/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_component(server_id):
    server = Server.query.get_or_404(server_id)
    
    if request.method == 'POST':
        try:
            # Validate inputs
            name = validate_required(request.form.get('name'), 'Name')
            oid = validate_oid(request.form.get('oid'))
            category = validate_category(request.form.get('category'))
            
            # Check for duplicate OID on same server
            existing = Component.query.filter_by(server_id=server.id, oid=oid).first()
            if existing:
                raise ValidationError(f'A component with OID {oid} already exists on this server', 'oid')
            
            component = Component(
                name=name,
                oid=oid,
                category=category,
                brand=server.brand,
                server_id=server.id
            )
            db.session.add(component)
            db.session.commit()
            
            # Trigger polling SNMP after adding component
            try:
                from app.scheduler.monitor import poll_all_with_context
                poll_all_with_context(current_app._get_current_object())
                logger.info(f'SNMP polling triggered after adding component {component.id}')
            except Exception as poll_error:
                logger.warning(f'Failed to trigger SNMP polling: {poll_error}')
            
            logger.info(f'Component {component.id} ({component.name}) added to server {server.id} by {current_user.username}')
            flash('Component added successfully!', 'success')
            return redirect(url_for('component.components', server_id=server.id))
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error adding component: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding component to server {server_id}: {e}', exc_info=True)
            flash('An error occurred while adding the component.', 'danger')
    
    return render_template('add_component.html', server=server)

@component_bp.route('/admin/server/<int:server_id>/components/edit/<int:component_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_component(server_id, component_id):
    server = Server.query.get_or_404(server_id)
    component = Component.query.get_or_404(component_id)
    
    # Ensure component belongs to server
    if component.server_id != server_id:
        flash('Component does not belong to this server.', 'danger')
        return redirect(url_for('component.components', server_id=server_id))
    
    if request.method == 'POST':
        try:
            # Validate inputs
            name = validate_required(request.form.get('name'), 'Name')
            oid = validate_oid(request.form.get('oid'))
            category = validate_category(request.form.get('category'))
            
            # Check for duplicate OID on same server (excluding current component)
            existing = Component.query.filter(
                Component.server_id == server.id,
                Component.oid == oid,
                Component.id != component.id
            ).first()
            if existing:
                raise ValidationError(f'A component with OID {oid} already exists on this server', 'oid')
            
            component.name = name
            component.oid = oid
            component.category = category
            db.session.commit()
            
            logger.info(f'Component {component.id} ({component.name}) updated by {current_user.username}')
            flash('Component updated successfully!', 'success')
            return redirect(url_for('component.components', server_id=server.id))
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error updating component {component_id}: {e.message}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating component {component_id}: {e}', exc_info=True)
            flash('An error occurred while updating the component.', 'danger')
    
    return render_template('edit_component.html', server=server, component=component)

@component_bp.route('/admin/server/<int:server_id>/components/delete/<int:component_id>', methods=['POST'])
@login_required
@admin_required
def delete_component(server_id, component_id):
    try:
        component = Component.query.get_or_404(component_id)
        
        # Ensure component belongs to server
        if component.server_id != server_id:
            flash('Component does not belong to this server.', 'danger')
            return redirect(url_for('component.components', server_id=server_id))
        
        component_name = component.name
        db.session.delete(component)
        db.session.commit()
        
        logger.info(f'Component {component_id} ({component_name}) deleted by {current_user.username}')
        flash('Component deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting component {component_id}: {e}', exc_info=True)
        flash('An error occurred while deleting the component.', 'danger')
    
    return redirect(url_for('component.components', server_id=server_id))
