# HRMS Django Application

This is a Django-based HRMS (Human Resource Management System) application with Docker support.

## Features

- Employee management
- Attendance tracking
- Chat functionality with WebSockets
- Background task processing with Celery
- REST API with JWT authentication

## Prerequisites

- Docker and Docker Compose

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hrms
   ```

2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your configuration (database passwords, email settings, etc.)

4. Build and run the application:
   ```bash
   docker-compose up --build
   ```

5. The application will be available at:
   - Web app: http://localhost
   - Admin panel: http://localhost/admin/

## Services

- **web**: Django application running on Daphne (ASGI server)
- **db**: PostgreSQL database
- **redis**: Redis for caching and Celery broker
- **celery**: Celery worker for background tasks
- **nginx**: Nginx reverse proxy and static file server

## Development

For development, you can run the services individually:

```bash
# Run only the database and redis
docker-compose up db redis

# Run the web app with auto-reload
docker-compose run --rm web python manage.py runserver 0.0.0.0:8000
```

## Production Deployment

The setup is configured for production with:
- Daphne ASGI server
- Nginx reverse proxy
- Static file serving
- Database migrations on startup

## API Documentation

The API endpoints are available at `/api/` with JWT authentication.

## License

[Add your license here]
