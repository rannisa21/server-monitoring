#!/usr/bin/env python3
"""
Script untuk membuat user admin.
Jalankan dengan: python scripts/create_admin.py

Atau dengan Docker:
docker-compose exec web python scripts/create_admin.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db, bcrypt
from app.models.user import User, RoleEnum


def create_admin_user(username, password):
    """Create an admin user."""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"❌ User '{username}' sudah ada!")
            return False
        
        # Create new admin user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            password_hash=password_hash,
            role=RoleEnum.admin
        )
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ Admin user '{username}' berhasil dibuat!")
        return True


def main():
    print("=" * 50)
    print("  CREATE ADMIN USER - Server Monitoring System")
    print("=" * 50)
    
    # Get username
    username = input("\nMasukkan username admin: ").strip()
    if not username:
        print("❌ Username tidak boleh kosong!")
        sys.exit(1)
    
    if len(username) < 3:
        print("❌ Username minimal 3 karakter!")
        sys.exit(1)
    
    # Get password
    import getpass
    password = getpass.getpass("Masukkan password: ")
    if len(password) < 6:
        print("❌ Password minimal 6 karakter!")
        sys.exit(1)
    
    password_confirm = getpass.getpass("Konfirmasi password: ")
    if password != password_confirm:
        print("❌ Password tidak cocok!")
        sys.exit(1)
    
    # Create user
    if create_admin_user(username, password):
        print("\n🎉 Anda bisa login dengan kredensial tersebut di http://localhost:5000")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
