from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.middleware import setup_cors
from .core.logging import setup_logging
from .api.routes import health, receipt, bill, split, session
import asyncio
import logging
from .services.sessionService import session_service

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bill Splitter API",
    description="A FastAPI application for splitting bills using OCR and AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
setup_cors(app)

# Include routers
app.include_router(health.router)
app.include_router(receipt.router)
app.include_router(bill.router)
app.include_router(split.router)
app.include_router(session.router)

# Background task for session cleanup
async def cleanup_sessions_periodically():
    """Background task to clean up expired sessions every 30 minutes"""
    while True:
        try:
            await session_service.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Session cleanup task failed: {str(e)}")
        # Wait 30 minutes before next cleanup
        await asyncio.sleep(30 * 60)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    logger.info("Starting Bill Splitter API")
    # Start session cleanup task in background
    asyncio.create_task(cleanup_sessions_periodically())
    logger.info("Session cleanup task started")


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to Bill Splitter API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
