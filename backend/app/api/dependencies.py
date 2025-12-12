# backend/app/api/dependencies.py
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_logger_dependency():
    """Dependency to get logger instance."""
    return logger