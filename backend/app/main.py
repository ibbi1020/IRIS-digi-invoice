"""
IRIS Digital Invoicing Backend API.

FastAPI application entry point with router registration and middleware configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth_router, health_router, invoices_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Runs startup and shutdown tasks.
    """
    # Startup
    # Future: Initialize database connection pool, background tasks, etc.
    yield
    # Shutdown
    # Future: Close connections, cleanup resources


app = FastAPI(
    title=settings.app_name,
    description="Backend API for submitting invoices to FBR/IRIS 2.0",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(invoices_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs" if settings.is_development else None,
    }
