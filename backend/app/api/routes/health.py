# backend/app/api/routes/health.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_logger_dependency

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check(logger=Depends(get_logger_dependency)):
    """Health check endpoint to verify the API is running."""
    return {
        "status": "healthy",
        "message": "Bill Splitter API is running",
        "version": "2.0.0"
    }


@router.get("/ready")
async def readiness_check(logger=Depends(get_logger_dependency)):
    """Readiness check endpoint."""
    return {
        "status": "ready",
        "message": "Bill Splitter API is ready to serve requests"
    }