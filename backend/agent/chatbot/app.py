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
    chat_router,
    conversations_router,
    documents_router,
    messages_router,
    users_router,
)

logger = logging.getLogger(__name__)
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
    logger.info("Starting AI Mentor API")
    yield
    # Shutdown
    logger.info("Shutting down AI Mentor API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Configure logfire if available (optional)
    try:
        import logfire

        logfire.configure(send_to_logfire="if-token-present")
        logfire.instrument_pydantic_ai()
    except ImportError:
        logger.info("Logfire not available, skipping instrumentation")

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

    # Instrument with logfire if available
    try:
        import logfire

        logfire.instrument_fastapi(app)
    except ImportError:
        pass

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

    # Diagnostic endpoint to test Voyage AI connectivity
    @app.get("/health/voyage", tags=["health"])
    async def voyage_health_check():
        """Test Voyage AI embedding service connectivity."""
        import asyncio
        import time

        from .services.embedding import EmbeddingService

        try:
            start = time.time()
            service = EmbeddingService()
            # Use a short test query
            embedding = await asyncio.wait_for(
                service.create_embedding("test query", input_type="query"),
                timeout=15.0,
            )
            elapsed = time.time() - start
            return {
                "status": "healthy",
                "embedding_dimension": len(embedding),
                "response_time_seconds": round(elapsed, 3),
            }
        except asyncio.TimeoutError:
            return {"status": "error", "error": "Voyage AI timeout (15s)"}
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    return app


# Create app instance
app = create_app()
