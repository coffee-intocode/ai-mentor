"""Main FastAPI application with proper architecture."""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import get_settings
from .routers import (
    ai_chat_router,
    conversations_router,
    documents_router,
    messages_router,
    users_router,
)

settings = get_settings()


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
    logging.getLogger("chatbot").setLevel(logging.INFO)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    _configure_logging()

    try:
        import haystack_ai

        haystack_ai.init(
            api_key=settings.haystack_api_key,
            endpoint="http://localhost:8080",
            environment="local",
        )
    except ImportError:
        pass

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

    # Include routers
    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(conversations_router, prefix=settings.api_v1_prefix)
    app.include_router(messages_router, prefix=settings.api_v1_prefix)
    app.include_router(documents_router, prefix=settings.api_v1_prefix)
    app.include_router(ai_chat_router, prefix=settings.api_v1_prefix)

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
