# backend/app/core/__init__.py
from .config import settings
from .logging import get_logger, setup_logging
from .middleware import setup_cors

__all__ = ["settings", "get_logger", "setup_logging", "setup_cors"]