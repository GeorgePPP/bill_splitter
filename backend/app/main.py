from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.middleware import setup_cors
from .core.logging import setup_logging
from .api.routes import health, receipt, bill, split

# Setup logging
setup_logging()

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
