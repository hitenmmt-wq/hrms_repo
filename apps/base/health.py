import redis
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Health check endpoint for deployment monitoring
    """
    health_status = {
        "status": "healthy",
        "checks": {"database": False, "redis": False, "cache": False},
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = True
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = str(e)

    # Check Redis connection
    try:
        r = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            db=0,
        )
        r.ping()
        health_status["checks"]["redis"] = True
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = str(e)

    # Check cache
    try:
        cache.set("health_check", "ok", 30)
        if cache.get("health_check") == "ok":
            health_status["checks"]["cache"] = True
        else:
            health_status["status"] = "unhealthy"
            health_status["checks"]["cache"] = "Cache read/write failed"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["cache"] = str(e)

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration
    """
    return JsonResponse({"status": "ready"})


def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    """
    return JsonResponse({"status": "alive"})
