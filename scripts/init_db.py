#!/usr/bin/env python3
"""
Script untuk inisialisasi database dan membuat admin default.
Jalankan dengan: python scripts/init_db.py

Atau dengan Docker:
docker-compose exec web python scripts/init_db.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db, bcrypt
from app.models.user import User, RoleEnum
from app.models.server import Server, Component
from app.models.metric import Metric


def init_database():
    """Initialize database and create default admin."""
    app = create_app()
    
    with app.app_context():
        print("📦 Membuat tabel database...")
        db.create_all()
        print("✅ Tabel database berhasil dibuat!")
        
        # Check if admin exists
        admin = User.query.filter_by(role=RoleEnum.admin).first()
        if not admin:
            print("\n👤 Membuat admin user default...")
            password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin',
                password_hash=password_hash,
                role=RoleEnum.admin
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin default dibuat:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  PENTING: Ganti password setelah login pertama!")
        else:
            print(f"\n✅ Admin user sudah ada: {admin.username}")
        
        print("\n🎉 Database siap digunakan!")


if __name__ == "__main__":
    print("=" * 50)
    print("  DATABASE INITIALIZATION - Server Monitoring")
    print("=" * 50)
    init_database()
