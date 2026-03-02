#!/bin/bash
set -e

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  echo "Redis not ready, waiting..."
  sleep 2
done
echo "Redis is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"
