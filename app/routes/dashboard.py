from flask import Blueprint, render_template, request, current_app, send_file, flash, session
from flask_login import login_required, current_user
from app.models.server import Server, Component
from app.models.metric import Metric
from app import db
from sqlalchemy import desc, asc, extract
from datetime import datetime
from io import BytesIO
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule
from collections import defaultdict
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
    """Download Excel report for selected month/year with 3 sheets."""
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
        ).order_by(Metric.timestamp.asc()).all()
        
        if not metrics:
            flash(f'Tidak ada data untuk bulan {month:02d}/{year}.', 'warning')
            return render_template('dashboard.html', dashboard_data=[], servers=[],
                                   server_filter=[], category_filter='', status_filter='',
                                   search_query='', sort_by='server', sort_order='asc',
                                   categories=[], total_items=0)
        
        # Get server SNMP versions
        server_snmp_versions = {}
        servers = Server.query.all()
        for s in servers:
            server_snmp_versions[s.name] = s.snmp_version
        
        # ============ SHEET 1: Raw Data ============
        raw_data = []
        for i, m in enumerate(metrics):
            snmp_version = server_snmp_versions.get(m.server_name, 'N/A')
            raw_data.append({
                'No': i + 1,
                'Server Name': m.server_name,
                'IP Address': m.server_ip,
                'Brand': m.brand,
                'SNMP Version': snmp_version,
                'Category': m.category,
                'Component Name': m.component_name,
                'OID': m.oid,
                'Value': m.value,
                'Timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': m.status
            })
        
        df_raw = pd.DataFrame(raw_data)
        
        # ============ SHEET 2: Period Analysis ============
        # Group metrics by server and component
        grouped = defaultdict(list)
        for m in raw_data:
            key = (m['Server Name'], m['IP Address'], m['Component Name'], m['Category'])
            grouped[key].append(m)
        
        analysis_results = []
        for (server_name, ip_address, component_name, category), records in grouped.items():
            # Sort by timestamp ascending for proper period calculation
            sorted_records = sorted(records, key=lambda x: x['Timestamp'])
            
            # Track periods - count when status CHANGES to that status
            periods = {
                'OK': [],
                'Warning': [],
                'Critical': [],
                'Failed': []
            }
            
            prev_status = None
            for record in sorted_records:
                current_status = record['Status']
                timestamp = record['Timestamp']
                
                # If status changed, record the new period
                if current_status != prev_status:
                    if current_status in periods:
                        periods[current_status].append(timestamp)
                
                prev_status = current_status
            
            # Build analysis row
            analysis_row = {
                'Server Name': server_name,
                'IP Address': ip_address,
                'Component Name': component_name,
                'Category': category,
                'Total OK Periods': len(periods['OK']),
                'Total Warning Periods': len(periods['Warning']),
                'Total Critical Periods': len(periods['Critical']),
                'Total Failed Periods': len(periods['Failed']),
                'Critical Period Timestamps': ', '.join(periods['Critical']) if periods['Critical'] else '-',
                'Warning Period Timestamps': ', '.join(periods['Warning']) if periods['Warning'] else '-',
                'Failed Period Timestamps': ', '.join(periods['Failed']) if periods['Failed'] else '-',
                'Total Records': len(sorted_records)
            }
            analysis_results.append(analysis_row)
        
        df_analysis = pd.DataFrame(analysis_results)
        
        # ============ SHEET 3: Server Summary for Visualization ============
        server_summary = defaultdict(lambda: {'OK': 0, 'Warning': 0, 'Critical': 0, 'Failed': 0})
        for row in analysis_results:
            server_name = row['Server Name']
            server_summary[server_name]['OK'] += row['Total OK Periods']
            server_summary[server_name]['Warning'] += row['Total Warning Periods']
            server_summary[server_name]['Critical'] += row['Total Critical Periods']
            server_summary[server_name]['Failed'] += row['Total Failed Periods']
        
        # ============ CREATE EXCEL FILE ============
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Header styling
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # --- Sheet 1: Raw Data ---
            df_raw.to_excel(writer, index=False, sheet_name='Raw Data')
            ws_raw = writer.sheets['Raw Data']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df_raw.columns):
                max_length = max(df_raw[col].astype(str).map(len).max(), len(str(col))) + 2
                ws_raw.column_dimensions[get_column_letter(idx + 1)].width = min(max_length, 50)
            
            # Style header
            for col in range(1, len(df_raw.columns) + 1):
                cell = ws_raw.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
            
            # --- Sheet 2: Period Analysis ---
            df_analysis.to_excel(writer, index=False, sheet_name='Period Analysis')
            ws_analysis = writer.sheets['Period Analysis']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df_analysis.columns):
                max_length = max(df_analysis[col].astype(str).map(len).max(), len(str(col))) + 2
                ws_analysis.column_dimensions[get_column_letter(idx + 1)].width = min(max_length, 50)
            
            # Style header
            for col in range(1, len(df_analysis.columns) + 1):
                cell = ws_analysis.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
            
            # Conditional formatting for critical/warning counts
            red_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            orange_fill = PatternFill(start_color="FFE6CC", end_color="FFE6CC", fill_type="solid")
            
            if len(df_analysis) > 0:
                critical_col = get_column_letter(df_analysis.columns.get_loc('Total Critical Periods') + 1)
                warning_col = get_column_letter(df_analysis.columns.get_loc('Total Warning Periods') + 1)
                data_rows = len(df_analysis) + 1
                
                ws_analysis.conditional_formatting.add(
                    f'{critical_col}2:{critical_col}{data_rows}',
                    CellIsRule(operator='greaterThan', formula=['0'], fill=red_fill)
                )
                ws_analysis.conditional_formatting.add(
                    f'{warning_col}2:{warning_col}{data_rows}',
                    CellIsRule(operator='greaterThan', formula=['0'], fill=orange_fill)
                )
            
            # --- Sheet 3: Visualization ---
            workbook = writer.book
            ws_viz = workbook.create_sheet(title='Visualization')
            
            # Title
            ws_viz['A1'] = f'Server Status Period Summary - {month:02d}/{year}'
            ws_viz['A1'].font = Font(bold=True, size=14)
            ws_viz.merge_cells('A1:E1')
            
            # Headers for chart data
            viz_headers = ['Server Name', 'OK Periods', 'Warning Periods', 'Critical Periods', 'Failed Periods']
            for col, header in enumerate(viz_headers, 1):
                cell = ws_viz.cell(row=3, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
            
            # Data rows
            row = 4
            for server_name, counts in server_summary.items():
                ws_viz.cell(row=row, column=1, value=server_name)
                ws_viz.cell(row=row, column=2, value=counts['OK'])
                ws_viz.cell(row=row, column=3, value=counts['Warning'])
                ws_viz.cell(row=row, column=4, value=counts['Critical'])
                ws_viz.cell(row=row, column=5, value=counts['Failed'])
                row += 1
            
            # Adjust column widths
            ws_viz.column_dimensions['A'].width = 30
            ws_viz.column_dimensions['B'].width = 15
            ws_viz.column_dimensions['C'].width = 18
            ws_viz.column_dimensions['D'].width = 18
            ws_viz.column_dimensions['E'].width = 15
            
            # Create Bar Chart
            if len(server_summary) > 0:
                chart1 = BarChart()
                chart1.type = "col"
                chart1.grouping = "clustered"
                chart1.title = f"Status Periods per Server ({month:02d}/{year})"
                chart1.y_axis.title = "Number of Periods"
                chart1.x_axis.title = "Server"
                
                data_end_row = 3 + len(server_summary)
                
                # Data references (Warning, Critical, Failed - columns 3,4,5)
                data = Reference(ws_viz, min_col=3, min_row=3, max_col=5, max_row=data_end_row)
                cats = Reference(ws_viz, min_col=1, min_row=4, max_row=data_end_row)
                
                chart1.add_data(data, titles_from_data=True)
                chart1.set_categories(cats)
                chart1.shape = 4
                chart1.width = 18
                chart1.height = 10
                
                # Color the series
                if len(chart1.series) >= 1:
                    chart1.series[0].graphicalProperties.solidFill = "FFC000"  # Warning - Orange
                if len(chart1.series) >= 2:
                    chart1.series[1].graphicalProperties.solidFill = "FF0000"  # Critical - Red
                if len(chart1.series) >= 3:
                    chart1.series[2].graphicalProperties.solidFill = "7030A0"  # Failed - Purple
                
                ws_viz.add_chart(chart1, "G3")
                
                # Create Stacked Bar Chart
                chart2 = BarChart()
                chart2.type = "col"
                chart2.grouping = "stacked"
                chart2.title = f"Total Issue Periods per Server ({month:02d}/{year})"
                chart2.y_axis.title = "Total Periods"
                chart2.x_axis.title = "Server"
                
                chart2.add_data(data, titles_from_data=True)
                chart2.set_categories(cats)
                chart2.width = 18
                chart2.height = 10
                
                # Color the series
                if len(chart2.series) >= 1:
                    chart2.series[0].graphicalProperties.solidFill = "FFC000"
                if len(chart2.series) >= 2:
                    chart2.series[1].graphicalProperties.solidFill = "FF0000"
                if len(chart2.series) >= 3:
                    chart2.series[2].graphicalProperties.solidFill = "7030A0"  # Failed - Purple
                
                ws_viz.add_chart(chart2, "G20")
            
            # Report info
            info_row = max(row + 2, 38)
            ws_viz.cell(row=info_row, column=1, value=f"Report Period: {month:02d}/{year}")
            ws_viz.cell(row=info_row, column=1).font = Font(italic=True)
            ws_viz.cell(row=info_row + 1, column=1, value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            ws_viz.cell(row=info_row + 1, column=1).font = Font(italic=True)
            ws_viz.cell(row=info_row + 2, column=1, value=f"Generated by: {current_user.username}")
            ws_viz.cell(row=info_row + 2, column=1).font = Font(italic=True)
        
        output.seek(0)
        filename = f"laporan_monitoring_{year}_{month:02d}.xlsx"
        
        logger.info(f'Report downloaded from dashboard for {month:02d}/{year} by {current_user.username}: {len(metrics)} records, 3 sheets')
        
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
