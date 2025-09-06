from fastapi import APIRouter, Depends
from ..dependencies import get_logger_dependency
from ...core.logging import get_logger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check(logger = Depends(get_logger_dependency)):
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "healthy",
        "message": "Bill Splitter API is running",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check(logger = Depends(get_logger_dependency)):
    """
    Readiness check endpoint to verify the API is ready to serve requests.
    """
    # Add checks for external services here if needed
    return {
        "status": "ready",
        "message": "Bill Splitter API is ready to serve requests"
    }
