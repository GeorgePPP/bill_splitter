# backend/app/main.py
"""
Bill Splitter API - Stateless Architecture
All endpoints are stateless - no server-side session storage.
"""
from fastapi import FastAPI
from .core.middleware import setup_cors
from .core.logging import setup_logging
from .api.routes import health, receipt, split
import logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bill Splitter API",
    description="A stateless API for splitting bills using OCR and AI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

setup_cors(app)

# Include routers - simplified, stateless
app.include_router(health.router)
app.include_router(receipt.router)
app.include_router(split.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Bill Splitter API v2.0.0 (stateless)")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Bill Splitter API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "process_receipt": "POST /receipt/process - Upload and process receipt image",
            "validate_receipt": "POST /receipt/validate - Validate corrected receipt data",
            "calculate_split": "POST /split/calculate - Calculate bill split",
            "preview_split": "POST /split/preview - Preview equal split"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)