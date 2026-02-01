"""
Health check router.

Provides endpoints for monitoring application health.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns basic health status for monitoring and load balancer health checks.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "iris-invoicing-backend",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """
    Readiness check endpoint.
    
    Indicates whether the application is ready to serve traffic.
    In future, this can check database connectivity, etc.
    """
    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
