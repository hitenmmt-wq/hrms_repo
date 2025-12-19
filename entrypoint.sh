#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the application
exec "$@"
