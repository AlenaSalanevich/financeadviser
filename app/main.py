from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import get_logger, setup_logging

setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("FinanceAdviser API starting up...")
    logger.info("Documentation available at: /docs")
    yield
    logger.info("FinanceAdviser API shutting down...")


# Create FastAPI application instance
app = FastAPI(
    title="FinanceAdviser",
    description="Production-ready Financial Advising Application using FastAPI and LangChain",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Serve frontend static assets if the dist directory exists
_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        index = _FRONTEND_DIST / "index.html"
        return FileResponse(str(index))

else:
    # Root endpoint — API-only mode (no built frontend)
    @app.get("/")
    async def root():
        """Root endpoint - API information"""
        return {
            "message": "Welcome to FinanceAdviser API",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
        }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "FinanceAdviser",
            "version": "0.1.0",
            "services": {
                "data": "/api/v1/data/health",
                "retrieval": "/api/v1/search/health",
            }
        }
    )

# Optional: Main function for running with python app/main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )