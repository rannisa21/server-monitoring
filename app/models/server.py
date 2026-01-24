from app import db

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    ip = db.Column(db.String(64), nullable=False)
    community = db.Column(db.String(128), nullable=True)
    brand = db.Column(db.String(64), nullable=False)
    snmp_version = db.Column(db.String(8), nullable=False)  # 'v2c' or 'v3'
    snmp_auth_user = db.Column(db.String(128), nullable=True)
    snmp_auth_pass = db.Column(db.String(128), nullable=True)
    snmp_priv_pass = db.Column(db.String(128), nullable=True)
    snmp_auth_proto = db.Column(db.String(16), nullable=True)
    snmp_priv_proto = db.Column(db.String(16), nullable=True)
    components = db.relationship('Component', backref='server', lazy=True, cascade="all, delete-orphan")
    metrics = db.relationship('Metric', backref='server', lazy=True, cascade="all, delete-orphan")

class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    oid = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(32), nullable=False)  # PSU, harddisk, suhu, fan
    brand = db.Column(db.String(64), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'), nullable=False)
    metrics = db.relationship('Metric', backref='component', lazy=True, cascade="all, delete-orphan")
