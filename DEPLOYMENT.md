# 🚀 Panduan Deployment - Server Monitoring System

## 📁 File yang Perlu Dikirim

Kirim folder `servermonitoring` **TANPA** folder berikut:
- `venv/` atau `.venv/` (virtual environment)
- `__pycache__/` (Python cache)
- `logs/` (log files)
- `.git/` (git repository)

### Struktur File yang Dikirim:
```
servermonitoring/
├── app/                    # Kode aplikasi utama
├── migrations/             # Database migrations
├── scripts/                # Script helper
│   ├── create_admin.py
│   └── init_db.py
├── docker-compose.yml      # Docker config
├── Dockerfile
├── requirements.txt
├── wsgi.py
├── .env.example
├── .dockerignore
└── README.md
```

---

## 🔧 Cara Deploy di Laptop Baru

### Prasyarat
1. Install **Docker Desktop** (https://www.docker.com/products/docker-desktop/)
2. Pastikan Docker sudah running

### Langkah-langkah

#### Opsi A: Menggunakan Docker (Direkomendasikan) ✅

```bash
# 1. Pindah ke folder project
cd servermonitoring

# 2. Copy dan edit file environment
cp .env.example .env

# 3. (Opsional) Edit .env sesuai kebutuhan
# Terutama ganti SECRET_KEY untuk production

# 4. Build dan jalankan dengan Docker Compose
docker-compose up --build -d

# 5. Tunggu sampai container siap (~30 detik)
docker-compose logs -f

# 6. Jalankan migrasi database
docker-compose exec web flask db upgrade

# 7. Buat admin user (pilih salah satu):

# Opsi 7a: Buat admin default (admin/admin123)
docker-compose exec web python scripts/init_db.py

# Opsi 7b: Buat admin dengan username/password custom
docker-compose exec web python scripts/create_admin.py

# 8. Akses aplikasi di browser
# http://localhost:5000
```

#### Opsi B: Tanpa Docker (Manual)

```bash
# 1. Install Python 3.11+
# Download dari https://www.python.org/downloads/

# 2. Install PostgreSQL
# Download dari https://www.postgresql.org/download/

# 3. Buat database
psql -U postgres
CREATE DATABASE monitoring;
\q

# 4. Pindah ke folder project
cd servermonitoring

# 5. Buat virtual environment
python -m venv venv

# 6. Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 7. Install dependencies
pip install -r requirements.txt

# 8. Set environment variables
# Windows PowerShell:
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/monitoring"
$env:SECRET_KEY="your-secret-key-here"
$env:FLASK_ENV="production"

# Linux/Mac:
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/monitoring"
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"

# 9. Jalankan migrasi database
flask db upgrade

# 10. Buat admin user
python scripts/init_db.py

# 11. Jalankan aplikasi
# Development:
flask run --host=0.0.0.0 --port=5000

# Production:
gunicorn -b 0.0.0.0:5000 --workers 2 wsgi:app
```

---

## 🗄️ Migrasi Database

### Fresh Install (Database Baru)
```bash
# Dengan Docker:
docker-compose exec web flask db upgrade
docker-compose exec web python scripts/init_db.py

# Tanpa Docker:
flask db upgrade
python scripts/init_db.py
```

### Update Schema (Jika Ada Perubahan Model)
```bash
# Dengan Docker:
docker-compose exec web flask db migrate -m "deskripsi perubahan"
docker-compose exec web flask db upgrade

# Tanpa Docker:
flask db migrate -m "deskripsi perubahan"
flask db upgrade
```

### Reset Database (Hapus Semua Data)
```bash
# Dengan Docker:
docker-compose down -v  # Hapus volume database
docker-compose up -d
docker-compose exec web flask db upgrade
docker-compose exec web python scripts/init_db.py

# Tanpa Docker (PostgreSQL):
psql -U postgres
DROP DATABASE monitoring;
CREATE DATABASE monitoring;
\q
flask db upgrade
python scripts/init_db.py
```

---

## 👤 Membuat User Admin

### Metode 1: Script Interaktif
```bash
# Dengan Docker:
docker-compose exec web python scripts/create_admin.py

# Tanpa Docker:
python scripts/create_admin.py
```

### Metode 2: Script Auto (admin/admin123)
```bash
# Dengan Docker:
docker-compose exec web python scripts/init_db.py

# Tanpa Docker:
python scripts/init_db.py
```

### Metode 3: Via Python Shell
```bash
# Dengan Docker:
docker-compose exec web flask shell

# Tanpa Docker:
flask shell
```

```python
from app import db, bcrypt
from app.models.user import User, RoleEnum

# Buat admin
password_hash = bcrypt.generate_password_hash('password123').decode('utf-8')
admin = User(username='myadmin', password_hash=password_hash, role=RoleEnum.admin)
db.session.add(admin)
db.session.commit()
print("Admin created!")
exit()
```

---

## 🔒 Konfigurasi Environment (.env)

```env
# Wajib diganti untuk production!
SECRET_KEY=ganti-dengan-random-string-panjang

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/monitoring
POSTGRES_PASSWORD=ganti-password-database

# Environment
FLASK_ENV=production
LOG_LEVEL=INFO

# Fitur
ITEMS_PER_PAGE=20
SNMP_POLL_INTERVAL=5
ENABLE_SCHEDULER=true
```

**Cara generate SECRET_KEY:**
```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32
```

---

## 🐛 Troubleshooting

### Container tidak bisa start
```bash
docker-compose logs web
docker-compose logs db
```

### Database connection error
```bash
# Pastikan PostgreSQL sudah ready
docker-compose exec db psql -U postgres -c "SELECT 1"
```

### Reset semua dan mulai ulang
```bash
docker-compose down -v
docker system prune -f
docker-compose up --build -d
```

### Cek status container
```bash
docker-compose ps
docker-compose logs -f
```

---

## ✅ Checklist Deployment

- [ ] Docker Desktop terinstall dan running
- [ ] File `.env` sudah dibuat dari `.env.example`
- [ ] `SECRET_KEY` sudah diganti
- [ ] `docker-compose up --build -d` berhasil
- [ ] `flask db upgrade` berhasil
- [ ] Admin user sudah dibuat
- [ ] Aplikasi bisa diakses di http://localhost:5000
- [ ] Login dengan admin berhasil

---

## 📞 Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |

**⚠️ PENTING: Ganti password setelah login pertama!**
