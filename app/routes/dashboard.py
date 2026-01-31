from flask import Blueprint, render_template, request, current_app, send_file, flash, session
from flask_login import login_required, current_user
from app.models.server import Server, Component
from app.models.metric import Metric
from app import db
from sqlalchemy import desc, asc, extract
from datetime import datetime
from io import BytesIO
import pandas as pd
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    try:
        # Get filter parameters
        server_filter = request.args.getlist('server_id', type=int)  # Multiple server filter
        category_filter = request.args.get('category', '')
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '').strip()
        
        # Get view type (table or card), default to table
        view_type = request.args.get('view', session.get('dashboard_view', 'table'))
        session['dashboard_view'] = view_type
        
        # Get sort parameters
        sort_by = request.args.get('sort', 'server')  # Default sort by server
        sort_order = request.args.get('order', 'asc')  # Default ascending
        
        # Get all servers for filter dropdown
        all_servers = Server.query.order_by(Server.name).all()
        
        # Build servers query
        if server_filter:
            servers = Server.query.filter(Server.id.in_(server_filter)).all()
        else:
            servers = all_servers  # Show all by default
        
        # Build data for dashboard with latest metrics
        dashboard_data = []
        for server in servers:
            for component in server.components:
                metric = Metric.query.filter_by(
                    server_id=server.id,
                    component_id=component.id
                ).order_by(desc(Metric.timestamp)).first()
                
                # Apply category filter
                if category_filter and component.category != category_filter:
                    continue
                
                # Apply status filter
                if status_filter:
                    if status_filter == 'no_data' and metric:
                        continue
                    elif status_filter != 'no_data' and (not metric or metric.status != status_filter):
                        continue
                
                # Apply search filter
                if search_query:
                    search_lower = search_query.lower()
                    if not (search_lower in server.name.lower() or 
                            search_lower in component.name.lower() or
                            search_lower in server.ip.lower() or
                            search_lower in component.oid.lower()):
                        continue
                
                dashboard_data.append({
                    'server': server,
                    'component': component,
                    'metric': metric
                })
        
        # Sort data
        def get_sort_key(item):
            if sort_by == 'server':
                return item['server'].name.lower()
            elif sort_by == 'component':
                return item['component'].name.lower()
            elif sort_by == 'category':
                return item['component'].category.lower()
            elif sort_by == 'status':
                return item['metric'].status if item['metric'] else 'zzz'
            elif sort_by == 'timestamp':
                return item['metric'].timestamp if item['metric'] else datetime.min
            return item['server'].name.lower()
        
        dashboard_data.sort(key=get_sort_key, reverse=(sort_order == 'desc'))
        
        # Get unique categories for filter
        categories = db.session.query(Component.category).distinct().all()
        categories = [c[0] for c in categories]
        
        total_items = len(dashboard_data)
        
        # For card view, group by server
        card_data = {}
        if view_type == 'card':
            for item in dashboard_data:
                server_id = item['server'].id
                if server_id not in card_data:
                    card_data[server_id] = {
                        'server': item['server'],
                        'components': []
                    }
                card_data[server_id]['components'].append(item)
        
        logger.debug(f'Dashboard loaded: {total_items} items, view: {view_type}')
        
        return render_template(
            'dashboard.html',
            dashboard_data=dashboard_data,
            card_data=card_data,
            view_type=view_type,
            servers=all_servers,
            server_filter=server_filter,
            category_filter=category_filter,
            status_filter=status_filter,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            categories=categories,
            total_items=total_items
        )
        
    except Exception as e:
        logger.error(f'Dashboard error: {e}', exc_info=True)
        return render_template(
            'dashboard.html',
            dashboard_data=[],
            card_data={},
            view_type='table',
            servers=[],
            server_filter=[],
            category_filter='',
            status_filter='',
            search_query='',
            sort_by='server',
            sort_order='asc',
            categories=[],
            total_items=0,
            error='Failed to load dashboard data'
        )


@dashboard_bp.route('/api/data')
@login_required
def api_dashboard_data():
    """API endpoint untuk mendapatkan data dashboard terbaru (JSON)."""
    try:
        from flask import jsonify
        
        # Get filter parameters
        server_filter = request.args.getlist('server_id', type=int)
        category_filter = request.args.get('category', '')
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'server')
        sort_order = request.args.get('order', 'asc')
        
        # Get all servers
        all_servers = Server.query.order_by(Server.name).all()
        
        # Build servers query
        if server_filter:
            servers = Server.query.filter(Server.id.in_(server_filter)).all()
        else:
            servers = all_servers
        
        # Build data for dashboard with latest metrics
        dashboard_data = []
        for server in servers:
            for component in server.components:
                metric = Metric.query.filter_by(
                    server_id=server.id,
                    component_id=component.id
                ).order_by(desc(Metric.timestamp)).first()
                
                # Apply category filter
                if category_filter and component.category != category_filter:
                    continue
                
                # Apply status filter
                if status_filter:
                    if status_filter == 'no_data' and metric:
                        continue
                    elif status_filter != 'no_data' and (not metric or metric.status != status_filter):
                        continue
                
                # Apply search filter
                if search_query:
                    search_lower = search_query.lower()
                    if not (search_lower in server.name.lower() or 
                            search_lower in component.name.lower() or
                            search_lower in server.ip.lower() or
                            search_lower in component.oid.lower()):
                        continue
                
                dashboard_data.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'server_ip': server.ip,
                    'server_brand': server.brand,
                    'component_id': component.id,
                    'component_name': component.name,
                    'component_oid': component.oid,
                    'category': component.category,
                    'metric_value': metric.value if metric else None,
                    'metric_status': metric.status if metric else None,
                    'metric_timestamp': metric.timestamp.strftime('%Y-%m-%d %H:%M:%S') if metric else None
                })
        
        # Sort data
        def get_sort_key(item):
            if sort_by == 'server':
                return item['server_name'].lower()
            elif sort_by == 'component':
                return item['component_name'].lower()
            elif sort_by == 'category':
                return item['category'].lower()
            elif sort_by == 'status':
                return item['metric_status'] if item['metric_status'] else 'zzz'
            elif sort_by == 'timestamp':
                return item['metric_timestamp'] if item['metric_timestamp'] else ''
            return item['server_name'].lower()
        
        dashboard_data.sort(key=get_sort_key, reverse=(sort_order == 'desc'))
        
        # Get last update time from newest metric
        latest_metric = Metric.query.order_by(desc(Metric.timestamp)).first()
        last_update = latest_metric.timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest_metric else None
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'total_items': len(dashboard_data),
            'last_update': last_update
        })
        
    except Exception as e:
        logger.error(f'API Dashboard error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'total_items': 0
        }), 500


@dashboard_bp.route('/download-report', methods=['POST'])
@login_required
def download_report():
    """Download Excel report for selected month/year."""
    try:
        month = request.form.get('month', type=int)
        year = request.form.get('year', type=int)
        
        if not month or not year:
            flash('Pilih bulan dan tahun terlebih dahulu.', 'danger')
            return render_template('dashboard.html', dashboard_data=[], servers=[], 
                                   server_filter=[], category_filter='', status_filter='',
                                   search_query='', sort_by='server', sort_order='asc',
                                   categories=[], total_items=0)
        
        if month < 1 or month > 12:
            flash('Bulan tidak valid.', 'danger')
            return render_template('dashboard.html', dashboard_data=[], servers=[],
                                   server_filter=[], category_filter='', status_filter='',
                                   search_query='', sort_by='server', sort_order='asc',
                                   categories=[], total_items=0)
        
        # Query metrics for the specified month/year
        metrics = Metric.query.filter(
            extract('month', Metric.timestamp) == month,
            extract('year', Metric.timestamp) == year
        ).order_by(Metric.timestamp.desc()).all()
        
        if not metrics:
            flash(f'Tidak ada data untuk bulan {month:02d}/{year}.', 'warning')
            return render_template('dashboard.html', dashboard_data=[], servers=[],
                                   server_filter=[], category_filter='', status_filter='',
                                   search_query='', sort_by='server', sort_order='asc',
                                   categories=[], total_items=0)
        
        # Build report data dengan kolom sesuai permintaan
        data = []
        for i, m in enumerate(metrics):
            data.append({
                'Nomor': i + 1,
                'Nama Server': m.server_name,
                'IP Server': m.server_ip,
                'Merk': m.brand,
                'Kategori Komponen': m.category,
                'Nama Komponen': m.component_name,
                'OID': m.oid,
                'Value': m.value,
                'Status': m.status,
                'Timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Report']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                # Gunakan openpyxl get_column_letter untuk kolom lebih dari 26
                from openpyxl.utils import get_column_letter
                worksheet.column_dimensions[get_column_letter(idx + 1)].width = min(max_length, 50)
        
        output.seek(0)
        filename = f"laporan_monitoring_{year}_{month:02d}.xlsx"
        
        logger.info(f'Report downloaded from dashboard for {month:02d}/{year} by {current_user.username}: {len(metrics)} records')
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f'Error downloading report: {e}', exc_info=True)
        flash('Terjadi kesalahan saat mengunduh report.', 'danger')
        return render_template('dashboard.html', dashboard_data=[], servers=[],
                               server_filter=[], category_filter='', status_filter='',
                               search_query='', sort_by='server', sort_order='asc',
                               categories=[], total_items=0)
