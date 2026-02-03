from app import db
from app.utils.encryption import encrypt_password, decrypt_password

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    ip = db.Column(db.String(64), nullable=False)
    community = db.Column(db.String(128), nullable=True)
    brand = db.Column(db.String(64), nullable=False)
    snmp_version = db.Column(db.String(8), nullable=False)  # 'v2c' or 'v3'
    snmp_auth_user = db.Column(db.String(128), nullable=True)
    # Encrypted password columns - increased size to accommodate encrypted data
    _snmp_auth_pass = db.Column('snmp_auth_pass', db.String(256), nullable=True)
    _snmp_priv_pass = db.Column('snmp_priv_pass', db.String(256), nullable=True)
    snmp_auth_proto = db.Column(db.String(16), nullable=True)
    snmp_priv_proto = db.Column(db.String(16), nullable=True)
    components = db.relationship('Component', backref='server', lazy=True, cascade="all, delete-orphan")
    metrics = db.relationship('Metric', backref='server', lazy=True, cascade="all, delete-orphan")

    @property
    def snmp_auth_pass(self):
        """Decrypt and return the auth password."""
        if self._snmp_auth_pass:
            decrypted = decrypt_password(self._snmp_auth_pass)
            # If decryption fails (old unencrypted data), return as-is
            return decrypted if decrypted else self._snmp_auth_pass
        return None

    @snmp_auth_pass.setter
    def snmp_auth_pass(self, value):
        """Encrypt and store the auth password."""
        if value:
            self._snmp_auth_pass = encrypt_password(value)
        else:
            self._snmp_auth_pass = None

    @property
    def snmp_priv_pass(self):
        """Decrypt and return the priv password."""
        if self._snmp_priv_pass:
            decrypted = decrypt_password(self._snmp_priv_pass)
            # If decryption fails (old unencrypted data), return as-is
            return decrypted if decrypted else self._snmp_priv_pass
        return None

    @snmp_priv_pass.setter
    def snmp_priv_pass(self, value):
        """Encrypt and store the priv password."""
        if value:
            self._snmp_priv_pass = encrypt_password(value)
        else:
            self._snmp_priv_pass = None

class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    oid = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(32), nullable=False)  # PSU, harddisk, suhu, fan
    brand = db.Column(db.String(64), nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'), nullable=False)
    metrics = db.relationship('Metric', backref='component', lazy=True, cascade="all, delete-orphan")
