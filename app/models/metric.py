from app import db
from datetime import datetime, timezone, timedelta

def wib_now():
    """Return current time in WIB (UTC+7) as naive datetime."""
    utc_now = datetime.now(timezone.utc)
    wib_time = utc_now + timedelta(hours=7)
    return wib_time.replace(tzinfo=None)  # Remove timezone info for PostgreSQL

class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('component.id'), nullable=False)
    oid = db.Column(db.String(128), nullable=False)
    value = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(16), nullable=False)  # OK, Warning, Critical
    timestamp = db.Column(db.DateTime, default=wib_now)
    brand = db.Column(db.String(64), nullable=False)
    component_name = db.Column(db.String(128), nullable=False)
    server_name = db.Column(db.String(128), nullable=False)
    server_ip = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(32), nullable=False)
