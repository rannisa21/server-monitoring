from flask import Blueprint, render_template, request, send_file, flash, current_app
from flask_login import login_required, current_user
from app.models.metric import Metric
from app.models.server import Server, Component
from io import BytesIO
import pandas as pd
from datetime import datetime
from app import db
from app.validators import admin_required, validate_month_year, ValidationError
from sqlalchemy import extract
import logging

logger = logging.getLogger(__name__)

report_bp = Blueprint('report', __name__)

@report_bp.route('/admin/report', methods=['GET', 'POST'])
@login_required
@admin_required
def report():
    if request.method == 'POST':
        try:
            # Validate inputs
            month, year = validate_month_year(
                request.form.get('month'),
                request.form.get('year')
            )
            
            # Query metrics for the specified month/year
            metrics = Metric.query.filter(
                extract('month', Metric.timestamp) == month,
                extract('year', Metric.timestamp) == year
            ).order_by(Metric.timestamp.desc()).all()
            
            if not metrics:
                flash(f'No data found for {month:02d}/{year}.', 'warning')
                return render_template('report.html')
            
            # Build report data
            data = [
                {
                    'No': i + 1,
                    'Nama Server': m.server_name,
                    'IP': m.server_ip,
                    'Nama Komponen': m.component_name,
                    'OID': m.oid,
                    'Merk': m.brand,
                    'Value': m.value,
                    'Status Metric': m.status,
                    'Timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'Kategori': m.category
                }
                for i, m in enumerate(metrics)
            ]
            
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
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
            
            output.seek(0)
            filename = f"report_{year}_{month:02d}.xlsx"
            
            logger.info(f'Report generated for {month:02d}/{year} by {current_user.username}: {len(metrics)} records')
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except ValidationError as e:
            flash(e.message, 'danger')
            logger.warning(f'Validation error generating report: {e.message}')
        except Exception as e:
            logger.error(f'Error generating report: {e}', exc_info=True)
            flash('An error occurred while generating the report.', 'danger')
    
    return render_template('report.html')


@report_bp.route('/admin/report/preview', methods=['GET'])
@login_required
@admin_required
def report_preview():
    """Preview metrics with pagination."""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
        
        if month and year:
            try:
                month, year = validate_month_year(month, year)
                
                pagination = Metric.query.filter(
                    extract('month', Metric.timestamp) == month,
                    extract('year', Metric.timestamp) == year
                ).order_by(Metric.timestamp.desc()).paginate(
                    page=page, per_page=per_page, error_out=False
                )
                
                return render_template(
                    'report.html',
                    metrics=pagination.items,
                    pagination=pagination,
                    month=month,
                    year=year
                )
            except ValidationError as e:
                flash(e.message, 'danger')
        
        return render_template('report.html')
        
    except Exception as e:
        logger.error(f'Error loading report preview: {e}', exc_info=True)
        flash('An error occurred while loading the report preview.', 'danger')
        return render_template('report.html')
