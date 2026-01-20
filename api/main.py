"""
Main FastAPI application for Medical Telegram Warehouse.

This module sets up the FastAPI application with all routes,
middleware, and configuration for serving the analytical API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from api.database import test_connection
from api.routes import reports, channels, search
from api.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="""
    Analytical API for querying insights from Ethiopian medical business Telegram channels.
    
    ## Features
    
    * **Product Analytics**: Top mentioned products and trends
    * **Visual Content**: Image analysis and object detection statistics
    * **Channel Activity**: Daily metrics and engagement patterns
    * **Message Search**: Full-text search across all messages
    
    ## Data Sources
    
    - CheMed123: Medical products
    - lobelia4cosmetics: Cosmetics and health products
    - tikvahpharma: Pharmaceuticals
    """,
    version="1.0.0",
    contact={
        "name": "Medical Telegram Warehouse",
        "url": "https://github.com/yourusername/medical-telegram-warehouse",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "error": str(exc)}
    )


# Include routers
app.include_router(reports.router)
app.include_router(channels.router)
app.include_router(search.router)


# Root endpoint
@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint with API information.

    Returns:
        Dictionary with API metadata
    """
    return {
        "name": "Medical Telegram Warehouse API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "reports": "/api/reports",
            "channels": "/api/channels",
            "search": "/api/search",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with system status
    """
    db_status = "connected" if test_connection() else "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.now(),
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Medical Telegram Warehouse API")

    # Test database connection
    if test_connection():
        logger.info("Database connection successful")
    else:
        logger.warning("Database connection failed")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Medical Telegram Warehouse API")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
