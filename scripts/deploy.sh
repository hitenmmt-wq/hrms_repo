#!/bin/bash

# HRMS Deployment Script
# Usage: ./deploy.sh [staging|production]

set -e

ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    error "Invalid environment. Use 'staging' or 'production'"
fi

log "Starting deployment to $ENVIRONMENT environment..."

# Load environment variables
if [[ -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]]; then
    log "Loading environment variables from .env.$ENVIRONMENT"
    export $(cat "$PROJECT_DIR/.env.$ENVIRONMENT" | grep -v '^#' | xargs)
else
    warn "No .env.$ENVIRONMENT file found. Using default values."
fi

# Set default values if not provided
export DOCKER_IMAGE=${DOCKER_IMAGE:-"ghcr.io/yourusername/hrms:latest"}
export DATABASE_NAME=${DATABASE_NAME:-"hrms_${ENVIRONMENT}"}
export DATABASE_USER=${DATABASE_USER:-"postgres"}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-"localhost,127.0.0.1"}

# Validate required environment variables
required_vars=("SECRET_KEY" "DATABASE_PASSWORD")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        error "Required environment variable $var is not set"
    fi
done

# Create backup directory
mkdir -p "$PROJECT_DIR/backups"

# Backup database (production only)
if [[ "$ENVIRONMENT" == "production" ]]; then
    log "Creating database backup..."
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$DATABASE_USER" "$DATABASE_NAME" > "backups/backup_$(date +%Y%m%d_%H%M%S).sql"
fi

# Pull latest images
log "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Stop services gracefully
log "Stopping services..."
docker-compose -f docker-compose.prod.yml down --remove-orphans

# Start services
log "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
log "Waiting for services to be healthy..."
timeout=300
counter=0
while ! docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; do
    if [[ $counter -ge $timeout ]]; then
        error "Services failed to become healthy within $timeout seconds"
    fi
    sleep 5
    counter=$((counter + 5))
    echo -n "."
done
echo ""

# Run migrations
log "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Collect static files
log "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Run health checks
log "Running health checks..."
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    log "Health check passed!"
else
    error "Health check failed!"
fi

# Clean up old images
log "Cleaning up old Docker images..."
docker image prune -f

log "Deployment to $ENVIRONMENT completed successfully!"

# Show running services
log "Running services:"
docker-compose -f docker-compose.prod.yml ps
