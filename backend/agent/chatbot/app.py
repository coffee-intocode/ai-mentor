"""Main FastAPI application with proper architecture."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()

import logfire
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import get_settings
from .routers import (
    ai_chat_router,
    chat_router,
    conversations_router,
    documents_router,
    messages_router,
    users_router,
)

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logfire.info("Starting AI Mentor API")
    yield
    # Shutdown
    logfire.info("Shutting down AI Mentor API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Configure logfire
    logfire.configure(send_to_logfire="if-token-present")
    logfire.instrument_pydantic_ai()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Instrument with logfire
    logfire.instrument_fastapi(app)

    # Include routers
    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(conversations_router, prefix=settings.api_v1_prefix)
    app.include_router(messages_router, prefix=settings.api_v1_prefix)
    app.include_router(documents_router, prefix=settings.api_v1_prefix)
    app.include_router(chat_router, prefix=settings.api_v1_prefix)

    # AI chat router (at /api for backward compatibility with frontend)
    app.include_router(ai_chat_router, prefix="/api")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for AWS App Runner and other services."""
        from sqlalchemy import text

        from .database import async_engine

        health_status = {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

        # Optional: Check database connectivity
        if async_engine:
            try:
                async with async_engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                health_status["database"] = "connected"
            except:
                health_status["database"] = f"error: unable to connect to database"
                # Still return 200 - app is running even if DB has issues
        else:
            health_status["database"] = "not_configured"

        return health_status

    return app


# Create app instance
app = create_app()
