"""
SaltBitter Dating Platform - Backend API

Main FastAPI application entry point for the SaltBitter dating platform.
This is a minimal bootstrap to enable the development environment to start.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.auth import auth_router
from services.auth.rate_limiter import rate_limit_middleware
from services.profile import profile_router

# Create FastAPI application
app = FastAPI(
    title="SaltBitter API",
    description="Psychology-informed ethical dating platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Include routers
app.include_router(auth_router)
app.include_router(profile_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - API information."""
    return {
        "name": "SaltBitter API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for monitoring and Docker healthchecks."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )
