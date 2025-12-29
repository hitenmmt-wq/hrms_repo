# HRMS CI/CD Pipeline Documentation

## Overview

This document explains the complete CI/CD pipeline implementation for the HRMS (Human Resource Management System) application.

## CI vs CD Explained

### Continuous Integration (CI) - What You Already Have
Your existing `django-ci.yml` workflow handles:
- **Code Quality**: Runs tests, linting, security checks
- **Validation**: Ensures code builds and passes all checks
- **Database**: Tests migrations and database operations
- **Dependencies**: Validates all requirements are installable
- **Triggers**: Runs on every push/PR to main branch

### Continuous Deployment (CD) - What We Added
The new `django-cd.yml` workflow handles:
- **Build**: Creates Docker images for deployment
- **Security**: Scans images for vulnerabilities
- **Deploy**: Automatically deploys to staging/production
- **Monitor**: Health checks and rollback capabilities
- **Notify**: Alerts on deployment success/failure

## Pipeline Architecture

```
Code Push → CI (Tests) → CD (Build) → Security Scan → Deploy Staging → Deploy Production
     ↓           ↓            ↓             ↓              ↓               ↓
   GitHub    Run Tests    Build Image   Scan Vulns    Auto Deploy    Manual Approval
```

## Files Created/Modified

### 1. CI/CD Workflows
- `.github/workflows/django-cd.yml` - Main CD pipeline
- `.github/workflows/django-ci.yml` - Your existing CI (unchanged)

### 2. Deployment Configuration
- `docker-compose.prod.yml` - Production Docker setup
- `.env.staging` - Staging environment variables
- `.env.production` - Production environment variables
- `nginx/nginx.conf` - Production web server config

### 3. Scripts
- `scripts/deploy.sh` - Automated deployment script
- `scripts/monitor.sh` - System monitoring script

### 4. Health Monitoring
- `apps/base/health.py` - Health check endpoints
- `hrms/urls.py` - Added health check routes

## Deployment Process

### Staging Deployment (Automatic)
1. CI pipeline passes
2. Docker image is built and pushed
3. Security scan runs
4. Automatic deployment to staging
5. Smoke tests execute

### Production Deployment (Manual Approval)
1. Staging deployment succeeds
2. Manual approval required (GitHub Environment)
3. Production deployment with health checks
4. Rollback capability if issues detected

## Environment Setup

### 1. GitHub Secrets
Add these secrets to your GitHub repository:

```
STAGING_SECRET_KEY=your-staging-secret
PRODUCTION_SECRET_KEY=your-production-secret
STAGING_DB_PASSWORD=staging-db-pass
PRODUCTION_DB_PASSWORD=production-db-pass
DOCKER_REGISTRY_TOKEN=ghcr-token
```

### 2. Environment Files
Update `.env.staging` and `.env.production` with your actual values:
- Database credentials
- Email configuration
- Domain names
- API keys

### 3. GitHub Environments
Create environments in GitHub:
- `staging` - No protection rules
- `production` - Require manual approval

## Monitoring & Health Checks

### Health Endpoints
- `/health/` - Complete system health check
- `/ready/` - Readiness probe for containers
- `/alive/` - Liveness probe for containers

### Monitoring Script
Run `./scripts/monitor.sh` to check:
- Application health
- Disk usage
- Memory usage
- Container status

## Security Features

### 1. Container Security
- Vulnerability scanning with Trivy
- Non-root user in containers
- Minimal base images

### 2. Network Security
- Nginx reverse proxy
- Rate limiting
- Security headers
- HTTPS ready

### 3. Application Security
- Environment variable isolation
- Secret management
- Database connection security

## Rollback Strategy

### Automatic Rollback
- Health checks fail → automatic rollback
- Database migration issues → manual intervention required

### Manual Rollback
```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
export DOCKER_IMAGE=previous-image-tag
docker-compose -f docker-compose.prod.yml up -d
```

## Performance Optimizations

### 1. Docker Optimizations
- Multi-stage builds
- Layer caching
- Minimal dependencies

### 2. Nginx Optimizations
- Gzip compression
- Static file caching
- Connection pooling

### 3. Database Optimizations
- Connection pooling
- Query optimization
- Backup automation

## Troubleshooting

### Common Issues

1. **Health Check Failures**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs web

   # Check database connection
   docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
   ```

2. **Image Build Failures**
   ```bash
   # Local build test
   docker build -t hrms:test .
   docker run --rm hrms:test python manage.py check
   ```

3. **Deployment Failures**
   ```bash
   # Check deployment logs
   ./scripts/deploy.sh staging

   # Monitor system resources
   ./scripts/monitor.sh
   ```

## Next Steps

### 1. Cloud Deployment
- AWS ECS/EKS
- Google Cloud Run
- Azure Container Instances

### 2. Advanced Monitoring
- Prometheus + Grafana
- ELK Stack
- Application Performance Monitoring

### 3. Database Management
- Automated backups
- Read replicas
- Connection pooling

### 4. Security Enhancements
- SSL/TLS certificates
- WAF integration
- Secrets management (AWS Secrets Manager, etc.)

## Usage Examples

### Deploy to Staging
```bash
# Automatic via GitHub Actions
git push origin main

# Manual deployment
./scripts/deploy.sh staging
```

### Deploy to Production
```bash
# Via GitHub Actions (requires approval)
# Or manual:
./scripts/deploy.sh production
```

### Monitor System
```bash
# Run health checks
./scripts/monitor.sh

# Check specific endpoints
curl http://localhost/health/
curl http://localhost/ready/
curl http://localhost/alive/
```

This CD pipeline provides a robust, secure, and scalable deployment solution for your HRMS application.
