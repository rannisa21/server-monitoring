from app import db
from flask_login import UserMixin
from sqlalchemy import Enum
import enum

class RoleEnum(enum.Enum):
    admin = 'admin'
    user = 'user'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.user, nullable=False)
    def __repr__(self):
        return f'<User {self.username}>'
