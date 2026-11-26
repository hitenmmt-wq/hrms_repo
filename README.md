# HRMS - Human Resource Management System

[![Django CI](https://github.com/your-username/hrms/workflows/Django%20CI/badge.svg)](https://github.com/your-username/hrms/actions)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-5.2.9-green.svg)](https://djangoproject.com)

A comprehensive Human Resource Management System built with Django, featuring real-time chat, attendance tracking, leave management, payroll processing, and automated background tasks.

> **Local setup (Docker + frontend + host Postgres/Redis):** see [SETUP.md](../SETUP.md) at the repository root.

## 🚀 Features

### Core Modules
- **👥 Employee Management**: Complete employee lifecycle management with profiles, departments, and positions
- **📅 Attendance Tracking**: Real-time check-in/check-out with break time logging
- **🏖️ Leave Management**: Leave applications, approvals, balance tracking, and smart deductions (sandwich rule: weekends/weekday holidays between leave days are ignored when surrounded by leave days)
- **💰 Payroll System**: Automated payslip generation with PDF export
- **💬 Real-time Chat**: WebSocket-based messaging system with file sharing
- **🤖 AI Assistant**: LLM-driven HR assistant with role-aware system prompts, intent-specific templates, and fuzzy intent matching to tolerate common misspellings
- **🔔 Notifications**: Real-time notifications for various HR activities
- **📊 Dashboard**: Comprehensive analytics and reporting

### Technical Features
- **🔐 JWT Authentication**: Secure token-based authentication
- **📱 REST API**: Complete RESTful API with OpenAPI documentation
- **⚡ Real-time Updates**: WebSocket support for live notifications and chat
- **🤖 AI Assistant & Prompt Templates**: Structured system prompts per role and intent-specific templates used to produce accurate, role-sensitive LLM responses
- **🔎 Fuzzy Intent Matching**: `IntentClassifier` uses fuzzy matching to handle common misspellings and reduce misclassification
- **🔄 Background Tasks**: Celery-based task processing for automated operations (timezone-aware configuration supported)
- **📝 Comprehensive Logging**: Structured logging with file rotation
- **🐳 Docker Support**: Complete containerization with Docker Compose
- **🔍 Advanced Filtering**: Django Filter integration for complex queries
- **📄 PDF Generation**: Automated payslip and report generation

## 🏗️ Architecture

```
HRMS/
├── apps/
│   ├── superadmin/     # User management, departments, holidays
│   ├── employee/       # Employee profiles, leave balance, payslips
│   ├── attendance/     # Attendance tracking and break logs
│   ├── chat/          # Real-time messaging system
│   ├── notification/   # Notification management
│   └── base/          # Shared utilities and base classes
├── hrms/              # Django project settings
├── logs/              # Application logs
├── media/             # User uploaded files
└── staticfiles/       # Static assets
```

## 🛠️ Technology Stack

- **Backend**: Django 5.2.9, Django REST Framework
- **Database**: PostgreSQL 14
- **Cache & Message Broker**: Redis
- **Task Queue**: Celery with Celery Beat
- **WebSockets**: Django Channels
- **Authentication**: JWT (Simple JWT)
- **API Documentation**: DRF Spectacular (OpenAPI/Swagger)
- **PDF Generation**: WeasyPrint, ReportLab
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production)
- **ASGI Server**: Daphne

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 14+ (for local development)
- Redis (for local development)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   ```

2. **Environment setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   cd hrms
   ```

3. **Build and run**:
   ```bash
   docker-compose up --build
   ```

4. **Create superuser**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application**:
   - **Web Application**: http://localhost
   - **Admin Panel**: http://localhost/admin/
   - **API Documentation**: http://localhost/api/schema/swagger-ui/

### Local Development Setup

1. **Create virtual environment**:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database setup**:
   ```bash
   python manage.py seed
   python manage.py init_defaults
   ```

4. **Run development server**:
   ```bash
   python manage.py runserver
   ```

5. **Run Celery (separate terminal)**:
   ```bash
   celery -A hrms worker --loglevel=info
   celery -A hrms beat --loglevel=info
   ```

## 🐳 Docker Services

| Service | Description | Port |
|---------|-------------|------|
| **web** | Django application (Gunicorn) | 8000 |
| **db** | PostgreSQL database | 5432 |
| **redis** | Redis cache & message broker | 6379 |
| **celery** | Celery worker for background tasks | - |
| **celery-beat** | Celery scheduler for cron jobs | - |
| **nginx** | Reverse proxy & static files | 80 |

## 📊 Database Models

### Core Models
- **Users**: Extended Django user model with employee details
- **Department**: Organizational departments
- **Position**: Job positions/roles
- **LeaveBalance**: Employee leave balances by year
- **EmployeeAttendance**: Daily attendance records
- **PaySlip**: Monthly salary slips
- **Notification**: System notifications
- **Conversation/Message**: Chat system

## 🔄 Background Tasks

Automated Celery tasks for:
- **Daily**: Mark absent employees
- **Birthday Notifications**: Daily birthday alerts
- **Annual Leave Credit**: Yearly leave balance updates
- **Payroll Processing**: Monthly payslip generation

Notes on scheduling & timezone handling:
- The project configures Celery with `CELERY_ENABLE_UTC = False` and `CELERY_TIMEZONE = "Asia/Kolkata"` to run scheduled jobs in local IST time. Containers set `TZ=Asia/Kolkata` to align OS time. The codebase still uses `USE_TZ = True` so datetimes are stored in UTC and localized for display; this is the recommended approach for accuracy across environments.

## 📝 API Endpoints

### Authentication
```
POST /superadmin/auth/login/          # Login
POST /superadmin/auth/refresh/        # Refresh token
POST /superadmin/auth/logout/         # Logout
```

### Employee Management
```
GET    /employee/employee/         # List employees
POST   /employee/employee/         # Create employee
GET    /employee/employee/{id}/    # Get employee details
PUT    /employee/employee/{id}/    # Update employee
DELETE /employee/employee/{id}/    # Delete employee
```

### Attendance
```
GET  /attendance/employee_attendance/             # List attendance
POST /attendance/employee_attendance/check_in/    # Check in
POST /attendance/employee_attendance/check_out/   # Check out
```

### Leave Management
```
GET  /api/leaves/              # List leaves
POST /api/leaves/              # Apply leave
PUT  /api/leaves/{id}/approve/ # Approve/reject leave
```


## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_NAME=hrms_db_demo1
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
SECRET_KEY=your-secret-key
DEBUG=False
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.employee

# Test logging system
python manage.py test_logging
```

## 📈 Monitoring

### Health Checks
- Database connectivity
- Redis connectivity
- Celery worker status

### Metrics
- API response times
- Task execution times
- Error rates
- User activity

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up SSL certificates
- [ ] Configure email settings
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Set up log aggregation

### Docker Production
```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build -d

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run migrations
docker-compose exec web python manage.py migrate
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgments

- Django community for the excellent framework
- Contributors and testers
- Open source libraries used in this project

---

**Built with ❤️ using Django**
