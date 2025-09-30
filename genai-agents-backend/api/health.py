"""
Health check API router
"""
from fastapi import APIRouter
from datetime import datetime
from config.settings import settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.app_version
    }

@router.get("/api/health")
async def api_health_check():
    """API health check endpoint (backward compatibility)"""
    return await health_check()