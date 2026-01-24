# Server Monitoring System

A centralized web-based server monitoring system using Flask, Postgres, SNMP (v2c/v3), Docker, and a modern UI.

## Features

### Core Features

- **Admin/user authentication** with role-based access control
- **CRUD for servers, components, and users**
- **SNMP v2c/v3 polling** with authentication for v3
- **Brand/component-based SNMP OID mapping** and status classification (OK, Warning, Critical)
- **Background metric polling** every 5 minutes (even if UI is closed)
- **Dashboard** with per-server columns, per-component rows, and auto-refresh
- **Monthly metric export** to Excel

### Recent Improvements

#### Error Handling & Validation

- Comprehensive input validation for all forms (IP addresses, OIDs, usernames, passwords)
- Global error handlers for 404, 500, and CSRF errors
- Try-except blocks in all routes with proper logging

#### Security

- CSRF protection on all POST forms using Flask-WTF
- Secure session configuration (HTTP-only cookies, same-site strict)
- Admin-only decorator for protected routes
- Password validation with minimum length requirements

#### Logging

- Rotating file handler (10MB, 10 backups) for application logs
- Debug, info, warning, and error level logging
- Request context logging with user info

#### User Interface Enhancements

- **Dashboard**: Filter by multiple servers, category, status; search; sort by various columns; no pagination (all items visible)
- **Server Management**: Search by name/IP, filter by brand/SNMP version, sort, pagination
- **User Management**: Search by username, filter by role, sort, pagination
- **Component Management**: Pagination support
- Modern toolbar UI with responsive design
- Status badges and role badges for better visualization

## Quick Start

1. Copy `.env.example` to `.env` and adjust as needed:

   ```sh
   cp .env.example .env
   ```

2. Build and run with Docker Compose:

   ```sh
   docker-compose up --build
   ```

3. Access the app at http://localhost:5000

4. Default admin credentials (change after first login):
   - Username: `admin`
   - Password: `admin123`

## Environment Variables

| Variable         | Description                          | Default                |
| ---------------- | ------------------------------------ | ---------------------- |
| `SECRET_KEY`     | Flask secret key                     | Auto-generated         |
| `DATABASE_URL`   | PostgreSQL connection string         | See docker-compose.yml |
| `FLASK_ENV`      | Environment (development/production) | `production`           |
| `ITEMS_PER_PAGE` | Pagination size                      | `20`                   |

## Folder Structure

```
servermonitoring/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration classes
│   ├── validators.py        # Input validation functions
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── server.py
│   │   └── metric.py
│   ├── routes/              # Blueprint routes
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── server.py
│   │   ├── component.py
│   │   ├── user_management.py
│   │   ├── report.py
│   │   └── admin.py
│   ├── scheduler/           # Background tasks
│   │   └── monitor.py
│   ├── static/              # CSS/JS assets
│   └── templates/           # Jinja2 templates
├── migrations/              # Alembic database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── wsgi.py
└── .env.example
```

## Admin Features

- Add/edit/delete servers and components
- Choose SNMP v2c or v3 (with authentication)
- Map OIDs and classify metrics per brand/component
- Manage users (add/edit/delete)
- Download monthly reports as Excel

## User Features

- View dashboard (read-only)
- See server/component status and metrics
- Filter and search dashboard data

## API Endpoints

### Authentication

- `GET/POST /login` - User login
- `GET /logout` - User logout

### Dashboard

- `GET /` - Main dashboard with filter/sort/search

### Server Management (Admin only)

- `GET /admin/servers` - List servers with pagination
- `GET/POST /admin/servers/add` - Add server
- `GET/POST /admin/servers/edit/<id>` - Edit server
- `POST /admin/servers/delete/<id>` - Delete server

### Component Management (Admin only)

- `GET /admin/components` - List components
- `GET/POST /admin/components/add` - Add component
- `GET/POST /admin/components/edit/<id>` - Edit component
- `POST /admin/components/delete/<id>` - Delete component

### User Management (Admin only)

- `GET/POST /admin/users` - List/add users
- `GET/POST /admin/users/edit/<id>` - Edit user
- `POST /admin/users/delete/<id>` - Delete user

### Reports (Admin only)

- `GET/POST /admin/report` - Download monthly Excel report

## Tech Stack

- **Backend**: Python 3.11, Flask 2.x
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy with Flask-Migrate
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Security**: Flask-WTF (CSRF), Flask-CORS
- **SNMP**: pysnmp
- **Scheduler**: APScheduler
- **Container**: Docker, Docker Compose
- **WSGI Server**: Gunicorn

## Development

### Running locally (without Docker)

1. Create a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL and update `.env`

4. Run migrations:

   ```sh
   flask db upgrade
   ```

5. Run the app:
   ```sh
   flask run
   ```

### Running tests

```sh
pytest
```

## License

MIT License

---

For more details, see `.github/copilot-instructions.md`.
