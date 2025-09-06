from fastapi import Depends, HTTPException, status
from typing import Generator
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_current_user():
    """
    Dependency to get current user.
    For now, returns a mock user. In a real application, this would
    validate JWT tokens or session data.
    """
    # Mock user for development
    return {
        "id": "user_123",
        "name": "Test User",
        "email": "test@example.com"
    }


def get_logger_dependency():
    """
    Dependency to get logger instance.
    """
    return logger
