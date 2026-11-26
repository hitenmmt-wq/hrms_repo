#!/bin/bash
set -e

REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
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